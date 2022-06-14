import pathlib

import toml

from .base import ApplicationStrategy, TestDetector


class PyTestDetector(TestDetector):
    def __init__(self, path2project: pathlib.Path):
        super().__init__(path2project)

    def matches(self) -> bool:
        if self._has_pytest_ini():
            return True

        if self._has_pytest_in_pyproject():
            return True

        return False

    def create_strategy(self) -> ApplicationStrategy:
        return PyTestStrategy()

    def _has_pytest_ini(self) -> bool:
        pytest_config = self.path2project / "pytest.ini"
        return pytest_config.is_file()

    def _has_pytest_in_pyproject(self) -> bool:
        pyproj = self.path2project / "pyproject.toml"
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
