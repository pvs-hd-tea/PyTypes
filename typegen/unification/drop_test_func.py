from re import Pattern

import pandas as pd

from .filter_base import TraceDataFilter
import constants


class DropTestFunctionDataFilter(TraceDataFilter):
    """Drops all data about test functions."""

    ident = "drop_test"

    test_func_name_pattern: Pattern[str] | None = None

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """Drops the data about test functions in the provided trace data and returns the processed trace data."""
        if self.test_func_name_pattern is None:
            raise AttributeError(
                f"{DropTestFunctionDataFilter.__name__} was not initialised properly: {self.test_func_name_pattern=}"
            )

        processed_trace_data = trace_data[
            ~trace_data[constants.TraceData.FUNCNAME].str.match(
                self.test_func_name_pattern
            )
        ]
        return processed_trace_data.astype(constants.TraceData.SCHEMA)
