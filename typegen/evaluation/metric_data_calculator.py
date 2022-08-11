from typing import Dict

import numpy as np
import pandas as pd

import constants


class MetricDataCalculator:
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

        subset_correctness = list(constants.TraceData.TYPE_HINT_SCHEMA.keys())
        subset_completeness = subset_correctness.copy()
        subset_completeness.remove(constants.TraceData.VARTYPE)

        # Calculates the completeness by checking
        # which rows of the original data are contained in the traced data (without type comparison).
        traced_type_hint_data_without_types = modified_type_hint_data.drop(constants.TraceData.VARTYPE, axis=1)
        merged_data_completeness = pd.merge(original_type_hint_data, traced_type_hint_data_without_types,
                                            on=subset_completeness, how='left',
                                            indicator=constants.TraceData.COMPLETENESS)  # type: ignore
        merged_data_completeness[constants.TraceData.COMPLETENESS] = \
            np.where(merged_data_completeness[constants.TraceData.COMPLETENESS] == "both", True, False)

        # Calculates the correctness by checking
        # which rows of the original data are contained in the traced data (with type comparison).
        merged_data_completeness_correctness = pd.merge(merged_data_completeness, modified_type_hint_data,
                                                        on=subset_correctness, how='left',
                                                        indicator=constants.TraceData.CORRECTNESS)  # type: ignore
        merged_data_completeness_correctness[constants.TraceData.CORRECTNESS] = \
            np.where(merged_data_completeness_correctness[constants.TraceData.CORRECTNESS] == "both", True, False)

        # Selects only the relevant columns.
        subset = list(constants.TraceData.METRICS_SCHEMA.keys())
        metric_data = merged_data_completeness_correctness[subset].astype(constants.TraceData.METRICS_SCHEMA)
        return metric_data
