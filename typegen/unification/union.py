import logging
from typegen.unification.filter_base import TraceDataFilter

import pandas as pd

from constants import AnnotationData


logger = logging.getLogger(__name__)


class UnionFilter(TraceDataFilter):
    """Replaces rows containing types in the data with their common base type."""

    ident = "union"

    def apply(self, trace_data: pd.DataFrame) -> pd.DataFrame:
        grouped = trace_data.groupby(
            by=[
                AnnotationData.CLASS_MODULE,
                AnnotationData.CLASS,
                AnnotationData.FUNCNAME,
                AnnotationData.LINENO,
                AnnotationData.CATEGORY,
                AnnotationData.VARNAME,
            ],
            dropna=False,
        )

        processed_trace_data = grouped.apply(lambda group: self._update_group(group))

        logger.debug(f"Calculated:\n{processed_trace_data}")
        restored = processed_trace_data.reset_index(drop=True).astype(
            AnnotationData.SCHEMA
        )
        restored.columns = list(AnnotationData.SCHEMA.keys())
        return restored

    def _update_group(self, group):
        if group.shape[0] == 1:
            logger.debug(
                f"No union to build from {group[AnnotationData.VARTYPE_MODULE].values[0]}.{group[AnnotationData.VARTYPE].values[0]}"
                "Only one value in this group"
            )
            return group

        new_module = ",".join(group[AnnotationData.VARTYPE_MODULE])
        new_type = " | ".join(group[AnnotationData.VARTYPE])

        group[AnnotationData.VARTYPE_MODULE] = new_module
        group[AnnotationData.VARTYPE] = new_type
        group[AnnotationData.UNION_IMPORT] = True
        return group
