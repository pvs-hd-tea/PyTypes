import sys

import pandas as pd
import typing
import pathlib

import constants
from tracing.trace_data_category import TraceDataCategory


class Tracer:
    def __init__(self, base_directory: pathlib.Path):
        self.trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA).astype(
            constants.TraceData.SCHEMA
        )
        self.basedir = base_directory
        self.old_values_by_variable_by_function_name = {}
        self._reset_members()

    def start_trace(self) -> None:
        """Resets the trace values and starts the trace."""
        self._reset_members()
        sys.settrace(self._on_trace_is_called)

    def stop_trace(self) -> None:
        """Stops the trace."""
        sys.settrace(None)
        self.trace_data.drop_duplicates(inplace=True, ignore_index=True)
        self.trace_data.drop(self.trace_data.tail(1).index, inplace=True) # Last row is trace data of stoptrace.

    def _reset_members(self) -> None:
        """Resets the variables of the tracer."""
        self.trace_data = pd.DataFrame(
            columns=constants.TraceData.SCHEMA.keys()
        ).astype(constants.TraceData.SCHEMA)
        self.old_values_by_variable_by_function_name = {}

    def _on_call(self, frame, arg: typing.Any) -> dict[str, type]:
        names2types = {
            var_name: type(var_value) for var_name, var_value in frame.f_locals.items()
        }
        return names2types

    def _on_return(self, frame, arg: typing.Any) -> dict[str, type]:
        code = frame.f_code
        function_name = code.co_name
        return {function_name: type(arg)}

    def _on_line(self, frame) -> dict[str, type]:
        code = frame.f_code
        function_name = code.co_name
        local_variable_name, local_variable_value = _get_new_defined_variable(
            self.old_values_by_variable_by_function_name[function_name], frame.f_locals
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
            self._update_trace_data_with(
                file_name, function_name, line_number, category, names2types
            )

        self.old_values_by_variable_by_function_name[function_name] = frame.f_locals.copy()
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
        update = pd.DataFrame.from_dict(d).astype(constants.TraceData.SCHEMA)
        self.trace_data = pd.concat(
            [self.trace_data, update], ignore_index=True
        ).astype(constants.TraceData.SCHEMA)


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
