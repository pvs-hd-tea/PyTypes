import enum


class TraceDataCategory(enum.IntEnum):
    INVALID = 0
    LOCAL_VARIABLE = 1
    FUNCTION_PARAMETER = 2
    FUNCTION_RETURN = 3
    CLASS_MEMBER = 4
