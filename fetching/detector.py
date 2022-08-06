from abc import ABC, abstractmethod
import logging
import pathlib

import toml

from .projio import Project
from .strat import ApplicationStrategy, PyTestStrategy


class TestDetector(ABC):
    """
    When given the path to a repo, attempts to detect a specific
    testing suite and create the appropriate application strategy
    if there is a match.
    """

    def __init__(self, project: Project):
        self.project = project

    @staticmethod
    def factory(proj: Project) -> "TestDetector":
        if (d := PyTestDetector(proj)).matches():
            logging.info(f"Detected pytest in {proj.root}")
            return d

        raise LookupError(f"Project at {proj.root} uses unknown testing suite")

    @abstractmethod
    def matches(self) -> bool:
        """Detect specific testing suite."""
        pass

    @abstractmethod
    def create_strategy(
        self, overwrite_tests: bool, recurse_into_subdirs: bool, use_performance: bool
    ) -> ApplicationStrategy:
        """Create application strategy."""
        pass


class PyTestDetector(TestDetector):
    def __init__(self, project: Project):
        super().__init__(project)

    def matches(self) -> bool:
        return self._has_pytest_ini() or self._has_pytest_in_pyproject()

    def create_strategy(
        self, overwrite_tests: bool, recurse_into_subdirs: bool, use_performance: bool
    ) -> ApplicationStrategy:
        return PyTestStrategy(
            pytest_root=pathlib.Path.cwd(),
            overwrite_tests=overwrite_tests,
            recurse_into_subdirs=recurse_into_subdirs,
            use_performance=use_performance
        )

    def _has_pytest_ini(self) -> bool:
        pytest_config = self.project.root / "pytest.ini"
        return pytest_config.is_file()

    def _has_pytest_in_pyproject(self) -> bool:
        pyproj = self.project.root / "pyproject.toml"
        if not pyproj.is_file():
            return False

        pyproj_cfg = toml.load(pyproj.open())
        if "tool" not in pyproj_cfg:
            return False
        elif "poetry" not in pyproj_cfg["tool"]:
            return False
        elif "dev-dependencies" not in pyproj_cfg["tool"]["poetry"]:
            return False
        return "pytest" in pyproj_cfg["tool"]["poetry"]["dev-dependencies"]
