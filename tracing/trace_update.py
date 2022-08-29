from __future__ import annotations

from dataclasses import dataclass, field
import pathlib
import operator

from common import TraceDataCategory

import pandas as pd

from constants import Column, Schema


@dataclass(frozen=True)
class TraceUpdate:
    """
    A simple dataclass holding the contents of a singular update

    :params file_name: The file name in which the variables are declared
    :params class_module: Module of the class the variable is in
    :params class_name: Name of the class the variable is in
    :params function_name: The function which declares the variable
    :params line_number: The line number
    :params category: The data category of the row
    :params names2types: A dictionary containing the variable name, the type's module and the type's name

    """

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
    """
    A builder-pattern style interface for each relevant category, allowing updates to be chained as each event requires. 
    After all updates have been handled, a DataFrame can be produced that is to added to the otherwise accumulated trace data.

    The constructor accepts values that are used by default to create instances of `TraceUpdate`,
    unless overwritten by an argument in one of the builder methods.
    
    TRACE_MAP is defined as `dict[str, tuple[str | None, str]]`, which is a map of identifiers to (module name, type name).
    The module_name is None if the type is builtin, such as int, str, float etc.

    :params file_name: The file name in which the variables are declared
    :params class_module: Module of the class the variable is in
    :params class_name: Name of the class the variable is in
    :params function_name: The function which declares the variable
    :params line_number: The line number
    """

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
        """
        Create an update consisting of local variables

        :params line_number: Because the line number that a variable is written on is not the same 
            as the one it is put on the stack, this must be manually specified
        :params names2types: Names of local variables mapped to the module and type names of their types
        :returns: A reference to newly updated batch
        """
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
        """
        Create an update consisting of global variables.
        Because they are stateful, their line number is always 0, and can only be
        differentiated by their name and the file they occur in

        :params names2types: Names of global variables mapped to the module and type names of their types
        :returns: A reference to newly updated batch
        """
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
        """
        Create an update consisting of return types from functions.
        Their line number is always 0, so that unifiers can group them together appropriately later.

        :params names2types: Names of functions mapped to the module and type name of their return types
        :returns: A reference to newly updated batch
        """
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
        """
        Create an update consisting of parameters for a callable.

        :params names2types: Names of the parameters to a callable mapped to the module and type names of their types
        :returns: A reference to newly updated batch
        """
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
        """
        Create an update consisting of attributes of a class.
        Because they are stateful, their line number is always 0, and can only be
        differentiated by the file they occur in, their identifier and the class they occur in

        :params names2types: Names of the members of a class mapped to the module and type names of their types
        :returns: A reference to newly updated batch
        """
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

    def to_frame(self: BatchTraceUpdate) -> pd.DataFrame:
        """
        Consume this batch of updates in order to produce a DataFrame.

        :params self: Nothing else :)
        :returns: A DataFrame encompassing the entire batch 
        """
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
