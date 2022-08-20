from __future__ import annotations

from dataclasses import dataclass, field
import pathlib
import operator

from .trace_data_category import TraceDataCategory

import pandas as pd

from constants import Column, Schema


@dataclass(frozen=True)
class TraceUpdate:

    # The file name in which the variables are declared
    file_name: pathlib.Path

    # Module of the class the variable is in
    class_module: str | None

    # Name of the class the variable is in
    class_name: str | None

    # The function which declares the variable
    function_name: str | None

    # The line number
    line_number: int

    # The data category of the row
    category: TraceDataCategory

    # A dictionary containing the variable name, the type's module and the type's name
    names2types: dict[str, tuple[str | None, str]]


TRACE_MAP = dict[str, tuple[str | None, str]]


@dataclass
class BatchTraceUpdate:
    file_name: pathlib.Path
    class_module: str | None
    class_name: str | None
    function_name: str
    line_number: int

    _updates: list[TraceUpdate] = field(default_factory=list)

    def local_variables(
        self,
        line_number: int,
        names2types: TRACE_MAP,
    ) -> BatchTraceUpdate:
        if names2types:
            update = TraceUpdate(
                file_name=self.file_name,
                class_module=self.class_module,
                class_name=self.class_name,
                function_name=self.function_name,
                line_number=line_number,
                category=TraceDataCategory.LOCAL_VARIABLE,
                names2types=names2types,
            )
            self._updates.append(update)

        return self

    def global_variables(
        self,
        names2types: TRACE_MAP,
    ) -> BatchTraceUpdate:
        if names2types:
            update = TraceUpdate(
                file_name=self.file_name,
                class_module=None,
                class_name=None,
                function_name=None,
                line_number=0,
                category=TraceDataCategory.GLOBAL_VARIABLE,
                names2types=names2types,
            )
            self._updates.append(update)

        return self

    def returns(
        self,
        names2types: TRACE_MAP,
    ) -> BatchTraceUpdate:
        if names2types:
            update = TraceUpdate(
                file_name=self.file_name,
                class_module=self.class_module,
                class_name=self.class_name,
                function_name=self.function_name,
                line_number=0,
                category=TraceDataCategory.FUNCTION_RETURN,
                names2types=names2types,
            )
            self._updates.append(update)

        return self

    def parameters(
        self,
        names2types: TRACE_MAP,
    ) -> BatchTraceUpdate:
        if names2types:
            update = TraceUpdate(
                file_name=self.file_name,
                class_module=self.class_module,
                class_name=self.class_name,
                function_name=self.function_name,
                line_number=self.line_number,
                category=TraceDataCategory.FUNCTION_PARAMETER,
                names2types=names2types,
            )
            self._updates.append(update)

        return self

    def members(
        self,
        names2types: TRACE_MAP,
    ) -> BatchTraceUpdate:
        if names2types:
            # Line number is 0 and function name is empty to
            # unify matching class members better.
            # Class Members contain state and can theoretically, at any time, 
            # on the same line, be of many types
            update = TraceUpdate(
                file_name=self.file_name,
                class_module=self.class_module,
                class_name=self.class_name,
                function_name=None,
                line_number=0,
                category=TraceDataCategory.CLASS_MEMBER,
                names2types=names2types,
            )

        self._updates.append(update)

        return self

    def to_frame(self) -> pd.DataFrame:
        updates = list()
        for update in self._updates:
            names2types = update.names2types
            varnames = list(names2types.keys())
            vartype_modules = list(map(operator.itemgetter(0), names2types.values()))
            vartypes = list(map(operator.itemgetter(1), names2types.values()))

            update_dict = {
                Column.FILENAME: [str(update.file_name)] * len(varnames),
                Column.CLASS_MODULE: [update.class_module] * len(varnames),
                Column.CLASS: [update.class_name] * len(varnames),
                Column.FUNCNAME: [update.function_name] * len(varnames),
                Column.LINENO: [update.line_number] * len(varnames),
                Column.CATEGORY: [update.category] * len(varnames),
                Column.VARNAME: varnames,
                Column.VARTYPE_MODULE: vartype_modules,
                Column.VARTYPE: vartypes,
            }
            update_df = pd.DataFrame(
                update_dict, columns=Schema.TraceData.keys()
            ).astype(Schema.TraceData)
            updates.append(update_df)

        if not updates:
            return pd.DataFrame(columns=Schema.TraceData.keys()).astype(
                Schema.TraceData
            )

        return pd.concat(updates, ignore_index=True).astype(Schema.TraceData)
