import os
import pathlib
import logging

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

    exp_types_and_module = expected_trace_data[[
        constants.TraceData.VARTYPE_MODULE,
        constants.TraceData.VARTYPE
    ]]
    act_types_and_module = actual_trace_data[[
        constants.TraceData.VARTYPE_MODULE,
        constants.TraceData.VARTYPE
    ]]

    logging.debug(f"expected: \n{exp_types_and_module}")
    logging.debug(f"actual: \n{act_types_and_module}")
    logging.debug(f"diff: \n{exp_types_and_module.compare(act_types_and_module)}")

    assert expected_trace_data.equals(actual_trace_data)