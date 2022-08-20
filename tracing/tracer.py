from __future__ import annotations

import abc
import contextlib
import functools
import logging
import inspect
import operator
import sys

import pandas as pd
import typing
import pathlib

from constants import Column, Schema
from tracing.resolver import Resolver
from tracing.trace_data_category import TraceDataCategory
from tracing.trace_update import BatchTraceUpdate, TraceUpdate

from .optimisation import (
    TriggerStatus,
    FrameWithMetadata,
    Ignore,
    Optimisation,
    TypeStableLoop,
)


logger = logging.getLogger(__name__)


class TracerBase(abc.ABC):
    def __init__(
        self,
        proj_path: pathlib.Path,
        stdlib_path: pathlib.Path,
        venv_path: pathlib.Path,
    ):
        self.trace_data = pd.DataFrame(columns=Schema.TraceData.keys()).astype(
            Schema.TraceData
        )

        self.proj_path = proj_path
        self.stdlib_path = stdlib_path
        self.venv_path = venv_path

        self._resolver = Resolver(self.stdlib_path, self.proj_path, self.venv_path)

        # Map of a function name to the variables in that functions scope
        self.old_local_vars: dict[str, dict[str, typing.Any]] = dict()

        # Map of filename to the global variables in that variable's scope
        self.old_global_vars: dict[str, dict[str, typing.Any]] = dict()

        # stack based in order to hold previous line when returning
        self._prev_line: list[int] = list()

        self.class_names_to_drop = [TracerBase.__name__]
        self.function_names_to_drop = [
            self.stop_trace.__name__,
            self.start_trace.__name__,
            self.active_trace.__name__,
        ]

        self._old_trace: typing.Callable | None = None

    def start_trace(self) -> None:
        """Starts the trace."""
        logger.info("Starting trace")
        self._old_trace = sys.gettrace()
        sys.settrace(self._on_trace_is_called)
        self._prev_line.clear()

    @contextlib.contextmanager
    def active_trace(self) -> typing.Iterator[None]:
        self.start_trace()
        try:
            yield None
        finally:
            self.stop_trace()

    def stop_trace(self):
        logger.info("Stopping trace")
        sys.settrace(self._old_trace)

        # Drop all references to the tracer
        self.trace_data = self.trace_data.drop_duplicates(ignore_index=True)

        drop_masks = [
            self.trace_data[Column.CLASS].isin(self.class_names_to_drop),
            self.trace_data[Column.FUNCNAME].isin(self.function_names_to_drop),
        ]
        td_drop = self.trace_data[functools.reduce(operator.and_, drop_masks)]
        self.trace_data = self.trace_data.drop(td_drop.index)

        self.trace_data = self.trace_data.astype(Schema.TraceData)

    @abc.abstractmethod
    def _on_trace_is_called(self, frame, event, arg: typing.Any) -> typing.Callable:
        pass


class NoOperationTracer(TracerBase):
    def _on_trace_is_called(self, frame, event, arg: typing.Any) -> typing.Callable:
        return self._on_trace_is_called


