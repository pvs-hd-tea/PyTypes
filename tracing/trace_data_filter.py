import typing
from abc import ABC, abstractmethod
import pandas as pd


class TraceDataFilter(ABC):
    """Filters the trace data."""
    def __init__(self):
        pass

    @abstractmethod
    def get_processed_data_and_difference(self, trace_data: pd.DataFrame) -> typing.Tuple[pd.DataFrame, float]:
        """
        Processes the provided trace data and returns the processed trace data and the difference between the old and new data.

        @param trace_data The provided trace data to process.
        """
        pass

    def _get_difference(self, new_trace_data: pd.DataFrame, old_trace_data: pd.DataFrame) -> float:
        """
        Returns the difference between the old and the new trace data.

        @param new_trace_data The new trace data.
        @param old_trace_data The old trace data.
        """
        if old_trace_data.shape[0] == 0:
            return 0
        return (old_trace_data.shape[0] - new_trace_data.shape[0]) / float(old_trace_data.shape[0])


class DropDuplicatesFilter(TraceDataFilter):
    """Drops all duplicates in the trace data."""
    def __init__(self):
        super().__init__()

    def get_processed_data_and_difference(self, trace_data: pd.DataFrame) -> typing.Tuple[pd.DataFrame, float]:
        """
        Drops the duplicates in the provided trace data and returns the processed trace data and the difference between the old and new data.

        @param trace_data The provided trace data to process.
        """
        processed_trace_data = trace_data.drop_duplicates(ignore_index=True)
        difference = self._get_difference(processed_trace_data, trace_data)
        return processed_trace_data, difference



