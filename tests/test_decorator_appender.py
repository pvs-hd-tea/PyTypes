import pathlib
import pytest

from tracing import TracerDecoratorAppender

cwd = pathlib.Path.cwd() / "sample_decorator_appender_folder"


def test_if_test_object_is_initialized_it_finds_test_files():
    test_object = TracerDecoratorAppender()
    test_object.append_decorator_on_all_files_in(cwd, True)
    test_file_paths = cwd.rglob('test_*.py')
    new_test_file_paths = [pathlib.Path(str(file_path).replace(".py", test_object.file_ending))
                           for file_path in test_file_paths if not str(file_path).endswith(test_object.file_ending)]
    for new_test_file_path in new_test_file_paths:
        assert pathlib.Path.exists(new_test_file_path)
