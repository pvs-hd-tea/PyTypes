import pandas as pd

import constants


class MetricDataCalculator:
    INDEX = "Index"
    INDEX2 = "Index 2"
    CUMCOUNT = "CumCount"

    """Calculates the metric data containing the correctness & completeness."""
    def __init__(self):
        self.generated_filenames_by_original: dict[str, str] = {}

    def add_filename_mapping(self, original_filename: str, generated_filename: str) -> None:
        """Adds a mapping: generated filename -> original filename. Used to calculate the metric data."""
        self.generated_filenames_by_original[generated_filename] = original_filename

    def get_metric_data(self, original_type_hint_data: pd.DataFrame, generated_type_hint_data: pd.DataFrame) \
            -> pd.DataFrame:
        """Calculates the metric data containing the correctness & completeness."""
        # Replaces the filenames of the traced type hint data with the original filename.
        generated_type_hint_data = generated_type_hint_data.replace(
            {constants.TraceData.FILENAME: self.generated_filenames_by_original})

        subset_merged = list(constants.TraceData.TYPE_HINT_SCHEMA.keys())
        subset_merged = subset_merged.copy()

        # Used to sort the values.
        original_type_hint_data[MetricDataCalculator.INDEX] = original_type_hint_data.index
        generated_type_hint_data[MetricDataCalculator.INDEX2] = generated_type_hint_data.index

        # Used to treat duplicate rows as separate rows (to merge the dataframes).
        original_type_hint_data[MetricDataCalculator.CUMCOUNT] = original_type_hint_data.groupby(
            subset_merged).cumcount()
        generated_type_hint_data[MetricDataCalculator.CUMCOUNT] = generated_type_hint_data.groupby(
            subset_merged).cumcount()
        subset_merged.append(MetricDataCalculator.CUMCOUNT)

        # Merges rows which match (including type).
        merged_data = pd.merge(original_type_hint_data, generated_type_hint_data,
                                            on=subset_merged, how='inner')  # type: ignore
        merged_data = merged_data.drop(MetricDataCalculator.CUMCOUNT, axis=1)
        merged_data[constants.TraceData.VARTYPE_ORIGINAL] = merged_data[constants.TraceData.VARTYPE]
        merged_data[constants.TraceData.VARTYPE_GENERATED] = merged_data[constants.TraceData.VARTYPE]
        merged_data = merged_data.drop(constants.TraceData.VARTYPE, axis=1)
        merged_data[constants.TraceData.CORRECTNESS] = True
        merged_data[constants.TraceData.COMPLETENESS] = True

        original_type_hint_data = original_type_hint_data[
            ~original_type_hint_data[MetricDataCalculator.INDEX].isin(merged_data[MetricDataCalculator.INDEX])]
        generated_type_hint_data = generated_type_hint_data[
            ~generated_type_hint_data[MetricDataCalculator.INDEX2].isin(merged_data[MetricDataCalculator.INDEX2])]

        subset_merged.remove(constants.TraceData.VARTYPE)

        original_type_hint_data = original_type_hint_data.rename(
            {constants.TraceData.VARTYPE: constants.TraceData.VARTYPE_ORIGINAL}, axis=1)
        generated_type_hint_data = generated_type_hint_data.rename(
            {constants.TraceData.VARTYPE: constants.TraceData.VARTYPE_GENERATED}, axis=1)

        original_type_hint_data[MetricDataCalculator.CUMCOUNT] = original_type_hint_data.groupby(
            subset_merged).cumcount()
        generated_type_hint_data[MetricDataCalculator.CUMCOUNT] = generated_type_hint_data.groupby(
            subset_merged).cumcount()

        # Merges remaining rows.
        merged_data2 = pd.merge(original_type_hint_data, generated_type_hint_data,
                                on=subset_merged, how='outer')  # type: ignore
        merged_data2 = merged_data2.drop(MetricDataCalculator.CUMCOUNT, axis=1)
        merged_data2[constants.TraceData.CORRECTNESS] = False
        merged_data2[constants.TraceData.COMPLETENESS] = False
        merged_data2.loc[
            ~merged_data2[constants.TraceData.VARTYPE_GENERATED].isna(), constants.TraceData.COMPLETENESS] = True
        indices_original_types_missing = merged_data2[constants.TraceData.VARTYPE_ORIGINAL].isna()
        merged_data2.loc[indices_original_types_missing, constants.TraceData.COMPLETENESS] = None
        merged_data2.loc[indices_original_types_missing, constants.TraceData.CORRECTNESS] = None

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
