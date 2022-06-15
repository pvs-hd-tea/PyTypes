import pathlib
import re


class TracerDecoratorAppender:
    """Appends the tracer decorators to pytest test functions in files in the specified path."""
    def __init__(self):
        self.pytest_function_regex_pattern = re.compile(r"[\w\s]*test_[\w\s]*\([\w\s]*\)[\w\s]*:[\w\s]*")
        self.decorator_to_append_line = "@register()\n"
        self.first_file_line = "from tracing import register, entrypoint\n"
        self.last_file_line = "\n@entrypoint()\ndef main():\n  ...\n"
        self.file_ending = "_decorators_appended.py"

        self.decorator_appended_file_paths = []

    def append_decorator_on_all_files_in(self, path: pathlib.Path,
                                         include_also_files_in_subdirectories: bool = False) -> None:
        """Finds all pytest files in the provided path argument and generates copies of these files with the
        decorators appended to the pytest functions. Stores the file paths of the new files."""
        if path is None:
            raise TypeError

        self.decorator_appended_file_paths.clear()

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
                if self.pytest_function_regex_pattern.fullmatch(line):
                    lines.insert(i, self.decorator_to_append_line)
                    skip_line = True
                    contains_pytest_test_function = True

            if contains_pytest_test_function:
                lines.insert(0, self.first_file_line)
                lines.append(self.last_file_line)

            file_path_with_appended_decorators = pathlib.Path(str(file_path).replace(".py", self.file_ending))
            with file_path_with_appended_decorators.open("w") as file:
                file.writelines(lines)

            self.decorator_appended_file_paths.append(file_path_with_appended_decorators)

    def execute_decorator_appended_files(self):
        """Executes the python files with the decorators appended to the pytest functions."""
        for decorator_appended_file_path in self.decorator_appended_file_paths:
            global_variables = {"__file__": decorator_appended_file_path}
            with decorator_appended_file_path.open("r") as file:
                exec(compile(file.read(), decorator_appended_file_path, 'exec'), global_variables, None)

