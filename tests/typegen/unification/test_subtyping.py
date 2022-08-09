import os
import pathlib
import logging

import pandas as pd
from tracing.trace_data_category import TraceDataCategory

from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.subtyping import ReplaceSubTypesFilter

from .data import get_sample_trace_data

import constants

proj_path = pathlib.Path.cwd()
venv_path = os.environ["VIRTUAL_ENV"]

strict_rstf = TraceDataFilter(
    ReplaceSubTypesFilter.ident,
    proj_path=proj_path,
    venv_path=venv_path,
    only_replace_if_base_was_traced=True,
)
relaxed_rstf = TraceDataFilter(
    ReplaceSubTypesFilter.ident,
    proj_path=proj_path,
    venv_path=venv_path,
    only_replace_if_base_was_traced=False,
)


def test_factory():
    assert isinstance(strict_rstf, ReplaceSubTypesFilter)
    assert isinstance(relaxed_rstf, ReplaceSubTypesFilter)


def test_replace_subtypes_filter_if_common_base_type_in_data_processes_and_returns_correct_data():
    expected_trace_data = get_sample_trace_data().reset_index(drop=True)
    expected_trace_data.loc[3, constants.TraceData.VARTYPE] = "SubClass1"
    expected_trace_data.loc[9, constants.TraceData.VARTYPE] = "SubClass1"
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    trace_data = get_sample_trace_data()
    actual_trace_data = strict_rstf.apply(trace_data)

    exp_types_and_module = expected_trace_data[
        [constants.TraceData.VARTYPE_MODULE, constants.TraceData.VARTYPE]
    ]
    act_types_and_module = actual_trace_data[
        [constants.TraceData.VARTYPE_MODULE, constants.TraceData.VARTYPE]
    ]

    logging.debug(f"expected: \n{exp_types_and_module}")
    logging.debug(f"actual: \n{act_types_and_module}")
    logging.debug(f"diff: \n{exp_types_and_module.compare(act_types_and_module)}")

    assert expected_trace_data.equals(actual_trace_data)


def test_replace_subtypes_filter_processes_and_returns_correct_data():
    expected_trace_data = get_sample_trace_data().reset_index(drop=True)
    expected_trace_data.loc[:3, constants.TraceData.VARTYPE] = "BaseClass"
    expected_trace_data.loc[3:, constants.TraceData.VARTYPE] = "SubClass1"
    expected_trace_data = expected_trace_data.astype(constants.TraceData.SCHEMA)

    trace_data = get_sample_trace_data()
    actual_trace_data = relaxed_rstf.apply(trace_data)

    exp_types_and_module = expected_trace_data[
        [constants.TraceData.VARTYPE_MODULE, constants.TraceData.VARTYPE]
    ]
    act_types_and_module = actual_trace_data[
        [constants.TraceData.VARTYPE_MODULE, constants.TraceData.VARTYPE]
    ]

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
    trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

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

    expected = trace_data.copy().astype(constants.TraceData.SCHEMA)

    # once for strict
    strict_actual = strict_rstf.apply(trace_data)

    # once for relaxed
    relaxed_actual = relaxed_rstf.apply(trace_data)

    assert expected.equals(strict_actual)
    assert expected.equals(relaxed_actual)


class Wacky(int):
    pass


def test_inherit_from_builtin_type():
    trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())

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
    expected.loc[len(trace_data.index) - 1, constants.TraceData.VARTYPE_MODULE] = None
    expected.loc[len(trace_data.index) - 1, constants.TraceData.VARTYPE] = "int"
    expected = expected.astype(constants.TraceData.SCHEMA)
    # once for strict
    strict_actual = strict_rstf.apply(trace_data)

    logging.debug(f": expected\n{expected}")
    logging.debug(f": actual\n{strict_actual}")
    logging.debug(f": diff\n{expected.compare(strict_actual)}")
    assert expected.equals(strict_actual)

    # once for relaxed
    relaxed_actual = relaxed_rstf.apply(trace_data)

    logging.debug(f": expected\n{expected}")
    logging.debug(f": actual\n{relaxed_actual}")
    logging.debug(f": diff\n{expected.compare(relaxed_actual)}")

    assert expected.equals(relaxed_actual)
