import pathlib

import toml

from .detector import TestDetector
from .strat import ApplicationStrategy
from .projio import Project


class PyTestDetector(TestDetector):
    def __init__(self, project: Project):
        super().__init__(project)

    def matches(self) -> bool:
        return self._has_pytest_ini() or self._has_pytest_in_pyproject()

    def create_strategy(self) -> ApplicationStrategy:
        return PyTestStrategy()

    def _has_pytest_ini(self) -> bool:
        pytest_config = self.project.root / "pytest.ini"
        return pytest_config.is_file()

    def _has_pytest_in_pyproject(self) -> bool:
        pyproj = self.project.root / "pyproject.toml"
        if not pyproj.is_file():
            return False

        pyproj_cfg = toml.load(pyproj.open())
        return (
            "tool" in pyproj_cfg
            and "poetry" in pyproj_cfg["tool"]
            and "dev-dependencies" in pyproj_cfg["tool"]["poetry"]
            and "pytest" in pyproj_cfg["tool"]["poetry"]["dev-dependencies"]
        )


class PyTestStrategy(ApplicationStrategy):
    pass
