import typing
from abc import ABC, abstractmethod
import pathlib

import pandas as pd
import constants
import logging

logger = logging.getLogger(__name__)


class DataFileCollector(ABC):
    """Collects data files in a given path."""

    def __init__(self, file_pattern: str):
        self.file_pattern = file_pattern
        self.collected_data = list()

    def collect_data(
        self, path: pathlib.Path, include_also_files_in_subdirectories: bool = False
    ) -> None:
        self.collected_data.clear()
        if include_also_files_in_subdirectories:
            potential_trace_data_file_paths = path.rglob(self.file_pattern)
        else:
            potential_trace_data_file_paths = path.glob(self.file_pattern)

        # Ensures that the order is deterministic.
        sorted_potential_trace_data_file_paths = sorted(potential_trace_data_file_paths)
        for potential_trace_data_file_path in sorted_potential_trace_data_file_paths:
            try:
                potential_data = self._on_potential_file_path_found(
                    potential_trace_data_file_path
                )
                if potential_data is not None:
                    self.collected_data.append(potential_data)
            except Exception as exception:
                print(exception)
                logger.error(
                    f"Error encountered for file: {str(potential_trace_data_file_path)}"
                )
                logger.error(exception)
                continue

    @abstractmethod
    def _on_potential_file_path_found(self, file_path: pathlib.Path) -> typing.Any:
        pass


class TraceDataFileCollector(DataFileCollector):
    """Collects trace data files in a given path."""

    def __init__(self):
        super().__init__(f"*{constants.TRACE_DATA_FILE_ENDING}")
        self.trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
        self.trace_data = self.trace_data.astype(constants.TraceData.SCHEMA)

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
