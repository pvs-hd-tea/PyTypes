import functools
import pathlib
import logging
import typing


class Project:
    """
    Represents a downloaded Python repository.
    Use for more intuitive navigation of the project
    """

    def __init__(self, root: pathlib.Path):
        assert root.is_dir()
        self.root = root

    @functools.cached_property
    def test_directories(self) -> list[pathlib.Path] | None:
        """Search for directories in the repository that could contain tests

        :return: List of existing candidate folders, None if none are found
        """
        tests: list[pathlib.Path] = []

        for candidate_subdir in self._candidate_subdirs():
            if (candidate := self.root / candidate_subdir).is_dir():
                logging.info(f"Detected test folder in root of project - {candidate}")
                tests.append(candidate)

        if not tests:
            logging.warning(f"Unable to find test directory for project at {self.root}")
            return None

        return tests

    def _candidate_subdirs(self) -> typing.Iterator[pathlib.Path]:
        yield from (
            pathlib.Path("tests"),
            pathlib.Path(self.root.name) / "tests",

            pathlib.Path("test"),
            pathlib.Path(self.root.name) / "test",

            pathlib.Path("testing"),
            pathlib.Path(self.root.name) / "testing",
        )
