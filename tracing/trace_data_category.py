import enum


class TraceDataCategory(enum.Enum):
    INVALID = 0
    LOCAL_VARIABLE = 1
    FUNCTION_ARGUMENT = 2
    FUNCTION_RETURN = 3
