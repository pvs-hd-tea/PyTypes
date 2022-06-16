import pathlib

import pytest

from tracing import TracerDecoratorAppender

cwd = pathlib.Path.cwd() / 'resource'


def test_if_argument_of_append_decorator_is_none_error_is_raised():
    test_object = TracerDecoratorAppender()
    test_object.append_decorator_on_all_files_in(None)


def test_if_test_object_searches_for_test_files_in_folders_it_generates_test_files():
    test_object = TracerDecoratorAppender()
    test_object.append_decorator_on_all_files_in(cwd, False)
    test_file_paths = cwd.glob('test_*.py')
    new_test_file_paths = [pathlib.Path(str(file_path).replace(".py", test_object.file_ending))
                           for file_path in test_file_paths if not str(file_path).endswith(test_object.file_ending)]
    for new_test_file_path in new_test_file_paths:
        assert pathlib.Path.exists(new_test_file_path)


def test_if_test_object_searches_for_test_files_in_folders_including_subfolders_it_generates_test_files():
    test_object = TracerDecoratorAppender()
    test_object.append_decorator_on_all_files_in(cwd, True)
    test_file_paths = cwd.rglob('test_*.py')
    new_test_file_paths = [pathlib.Path(str(file_path).replace(".py", test_object.file_ending))
                           for file_path in test_file_paths if not str(file_path).endswith(test_object.file_ending)]
    for new_test_file_path in new_test_file_paths:
        assert pathlib.Path.exists(new_test_file_path)
