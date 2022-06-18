import functools
import pathlib
import logging


class Project:
    """
    Represents a downloaded Python repository.
    Use for more intuitive navigation of the project
    """

    def __init__(self, root: pathlib.Path):
        assert root.is_dir()
        self.root = root

    @functools.cached_property
    def test_directory(self) -> pathlib.Path | None:
        # tests folder in root of project?
        if (p := self.root / "tests").is_dir():
            logging.info(f"Detected test folder in root of project - {p}")
            return p

        if (p := self.root / self.root.name / "tests").is_dir():
            logging.info(f"Detected test folder in folder by name of project - {p}")
            return p

        logging.warning(f"Unable to find test directory for project at {self.root}")
        return None
