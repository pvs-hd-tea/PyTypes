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
        for path in filter(self._test_file_filter, self.globber(project.test_directory, "*")):
            self._apply(path)

    @abstractmethod
    def _apply(self, path: pathlib.Path) -> None:
        """Perform IO operation to modify the file pointed to by path"""
        pass

    @abstractmethod
    def _test_file_filter(self, path: pathlib.Path) -> bool:
        """True iff path is a file / folder that will be executed by the framework"""
        pass


class PyTestStrategy(ApplicationStrategy):
    FUNCTION_PATTERN = re.compile(r"[\w\s]*test_[\w\s]*\([\w\s]*\)[\w\s]*:[\w\s]*")
    IMPORTS = "from tracing import register, entrypoint\n"
    REGISTER = "@register()\n"
    ENTRYPOINT = "\n@entrypoint()\ndef main():\n  ...\n"
    APPENDED_FILEPATH = "_decorators_appended.py"

    def __init__(self, recurse_into_subdirs: bool = True):
        super().__init__(recurse_into_subdirs)

        self.decorator_appended_file_paths: list[pathlib.Path] = []

    def _apply(self, path: pathlib.Path) -> None:
        with path.open("r") as file:
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
            lines.append(PyTestStrategy.ENTRYPOINT)

        file_path_with_appended_decorators = pathlib.Path(
            str(path).replace(".py", PyTestStrategy.APPENDED_FILEPATH)
        )
        with file_path_with_appended_decorators.open("w") as file:
            file.writelines(lines)

        self.decorator_appended_file_paths.append(file_path_with_appended_decorators)

    def _test_file_filter(self, path: pathlib.Path) -> bool:
        p = str(path)

        if not (p.startswith("test_") and p.endswith(".py")):
            return False
        return not p.endswith(PyTestStrategy.APPENDED_FILEPATH)


    def execute_decorator_appended_files(self):
        """Executes the python files with the decorators appended to the pytest functions."""
        for decorator_appended_file_path in self.decorator_appended_file_paths:
            global_variables = {"__file__": decorator_appended_file_path}
            with decorator_appended_file_path.open("r") as file:
                exec(
                    compile(file.read(), decorator_appended_file_path, "exec"),
                    global_variables,
                    None,
                )
