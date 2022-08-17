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
            group_keys=False,
            sort=False
        )

        unions = [self._update_group(group) for _, group in grouped]
        processed_trace_data = pd.concat(unions)

        restored = pd.DataFrame(
            processed_trace_data.reset_index(drop=True),
            columns=list(AnnotationData.SCHEMA.keys()),
        ).astype(AnnotationData.SCHEMA)
        return restored

    def _update_group(self, group):
        if group.shape[0] == 1:
            module = group[AnnotationData.VARTYPE_MODULE].values[0]
            vartype = group[AnnotationData.VARTYPE].values[0]
            logger.debug(
                f"No union to build from module {module}, type {vartype}: Only one value in this group"
            )
            return group

        new_module = ",".join(group[AnnotationData.VARTYPE_MODULE])
        new_type = " | ".join(group[AnnotationData.VARTYPE])

        updateable = group.copy()

        updateable[AnnotationData.VARTYPE_MODULE] = new_module
        updateable[AnnotationData.VARTYPE] = new_type
        updateable[AnnotationData.UNION_IMPORT] = True

        return updateable
