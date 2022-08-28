import typing
import pathlib

import pandas as pd
import constants
from common import DataFileCollector
from constants import Schema
import logging

logger = logging.getLogger(__name__)


class TraceDataFileCollector(DataFileCollector):
    """Collects trace data files in a given path."""

    def __init__(self):
        super().__init__(f"*{constants.TRACE_DATA_FILE_ENDING}")
        self.trace_data = pd.DataFrame(columns=Schema.TraceData.keys())
        self.trace_data = self.trace_data.astype(Schema.TraceData)

    def collect_data(
        self, path: pathlib.Path, include_also_files_in_subdirectories: bool = False
    ) -> None:
        """Collects the data in a given path."""
        super().collect_data(path, include_also_files_in_subdirectories)

        if len(self.collected_data) > 0:
            self.trace_data = pd.concat(
                self.collected_data, ignore_index=True, sort=False
            )

    def _on_potential_file_path_found(self, file_path: pathlib.Path) -> typing.Any:
        potential_trace_data = pd.read_pickle(file_path)
        if (self.trace_data.dtypes == potential_trace_data.dtypes).all():
            return potential_trace_data
        else:
            logger.info(f"Invalid column types for file: {str(file_path)}")
            return None
