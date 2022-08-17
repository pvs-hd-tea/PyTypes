import logging
from typegen.unification.filter_base import TraceDataFilter

import pandas as pd

from constants import Column, Schema


logger = logging.getLogger(__name__)


class UnionFilter(TraceDataFilter):
    """Replaces rows containing types in the data with their common base type."""

    ident = "union"

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        grouped = trace_data.groupby(
            by=[
                Column.CLASS_MODULE,
                Column.CLASS,
                Column.FUNCNAME,
                Column.LINENO,
                Column.CATEGORY,
                Column.VARNAME,
            ],
            dropna=False,
            group_keys=False,
            sort=False,
        )

        # Update group changes the values of every element in the group; only keep the first occurrence
        unions = [self._update_group(group).drop_duplicates() for _, group in grouped]
        processed_trace_data = pd.concat(unions)

        restored = pd.DataFrame(
            processed_trace_data.reset_index(drop=True),
            columns=list(Schema.TraceData.keys()),
        ).astype(Schema.TraceData)
        return restored

    def _update_group(self, group):
        if group.shape[0] == 1:
            module = group[Column.VARTYPE_MODULE].values[0]
            vartype = group[Column.VARTYPE].values[0]
            logger.debug(
                f"No union to build from module {module}, type {vartype}: Only one value in this group"
            )
            return group

        new_module = ",".join(group[Column.VARTYPE_MODULE].fillna(""))
        new_type = " | ".join(group[Column.VARTYPE])

        updated_group = group.copy()

        updated_group[Column.VARTYPE_MODULE] = new_module
        updated_group[Column.VARTYPE] = new_type

        return updated_group
