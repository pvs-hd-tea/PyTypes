import importlib
from importlib.machinery import SourceFileLoader
from operator import mod
import os
import pandas as pd
import pathlib

from .filter_base import TraceDataFilter
import constants


class ReplaceSubTypesFilter(TraceDataFilter):
    """Replaces rows containing types in the data with their common base type."""

    ident = "repl_subty"

    proj_path: pathlib.Path | None = None
    venv_path: pathlib.Path | None = None
    only_replace_if_base_was_traced: bool | None = None

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Replaces the rows containing types with their common base type and returns the processed trace data. If
        only_replace_if_base_type_already_in_data is True, only rows of types whose base type is already in the data
        are replaced.

        @param trace_data The provided trace data to process.
        """
        if self.proj_path is None:
            raise AttributeError(
                f"{ReplaceSubTypesFilter.__name__} was not initialised properly: {self.proj_path=}"
            )
        if self.venv_path is None:
            raise AttributeError(
                f"{ReplaceSubTypesFilter.__name__} was not initialised properly: {self.venv_path=}"
            )
        if self.only_replace_if_base_was_traced is None:
            raise AttributeError(
                f"{ReplaceSubTypesFilter.__name__} was not initialised properly: {self.only_replace_if_base_was_traced=}"
            )

        subset = list(constants.TraceData.SCHEMA.keys())
        subset.remove(constants.TraceData.VARTYPE_MODULE)
        subset.remove(constants.TraceData.VARTYPE)
        subset.remove(constants.TraceData.FILENAME)
        grouped_trace_data = trace_data.groupby(subset, dropna=False)
        processed_trace_data = grouped_trace_data.apply(
            lambda group: self._update_group(trace_data, group)
        )
        return processed_trace_data.reset_index(drop=True).astype(
            constants.TraceData.SCHEMA
        )

    def _update_group(self, entire: pd.DataFrame, group):
        modules_with_types_in_group = group[
            [
                constants.TraceData.FILENAME,
                constants.TraceData.VARTYPE_MODULE,
                constants.TraceData.VARTYPE,
            ]
        ]
        common = self._get_common_base_type(modules_with_types_in_group)
        if common is None:
            return group

        basetype_module, basetype = common
        if self.only_replace_if_base_was_traced:
            if basetype_module not in entire[constants.TraceData.VARTYPE_MODULE].values:
                return group

            if basetype not in entire[constants.TraceData.VARTYPE].values:
                return group

        group[constants.TraceData.VARTYPE_MODULE] = basetype_module
        group[constants.TraceData.VARTYPE] = basetype
        return group

    def _get_common_base_type(
        self, modules_with_types: pd.DataFrame
    ) -> tuple[str | None, str] | None:
        type2bases = {}
        for _, row in modules_with_types.iterrows():
            varmodule, vartyp = (
                row[constants.TraceData.VARTYPE_MODULE],
                row[constants.TraceData.VARTYPE],
            )
            types_topologically_sorted = self._get_type_and_mro(varmodule, vartyp)

            # drop mros that are useless
            abcless = list(filter(lambda p: p[0] != "abc", types_topologically_sorted))

            # also remove object from the end, as means that there is no common type
            abcless.pop()

            if len(abcless):
                type2bases[(varmodule, vartyp)] = abcless
            else:
                # There is no common base type for the requested types, do not change anything
                return None

        # Pick shortest base types to minimise runtime
        smallest = min(type2bases.items(), key=lambda kv: len(kv[1]))
        smallest_bases = type2bases.pop(smallest[0])

        print(smallest_bases)
        print(type2bases)

        # Loop will only end if all objects share "object"
        # object is always the very last element of mro, but was removed in the
        # assignment to `abcless`,
        for modty in smallest_bases:
            if all(modty in bases for bases in type2bases.values()):
                return modty
        return None

    def _get_type_and_mro(
        self, relative_type_module_name: str | None, variable_type_name: str
    ) -> list[tuple[str | None, str]]:
        # builtin types
        if relative_type_module_name is None:
            builtin_ty: type = __builtins__[variable_type_name]
            mros = builtin_ty.mro()

        else:
            # recreate filename
            lookup_path = pathlib.Path(
                relative_type_module_name.replace(".", os.path.sep) + ".py"
            )

            # project import
            loader = SourceFileLoader(
                relative_type_module_name, str(self.proj_path / lookup_path)
            )

            spec = importlib.util.spec_from_loader(loader.name, loader)
            module = importlib.util.module_from_spec(spec)
            loader.exec_module(module)
            variable_type: type = getattr(module, variable_type_name)

            # TODO: venv import

            mros = variable_type.mro()

        def none_if_builtin(module: str) -> str | None:
            return module if module != "builtins" else None

        module_and_name = list()
        for m in mros:
            module_and_name.append((none_if_builtin(m.__module__), m.__name__))
        return module_and_name
