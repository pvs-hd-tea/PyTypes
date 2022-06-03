from .enums import TriggerStatus
from abc import abstractmethod

class Optimisation:
    """Base class for tracing-oriented optimisations"""

    def apply(self, frame):
        if (status := self.status()) in (TriggerStatus.ENTRY, TriggerStatus.ONGOING):
            frame.f_trace_lines = False
        else:
            frame.f_trace_lines = True
        return frame.f_trace_lines

    @abstractmethod
    def status(self) -> TriggerStatus:
        pass

    @abstractmethod
    def advance(self, current_frame) -> None:
        pass

    @abstractmethod
    def __eq__(self, o: object) -> bool:
        pass