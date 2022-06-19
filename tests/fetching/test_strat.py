import pathlib
import pytest
from unittest import mock

from fetching.projio import Project

from fetching.strat import PyTestStrategy

cwd = pathlib.Path.cwd() / "tests" / "resource" / "sample_decorator_appender_folder"


@pytest.fixture()
def project_folder():
    with mock.patch(
        "fetching.projio.Project.test_directory",
        new_callable=mock.PropertyMock,
    ) as m:
        m.return_value = cwd
        p = Project(cwd)

        yield p


def test_if_test_object_searches_for_test_files_in_folders_it_generates_test_files(
    project_folder,
):
    test_object = PyTestStrategy(False)
    test_object.apply(project_folder)
    test_file_paths = cwd.glob("test_*.py")
    new_test_file_paths = [
        pathlib.Path(str(file_path).replace(".py", test_object.APPENDED_FILEPATH))
        for file_path in test_file_paths
        if not str(file_path).endswith(test_object.APPENDED_FILEPATH)
    ]
    assert len(new_test_file_paths) != 0

    for new_test_file_path in new_test_file_paths:
        assert new_test_file_path.exists()


def test_if_test_object_searches_for_test_files_in_folders_including_subfolders_it_generates_test_files(
    project_folder,
):
    test_object = PyTestStrategy(True)
    test_object.apply(project_folder)
    test_file_paths = cwd.rglob("test_*.py")
    new_test_file_paths = [
        pathlib.Path(str(file_path).replace(".py", test_object.APPENDED_FILEPATH))
        for file_path in test_file_paths
        if not str(file_path).endswith(test_object.APPENDED_FILEPATH)
    ]
    assert len(new_test_file_paths) != 0

    for new_test_file_path in new_test_file_paths:
        assert new_test_file_path.exists()
