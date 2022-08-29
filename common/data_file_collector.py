import typing
import pathlib
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class DataFileCollector(ABC):
    """Collects data files in a given path."""

    def __init__(self, file_pattern: str):
        """Creates an instance of DataFileCollector.
        :param file_pattern: The file pattern of the data files to be collected."""
        self.file_pattern = file_pattern
        self.collected_data: list[typing.Any] = list()

    def collect_data(
        self, path: pathlib.Path, include_also_files_in_subdirectories: bool = True
    ) -> None:
        """Collects the data in a given path.
        :param path: The path of the folder containing the files. 
        :param include_also_files_in_subdirectories: Whether the data files in the subfolders should also be collected."""
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
