import pandas as pd

from .filter_base import TraceDataFilter

import constants


class MinThresholdFilter(TraceDataFilter):
    """Drops all rows whose types appear less often than the minimum threshold."""

    COUNT_COLUMN = "count"
    MAX_COUNT_COLUMN = "max_count"

    ident = "drop_min_threshold"

    min_threshold: float = 0.25

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Drops all rows whose types appear less often than the minimum
        threshold in the provided trace data and returns the processed trace data.

        @param trace_data The provided trace data to process.
        """
        subset = list(constants.AnnotationData.SCHEMA.keys())
        grouped_trace_data = (
            trace_data.groupby(subset, dropna=False)[constants.AnnotationData.VARTYPE]
            .count()
            .reset_index(name=MinThresholdFilter.COUNT_COLUMN)
        )
        joined_trace_data = pd.merge(
            trace_data, grouped_trace_data, on=subset, how="inner"
        )
        subset.remove(constants.AnnotationData.VARTYPE_MODULE)
        subset.remove(constants.AnnotationData.VARTYPE)

        grouped_trace_data = (
            joined_trace_data.groupby(subset, dropna=False)[
                MinThresholdFilter.COUNT_COLUMN
            ]
            .max()
            .reset_index(name=MinThresholdFilter.MAX_COUNT_COLUMN)
        )

        joined_trace_data = pd.merge(
            joined_trace_data, grouped_trace_data, on=subset, how="inner"
        )

        indices = (
            joined_trace_data[MinThresholdFilter.COUNT_COLUMN]
            / joined_trace_data[MinThresholdFilter.MAX_COUNT_COLUMN]
            > self.min_threshold
        )
        processed_data = joined_trace_data[indices]
        processed_data = processed_data.drop(
            [MinThresholdFilter.COUNT_COLUMN, MinThresholdFilter.MAX_COUNT_COLUMN],
            axis=1,
        )
        return processed_data.reset_index(drop=True).astype(
            constants.AnnotationData.SCHEMA
        )
