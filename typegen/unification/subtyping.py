import importlib
import importlib.util
from importlib.machinery import SourceFileLoader
import logging
import os
from types import ModuleType
import pandas as pd
import pathlib
import sys

from .filter_base import TraceDataFilter
import constants

logger = logging.getLogger(__name__)


def _attempt_module_lookup(
    module_name: str, root: pathlib.Path, lookup_path: pathlib.Path
) -> ModuleType | None:
    try:
        loader = SourceFileLoader(module_name, str(root / lookup_path))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        if spec is not None:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            loader.exec_module(module)

            logger.debug(f"Imported {module_name} from {str(root / lookup_path)}")
            return module

    except FileNotFoundError:
        logger.debug(f"Could not import {module_name} from {str(root / lookup_path)}")

    return None


class ReplaceSubTypesFilter(TraceDataFilter):
    """Replaces rows containing types in the data with their common base type."""

    ident = "repl_subty"

    stdlib_path: pathlib.Path | None = None
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
        subset = list(constants.TraceData.SCHEMA.keys())
        subset.remove(constants.TraceData.VARTYPE_MODULE)
        subset.remove(constants.TraceData.VARTYPE)
        subset.remove(constants.TraceData.FILENAME)
        grouped_trace_data = trace_data.groupby(subset, dropna=False)
        processed_trace_data = grouped_trace_data.apply(
            lambda group: self._update_group(trace_data, group)
        )
        typed = processed_trace_data.reset_index(drop=True).astype(
            constants.TraceData.SCHEMA
        )
        typed.columns = constants.TraceData.SCHEMA.keys()
        return typed

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
                logger.debug(f"Discarding {common}; module was not found in trace data")
                return group

            if basetype not in entire[constants.TraceData.VARTYPE].values:
                logger.debug(f"Discarding {common}; type was not found in trace data")
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
        self, relative_type_module_name: str | None, variable_type_name: str
    ) -> list[tuple[str | None, str]]:
        if self.stdlib_path is None:
            raise AttributeError(
                f"{ReplaceSubTypesFilter.__name__} was not initialised properly: {self.stdlib_path=}"
            )
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
        # Follow import order specified by sys.path

        # 0. builtin types
        if relative_type_module_name is None or isinstance(
            relative_type_module_name, type(pd.NA)
        ):
            # __builtins__ is typed as Module by mypy, but is dict in the REPL?
            builtin_ty: type = __builtins__[variable_type_name]  # type: ignore
            mros = builtin_ty.mro()

        else:
            # recreate filename
            lookup_path = pathlib.Path(
                relative_type_module_name.replace(".", os.path.sep) + ".py"
            )

            # 1. project path
            module = _attempt_module_lookup(
                relative_type_module_name, self.proj_path, lookup_path
            )
            if module is None:
                # 2. stdlib
                module = _attempt_module_lookup(
                    relative_type_module_name, self.stdlib_path, lookup_path
                )

            if module is None:
                # 23 venv
                major, minor = sys.version_info[:2]
                site_packages = (
                    self.venv_path / "lib" / f"python{major}.{minor}" / "site-packages"
                )
                module = _attempt_module_lookup(
                    relative_type_module_name, site_packages, lookup_path
                )

            if module is None:
                raise ImportError(
                    f"Failed to import {relative_type_module_name} from {self.stdlib_path}, {self.venv_path}, {self.proj_path}"
                )
            variable_type: type = getattr(module, variable_type_name)

            # TODO: venv import

            mros = variable_type.mro()

        def none_if_builtin(module: str) -> str | None:
            return module if module != "builtins" else None

        module_and_name = list()
        for m in mros:
            module_and_name.append((none_if_builtin(m.__module__), m.__name__))
        return module_and_name
