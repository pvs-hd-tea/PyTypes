import logging
from typegen.unification.filter_base import TraceDataFilter

import pandas as pd

from constants import TraceData


logger = logging.getLogger(__name__)


class UnionFilter(TraceDataFilter):
    """Replaces rows containing types in the data with their common base type."""

    ident = "union"

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        grouped = trace_data.groupby(
            by=[
                TraceData.CLASS_MODULE,
                TraceData.CLASS,
                TraceData.FUNCNAME,
                TraceData.LINENO,
                TraceData.CATEGORY,
                TraceData.VARNAME,
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
            columns=list(TraceData.SCHEMA.keys()),
        ).astype(TraceData.SCHEMA)
        return restored

    def _update_group(self, group):
        if group.shape[0] == 1:
            module = group[TraceData.VARTYPE_MODULE].values[0]
            vartype = group[TraceData.VARTYPE].values[0]
            logger.debug(
                f"No union to build from module {module}, type {vartype}: Only one value in this group"
            )
            return group

        new_module = ",".join(group[TraceData.VARTYPE_MODULE].fillna(""))
        new_type = " | ".join(group[TraceData.VARTYPE])

        updateable = group.copy()

        updateable[TraceData.VARTYPE_MODULE] = new_module
        updateable[TraceData.VARTYPE] = new_type

        return updateable
