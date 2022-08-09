import operator
from abc import ABC, abstractmethod
from re import Pattern
import importlib

from importlib.machinery import SourceFileLoader
import pandas as pd
from functools import reduce
from collections import Counter  # type: ignore

from pandas._libs.missing import NAType

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
        return processed_trace_data.reset_index(drop=True)


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
        subset.remove(constants.TraceData.VARTYPE_MODULE)
        subset.remove(constants.TraceData.VARTYPE)
        subset.remove(constants.TraceData.FILENAME)
        grouped_trace_data = trace_data.groupby(subset, dropna=False)
        processed_trace_data = grouped_trace_data.apply(lambda group: self._update_group(group))
        return processed_trace_data.reset_index(drop=True)

    def _update_group(self, group):
        modules_with_types_in_group = group[[constants.TraceData.FILENAME, constants.TraceData.VARTYPE_MODULE, constants.TraceData.VARTYPE]]
        common_base_type = self._get_common_base_type(modules_with_types_in_group)
        print("Common base type: " + str(common_base_type))
        types_in_group = modules_with_types_in_group[constants.TraceData.VARTYPE].tolist()
        if not self.only_replace_if_base_type_already_in_data or common_base_type in types_in_group:
            group[constants.TraceData.VARTYPE] = common_base_type
        return group

    def _get_common_base_type(self, modules_with_types: pd.DataFrame) -> type:
        common_base_type_counters_of_subtypes = []
        for _, row in modules_with_types.iterrows():
            types_topologically_sorted = self._get_mro_of_type(row[constants.TraceData.VARTYPE_MODULE],
                                                               row[constants.TraceData.VARTYPE])
            counter = Counter(types_topologically_sorted)
            common_base_type_counters_of_subtypes.append(counter)
        common_base_types_in_order = reduce(operator.and_, common_base_type_counters_of_subtypes).keys()
        first_common_base_type = next(iter(common_base_types_in_order))
        return first_common_base_type

    def _get_mro_of_type(self, relative_type_module_name: str | None, variable_type_name: str) -> list[str]:
        if relative_type_module_name is not None and not isinstance(relative_type_module_name, NAType):
            try:
                loader = SourceFileLoader("temp", relative_type_module_name)
                spec = importlib.util.spec_from_loader(loader.name, loader)
                module = importlib.util.module_from_spec(spec)
                loader.exec_module(module)
                variable_type = getattr(module, variable_type_name)
            except Exception as e:
                print("Import error: " + str(e))
                return [object.__name__]
        else:
            try:
                variable_type = globals()[variable_type_name]
            except KeyError:
                # Builtin type.
                return [variable_type_name, object.__name__]
        types_topologically_sorted = variable_type.mro()
        print(types_topologically_sorted)
        return [type_in_hierarchy.__name__ for type_in_hierarchy in types_topologically_sorted]


class DropVariablesOfMultipleTypesFilter(TraceDataFilter):
    """Drops rows containing variables of multiple types."""
    def __init__(self, min_amount_types_to_drop: int = 2):
        """
        @param min_amount_types_to_drop The minimum amount of types to drop the data of the corresponding variable.
        """
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
        grouped_trace_data_with_unique_count = trace_data.groupby(subset, dropna=False)[constants.TraceData.VARTYPE].nunique()\
            .reset_index(name="amount_types")
        joined_trace_data = pd.merge(trace_data, grouped_trace_data_with_unique_count, on=subset, how='inner')
        print(joined_trace_data)
        trace_data_with_dropped_variables = joined_trace_data[
            joined_trace_data["amount_types"] < self.min_amount_types_to_drop]
        processed_data = trace_data_with_dropped_variables.drop(["amount_types"], axis=1)
        return processed_data.reset_index(drop=True)


class TraceDataFilterList(TraceDataFilter):
    """Applies the filters in this list on the trace data."""

    def __init__(self):
        self.filters: list[TraceDataFilter] = []

    def append(self, trace_data_filter: TraceDataFilter) -> None:
        """Appends a filter to the list."""
        self.filters.append(trace_data_filter)

    def get_processed_data(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the filters on the provided trace data and returns the processed trace data.

        @param trace_data The provided trace data to process.
        """
        for trace_data_filter in self.filters:
            trace_data = trace_data_filter.get_processed_data(trace_data)

        return trace_data.copy().reset_index(drop=True)


class DropTestFunctionDataFilter(TraceDataFilter):
    """Drops all data about test functions."""
    def __init__(self, test_function_name_pattern: Pattern[str]):
        self.test_function_name_pattern: Pattern[str] = test_function_name_pattern

    def get_processed_data(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """Drops the data about test functions in the provided trace data and returns the processed trace data."""
        processed_trace_data = trace_data[~trace_data[constants.TraceData.FUNCNAME].str.match(self.test_function_name_pattern)]
        return processed_trace_data

