import pandas as pd

from .filter_base import TraceDataFilter


class DropDuplicatesFilter(TraceDataFilter):
    """Drops all duplicates in the trace data."""

    ident = "dedup"

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Drops the duplicates in the provided trace data and returns the processed trace data.

        @param trace_data The provided trace data to process.
        """
        processed_trace_data = trace_data.drop_duplicates(ignore_index=True)
        return processed_trace_data.reset_index(drop=True)
