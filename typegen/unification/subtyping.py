import importlib
from importlib.machinery import SourceFileLoader
import os
import pandas as pd
import pathlib

from .filter_base import TraceDataFilter
import constants

class ReplaceSubTypesFilter(TraceDataFilter):
    """Replaces rows containing types in the data with their common base type."""

    ident = "repl_subty"

    def __init__(
        self,
        proj_root: pathlib.Path,
        venv_path: pathlib.Path,
        only_replace_if_base_type_already_in_data: bool = True,
    ):
        """
        @param only_replace_if_base_type_already_in_data Only replaces types if their common base type is already in the data.
        """
        super().__init__()
        self.proj_root = proj_root
        self.only_replace_if_base_type_already_in_data = (
            only_replace_if_base_type_already_in_data
        )

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
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
        processed_trace_data = grouped_trace_data.apply(
            lambda group: self._update_group(trace_data, group)
        )
        return processed_trace_data.reset_index(drop=True).astype(constants.TraceData.SCHEMA)

    def _update_group(self, entire: pd.DataFrame, group):
        modules_with_types_in_group = group[
            [
                constants.TraceData.FILENAME,
                constants.TraceData.VARTYPE_MODULE,
                constants.TraceData.VARTYPE,
            ]
        ]
        basetype_module, basetype = self._get_common_base_type(
            modules_with_types_in_group
        )
        print(f"Base Type Module: {basetype_module}, Base Type: {basetype}")

        if self.only_replace_if_base_type_already_in_data:
            if basetype_module not in entire[constants.TraceData.VARTYPE_MODULE].values:
                return group

            if basetype not in entire[constants.TraceData.VARTYPE].values:
                return group

        
        group[constants.TraceData.VARTYPE_MODULE] = basetype_module
        group[constants.TraceData.VARTYPE] = basetype
        return group

    def _get_common_base_type(
        self, modules_with_types: pd.DataFrame
    ) -> tuple[str, str]:
        type2bases = {}
        for _, row in modules_with_types.iterrows():
            varmodule, vartyp = (
                row[constants.TraceData.VARTYPE_MODULE],
                row[constants.TraceData.VARTYPE],
            )
            types_topologically_sorted = self._get_type_and_mro(varmodule, vartyp)

            # drop mros that are useless
            abcless = list(filter(lambda p: p[0] != "abc", types_topologically_sorted))
            type2bases[(varmodule, vartyp)] = abcless

        # Pick shortest base types to minimise runtime
        smallest = min(type2bases.items(), key=lambda kv: len(kv[1]))
        smallest_bases = type2bases.pop(smallest[0])

        # Loop is guaranteed to return as all objects share "object" at a minimum
        for ty in smallest_bases:
            if all(ty in bases for bases in type2bases.values()):
                return ty

        raise AssertionError(
            f"MRO Search loop failed to terminate:\nNeedles: {smallest}, Haystack: {type2bases}"
        )

    def _get_type_and_mro(
        self, relative_type_module_name: str | None, variable_type_name: str
    ) -> list[tuple[str, str]]:
        print(relative_type_module_name, variable_type_name)

        if relative_type_module_name is not None:
            # recreate filename
            lookup_path = pathlib.Path(
                relative_type_module_name.replace(".", os.path.sep) + ".py"
            )

            # project import
            loader = SourceFileLoader(
                relative_type_module_name, str(self.proj_root / lookup_path)
            )

            

            spec = importlib.util.spec_from_loader(loader.name, loader)
            module = importlib.util.module_from_spec(spec)
            loader.exec_module(module)
            variable_type: type = getattr(module, variable_type_name)

            # TODO: venv import

            mros = variable_type.mro()

        module_and_name = list(map(lambda m: (m.__module__, m.__name__), mros))
        return module_and_name