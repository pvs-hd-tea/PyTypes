from re import Pattern

import pandas as pd

from .filter_base import TraceDataFilter

from constants import Column, Schema


class DropTestFunctionDataFilter(TraceDataFilter):
    """Drops all data about test functions."""

    ident = "drop_test"

    test_name_pat: Pattern[str] | None = None

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """Drops the data about test functions in the provided trace data and returns the processed trace data."""
        if self.test_name_pat is None:
            raise AttributeError(
                f"{DropTestFunctionDataFilter.__name__} was not initialised properly: {self.test_name_pat=}"
            )

        processed_trace_data = trace_data[
            ~trace_data[Column.FUNCNAME].str.match(self.test_name_pat)
        ]
        return processed_trace_data.astype(Schema.TraceData)
