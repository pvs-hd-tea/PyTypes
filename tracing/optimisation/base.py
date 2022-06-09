from .enums import TriggerStatus
from .utils import FrameWithLine
from abc import abstractmethod

import pandas as pd


class Optimisation:
    """Base class for tracing-oriented optimisations"""

    def __init__(self, frame):
        self.frame = frame

    def apply(self, frame):
        """
        Apply the derived optimization to the given frame.
        Whether tracing is turned off for a given line depends on the
        optimisation's status
        """
        if (status := self.status()) in (TriggerStatus.ENTRY, TriggerStatus.ONGOING):
            frame.f_trace_lines = False
        else:
            frame.f_trace_lines = True
        return frame.f_trace_lines

    @abstractmethod
    def status(self) -> TriggerStatus:
        """
        Get the optimization's status.
        See TriggerStatus for an explanation of how each one
        influences the impact of the optimization upon a frame in self.apply
        """
        pass

    @abstractmethod
    def advance(self, current_frame: FrameWithLine, traced: pd.DataFrame) -> None:
        """
        Modify the optimization's internal state based on given frame
        """
        pass

    @abstractmethod
    def __eq__(self, o: object) -> bool:
        """
        Overloaded equality in order to check for already 
        active / duplicate optimizations
        """
        pass
