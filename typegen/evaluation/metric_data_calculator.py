from typing import Dict

import numpy as np
import pandas as pd

import constants


class MetricDataCalculator:
    INDEX = "Index"
    INDEX2 = "Index 2"
    CUMCOUNT = "CumCount"

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

        # Used to sort the values.
        original_type_hint_data[MetricDataCalculator.INDEX] = original_type_hint_data.index
        modified_type_hint_data[MetricDataCalculator.INDEX2] = modified_type_hint_data.index

        # Used to treat duplicate rows as separate rows (to merge the dataframes).
        original_type_hint_data[MetricDataCalculator.CUMCOUNT] = original_type_hint_data.groupby(
            subset_merged).cumcount()
        modified_type_hint_data[MetricDataCalculator.CUMCOUNT] = modified_type_hint_data.groupby(
            subset_merged).cumcount()
        subset_merged.append(MetricDataCalculator.CUMCOUNT)

        merged_data = pd.merge(original_type_hint_data, modified_type_hint_data,
                                            on=subset_merged, how='inner')  # type: ignore
        merged_data = merged_data.drop(MetricDataCalculator.CUMCOUNT, axis=1)
        merged_data[constants.TraceData.VARTYPE2] = merged_data[constants.TraceData.VARTYPE]
        merged_data[constants.TraceData.CORRECTNESS] = True
        merged_data[constants.TraceData.COMPLETENESS] = True

        original_type_hint_data = original_type_hint_data[
            ~original_type_hint_data[MetricDataCalculator.INDEX].isin(merged_data[MetricDataCalculator.INDEX])]
        modified_type_hint_data = modified_type_hint_data[
            ~modified_type_hint_data[MetricDataCalculator.INDEX2].isin(merged_data[MetricDataCalculator.INDEX2])]

        subset_merged.remove(constants.TraceData.VARTYPE)

        modified_type_hint_data[constants.TraceData.VARTYPE2] = modified_type_hint_data[constants.TraceData.VARTYPE]
        modified_type_hint_data = modified_type_hint_data.drop(constants.TraceData.VARTYPE, axis=1)

        original_type_hint_data[MetricDataCalculator.CUMCOUNT] = original_type_hint_data.groupby(
            subset_merged).cumcount()
        modified_type_hint_data[MetricDataCalculator.CUMCOUNT] = modified_type_hint_data.groupby(
            subset_merged).cumcount()

        merged_data2 = pd.merge(original_type_hint_data, modified_type_hint_data,
                                on=subset_merged, how='outer')  # type: ignore
        merged_data2 = merged_data2.drop(MetricDataCalculator.CUMCOUNT, axis=1)
        merged_data2[constants.TraceData.CORRECTNESS] = False
        merged_data2[constants.TraceData.COMPLETENESS] = False
        merged_data2[constants.TraceData.COMPLETENESS][~merged_data2[constants.TraceData.VARTYPE2].isna()] = True
        merged_data2[constants.TraceData.COMPLETENESS][merged_data2[constants.TraceData.VARTYPE].isna()] = None
        merged_data2[constants.TraceData.CORRECTNESS][merged_data2[constants.TraceData.VARTYPE].isna()] = None

        columns_in_correct_order = list(constants.TraceData.METRICS_SCHEMA.keys())
        columns_in_correct_order.append(MetricDataCalculator.INDEX)
        columns_in_correct_order.append(MetricDataCalculator.INDEX2)
        merged_data2 = merged_data2[columns_in_correct_order]
        merged_data = merged_data[columns_in_correct_order]
        processed_data = pd.concat(
            [merged_data, merged_data2], ignore_index=True
        )
        processed_data = processed_data.sort_values(by=[MetricDataCalculator.INDEX, MetricDataCalculator.INDEX2])\
            .reset_index(drop=True)
        processed_data = processed_data.drop([MetricDataCalculator.INDEX, MetricDataCalculator.INDEX2], axis=1)
        processed_data = processed_data.astype(constants.TraceData.METRICS_SCHEMA)

        return processed_data

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
