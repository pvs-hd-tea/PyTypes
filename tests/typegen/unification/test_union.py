import logging
import pathlib
from tracing.trace_data_category import TraceDataCategory
from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.union import UnionFilter

import pandas as pd


from .data import sample_trace_data, resource_module
from constants import AnnotationData

unionf = TraceDataFilter(UnionFilter.ident)  # type: ignore


def test_factory():
    assert isinstance(unionf, UnionFilter)


def test_all_types_are_unified(sample_trace_data):
    expected_trace_data = sample_trace_data.copy().reset_index(drop=True)

    # argument1
    expected_trace_data.loc[0:3, AnnotationData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 3
    )
    expected_trace_data.loc[0:3, AnnotationData.VARTYPE] = " | ".join(
        ["SubClass2", "SubClass2", "SubClass3"]
    )

    # local_variable1
    expected_trace_data.loc[3:5, AnnotationData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 2
    )
    expected_trace_data.loc[3:5, AnnotationData.VARTYPE] = " | ".join(
        ["SubClass11", "SubClass1"]
    )

    # local_variable2
    expected_trace_data.loc[5:7, AnnotationData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 2
    )
    expected_trace_data.loc[5:7, AnnotationData.VARTYPE] = " | ".join(
        ["SubClass1", "SubClass1"]
    )

    # class_member1
    expected_trace_data.loc[7:10, AnnotationData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 3
    )
    expected_trace_data.loc[7:10, AnnotationData.VARTYPE] = " | ".join(
        ["SubClass1", "SubClass1", "SubClass11"]
    )

    # local_variable
    expected_trace_data.loc[10:15, AnnotationData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 5
    )
    expected_trace_data.loc[10:15, AnnotationData.VARTYPE] = " | ".join(
        ["SubClass1", "SubClass1", "SubClass1", "SubClass1", "SubClass2"]
    )

    expected_trace_data.loc[:, AnnotationData.UNION_IMPORT] = True
    expected_trace_data = expected_trace_data.drop_duplicates(ignore_index=True)
    expected_trace_data: pd.DataFrame = expected_trace_data.astype(AnnotationData.SCHEMA)

    actual = sample_trace_data
    actual_trace_data = unionf.apply(actual)

    exp_types_and_module = expected_trace_data[
        [
            AnnotationData.VARTYPE_MODULE,
            AnnotationData.VARTYPE,
            AnnotationData.UNION_IMPORT,
        ]
    ]
    act_types_and_module = actual_trace_data[
        [
            AnnotationData.VARTYPE_MODULE,
            AnnotationData.VARTYPE,
            AnnotationData.UNION_IMPORT,
        ]
    ]

    logging.debug(f"expected: \n{exp_types_and_module}")
    logging.debug(f"actual: \n{act_types_and_module}")
    logging.debug(f"diff: \n{exp_types_and_module.compare(act_types_and_module)}")

    # Side effect of unioning: the order is changed
    #expected_trace_data = expected_trace_data.sort

    logging.debug(f"{expected_trace_data.columns} vs {actual_trace_data.columns}")

    assert expected_trace_data.equals(actual_trace_data)

    # trace_data = get_sample_trace_data()
    # actual_trace_data = unionf.apply(trace_data)

    # assert expected_trace_data.equals(actual_trace_data)


def test_all_builtins_get_empty_strings():
    traced = pd.DataFrame(columns=AnnotationData.SCHEMA.keys())

    traced.loc[len(traced.index)] = [
        "",
        None,
        None,
        "stringify",
        0,
        TraceDataCategory.FUNCTION_PARAMETER,
        "a",
        None,
        f"{int.__name__}",
        False,
    ]
    traced.loc[len(traced.index)] = [
        "",
        None,
        None,
        "stringify",
        0,
        TraceDataCategory.FUNCTION_PARAMETER,
        "a",
        None,
        f"{str.__name__}",
        False,
    ]
    traced.loc[len(traced.index)] = [
        "",
        None,
        None,
        "stringify",
        0,
        TraceDataCategory.FUNCTION_PARAMETER,
        "a",
        "pathlib",
        f"{pathlib.Path.__name__}",
        False,
    ]

    expected_trace_data = pd.DataFrame(columns=AnnotationData.SCHEMA.keys())
    expected_trace_data.loc[len(expected_trace_data)] = [
        "",
        None,
        None,
        "stringify",
        0,
        TraceDataCategory.FUNCTION_PARAMETER,
        "a",
        ",,pathlib",
        f"{int.__name__} | {str.__name__} | {pathlib.Path.__name__}",
        True,
    ]
    expected_trace_data: pd.DataFrame = expected_trace_data.astype(AnnotationData.SCHEMA)

    actual_trace_data = unionf.apply(traced)

    exp_types_and_module = expected_trace_data[
        [
            AnnotationData.VARTYPE_MODULE,
            AnnotationData.VARTYPE,
            AnnotationData.UNION_IMPORT,
        ]
    ]
    act_types_and_module = actual_trace_data[
        [
            AnnotationData.VARTYPE_MODULE,
            AnnotationData.VARTYPE,
            AnnotationData.UNION_IMPORT,
        ]
    ]

    logging.debug(f"expected: \n{exp_types_and_module}")
    logging.debug(f"actual: \n{act_types_and_module}")
    logging.debug(f"diff: \n{exp_types_and_module.compare(act_types_and_module)}")

    # Side effect of unioning: the order is changed
    #expected_trace_data = expected_trace_data.sort

    logging.debug(f"{expected_trace_data.columns} vs {actual_trace_data.columns}")

    assert expected_trace_data.equals(actual_trace_data)

    # trace_data = get_sample_trace_data()
    # actual_trace_data = unionf.apply(trace_data)

    # assert expected_trace_data.equals(actual_trace_data)
