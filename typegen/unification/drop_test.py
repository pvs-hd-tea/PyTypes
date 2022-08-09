from re import Pattern

import pandas as pd

from .filter_base import TraceDataFilter
import constants

class DropTestFunctionDataFilter(TraceDataFilter):
    """Drops all data about test functions."""

    ident = "drop_test"

    def __init__(self, test_function_name_pattern: Pattern[str]):
        self.test_function_name_pattern: Pattern[str] = test_function_name_pattern

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """Drops the data about test functions in the provided trace data and returns the processed trace data."""
        processed_trace_data = trace_data[
            ~trace_data[constants.TraceData.FUNCNAME].str.match(
                self.test_function_name_pattern
            )
        ]
        return processed_trace_data
