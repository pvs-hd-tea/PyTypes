from abc import abstractmethod
import enum

from .enums import TriggerStatus
from .base import Optimisation
from .ignore import Ignore
from .looping import TypeStableLoop
from .utils import FrameWithMetadata


__all__ = [
    TriggerStatus.__name__,
    Optimisation.__name__,
    Ignore.__name__,
    TypeStableLoop.__name__,
    FrameWithMetadata.__name__
]
