import pandas as pd

from .filter_base import TraceDataFilter

from constants import Column, Schema


class KeepOnlyFirstFilter(TraceDataFilter):
    """Keeps only the first row of each variable."""

    ident = "keep_only_first"

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        subset = list(Schema.TraceData.keys())
        subset.remove(Column.VARTYPE_MODULE)
        subset.remove(Column.VARTYPE)

        grouped_data = trace_data.groupby(subset, as_index=False, dropna=False)
        processed_data = grouped_data.nth(0)
        return processed_data.reset_index(drop=True).astype(Schema.TraceData)
