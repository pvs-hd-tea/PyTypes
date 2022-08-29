from abc import ABC, abstractmethod

from .enums import TriggerStatus
from .utils import FrameWithMetadata

import pandas as pd


class Optimisation(ABC):
    """Base class for tracing-related optimisations. 
    If more optimisations need to be made, this class should be inherited from 
    and the abstract methods are to be implemented"""

    OPTIMIZING_STATES = (TriggerStatus.ENTRY, TriggerStatus.ONGOING)
    PESSIMIZING_STATES = (TriggerStatus.INACTIVE, TriggerStatus.EXITED)

    def __init__(self, fwm: FrameWithMetadata):
        """
        Construct an Optimisation for a stack frame
        
        :param fwm: The frame that originally activates the Optimisation
        """
        self.fwm = fwm

    @abstractmethod
    def status(self) -> TriggerStatus:
        """
        Get the optimisation's status.
        See TriggerStatus for an explanation of how each one
        influences the impact of the optimization upon a frame in self.apply

        :returns: The optimisation's status
        """
        pass

    @abstractmethod
    def advance(self, current_frame: FrameWithMetadata, traced: pd.DataFrame) -> None:
        """
        Modify the optimization's internal state based on given frame.
        The traced DataFrame should be treated as read-only

        :param current_frame: The current stack frame
        :param traced: The current trace data from the Tracer
        """
        pass

    @abstractmethod
    def __eq__(self, o: object) -> bool:
        """
        Overloaded equality in order to check for already
        active / duplicate optimizations
        :returns: True if the other optimisation is of the same type and references the same frame
        """
        pass
