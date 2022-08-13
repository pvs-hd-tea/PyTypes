from typing import Dict

import numpy as np
import pandas as pd

import constants


class MetricDataCalculator:
    """Calculates the metric data containing the correctness & completeness."""
    def __init__(self):
        self.modified_filenames_by_original: Dict[str, str] = {}

    def add_filename_mapping(self, original_filename: str, modified_filename: str) -> None:
        """Adds a mapping: modified filename -> original filename. Used to calculate the metric data."""
        self.modified_filenames_by_original[modified_filename] = original_filename

    def get_metric_data(self, original_type_hint_data: pd.DataFrame, traced_type_hint_data: pd.DataFrame) \
            -> pd.DataFrame:
        """Calculates the metric data containing the correctness & completeness."""
        # Replaces the filenames of the traced type hint data with the original filename.
        modified_type_hint_data = traced_type_hint_data.replace(
            {constants.TraceData.FILENAME: self.modified_filenames_by_original})

        subset_merged = list(constants.TraceData.TYPE_HINT_SCHEMA.keys())
        subset_merged = subset_merged.copy()
        subset_merged.remove(constants.TraceData.VARTYPE)

        modified_type_hint_data[constants.TraceData.VARTYPE2] = modified_type_hint_data[constants.TraceData.VARTYPE]
        modified_type_hint_data = modified_type_hint_data.drop(constants.TraceData.VARTYPE, axis=1)
        merged_data = pd.merge(original_type_hint_data, modified_type_hint_data,
                                            on=subset_merged, how='outer')  # type: ignore

        merged_data[constants.TraceData.COMPLETENESS] = ~merged_data[constants.TraceData.VARTYPE2].isna()
        merged_data[constants.TraceData.COMPLETENESS][merged_data[constants.TraceData.VARTYPE].isna()] = None

        merged_data[constants.TraceData.CORRECTNESS] = merged_data[constants.TraceData.VARTYPE] \
                                                       == merged_data[constants.TraceData.VARTYPE2]
        merged_data[constants.TraceData.CORRECTNESS][merged_data[constants.TraceData.VARTYPE].isna()] = None

        merged_data = merged_data.astype(constants.TraceData.METRICS_SCHEMA)

        return merged_data

    def get_total_completeness_and_correctness(self, metric_data: pd.DataFrame) -> tuple[float, float]:
        """Gets the total completeness & correctness of a given metric data."""
        completeness_column = metric_data[constants.TraceData.COMPLETENESS]
        correctness_column = metric_data[constants.TraceData.CORRECTNESS]

        total_completeness_count = completeness_column[~completeness_column.isna()].shape[0]
        total_completeness_is_true_count = completeness_column[completeness_column].shape[0]
        total_correctness_count = correctness_column[correctness_column].shape[0]

        total_completeness = total_completeness_is_true_count / total_completeness_count
        total_correctness = total_correctness_count / total_completeness_is_true_count

        return total_completeness, total_correctness