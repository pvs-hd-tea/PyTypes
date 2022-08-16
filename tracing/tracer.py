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

import constants
from tracing.resolver import Resolver
from tracing.trace_data_category import TraceDataCategory

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
        self.trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA).astype(
            constants.TraceData.SCHEMA
        )

        self.proj_path = proj_path
        self.stdlib_path = stdlib_path
        self.venv_path = venv_path

        self._resolver = Resolver(self.stdlib_path, self.proj_path, self.venv_path)

        # Map of a function name to the variables in that functions scope
        self.old_vars: dict[str, dict[str, typing.Any]] = dict()

        # stack based in order to hold previous line when returning
        self._prev_line: list[int] = list()

        self.class_names_to_drop = [TracerBase.__name__]
        self.function_names_to_drop = [
            self.stop_trace.__name__,
            self.start_trace.__name__,
            self.active_trace.__name__,
        ]

    def start_trace(self) -> None:
        """Starts the trace."""
        logger.info("Starting trace")
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
        sys.settrace(None)

        # Drop all references to the tracer
        self.trace_data = self.trace_data.drop_duplicates(ignore_index=True)

        drop_masks = [
            self.trace_data[constants.TraceData.CLASS].isin(self.class_names_to_drop),
            self.trace_data[constants.TraceData.FUNCNAME].isin(
                self.function_names_to_drop
            ),
        ]
        td_drop = self.trace_data[functools.reduce(operator.and_, drop_masks)]
        self.trace_data = self.trace_data.drop(td_drop.index)

        self.trace_data = self.trace_data.astype(constants.TraceData.SCHEMA)

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
        # Check we do not trace somewhere we do not belong, e.g. Python's stdlib!
        # NOTE: De Morgan - if no optimisations are on and we are in an unwanted path OR
        # NOTE: if the newest optimisation is not a currently active Ignore and we are in an unwanted path
        ignore = Ignore(fwm)
        frame_path = pathlib.Path(fwm.co_filename)
        if not self.optimisation_stack or not isinstance(
            self.optimisation_stack[-1], Ignore
        ):
            if not frame_path.is_relative_to(self.proj_path):
                logger.debug(f"Applying Ignore for {inspect.getframeinfo(fwm._frame)}")
                self.optimisation_stack.append(ignore)
                return

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

    def _on_call(self, frame, _: typing.Any) -> dict[str, tuple[str | None, str]]:
        names2types = dict()

        for name, value in frame.f_locals.items():
            modname = self._resolver.get_module_and_name(type(value))
            if modname is None:
                self._on_non_importable(type(value))
            names2types[name] = modname

        return names2types

    def _on_return(self, frame, arg: typing.Any) -> dict[str, tuple[str | None, str]]:
        code = frame.f_code
        function_name = code.co_name

        modname = self._resolver.get_module_and_name(type(arg))
        if modname is None:
            self._on_non_importable(type(arg))
        names2types = {function_name: modname}

        return names2types

    def _on_line(self, frame) -> dict[str, tuple[str | None, str]]:
        code = frame.f_code
        function_name = code.co_name
        names2types = self._get_new_defined_local_variables_with_types(
            self.old_vars[function_name],
            frame.f_locals,
        )
        return names2types

    def _on_class_function_return(self, frame) -> dict[str, tuple[str | None, str]]:
        """Updates the trace data with the members of the class object."""
        first_element_name = next(iter(frame.f_locals), None)
        if first_element_name is None:
            return dict()
        self_object = frame.f_locals[first_element_name]
        return self._evaluate_object(self_object)

    def _evaluate_object(
        self, class_object: typing.Any
    ) -> dict[str, tuple[str | None, str]]:
        names2types = dict()

        object_dict = class_object.__dict__
        for name, value in object_dict.items():
            modname = self._resolver.get_module_and_name(type(value))
            if modname is None:
                self._on_non_importable(type(value))
            names2types[name] = modname

        return names2types

    def _on_trace_is_called(self, frame, event, arg: typing.Any) -> typing.Callable:
        """Called during execution of a function which is traced. Collects trace data from the frame."""
        # Ignore out of project files
        if not pathlib.Path(frame.f_code.co_filename).is_relative_to(self.proj_path):
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

        code = frame.f_code
        function_name = code.co_name
        possible_class = _get_class_in_frame(frame)

        if possible_class is not None:
            modname = self._resolver.get_module_and_name(possible_class)
            if modname is None:
                self._on_non_importable(possible_class)
            class_module, class_name = modname
        else:
            class_module, class_name = None, None

        file_name = pathlib.Path(code.co_filename).relative_to(self.proj_path)
        line_number = frame.f_lineno

        names2types, category = None, None
        frameinfo = inspect.getframeinfo(frame)

        if event == "call":
            self._prev_line.append(line_number)
            logger.info(f"Tracing call: {frameinfo}")
            names2types = self._on_call(frame, arg)
            category = TraceDataCategory.FUNCTION_PARAMETER

        elif event == "return":
            logger.info(f"Tracing return: {frameinfo}")
            names2types = self._on_return(frame, arg)
            category = TraceDataCategory.FUNCTION_RETURN

            # Remove from storage
            self.old_vars.pop(function_name)
            self._prev_line.pop()

            # Special case
            line_number = 0

            # Adds tracing data of class members if the return is from a class function.
            if possible_class is not None:
                names2types2 = self._on_class_function_return(frame)
                category2 = TraceDataCategory.CLASS_MEMBER

                # Line number is 0 and function name is empty to
                # unify matching class members more better.

                # Class Members contain state and can theoretically, at any time, on the same line, be of many types

                self._update_trace_data_with(
                    file_name,
                    class_module,
                    class_name,
                    "",
                    0,
                    category2,
                    names2types2,
                )

        elif event == "line":
            line_number, self._prev_line[-1] = self._prev_line[-1], line_number
            logger.info(f"Tracing line: {frameinfo}")
            names2types = self._on_line(frame)
            category = TraceDataCategory.LOCAL_VARIABLE

        logger.debug(
            f"{event} @ {line_number} {names2types or 'NO NEW TYPES'} {category or 'NO CATEGORY'}"
        )
        if names2types and category:
            self._update_trace_data_with(
                file_name,
                class_module,
                class_name,
                function_name,
                line_number,
                category,
                names2types,
            )

        self.old_vars[function_name] = frame.f_locals.copy()
        if self.apply_opts:
            self.trace_data = self.trace_data.drop_duplicates()
        return self._on_trace_is_called

    def _update_trace_data_with(
        self,
        file_name: pathlib.Path,
        class_module: str | None,
        class_name: str | None,
        function_name: str | None,
        line_number: int,
        category: TraceDataCategory,
        names2types: dict[str, tuple[str | None, str]],
    ) -> None:
        """
        Constructs a DataFrame from the provided arguments, and appends
        it to the existing trace data collection.

        @param file_name The file name in which the variables are declared.
        @param class_module Module of the class the variable is in
        @param class_name Name of the class the variable is in
        @param function_name The function which declares the variable.
        @param line_number The line number.
        @param category The data category of the row.
        @param names2types A dictionary containing the variable name, the type's module and the type's name.
        """
        varnames = list(names2types.keys())

        vartype_modules = list(map(operator.itemgetter(0), names2types.values()))
        vartypes = list(map(operator.itemgetter(1), names2types.values()))

        d = {
            constants.TraceData.FILENAME: [str(file_name)] * len(varnames),
            constants.TraceData.CLASS_MODULE: [class_module] * len(varnames),
            constants.TraceData.CLASS: [class_name] * len(varnames),
            constants.TraceData.FUNCNAME: [function_name] * len(varnames),
            constants.TraceData.LINENO: [line_number] * len(varnames),
            constants.TraceData.CATEGORY: [category] * len(varnames),
            constants.TraceData.VARNAME: varnames,
            constants.TraceData.VARTYPE_MODULE: vartype_modules,
            constants.TraceData.VARTYPE: vartypes,
        }
        update = pd.DataFrame(d).astype(constants.TraceData.SCHEMA)

        self.trace_data = pd.concat(
            [self.trace_data, update], ignore_index=True
        ).astype(constants.TraceData.SCHEMA)

    def _get_new_defined_local_variables_with_types(
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
