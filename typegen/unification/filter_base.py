from abc import ABC, abstractmethod
import typing

import pandas as pd


class TraceDataFilter(ABC):
    """Base class for different strategies of trace data filtering"""

    _REGISTRY: dict[str, typing.Type["TraceDataFilter"]] = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        TraceDataFilter._REGISTRY[cls.ident] = cls

    def __new__(
        cls: typing.Type["TraceDataFilter"], /, ident: str, **kwargs
    ) -> "TraceDataFilter":
        if (subcls := TraceDataFilter._REGISTRY.get(ident, None)) is not None:
            subinst = object.__new__(subcls)
            for attr, value in kwargs.items():
                setattr(subinst, attr, value)

            return subinst

        raise LookupError(f"Unsupported filter: {ident}")

    @abstractmethod
    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Processes the provided trace data and returns the processed trace data and the difference between the old and new data.

        @param trace_data The provided trace data to process.
        """
        pass


class TraceDataFilterList(TraceDataFilter):
    """Applies the filters in this list on the trace data."""

    ident = "list"

    def __init__(self):
        self.filters: list[TraceDataFilter] = []

    def append(self, trace_data_filter: TraceDataFilter) -> None:
        """Appends a filter to the list."""
        self.filters.append(trace_data_filter)

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the filters on the provided trace data and returns the processed trace data.

        @param trace_data The provided trace data to process.
        """
        for trace_data_filter in self.filters:
            trace_data = trace_data_filter.apply(trace_data)

        return trace_data.copy().reset_index(drop=True)
