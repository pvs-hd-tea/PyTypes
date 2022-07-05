import operator
from abc import ABC, abstractmethod
import pandas as pd
from functools import reduce
from collections import Counter  # type: ignore
import constants


class TraceDataFilter(ABC):
    """Filters the trace data."""

    def __init__(self):
        pass

    @abstractmethod
    def get_processed_data(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Processes the provided trace data and returns the processed trace data and the difference between the old and new data.

        @param trace_data The provided trace data to process.
        """
        pass


class DropDuplicatesFilter(TraceDataFilter):
    """Drops all duplicates in the trace data."""

    def __init__(self):
        super().__init__()

    def get_processed_data(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Drops the duplicates in the provided trace data and returns the processed trace data.

        @param trace_data The provided trace data to process.
        """
        processed_trace_data = trace_data.drop_duplicates(ignore_index=True)
        return processed_trace_data


class ReplaceSubTypesFilter(TraceDataFilter):
    """Replaces rows containing types in the data with their common base type."""
    def __init__(self, only_replace_if_base_type_already_in_data: bool = True):
        """
        @param only_replace_if_base_type_already_in_data Only replaces types if their common base type is already in the data.
        """
        super().__init__()
        self.only_replace_if_base_type_already_in_data = only_replace_if_base_type_already_in_data

    def get_processed_data(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Replaces the rows containing types with their common base type and returns the processed trace data. If
        only_replace_if_base_type_already_in_data is True, only rows of types whose base type is already in the data
        are replaced.

        @param trace_data The provided trace data to process.
        """
        subset = list(constants.TraceData.SCHEMA.keys())
        subset.remove(constants.TraceData.VARTYPE)
        grouped_trace_data = trace_data.groupby(subset)
        processed_trace_data = grouped_trace_data.apply(lambda group: self._update_group(group))
        return processed_trace_data

    def _update_group(self, group):
        types_in_group = group[constants.TraceData.VARTYPE].tolist()
        common_base_type = self._get_common_base_type(types_in_group)
        if not self.only_replace_if_base_type_already_in_data or common_base_type in types_in_group:
            group[constants.TraceData.VARTYPE] = common_base_type
        return group

    def _get_common_base_type(self, types: list[type]) -> type:
        common_base_type_counters_of_subtypes = [Counter(subtype.mro()) for subtype in types]
        common_base_types_in_order = reduce(operator.and_, common_base_type_counters_of_subtypes).keys()
        first_common_base_type = next(iter(common_base_types_in_order))
        return first_common_base_type


class DropVariablesOfMultipleTypesFilter(TraceDataFilter):
    """Drops rows containing variables of multiple types."""
    def __init__(self, min_amount_types_to_drop: int = 2):
        super().__init__()
        self.min_amount_types_to_drop = min_amount_types_to_drop

    def get_processed_data(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Drops rows containing variables if the amount of inferred types is higher than self.min_amount_types_to_drop
        and returns the processed data.

        @param trace_data The provided trace data to process.
        """
        subset = list(constants.TraceData.SCHEMA.keys())
        subset.remove(constants.TraceData.VARTYPE)
        grouped_trace_data_with_unique_count = trace_data.groupby(subset)[constants.TraceData.VARTYPE].nunique()\
            .reset_index(name="amount_types")
        joined_trace_data = pd.merge(trace_data, grouped_trace_data_with_unique_count, on=subset, how='inner')
        trace_data_with_dropped_variables = joined_trace_data[
            joined_trace_data["amount_types"] < self.min_amount_types_to_drop]
        processed_data = trace_data_with_dropped_variables.drop(["amount_types"], axis=1)
        return processed_data
