import enum


class TriggerStatus(enum.IntEnum):
    """
    The different states an Optimisation can find itself in
    """
    
    INACTIVE = 0
    """Non-optimising, usually for gathering information during execution"""
    
    ENTRY = 1
    """Optimising, first time the tracer will be turned off"""
    
    ONGOING = 2
    """Optimising, tracer is continually being turned off"""
    
    EXITED = 3
    """Non-optimising, the tracer will remove this optimisation at the first opportunity"""