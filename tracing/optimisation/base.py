from abc import abstractmethod
import inspect
import logging

from .enums import TriggerStatus
from .utils import FrameWithMetadata

import pandas as pd


class Optimisation:
    """Base class for tracing-oriented optimisations"""

    def __init__(self, fwm: FrameWithMetadata):
        self.fwm = fwm

    def apply(self, fwm: FrameWithMetadata) -> bool:
        """
        Apply the derived optimization to the given frame.
        Whether tracing is turned off for a given line depends on the
        optimisation's status
        """
        if self.status() in (TriggerStatus.ENTRY, TriggerStatus.ONGOING):
            fwm.frame.f_trace_lines = False
        else:
            fwm.frame.f_trace_lines = True
        return fwm.frame.f_trace_lines

    @abstractmethod
    def status(self) -> TriggerStatus:
        """
        Get the optimization's status.
        See TriggerStatus for an explanation of how each one
        influences the impact of the optimization upon a frame in self.apply
        """
        pass

    @abstractmethod
    def advance(self, current_frame: FrameWithMetadata, traced: pd.DataFrame) -> None:
        """
        Modify the optimization's internal state based on given frame
        The traced DataFrame should be treated as read-only
        """
        pass

    @abstractmethod
    def __eq__(self, o: object) -> bool:
        """
        Overloaded equality in order to check for already 
        active / duplicate optimizations
        """
        pass
