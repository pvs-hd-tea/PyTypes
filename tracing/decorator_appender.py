import pathlib
import re


class DecoratorAppender:
    """Appends the tracer decorators to pytest test functions in files in the specified path."""
    def __init__(self):
        self.test_function_pattern = re.compile(r"[\w\s]*test_[\w\s]*\([\w\s]*\)[\w\s]*:[\w\s]*")
        self.decorator_to_append_line = "@register\n"
        self.import_decorator_line = "from tracing import register\n"
        self.file_ending = "_decorators_appended.py"

    def append_decorator_on_all_files_in(self, path: pathlib.Path,
                                         include_also_files_in_subdirectories: bool = False) -> None:
        if include_also_files_in_subdirectories:
            file_paths = path.rglob('test_*.py')
        else:
            file_paths = path.glob('test_*.py')
        for file_path in file_paths:
            if str(file_path).endswith(self.file_ending):
                continue
            with file_path.open("r") as file:
                lines = file.readlines()

            skip_line = False
            contains_pytest_test_function = False
            for i, line in enumerate(lines):
                if skip_line:
                    skip_line = False
                    continue
                if self.test_function_pattern.fullmatch(line):
                    lines.insert(i, self.decorator_to_append_line)
                    skip_line = True
                    contains_pytest_test_function = True

            if contains_pytest_test_function:
                lines.insert(0, self.import_decorator_line)

            file_path_with_appended_decorators = pathlib.Path(str(file_path).replace(".py", self.file_ending))
            with file_path_with_appended_decorators.open("w") as file:
                file.writelines(lines)