class Tracer(TracerBase):
    def __init__(
        self,
        proj_path: pathlib.Path,
        stdlib_path: pathlib.Path,
        venv_path: pathlib.Path,
        apply_opts=True,
    ):
        super().__init__(proj_path, stdlib_path, venv_path)
        self.class_names_to_drop.append(Tracer.__name__)
        self.apply_opts = apply_opts

        if self.apply_opts:
            self.optimisation_stack: list[Optimisation] = list()

    def stop_trace(self) -> None:
        """Stops the trace."""
        # Clear out all optimisations
        if self.apply_opts:
            self.optimisation_stack.clear()

        super().stop_trace()

    def _update_optimisations(self, fwm: FrameWithMetadata) -> None:
        """Remove optimisations that are marked as TriggerStatus.EXITED, and insert new ones as needed."""
        # Remove dead optimisations
        while self.optimisation_stack:
            top = self.optimisation_stack[-1]
            if top.status() == TriggerStatus.EXITED:
                logger.debug(
                    f"Removing {self.optimisation_stack[-1].__class__.__name__} from optimisations"
                )
                self.optimisation_stack.pop()
            else:
                break

        # Appending; only one optimisation at a time
        # Entering a loop for the first time
        if not self.optimisation_stack or not isinstance(
            self.optimisation_stack[-1], TypeStableLoop
        ):
            if fwm.is_for_loop():
                logger.debug(
                    f"Applying TypeStableLoop for {inspect.getframeinfo(fwm._frame)}"
                )
                tsl = TypeStableLoop(fwm)
                if not self.optimisation_stack or tsl != self.optimisation_stack[-1]:
                    self.optimisation_stack.append(tsl)
                    return

    def _advance_optimisations(self, fwm: FrameWithMetadata) -> None:
        for optimisation in self.optimisation_stack:
            optimisation.advance(fwm, self.trace_data)

    def _on_call(self, frame, batch: BatchTraceUpdate) -> BatchTraceUpdate:
        names2types = dict()

        for name, value in frame.f_locals.items():
            modname = self._resolver.get_module_and_name(type(value))
            if modname is None:
                self._on_non_importable(type(value))
            names2types[name] = modname

        return batch.parameters(names2types)

    def _on_return(
        self, frame, arg: typing.Any, batch: BatchTraceUpdate
    ) -> BatchTraceUpdate:
        code = frame.f_code
        function_name = code.co_name

        modname = self._resolver.get_module_and_name(type(arg))
        if modname is None:
            self._on_non_importable(type(arg))
        names2types = {function_name: modname}

        return batch.returns(names2types)

    def _on_line(
        self, frame, real_line_number: int, batch: BatchTraceUpdate
    ) -> BatchTraceUpdate:
        local_names2types = self._get_new_defined_variables_with_types(
            self.old_local_vars[frame.f_code.co_name],
            frame.f_locals,
        )
        with_local = batch.local_variables(
            line_number=real_line_number, names2types=local_names2types
        )

        global_names2types = self._get_new_defined_variables_with_types(
            self.old_global_vars[frame.f_code.co_filename],
            frame.f_globals,
        )
        with_global = with_local.global_variables(global_names2types)

        return with_global

    def _on_class_function_return(
        self, frame, batch: BatchTraceUpdate
    ) -> BatchTraceUpdate:
        """Updates the trace data with the members of the class object."""
        first_element_name = next(iter(frame.f_locals), None)
        if first_element_name is None:
            return batch
        
        class_object = frame.f_locals[first_element_name]
        names2types = dict()

        object_dict = class_object.__dict__
        for name, value in object_dict.items():
            modname = self._resolver.get_module_and_name(type(value))
            if modname is None:
                self._on_non_importable(type(value))
            names2types[name] = modname

        return batch.members(names2types)

    def _on_trace_is_called(self, frame, event, arg: typing.Any) -> typing.Callable:
        """Called during execution of a function which is traced. Collects trace data from the frame."""
        # Ignore out of project files
        file_name = pathlib.Path(frame.f_code.co_filename)

        if not file_name.is_relative_to(self.proj_path):
            return self._on_trace_is_called

        if self.apply_opts:
            fwm = FrameWithMetadata(frame)

            self._advance_optimisations(fwm)
            self._update_optimisations(fwm)

            # Tracing has been toggled off for this line now, simply return
            if any(
                opt.status() in Optimisation.OPTIMIZING_STATES
                for opt in self.optimisation_stack
            ):
                return self._on_trace_is_called

        function_name = frame.f_code.co_name
        enclosing_class = _get_class_in_frame(frame)

        if enclosing_class is not None:
            modname = self._resolver.get_module_and_name(enclosing_class)
            if modname is None:
                self._on_non_importable(enclosing_class)
            class_module, class_name = modname
        else:
            class_module, class_name = None, None

        file_name = file_name.relative_to(self.proj_path)
        line_number = frame.f_lineno

        frameinfo = inspect.getframeinfo(frame)

        batch = BatchTraceUpdate(
            file_name=file_name,
            class_module=class_module,
            class_name=class_name,
            function_name=function_name,
            line_number=line_number,
        )

        if event == "call":
            logger.info(f"Tracing call: {frameinfo}")

            # Add to storage
            self.old_local_vars[function_name] = dict()
            self.old_global_vars[frame.f_code.co_filename] = dict()
            self._prev_line.append(line_number)

            
            batch = self._on_call(frame, batch)

        elif event == "return":
            logger.info(f"Tracing return: {frameinfo}")

            # Catch locals and globals that are changed on last line
            line_number = self._prev_line[-1]
            batch = self._on_line(frame, line_number, batch)

            # Adds tracing data of class members if the return is from a class function / method.
            if enclosing_class is not None:
                batch = self._on_class_function_return(frame, batch)

            batch = self._on_return(frame, arg, batch)

            # Remove from storage
            self.old_local_vars.pop(function_name)
            self.old_global_vars.pop(frame.f_code.co_filename)
            self._prev_line.pop()

        elif event == "line":
            line_number, self._prev_line[-1] = self._prev_line[-1], line_number
            logger.info(f"Tracing line: {frameinfo}")
            batch = self._on_line(frame, line_number, batch)

        self._update_trace_data_with(batch)

        self.old_local_vars[function_name] = frame.f_locals.copy()
        self.old_global_vars[frame.f_code.co_filename] = frame.f_globals.copy()
        if self.apply_opts:
            self.trace_data = self.trace_data.drop_duplicates()

        return self._on_trace_is_called

    def _update_trace_data_with(self, batch_update: BatchTraceUpdate) -> None:
        """
        Constructs a DataFrame from the provided updates, and appends
        it to the existing trace data collection.
        """

        batch = batch_update.to_frame()
        if batch.empty:
            return
        self.trace_data = pd.concat([self.trace_data, batch], ignore_index=True).astype(
            Schema.TraceData
        )

    def _get_new_defined_variables_with_types(
        self,
        prev_vars2vals: dict[str, typing.Any],
        new_vars2vals: dict[str, typing.Any],
    ) -> dict[str, tuple[str | None, str]]:
        """Gets the new defined variable from one frame to the next frame."""
        names2types = {}

        for name, value in new_vars2vals.items():
            if name not in prev_vars2vals or value != prev_vars2vals[name]:
                valt = type(value)
                modname = self._resolver.get_module_and_name(valt)
                if modname is None:
                    self._on_non_importable(valt)
                names2types[name] = modname

        return names2types

    def _on_non_importable(self, ty: type) -> typing.NoReturn:
        raise ImportError(
            f"Failed to import {ty} from {self.stdlib_path}, {self.venv_path}, {self.proj_path}"
        )


def _get_class_in_frame(frame) -> type | None:
    code = frame.f_code
    function_name = code.co_name
    all_possible_classes = filter(inspect.isclass, frame.f_globals.values())
    for possible_class in all_possible_classes:
        if hasattr(possible_class, function_name):
            member = getattr(possible_class, function_name)
            if not inspect.isfunction(member):
                continue

            if member.__code__ == code:
                return possible_class

    return None
