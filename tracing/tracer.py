import contextlib
import sys

import pandas as pd
import typing
import pathlib

import constants
from tracing.trace_data_category import TraceDataCategory


class Tracer:
    def __init__(self, project_dir: pathlib.Path):
        self.trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA).astype(
            constants.TraceData.SCHEMA
        )
        self.project_dir = project_dir
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

    @contextlib.contextmanager
    def active_trace(self) -> None:
        self.start_trace()
        try:
            yield None
        finally:
            self.stop_trace()

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
        names2types = _get_new_defined_local_variables_with_types(
            self.old_values_by_variable_by_function_name[function_name], frame.f_locals)
        return names2types

    def _on_trace_is_called(self, frame, event, arg: any) -> typing.Callable:
        """Is called during execution of a function which is traced. Collects trace data from the frame."""

        code = frame.f_code
        function_name = code.co_name

        # Check we do not trace somewhere we do not belong, e.g. Python's stdlib!
        full_path = pathlib.Path(code.co_filename)
        if not full_path.is_relative_to(self.project_dir):
            return self._on_trace_is_called

        file_name = pathlib.Path(code.co_filename).relative_to(self.project_dir)
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

        elif event == "exception":
            pass

        else:
            self.stop_trace()
            print("The event " + str(event) + " is unknown.")
            # Note: The value error does not stop the program for some reason.
            raise ValueError("The event" + str(event) + " is unknown.")

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


def _get_new_defined_local_variables_with_types(
    old_values_by_variable: dict[str, any], new_values_by_variable: dict[str, any]
) -> dict[str, any]:
    """Gets the new defined variable from one frame to the next frame."""
    names2types = {}
    for item in new_values_by_variable.items():
        variable_name, variable_value = item[0], item[1]
        if variable_name not in old_values_by_variable:
            names2types[variable_name] = type(variable_value)
    return names2types
