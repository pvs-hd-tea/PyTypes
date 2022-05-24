import sys
from pathlib import Path

import pandas as pd
import typing

import pathlib

import constants
from tracing.trace_data_category import TraceDataCategory


class Tracer:
    def __init__(self, base_directory: pathlib.Path):
        self.trace_data = pd.DataFrame(columns=constants.TRACE_DATA_COLUMNS)
        self.basedir = base_directory

    def reset_members(self) -> None:
        """Resets the variables of the tracer."""
        self.trace_data = pd.DataFrame(columns=constants.TRACE_DATA_COLUMNS)

    def start_trace(self, function_name: str) -> None:
        """Resets the trace values, starts the trace and infers the types of variables of the provided function name
        argument."""
        if not isinstance(function_name, str):
            raise TypeError()

        sys.settrace(self.on_trace_is_called)
        self.function_name = function_name

    def stop_trace(self) -> None:
        """Stops the trace."""
        sys.settrace(None)

    def _on_call(self, frame, arg: typing.Any) -> dict[str, type]:
        names2types = {
            var_name: type(var_value) for var_name, var_value in frame.f_locals.items()
        }
        return names2types

    def _on_return(self, frame, arg: typing.Any) -> dict[None, type]:
        # TODO: We must find an identifier for this. Otherwise multiple returns cannot be disambiguated,
        # TODO: which is problematic if different types are returned!
        return {None: type(arg)}

    def _on_line(self, frame) -> dict[str, type]:
        local_variable_name, local_variable_value = _get_new_defined_variable(
            self.old_values_by_variable, frame.f_locals
        )
        if local_variable_name:
            class_name_of_return_value = type(local_variable_value)
            names2types = {local_variable_name: class_name_of_return_value}
            return names2types

        return dict()

    def on_trace_is_called(self, frame, event, arg: any) -> typing.Callable:
        """Is called during execution of a function which is traced. Collects trace data from the frame."""
        code = frame.f_code
        function_name = code.co_name

        # TODO: What does this do? and why do we need it @RecurvedBow
        if function_name != self.function_name:
            return self.on_trace_is_called

        file_name = pathlib.Path(code.co_filename).relative_to(self.basedir)
        line_number = frame.f_lineno

        if event == "call":
            names2types = self._on_call(frame, arg)
            category = TraceDataCategory.FUNCTION_ARGUMENT

        elif event == "return":
            names2types = self._on_return(frame, arg)
            category = TraceDataCategory.FUNCTION_RETURN

        elif event == "line":
            names2types = self._on_line(frame)
            category = TraceDataCategory.LOCAL_VARIABLE

        else:
            names2types, category = None, None

        if names2types:
            df = _build_frame_from(
                file_name, function_name, names2types, line_number, category
            )
            self.trace_data = pd.concat((self.trace_data, df), ignore_index=True)

        self.old_values_by_variable = frame.f_locals.copy()
        return self.on_trace_is_called


def _build_frame_from(
    filename: pathlib.Path,
    function_name: str,
    names2types: dict[str | None, type],
    line_number: int,
    category: TraceDataCategory,
) -> pd.DataFrame:
    """
    Construct a DataFrame from the information passed

    @param filename which file the variables were found in
    @param function_name in which function the variables were found in
    @param names2types a mapping of
    """

    varnames = list(names2types.keys())
    vartypes = list(names2types.values())

    d = {
        constants.TraceData.FILENAME: [str(filename)] * len(varnames),
        constants.TraceData.FUNCNAME: [function_name] * len(varnames),
        constants.TraceData.VARNAME: varnames,
        constants.TraceData.VARTYPE: vartypes,
        constants.TraceData.LINENO: [line_number] * len(varnames),
        constants.TraceData.CATEGORY: [category] * len(varnames),
    }
    return pd.DataFrame.from_dict(d)


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


def _get_filepath_from(code_filepath: str) -> str:
    """Gets the relative file path from the static file path."""
    return code_filepath
