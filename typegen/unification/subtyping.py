import logging
import pandas as pd
import pathlib

from common.resolver import Resolver

from .filter_base import TraceDataFilter
from constants import Column, Schema

logger = logging.getLogger(__name__)


def _none_if_builtin(module: str) -> str | None:
    return module if module != "builtins" else None


class UnifySubTypesFilter(TraceDataFilter):
    """Replaces rows containing types in the data with their common base type."""

    ident = "unify_subty"

    stdlib_path: pathlib.Path
    proj_path: pathlib.Path
    venv_path: pathlib.Path
    only_unify_if_base_was_traced: bool = False

    _UNDESIRABLE_MODULES = ("abc",)

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        """
        Unify rows containing types using their common base type. 
        If only_unify_if_base_was_traced is True, only rows of types whose base type is already in the data
        are replaced.

        @param trace_data The provided trace data to process.
        """
        self._resolver = Resolver(self.stdlib_path, self.proj_path, self.venv_path)

        grouped_trace_data = trace_data.groupby(
            by=[
                Column.CLASS_MODULE,
                Column.CLASS,
                Column.FUNCNAME,
                Column.LINENO,
                Column.CATEGORY,
                Column.VARNAME,
            ],
            dropna=False,
            sort=False,
        )

        unified = [
            self._update_group(trace_data, group).drop_duplicates()
            for _, group in grouped_trace_data
        ]

        processed_trace_data = pd.concat(unified)

        restored = pd.DataFrame(
            processed_trace_data.reset_index(drop=True),
            columns=list(Schema.TraceData.keys()),
        ).astype(Schema.TraceData)
        return restored

    def _update_group(self, entire: pd.DataFrame, group):
        modules_with_types_in_group = group[
            [
                Column.FILENAME,
                Column.VARTYPE_MODULE,
                Column.VARTYPE,
            ]
        ]
        common = self._get_common_base_type(modules_with_types_in_group)
        if common is None:
            return group

        basetype_module, basetype = common
        if self.only_unify_if_base_was_traced:
            if basetype_module not in entire[Column.VARTYPE_MODULE].values:
                logger.debug(f"Discarding {common}; module was not found in trace data")
                return group

            if basetype not in entire[Column.VARTYPE].values:
                logger.debug(f"Discarding {common}; type was not found in trace data")
                return group

        updated_group = group.copy()

        updated_group[Column.VARTYPE_MODULE] = basetype_module
        updated_group[Column.VARTYPE] = basetype
        return updated_group

    def _get_common_base_type(
        self, modules_with_types: pd.DataFrame
    ) -> tuple[str | None, str] | None:
        type2bases = {}
        for _, row in modules_with_types.iterrows():
            varmodule, vartyp = (
                row[Column.VARTYPE_MODULE],
                row[Column.VARTYPE],
            )
            types_topologically_sorted = self._get_type_and_mro(varmodule, vartyp)

            # drop base types which are considered too common (ABC, ABCMeta, object)
            abcless: list[tuple[str | None, str]] = list()
            for mod, ty in types_topologically_sorted:
                if mod not in UnifySubTypesFilter._UNDESIRABLE_MODULES:
                    abcless.append((mod, ty))
            abcless.pop()

            if len(abcless):
                type2bases[(varmodule, vartyp)] = abcless
            else:
                # There is no common base type for the requested types, do not change anything
                return None

        # Use shortest list of base types in order to
        # speed up intersection searching
        smallest = min(type2bases.items(), key=lambda kv: len(kv[1]))
        smallest_bases = type2bases.pop(smallest[0])

        logger.debug(smallest_bases)
        logger.debug(type2bases)

        # Loop will only end if all objects share "object"
        # object is always the very last element of mro, but was removed in the
        # assignment to `abcless`,
        for modty in smallest_bases:
            if all(modty in bases for bases in type2bases.values()):
                logger.debug(f"Finishing MRO traversal; common base type is {modty}")
                return modty

        logger.debug(
            "Finishing MRO traversal; there is no common base type except object"
        )
        return None

    def _get_type_and_mro(
        self, module_name: str | None, type_name: str
    ) -> list[tuple[str | None, str]]:
        variable_type = self._resolver.type_lookup(module_name, type_name)
        if variable_type is None:
            raise ImportError(
                f"Failed to import {module_name} from {self.stdlib_path}, {self.venv_path}, {self.proj_path}"
            )
        mros = variable_type.mro()

        module_and_name = list()
        for m in mros:
            module_and_name.append((_none_if_builtin(m.__module__), m.__name__))
        return module_and_name
