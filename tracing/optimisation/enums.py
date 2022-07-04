import enum


class TriggerStatus(enum.IntEnum):
    """
    INACTIVE: Non-optimising, usually for gathering information during execution
    ENTRY: Optimising, first time the tracer will be turned off
    ONGOING: Optimising, tracer is continually being turned off
    EXITED: Non-optimising, the tracer will remove this optimisation at the first opportunity
    """

    INACTIVE = 0
    ENTRY = 1
    ONGOING = 2
    EXITED = 3
