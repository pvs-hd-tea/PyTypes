from abc import ABC, abstractmethod
import pathlib
import re

from .projio import Project


class ApplicationStrategy(ABC):
    """
    Implement for a specific test framework;
    When given a file that uses the specified framework,
    parse this file and insert code that will cause the test
    functions to be traced upon execution.
    """

    def __init__(self, recurse_into_subdirs: bool = True):
        self.globber = pathlib.Path.rglob if recurse_into_subdirs else pathlib.Path.glob

    def apply(self, project: Project):
        assert project.test_directory is not None
        for path in filter(
            self._is_test_file, self.globber(project.test_directory, "*")
        ):
            self._apply(path)

    @abstractmethod
    def _apply(self, path: pathlib.Path) -> None:
        """Perform IO operation to modify the file pointed to by path"""
        pass

    @abstractmethod
    def _is_test_file(self, path: pathlib.Path) -> bool:
        """True iff path is a file / folder that will be executed by the framework"""
        pass


class PyTestStrategy(ApplicationStrategy):
    FUNCTION_PATTERN = re.compile(r"[\w\s]*test_[\w\s]*\([\w\s]*\)[\w\s]*:[\w\s]*")
    IMPORTS = "import sys; from tracing import register, entrypoint\n"
    REGISTER = "@register()\n"
    ENTRYPOINT = "\n@entrypoint()\ndef main():\n  ...\n"
    APPENDED_FILEPATH = "_decorators_appended.py"

    def __init__(self, pytest_root: pathlib.Path, recurse_into_subdirs: bool = True):
        super().__init__(recurse_into_subdirs)

        self.pytest_root = pytest_root
        self.decorator_appended_file_paths: list[pathlib.Path] = []

        self.sys_path_ext = f"sys.path.append({self.pytest_root}"

    def _apply(self, path: pathlib.Path) -> None:
        with path.open() as file:
            lines = file.readlines()

        skip_line = False
        contains_pytest_test_function = False
        for i, line in enumerate(lines):
            if skip_line:
                skip_line = False
                continue
            if PyTestStrategy.FUNCTION_PATTERN.fullmatch(line):
                lines.insert(i, PyTestStrategy.REGISTER)
                skip_line = True
                contains_pytest_test_function = True

        if contains_pytest_test_function:
            lines.insert(0, PyTestStrategy.IMPORTS)
            lines.insert(1, self.sys_path_ext)
            lines.append(PyTestStrategy.ENTRYPOINT)

        with path.open("w") as file:
            file.writelines(lines)

        self.decorator_appended_file_paths.append(path)

    def _is_test_file(self, path: pathlib.Path) -> bool:
        if (
            path.name.startswith("test_")
            and path.name.endswith(".py")
            and not path.name.endswith(PyTestStrategy.APPENDED_FILEPATH)
        ):
            return True

        return path.name.endswith("_test.py")
