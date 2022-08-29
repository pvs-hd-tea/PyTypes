import enum


class TraceDataCategory(enum.IntEnum):
    """The trace data category. Used by the tracer to mark the semantic of each row"""

    LOCAL_VARIABLE = 1
    """Signifies a local variable in the trace data"""

    FUNCTION_PARAMETER = 2
    """Indicates that the traced instance is a function parameter"""

    FUNCTION_RETURN = 3
    """Marks the return type of a callable"""

    CLASS_MEMBER = 4
    """Indicates a class member / attribute"""

    GLOBAL_VARIABLE = 5
    """Signifies a global variable"""

    INVALID = 0
    """Denotes otherwise unknown category. Currently unused"""
