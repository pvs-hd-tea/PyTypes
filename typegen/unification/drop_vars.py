import pandas as pd

from .filter_base import TraceDataFilter
import constants

class DropVariablesOfMultipleTypesFilter(TraceDataFilter):
    """Drops rows containing variables of multiple types."""

    ident = "drop_mult_var"

    min_amount_types_to_drop: int = 2
    
    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Drops rows containing variables if the amount of inferred types is higher than self.min_amount_types_to_drop
        and returns the processed data.

        @param trace_data The provided trace data to process.
        """
        subset = list(constants.TraceData.SCHEMA.keys())
        subset.remove(constants.TraceData.VARTYPE)
        grouped_trace_data_with_unique_count = (
            trace_data.groupby(subset, dropna=False)[constants.TraceData.VARTYPE]
            .nunique()
            .reset_index(name="amount_types")
        )
        joined_trace_data = pd.merge(
            trace_data, grouped_trace_data_with_unique_count, on=subset, how="inner"
        )
        print(joined_trace_data)
        trace_data_with_dropped_variables = joined_trace_data[
            joined_trace_data["amount_types"] < self.min_amount_types_to_drop
        ]
        processed_data = trace_data_with_dropped_variables.drop(
            ["amount_types"], axis=1
        )
        return processed_data.reset_index(drop=True)
