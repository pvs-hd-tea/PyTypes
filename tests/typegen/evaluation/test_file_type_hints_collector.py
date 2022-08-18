import pathlib
import typing

import pandas as pd
from constants import Column, Schema
from typegen.evaluation import FileTypeHintsCollector
from typegen.evaluation.normalize_types import normalize_type

root = pathlib.Path.cwd()
relative_sample_folder_path = (
    pathlib.Path("tests")
    / "resource"
    / "typegen"
    / "evaluation"
    / "file_type_hints_collector"
)
sample_folder_path = root / relative_sample_folder_path
sample_data_folder_path = (
    root
    / "tests"
    / "resource"
    / "external"
    / "PyTypes_BinaryFiles"
    / "sample_typehint_data_files"
)


def test_file_type_hints_collector_returns_correct_data_for_filename():
    filename1 = str(relative_sample_folder_path / "file_with_type_hints.py")
    filename2 = "file_with_type_hints.py"

    test_object = FileTypeHintsCollector()
    method_to_tests_to_test = [
        lambda: test_object.collect_data_from_file(root, filename1),
        lambda: test_object.collect_data_from_file(sample_folder_path, filename2),
    ]
    _test_with(
        [
            "sample_data_of_one_file_root.pytype",
            "sample_data_of_one_file_sample_folder.pytype",
        ],
        test_object,
        method_to_tests_to_test,
        25,
    )


def test_file_type_hints_collector_returns_correct_data_for_filenames():
    filenames1 = [
        str(relative_sample_folder_path / "file_with_type_hints.py"),
        str(relative_sample_folder_path / "subfolder/file_with_type_hints2.py"),
    ]
    filenames2 = ["file_with_type_hints.py", "subfolder/file_with_type_hints2.py"]

    test_object = FileTypeHintsCollector()
    method_to_tests_to_test = [
        lambda: test_object.collect_data_from_files(root, filenames1),
        lambda: test_object.collect_data_from_files(sample_folder_path, filenames2),
    ]
    _test_with(
        [
            "sample_data_of_two_files_root.pytype",
            "sample_data_of_two_files_sample_folder.pytype",
        ],
        test_object,
        method_to_tests_to_test,
        28,
    )


def test_file_type_hints_collector_returns_correct_data_for_folder():
    folder_path = sample_folder_path

    test_object = FileTypeHintsCollector()
    method_to_tests_to_test = [
        lambda: test_object.collect_data_from_folder(root, folder_path, False),
        lambda: test_object.collect_data_from_folder(
            sample_folder_path, folder_path, False
        ),
    ]
    _test_with(
        [
            "sample_data_of_folder_root.pytype",
            "sample_data_of_folder_sample_folder.pytype",
        ],
        test_object,
        method_to_tests_to_test,
        35,
    )


def test_file_type_hints_collector_returns_correct_data_for_folder_including_subdirs():
    folder_path = sample_folder_path

    test_object = FileTypeHintsCollector()
    method_to_tests_to_test = [
        lambda: test_object.collect_data_from_folder(root, folder_path, True),
        lambda: test_object.collect_data_from_folder(
            sample_folder_path, folder_path, True
        ),
    ]
    _test_with(
        [
            "sample_data_of_folder_root_including_subdirs.pytype",
            "sample_data_of_folder_sample_folder_including_subdirs.pytype",
        ],
        test_object,
        method_to_tests_to_test,
        38,
    )


def test_file_type_hints_collector_returns_correct_data_for_multiple_file_paths():
    file_paths = [
        sample_folder_path / "file_with_type_hints.py",
        sample_folder_path / "subfolder" / "file_with_type_hints2.py",
    ]
    test_object = FileTypeHintsCollector()
    method_to_tests_to_test = [
        lambda: test_object.collect_data(root, file_paths),
        lambda: test_object.collect_data(sample_folder_path, file_paths),
    ]
    _test_with(
        [
            "sample_data_of_two_files_root.pytype",
            "sample_data_of_two_files_sample_folder.pytype",
        ],
        test_object,
        method_to_tests_to_test,
        28,
    )


def test_file_type_hints_collector_returns_correct_data_for_complex_type_hints():
    filename = "file_with_complex_type_hints.py"
    expected_typehints = [
        "None | bool",
        "dict[str, typegen.evaluation.FileTypeHintsCollector]",
        "None | float | int | str",
        "None | bool | numpy.ndarray | str",
        "dict[None | typegen.evaluation.FileTypeHintsCollector, dict[float, None | bool | int]] | list[str]",
    ]
    test_object = FileTypeHintsCollector()
    test_object.collect_data_from_file(sample_folder_path, filename)
    actual_data = test_object.typehint_data
    actual_typehints = actual_data[Column.VARTYPE].tolist()
    print(actual_typehints)
    for actual_typehint, expected_typehint in zip(actual_typehints, expected_typehints):
        assert actual_typehint == expected_typehint


def _test_with(
    expected_data_filenames: list[str],
    test_object: FileTypeHintsCollector,
    method_to_tests_to_test: list[typing.Callable],
    amount_rows: int,
):
    actual_data_elements = []
    for i, expected_data_filename in enumerate(expected_data_filenames):
        method_to_test = method_to_tests_to_test[i]
        actual_typehint_data = _test_and_get_actual_data(
            expected_data_filename, test_object, method_to_test, amount_rows
        )

        actual_typehint_data = actual_typehint_data.drop(
            Column.FILENAME, axis=1
        )
        actual_data_elements.append(actual_typehint_data)

    for i, actual_typehint_data in enumerate(actual_data_elements):
        if i == 0:
            continue
        data_to_compare = actual_data_elements[i - 1]
        assert actual_typehint_data.equals(data_to_compare)


def _test_and_get_actual_data(
    expected_data_filename: str,
    test_object: FileTypeHintsCollector,
    method_to_test: typing.Callable,
    amount_rows: int,
) -> pd.DataFrame:
    expected_trace_data_file_path = sample_data_folder_path / expected_data_filename
    expected_typehint_data = pd.read_pickle(expected_trace_data_file_path)
    expected_typehint_data = expected_typehint_data.astype(
        Schema.TypeHintData
    )

    method_to_test()
    actual_typehint_data = test_object.typehint_data

    print(actual_typehint_data)

    assert actual_typehint_data.shape[0] == amount_rows

    merged_data = actual_typehint_data.merge(
        expected_typehint_data, indicator="Merge", how="outer"
    )
    merged_data = merged_data[merged_data["Merge"] != "both"]
    print("--- Difference ---")
    print(merged_data)

    assert expected_typehint_data.equals(actual_typehint_data)

    for type_name in actual_typehint_data[Column.VARTYPE].dropna():
        normalized_type_name = normalize_type(type_name)
        assert type_name == normalized_type_name

    return actual_typehint_data
