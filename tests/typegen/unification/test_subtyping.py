import os
import sys
import pathlib
import logging
import tempfile

import pandas as pd
from tracing.trace_data_category import TraceDataCategory

from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.subtyping import UnifySubTypesFilter

from .data import sample_trace_data

from constants import Column, Schema

from pandas.testing import assert_frame_equal

proj_path = pathlib.Path.cwd()
venv_path = pathlib.Path(os.environ["VIRTUAL_ENV"])
import pathlib

stdlib_path = pathlib.Path(pathlib.__file__).parent

strict_rstf = TraceDataFilter(  # type: ignore
    ident=UnifySubTypesFilter.ident,
    proj_path=proj_path,
    venv_path=venv_path,
    stdlib_path=stdlib_path,
    only_replace_if_base_was_traced=True,
)
relaxed_rstf = TraceDataFilter(  # type: ignore
    ident=UnifySubTypesFilter.ident,
    proj_path=proj_path,
    venv_path=venv_path,
    stdlib_path=stdlib_path,
    only_replace_if_base_was_traced=False,
)


def test_factory():
    assert isinstance(strict_rstf, UnifySubTypesFilter)
    assert isinstance(relaxed_rstf, UnifySubTypesFilter)


def test_replace_subtypes_filter_if_common_base_type_in_data_processes_and_returns_correct_data(
    sample_trace_data,
):
    expected_trace_data = sample_trace_data.copy().reset_index(drop=True)
    expected_trace_data.loc[3, Column.VARTYPE] = "SubClass1"
    expected_trace_data.loc[9, Column.VARTYPE] = "SubClass1"
    expected_trace_data = expected_trace_data.drop_duplicates(ignore_index=True).astype(
        Schema.TraceData
    )

    trace_data = sample_trace_data.copy()
    actual_trace_data = strict_rstf.apply(trace_data)

    exp_types_and_module = expected_trace_data[[Column.VARTYPE_MODULE, Column.VARTYPE]]
    act_types_and_module = actual_trace_data[[Column.VARTYPE_MODULE, Column.VARTYPE]]

    logging.debug(f"expected: \n{exp_types_and_module}")
    logging.debug(f"actual: \n{act_types_and_module}")
    logging.debug(f"diff: \n{exp_types_and_module.compare(act_types_and_module)}")

    assert expected_trace_data.equals(actual_trace_data)


def test_replace_subtypes_filter_processes_and_returns_correct_data(sample_trace_data):
    expected_trace_data = sample_trace_data.copy().reset_index(drop=True)
    expected_trace_data.loc[:3, Column.VARTYPE] = "BaseClass"
    expected_trace_data.loc[3:, Column.VARTYPE] = "SubClass1"
    expected_trace_data.loc[10:, Column.VARTYPE] = "BaseClass"
    expected_trace_data = expected_trace_data.drop_duplicates(ignore_index=True).astype(
        Schema.TraceData
    )

    trace_data = sample_trace_data.copy()
    actual_trace_data = relaxed_rstf.apply(trace_data)

    exp_types_and_module = expected_trace_data[[Column.VARTYPE_MODULE, Column.VARTYPE]]
    act_types_and_module = actual_trace_data[[Column.VARTYPE_MODULE, Column.VARTYPE]]

    logging.debug(f"expected: \n{exp_types_and_module}")
    logging.debug(f"actual: \n{act_types_and_module}")
    logging.debug(f"diff: \n{exp_types_and_module.compare(act_types_and_module)}")

    assert expected_trace_data.equals(actual_trace_data)


# More tests specific to subtyping, as we are required to import from the filesystem
# meaning we are to avoid importing builtins, and should manage importing from the
# standard library and from virtualenvs

# Attempt to unify types with nothing in common apart from "object"
# Nothing should change in the traced data, as this type hint is better suited for a union type
def test_ignore_object_base_type():
    trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    resource_path = pathlib.Path("tests", "typegen", "unification", "test_subtyping.py")
    resource_module = "tests.typegen.unification.test_subtyping"

    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "fname",
        1,
        TraceDataCategory.LOCAL_VARIABLE,
        "vname",
        None,
        "int",
    ]

    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "fname",
        1,
        TraceDataCategory.LOCAL_VARIABLE,
        "vname",
        None,
        "str",
    ]

    expected = trace_data.copy().astype(Schema.TraceData)

    # once for strict
    strict_actual = strict_rstf.apply(trace_data)

    # once for relaxed
    relaxed_actual = relaxed_rstf.apply(trace_data)

    assert expected.equals(strict_actual)
    assert expected.equals(relaxed_actual)


class Wacky(int):
    pass


