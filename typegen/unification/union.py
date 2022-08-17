import logging
from typegen.unification.filter_base import TraceDataFilter

import pandas as pd

from constants import TraceData


logger = logging.getLogger(__name__)


class UnionFilter(TraceDataFilter):
    """Replaces rows containing types in the data with their common base type."""

    ident = "union"

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        trace_data["union_import"] = False
        grouped = trace_data.groupby(
            by=[
                TraceData.CLASS_MODULE,
                TraceData.CLASS,
                TraceData.FUNCNAME,
                TraceData.LINENO,
                TraceData.CATEGORY,
                TraceData.VARNAME,
                "union_import"
            ],
            dropna=False,
        )

        processed_trace_data = grouped.apply(lambda group: self._update_group(group))
        typed = processed_trace_data.reset_index(drop=True).astype(TraceData.SCHEMA)
        typed.columns = list(TraceData.SCHEMA.keys()) + ["union_import"]
        return typed

    def _update_group(self, group):
        to_group = group[[TraceData.VARTYPE, TraceData.VARTYPE_MODULE]]
        if group.shape[0] == 1:
            logger.debug(
                f"No union to build from {to_group[TraceData.VARTYPE_MODULE].values[0]}.{to_group[TraceData.VARTYPE].values[0]}"
                "Only one value in this group"
            )
            return group

        new_module = ",".join(to_group[TraceData.VARTYPE_MODULE])
        new_type = " | ".join(to_group[TraceData.VARTYPE])

        group[TraceData.VARTYPE_MODULE] = new_module
        group[TraceData.VARTYPE] = new_type
        group["union_import"] = True
        return group
