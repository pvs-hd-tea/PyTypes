from abc import abstractmethod
import pathlib

class TestDetector:
    def __init__(self, path2project: pathlib.Path):
        self.path2project = path2project

    @abstractmethod
    def matches(self) -> bool:
        pass


class PyTestDetector(TestDetector):
    def __init__(self, path2project: pathlib.Path):
        super().__init__(path2project)

    def matches(self) -> bool:
        pytest_config = self.path2project / "pytest.ini"
        if pytest_config.is_file():
            return True

        # TODO: support pyproject.toml


        return False