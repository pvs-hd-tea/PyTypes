import sys

import pandas as pd
import typing
import pathlib

import constants
from tracing.trace_data_category import TraceDataCategory


class Tracer:
    def __init__(self, base_directory: pathlib.Path):
        self.trace_data = pd.DataFrame(columns=constants.TRACE_DATA_COLUMNS)
        self.basedir = base_directory
        self.function_name = ""
        self.old_values_by_variable = {}

    def start_trace(self, function_name: str) -> None:
        """Resets the trace values, starts the trace and infers the types of variables of the provided function name
        argument."""
        if not isinstance(function_name, str):
            raise TypeError()

        self._reset_members()
        sys.settrace(self._on_trace_is_called)
        self.function_name = function_name

    def stop_trace(self) -> None:
        """Stops the trace."""
        sys.settrace(None)

    def _reset_members(self) -> None:
        """Resets the variables of the tracer."""
        self.trace_data = pd.DataFrame(columns=constants.TRACE_DATA_COLUMNS)

    def _on_call(self, frame, arg: typing.Any) -> dict[str, type]:
        names2types = {
            var_name: type(var_value) for var_name, var_value in frame.f_locals.items()
        }
        return names2types

    def _on_return(self, frame, arg: typing.Any) -> dict[None, type]:
        code = frame.f_code
        function_name = code.co_name
        return {function_name: type(arg)}

    def _on_line(self, frame) -> dict[str, type]:
        local_variable_name, local_variable_value = _get_new_defined_variable(
            self.old_values_by_variable, frame.f_locals
        )
        if local_variable_name:
            class_name_of_return_value = type(local_variable_value)
            names2types = {local_variable_name: class_name_of_return_value}
            return names2types

        return dict()

    def _on_trace_is_called(self, frame, event, arg: any) -> typing.Callable:
        """Is called during execution of a function which is traced. Collects trace data from the frame."""
        code = frame.f_code
        function_name = code.co_name

        # TODO: What does this do? and why do we need it @RecurvedBow ->
        #  Because the dictionary containing the local variables changes/is a different dictionary compared
        #  to the one of the previous frame when calling an inner function.
        #  An improvement is worked on (See #20)
        if function_name != self.function_name:
            return self._on_trace_is_called

        file_name = pathlib.Path(code.co_filename).relative_to(self.basedir)
        line_number = frame.f_lineno

        names2types, category = None, None
        if event == "call":
            names2types = self._on_call(frame, arg)
            category = TraceDataCategory.FUNCTION_ARGUMENT

        elif event == "return":
            names2types = self._on_return(frame, arg)
            category = TraceDataCategory.FUNCTION_RETURN

        elif event == "line":
            names2types = self._on_line(frame)
            category = TraceDataCategory.LOCAL_VARIABLE

        if names2types:
            self._update_trace_data_with(file_name, function_name, line_number, category, names2types)

        self.old_values_by_variable = frame.f_locals.copy()
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
        Constructs a DataFrame from the provided arguments.

        @param file_name The file name in which the variables are declared.
        @param function_name The function which declares the variable.
        @param names2types A dictionary containing the variable name and its type.
        @param line_number The line number.
        @param category The data category of the row.
        """
        for variable_name in names2types.keys():
            variable_type = names2types[variable_name]
            row_to_append = [file_name, function_name, line_number, category, variable_name, variable_type]
            self.trace_data.loc[len(self.trace_data)] = row_to_append


def _get_new_defined_variable(
        old_values_by_variable: dict[str, any], new_values_by_variable: dict[str, any]
) -> tuple[str, any]:
    """Gets the new defined variable from one frame to the next frame."""
    local_variable_name = None
    local_variable_value = None
    for item in new_values_by_variable.items():
        variable_name, variable_value = item[0], item[1]
        if variable_name not in old_values_by_variable:
            # A new local variable has been defined.
            if local_variable_name:
                # A already new local variable has been found in this frame.
                # Todo: Implement how multiple definitions of local variables are handled.
                return None, None

            local_variable_name = variable_name
            local_variable_value = variable_value
    return local_variable_name, local_variable_value