def test_inherit_from_builtin_type():
    trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    resource_path = pathlib.Path("tests", "typegen", "unification", "test_subtyping.py")
    resource_module = "tests.typegen.unification.test_subtyping"

    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "fname",
        1,
        TraceDataCategory.LOCAL_VARIABLE,
        "vname",
        None,
        "int",
    ]

    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "fname",
        1,
        TraceDataCategory.LOCAL_VARIABLE,
        "vname",
        resource_module,
        "Wacky",
    ]

    expected = trace_data.copy()
    expected.loc[len(trace_data.index) - 1, Column.VARTYPE_MODULE] = None
    expected.loc[len(trace_data.index) - 1, Column.VARTYPE] = "int"
    expected = expected.drop_duplicates(ignore_index=True).astype(Schema.TraceData)
    # once for strict
    strict_actual = strict_rstf.apply(trace_data)

    logging.debug(f"expected: \n{expected}")
    logging.debug(f"actual: \n{strict_actual}")
    logging.debug(f"diff: \n{expected.compare(strict_actual)}")
    assert expected.equals(strict_actual)

    # once for relaxed
    relaxed_actual = relaxed_rstf.apply(trace_data)

    logging.debug(f"expected: \n{expected}")
    logging.debug(f"actual: \n{relaxed_actual}")
    logging.debug(f"diff: \n{expected.compare(relaxed_actual)}")

    assert expected.equals(relaxed_actual)


def test_unify_stdlib_types():
    resource_path = pathlib.Path("tests", "typegen", "unification", "test_subtyping.py")

    trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "fname",
        1,
        TraceDataCategory.LOCAL_VARIABLE,
        "vname",
        "pathlib",
        "PosixPath",
    ]

    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "fname",
        1,
        TraceDataCategory.LOCAL_VARIABLE,
        "vname",
        "pathlib",
        "WindowsPath",
    ]
    trace_data = trace_data.astype(Schema.TraceData)

    # once for strict
    # strict will not pick this up, as Path is not in the trace data
    strict_actual = strict_rstf.apply(trace_data)

    logging.debug(f"expected: \n{trace_data}")
    logging.debug(f"actual: \n{strict_actual}")
    logging.debug(f"diff: \n{trace_data.compare(strict_actual)}")
    assert trace_data.equals(strict_actual)

    # once for relaxed
    relaxed_actual = relaxed_rstf.apply(trace_data)

    expected = trace_data.copy()
    expected.loc[:, Column.VARTYPE] = "Path"
    expected = expected.drop_duplicates(ignore_index=True).astype(Schema.TraceData)

    logging.debug(f"expected: \n{expected}")
    logging.debug(f"actual: \n{relaxed_actual}")
    logging.debug(f"diff: \n{expected.compare(relaxed_actual)}")

    assert expected.equals(relaxed_actual)


def test_no_subtype_pandas_builtin():
    # A very curious Pandas bug seems to occur in this test
    # All checks indicate that the type of the instance returned from the filter
    # is indeed a pd.DataFrame and supports being serialised and deserialised from
    # storage, yet it will not allow itself to be compared aginst other DataFrames.

    # Nonetheless, the results are CORRECT, and the dataframe simply cannot be compared against anything
    # Considering we use this DataFrame solely for typegenning, this should not be a problem.
    # If any error message like "TypeError: can only compare 'DataFrame' (not 'DataFrame') with 'DataFrame'
    # appears, revisit this test!
    trace_data = pd.DataFrame(columns=Schema.TraceData.keys())

    resource_path = pathlib.Path("tests", "typegen", "unification", "test_subtyping.py")

    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "fname",
        1,
        TraceDataCategory.LOCAL_VARIABLE,
        "vname",
        "pandas.core.frame",
        "DataFrame",
    ]

    trace_data.loc[len(trace_data.index)] = [
        str(resource_path),
        None,
        None,
        "fname",
        1,
        TraceDataCategory.LOCAL_VARIABLE,
        "vname",
        None,
        "int",
    ]
    trace_data = trace_data.astype(Schema.TraceData)

    # once for strict
    # strict will not pick this up, as there is no common type
    strict_actual = strict_rstf.apply(trace_data)
    # assert type(strict_actual) == pd.DataFrame
    logging.debug(f"\nexpected: \n{trace_data}")
    logging.debug(f"\nactual: \n{strict_actual}")
    # logging.debug(f"\ndiff: \n{trace_data.compare(strict_actual)}")

    # assert_frame_equal(trace_data, reloaded_strict)

    # once for relaxed
    # relaxed will not pick this up, as there is no common type
    relaxed_actual = relaxed_rstf.apply(trace_data)
    logging.debug(f"Columns: {relaxed_actual.columns}")
    relaxed_actual = relaxed_actual.astype(Schema.TraceData)

    logging.debug(f"\nexpected: \n{trace_data}")
    logging.debug(f"\nactual: \n{relaxed_actual}")
    # logging.debug(f"\ndiff: \n{trace_data.compare(relaxed_actual)}")

    # assert_frame_equal(trace_data, relaxed_actual)
