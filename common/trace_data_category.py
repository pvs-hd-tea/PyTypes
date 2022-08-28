import enum


class TraceDataCategory(enum.IntEnum):
    """The trace data category."""

    INVALID = 0
    LOCAL_VARIABLE = 1
    FUNCTION_PARAMETER = 2
    FUNCTION_RETURN = 3
    CLASS_MEMBER = 4
    GLOBAL_VARIABLE = 5
