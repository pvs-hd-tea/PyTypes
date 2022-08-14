import logging
import pathlib

import typing

import constants
from typegen import DataFileCollector
import numpy as np

logger = logging.getLogger(__name__)


class PerformanceDataFileCollector(DataFileCollector):
    """Collects performance data files in a given path."""
    TARGET_SHAPE = np.array([4])

    def __init__(self):
        super().__init__()
        self.performance_data = np.zeros(PerformanceDataFileCollector.TARGET_SHAPE)
        self.performance_data = np.expand_dims(self.performance_data, axis=0)
        file_ending = constants.NP_ARRAY_FILE_ENDING
        self.file_pattern = "*" + file_ending + ".npy"

    def collect_data(
            self, path: pathlib.Path, include_also_files_in_subdirectories: bool = False
    ) -> None:
        """Collects the data in a given path."""
        super().collect_data(path, include_also_files_in_subdirectories)

        if len(self.collected_data) > 0:
            self.performance_data = np.array(self.collected_data)

    def _on_potential_file_path_found(self, file_path: pathlib.Path) -> typing.Any:
        potential_data = np.load(file_path)
        if (potential_data.shape == PerformanceDataFileCollector.TARGET_SHAPE).all():
            return potential_data
        else:
            logger.info(f"Invalid array shape for file: {str(file_path)} - Actual shape: {potential_data.shape}")
            return None
