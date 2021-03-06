import contextlib
import logging
import inspect
import sys

import pandas as pd
import typing
import pathlib

import constants
from tracing.trace_data_category import TraceDataCategory

from .optimisation import (
    TriggerStatus,
    FrameWithMetadata,
    Ignore,
    Optimisation,
    TypeStableLoop,
)


logger = logging.getLogger(__name__)


class Tracer:
    def __init__(self, project_dir: pathlib.Path):
        self.trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA).astype(
            constants.TraceData.SCHEMA
        )
        self.project_dir = project_dir

        self.optimisation_stack: list[Optimisation] = list()
        self.old_values_by_variable_by_function_name: dict[str, dict] = dict()

    def start_trace(self) -> None:
        """Starts the trace."""
        logger.info("Starting trace")
        sys.settrace(self._on_trace_is_called)
        # sys.setprofile(self._on_trace_is_called)

    def stop_trace(self) -> None:
        """Stops the trace."""
        # Clear out all optimisations
        self.optimisation_stack = list()

        logger.info("Stopping trace")
        sys.settrace(None)

        # Drop all references to the tracer
        self.trace_data = self.trace_data.drop_duplicates(ignore_index=True)
        self.trace_data = self.trace_data[
            self.trace_data[constants.TraceData.CLASS] != Tracer
        ]

    @contextlib.contextmanager
    def active_trace(self) -> typing.Iterator[None]:
        self.start_trace()
        try:
            yield None
        finally:
            self.stop_trace()

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
            if not frame_path.is_relative_to(self.project_dir):
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

    def _on_call(self, frame, arg: typing.Any) -> dict[str, type]:
        names2types = {
            var_name: type(var_value) for var_name, var_value in frame.f_locals.items()
        }

        return names2types

    def _on_return(self, frame, arg: typing.Any) -> dict[str, type]:
        code = frame.f_code
        function_name = code.co_name
        names2types = {function_name: type(arg)}
        return names2types

    def _on_line(self, frame) -> dict[str, type]:
        code = frame.f_code
        function_name = code.co_name
        names2types = _get_new_defined_local_variables_with_types(
            self.old_values_by_variable_by_function_name[function_name], frame.f_locals
        )
        return names2types

    def _on_class_function_return(self, frame) -> dict[str, type]:
        """Updates the trace data with the members of the class object."""
        first_element_name = next(iter(frame.f_locals))
        self_object = frame.f_locals[first_element_name]
        return self._evaluate_object(self_object)

    def _evaluate_object(self, class_object: typing.Any) -> dict[str, type]:
        object_dict = class_object.__dict__
        names2types = {
            var_name: type(var_value) for var_name, var_value in object_dict.items()
        }
        return names2types

    def _on_trace_is_called(self, frame, event, arg: typing.Any) -> typing.Callable:
        """Called during execution of a function which is traced. Collects trace data from the frame."""
        # Ignore out of project files
        if not pathlib.Path(frame.f_code.co_filename).is_relative_to(self.project_dir):
            return self._on_trace_is_called

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

        file_name = pathlib.Path(code.co_filename).relative_to(self.project_dir)
        line_number = frame.f_lineno

        names2types, category = None, None
        frameinfo = inspect.getframeinfo(frame)

        if event == "call":
            logger.info(f"Tracing call: {frameinfo}")
            names2types = self._on_call(frame, arg)
            category = TraceDataCategory.FUNCTION_ARGUMENT

        elif event == "return":
            logger.info(f"Tracing return: {frameinfo}")
            names2types = self._on_return(frame, arg)
            category = TraceDataCategory.FUNCTION_RETURN

            # Special case
            line_number = 0

            # Adds tracing data of class members if the return is from a class function.
            if possible_class is not None:
                names2types2 = self._on_class_function_return(frame)
                category2 = TraceDataCategory.CLASS_MEMBER
                self._update_trace_data_with(
                    file_name, possible_class, "", 0, category2, names2types2
                )
                # Line number is 0 and function name is empty to unify matching class members more easily.

        elif event == "line":
            logger.info(f"Tracing line: {frameinfo}")
            names2types = self._on_line(frame)
            category = TraceDataCategory.LOCAL_VARIABLE

        elif event == "exception":
            logger.info(f"Skipping exception: {frameinfo}")
            pass

        # NOTE: If there is any error occurred in the trace function, it will be unset, just like settrace(None) is called.
        # NOTE: therefore, throwing an exception does not work, as the trace function will simply be unset

        if names2types and category:
            logger.debug(f"{event}: {names2types} {category}")
            self._update_trace_data_with(
                file_name,
                possible_class,
                function_name,
                line_number,
                category,
                names2types,
            )

        self.old_values_by_variable_by_function_name[
            function_name
        ] = frame.f_locals.copy()

        return self._on_trace_is_called

    def _update_trace_data_with(
        self,
        file_name: pathlib.Path,
        class_type: type | None,
        function_name: str,
        line_number: int,
        category: TraceDataCategory,
        names2types: dict[str, type],
    ) -> None:
        """
        Constructs a DataFrame from the provided arguments, and appends
        it to the existing trace data collection.

        @param file_name The file name in which the variables are declared.
        @param function_name The function which declares the variable.
        @param names2types A dictionary containing the variable name and its type.
        @param line_number The line number.
        @param category The data category of the row.
        """
        varnames = list(names2types.keys())
        vartypes = list(names2types.values())

        d = {
            constants.TraceData.FILENAME: [str(file_name)] * len(varnames),
            constants.TraceData.CLASS: [class_type] * len(varnames),
            constants.TraceData.FUNCNAME: [function_name] * len(varnames),
            constants.TraceData.VARNAME: varnames,
            constants.TraceData.VARTYPE: vartypes,
            constants.TraceData.LINENO: [line_number] * len(varnames),
            constants.TraceData.CATEGORY: [category] * len(varnames),
        }
        update = pd.DataFrame(d).astype(constants.TraceData.SCHEMA)
        self.trace_data = pd.concat(
            [self.trace_data, update], ignore_index=True
        ).astype(constants.TraceData.SCHEMA)


def _get_new_defined_local_variables_with_types(
    old_values_by_variable: dict[str, str],
    new_values_by_variable: dict[str, str],
) -> dict[str, type]:
    """Gets the new defined variable from one frame to the next frame."""
    names2types = {}
    for item in new_values_by_variable.items():
        variable_name, variable_value = item[0], item[1]
        if variable_name not in old_values_by_variable:
            names2types[variable_name] = type(variable_value)
    return names2types


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
