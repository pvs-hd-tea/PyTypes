import pandas as pd

from .filter_base import TraceDataFilter

from constants import Column, Schema


class DropVariablesOfMultipleTypesFilter(TraceDataFilter):
    """Drops rows containing variables the amount of the corresponding types is higher or equal than the specified min amount."""

    ident = "drop_mult_var"

    min_amount_types_to_drop: int = 2

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        subset = list(Schema.TraceData.keys())
        subset.remove(Column.VARTYPE)
        grouped_trace_data_with_unique_count = (
            trace_data.groupby(subset, dropna=False)[Column.VARTYPE]
            .nunique()
            .reset_index(name="amount_types")
        )
        joined_trace_data = pd.merge(
            trace_data, grouped_trace_data_with_unique_count, on=subset, how="inner"
        )
        trace_data_with_dropped_variables = joined_trace_data[
            joined_trace_data["amount_types"] < self.min_amount_types_to_drop
        ]
        processed_data = trace_data_with_dropped_variables.drop(
            ["amount_types"], axis=1
        )
        return processed_data.reset_index(drop=True).astype(Schema.TraceData)
