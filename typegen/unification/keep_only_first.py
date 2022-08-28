import pandas as pd

from .filter_base import TraceDataFilter

from constants import Column, Schema


class KeepOnlyFirstFilter(TraceDataFilter):
    """Keeps only the first row of each variable."""

    ident = "keep_only_first"

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Keeps only the first row of each variable in the provided trace data and returns the processed trace data.

        :param trace_data: The provided trace data to process.
        :returns: The processed trace data.
        
        """

        subset = list(Schema.TraceData.keys())
        subset.remove(Column.VARTYPE_MODULE)
        subset.remove(Column.VARTYPE)

        grouped_data = trace_data.groupby(subset, as_index=False, dropna=False)
        processed_data = grouped_data.nth(0)
        return processed_data.reset_index(drop=True).astype(Schema.TraceData)
