import logging
from typegen.unification.filter_base import TraceDataFilter
from typegen.unification.union import UnionFilter

from .data import get_sample_trace_data, resource_module, resource_path

from constants import TraceData

unionf = TraceDataFilter(UnionFilter.ident)  # type: ignore


def test_factory():
    assert isinstance(unionf, UnionFilter)


def test_drop_duplicates_filter_processes_and_returns_correct_data_and_difference():
    expected_trace_data = get_sample_trace_data().reset_index(drop=True)

    # argument1
    expected_trace_data.loc[0:3, TraceData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 3
    )
    expected_trace_data.loc[0:3, TraceData.VARTYPE] = " | ".join(
        ["SubClass2", "SubClass2", "SubClass3"]
    )

    # local_variable1
    expected_trace_data.loc[3:5, TraceData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 2
    )
    expected_trace_data.loc[3:5, TraceData.VARTYPE] = " | ".join(
        ["SubClass11", "SubClass1"]
    )

    # local_variable2
    expected_trace_data.loc[5:7, TraceData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 2
    )
    expected_trace_data.loc[5:7, TraceData.VARTYPE] = " | ".join(
        ["SubClass1", "SubClass1"]
    )

    # class_member1
    expected_trace_data.loc[7:10, TraceData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 3
    )
    expected_trace_data.loc[7:10, TraceData.VARTYPE] = " | ".join(
        ["SubClass1", "SubClass1", "SubClass11"]
    )

    # local_variable
    expected_trace_data.loc[10:15, TraceData.VARTYPE_MODULE] = ",".join(
        [resource_module] * 5
    )
    expected_trace_data.loc[10:15, TraceData.VARTYPE] = " | ".join(
        ["SubClass1", "SubClass1", "SubClass1", "SubClass1", "SubClass2"]
    )

    expected_trace_data = expected_trace_data.astype(TraceData.SCHEMA)

    actual_trace_data = unionf.apply(get_sample_trace_data())

    exp_types_and_module = expected_trace_data[
        [TraceData.VARTYPE_MODULE, TraceData.VARTYPE]
    ]
    act_types_and_module = actual_trace_data[
        [TraceData.VARTYPE_MODULE, TraceData.VARTYPE]
    ]

    logging.debug(f"expected: \n{exp_types_and_module}")
    logging.debug(f"actual: \n{act_types_and_module}")
    logging.debug(f"diff: \n{exp_types_and_module.compare(act_types_and_module)}")

    assert expected_trace_data.equals(actual_trace_data.drop("union_import", axis=1))

    # trace_data = get_sample_trace_data()
    # actual_trace_data = unionf.apply(trace_data)

    # assert expected_trace_data.equals(actual_trace_data)
