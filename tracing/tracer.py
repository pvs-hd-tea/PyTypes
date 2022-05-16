from sys import settrace
import inspect

import constants
from tracing.trace_data_element import TraceDataElement
from tracing.trace_data_category import TraceDataCategory


class Tracer:
    def __init__(self):
        self.trace_data = []
        self.old_values_by_variable = {}
        self.function_name = ""
        self.reset_members()

    def reset_members(self):
        """Resets the variables of the tracer."""
        self.trace_data = []
        self.old_values_by_variable = {}
        self.function_name = ""

    def starttrace(self, function_name):
        """Resets the trace values, starts the trace and infers the types of variables of the provided function name
        argument. """
        if not isinstance(function_name, str):
            raise TypeError()
        self.reset_members()
        settrace(self.on_trace_is_called)
        self.function_name = function_name

    def stoptrace(self):
        """Stops the trace."""
        settrace(None)

    def on_trace_is_called(self, frame, event, arg):
        """Is called during execution of a function which is traced. Collects trace data from the frame."""
        code = frame.f_code
        function_name = code.co_name

        if function_name != self.function_name:
            return self.on_trace_is_called

        file_name = get_filepath_from(code.co_filename)
        line_number = frame.f_lineno

        values_by_variable = frame.f_locals
        if event == 'call':
            for item in values_by_variable.items():
                variable_name, variable_value = item[0], item[1]
                class_name_of_return_value = get_class_name_from(variable_value)
                trace_data_element = TraceDataElement(file_name, function_name, line_number,
                                                      TraceDataCategory.FUNCTION_ARGUMENT, variable_name,
                                                      class_name_of_return_value)
                self.trace_data.append(trace_data_element)

        elif event == 'return':
            class_name_of_return_value = get_class_name_from(arg)
            trace_data_element = TraceDataElement(file_name, function_name, line_number,
                                                  TraceDataCategory.FUNCTION_RETURN, None, class_name_of_return_value)
            self.trace_data.append(trace_data_element)

        elif event == 'line':
            local_variable_name, local_variable_value = get_new_defined_variable(self.old_values_by_variable,
                                                                                 values_by_variable)
            if local_variable_name:
                class_name_of_return_value = get_class_name_from(local_variable_value)
                trace_data_element = TraceDataElement(file_name, function_name, line_number - 1,
                                                      TraceDataCategory.LOCAL_VARIABLE, local_variable_name,
                                                      class_name_of_return_value)
                self.trace_data.append(
                    trace_data_element)
            self.old_values_by_variable = values_by_variable.copy()

        return self.on_trace_is_called


def get_class_name_from(variable):
    """Gets the class name of a variable."""
    members = inspect.getmembers(variable)
    type_name = [member[1] for member in members if member[0] == '__class__'][0]
    type_name = str(type_name).split("'")[1]
    return type_name


def get_new_defined_variable(old_values_by_variable, new_values_by_variable):
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


def get_filepath_from(static_filepath):
    """Gets the relative file path from the static file path."""
    return static_filepath.split(constants.PROJECT_NAME)[1]
