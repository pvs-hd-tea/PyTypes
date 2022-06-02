from abc import abstractmethod
import enum

class TriggerStatus(enum.Enum):
    INACTIVE = 0
    ENTRY = 1
    ONGOING = 2
    EXIT = 3

class Optimisation:
    """Base class for tracing-oriented optimisations"""
    def apply(self, frame):
        if status := self.status() in (TriggerStatus.ENTRY, TriggerStatus.ONGOING):
            frame.f_trace_lines = False
        else:
            frame.f_trace_lines = True
        return frame.f_trace_lines

    @abstractmethod
    def status(self) -> TriggerStatus:
        pass

    @abstractmethod
    def advance(self) -> None:
        pass