import inspect
import contextlib
import sys

import pandas as pd
import typing
import pathlib

import constants
from tracing.trace_data_category import TraceDataCategory

from .optimisation import Ignore, Optimisation, TypeStableLoop


class Tracer:
    def __init__(self, project_dir: pathlib.Path):
        self.trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA).astype(
            constants.TraceData.SCHEMA
        )
        self.optimisation_stack: list[Optimisation] = list()
        self.project_dir = project_dir
        self.old_values_by_variable_by_function_name: dict[str, dict] = dict()

    def start_trace(self) -> None:
        """Starts the trace."""
        sys.settrace(self._on_trace_is_called)
        # sys.setprofile(self._on_trace_is_called)

    def stop_trace(self) -> None:
        """Stops the trace."""
        sys.settrace(None)
        self.trace_data.drop_duplicates(inplace=True, ignore_index=True)
        self.trace_data.drop(self.trace_data.tail(1).index, inplace=True)

    @contextlib.contextmanager
    def active_trace(self) -> typing.Iterator[None]:
        self.start_trace()
        try:
            yield None
        finally:
            self.stop_trace()

    def _update_optimisations(self, frame) -> None:
        ## TODO: Removal

        ## Appending
        # Check we do not trace somewhere we do not belong, e.g. Python's stdlib!
        # NOTE: De Morgan - if no optimisations are on and we are in an unwanted path OR
        # NOTE: if the newest optimisation is not the same Ignore and we are in an unwanted path
        ignore = Ignore()
        frame_path = pathlib.Path(frame.f_code.co_filename)
        if (
            not self.optimisation_stack or ignore != self.optimisation_stack[-1]
        ) and not frame_path.is_relative_to(self.project_dir):
            self.optimisation_stack.append(ignore)
            return

        # Entering a loop for the first time
        tsl = TypeStableLoop(frame)
        if not self.optimisation_stack or tsl != self.optimisation_stack[-1]:
            self.optimisation_stack.append(tsl)
            return

    def _advance_optimisation(self, frame) -> None:
        if self.optimisation_stack is not None:
            self.optimisation_stack[-1].advance(frame)
        pass

    def _apply_optimisation(self, frame) -> None:
        if self.optimisation_stack:
            self.optimisation_stack[-1].apply(frame)

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
        """Is called during execution of a function which is traced. Collects trace data from the frame."""

        self._update_optimisations(frame)
        self._apply_optimisation(frame)

        # Tracing has been toggled off for this line now, simply return
        if self.optimisation_stack and isinstance(self.optimisation_stack[-1], Ignore):
            return self._on_trace_is_called

        code = frame.f_code
        function_name = code.co_name

        file_name = pathlib.Path(code.co_filename).relative_to(self.project_dir)
        line_number = frame.f_lineno

        names2types, category = None, None
        if event == "call":
            names2types = self._on_call(frame, arg)
            category = TraceDataCategory.FUNCTION_ARGUMENT

        elif event == "return":
            names2types = self._on_return(frame, arg)
            category = TraceDataCategory.FUNCTION_RETURN

            # Adds tracing data of class members if the return is from a class function.
            if _is_frame_within_class_function(frame):
                names2types2 = self._on_class_function_return(frame)
                category2 = TraceDataCategory.CLASS_MEMBER
                self._update_trace_data_with(file_name, function_name, line_number, category2, names2types2)

        elif event == "line":
            names2types = self._on_line(frame)
            category = TraceDataCategory.LOCAL_VARIABLE

        elif event == "exception":
            pass

        # NOTE: If there is any error occurred in the trace function, it will be unset, just like settrace(None) is called.
        # NOTE: therefore, throwing an exception does not work, as the trace function will simply be unset

        if names2types and category:
            self._update_trace_data_with(
                file_name, function_name, line_number, category, names2types
            )

        self.old_values_by_variable_by_function_name[
            function_name
        ] = frame.f_locals.copy()

        self._advance_optimisation(frame)
        return self._on_trace_is_called

    def _update_trace_data_with(
            self,
            file_name: pathlib.Path,
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
    old_values_by_variable: dict[str, typing.Any],
    new_values_by_variable: dict[str, typing.Any],
) -> dict[str, typing.Any]:
    """Gets the new defined variable from one frame to the next frame."""
    names2types = {}
    for item in new_values_by_variable.items():
        variable_name, variable_value = item[0], item[1]
        if variable_name not in old_values_by_variable:
            names2types[variable_name] = type(variable_value)
    return names2types


def _is_frame_within_class_function(frame) -> bool:
    code = frame.f_code
    function_name = code.co_name
    all_possible_classes = [value for value in frame.f_globals.values() if inspect.isclass(value)]
    for possible_class in all_possible_classes:
        if hasattr(possible_class, function_name):
            member = getattr(possible_class, function_name)
            if not inspect.isfunction(member):
                continue

            if member.__code__ == code:
                return True

    return False
