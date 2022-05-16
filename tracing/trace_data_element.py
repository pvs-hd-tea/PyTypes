class TraceDataElement:
    def __init__(self, file_name, function_name, line_number, category, variable_name, value_type):
        self.file_name = file_name
        self.function_name = function_name
        self.line_number = line_number
        self.category = category
        self.variable_name = variable_name
        self.value_type = value_type

    def __eq__(self, other):
        if isinstance(other, TraceDataElement):
            return self.file_name == other.file_name and self.function_name == other.function_name and \
                   self.line_number == other.line_number and \
                   self.category == other.category and \
                   self.variable_name == other.variable_name and \
                   self.value_type == other.value_type
        else:
            return False
