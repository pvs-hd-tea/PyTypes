import logging
import click
import pathlib
from typegen.trace_data_file_collector import TraceDataFileCollector, DataFileCollector


from constants import CONFIG_FILE_NAME

from tracing import ptconfig

from .unification import TraceDataFilter
from .unification.drop_dupes import DropDuplicatesFilter
from .unification.drop_test_func import DropTestFunctionDataFilter
from .unification.drop_vars import DropVariablesOfMultipleTypesFilter
from .unification.filter_base import TraceDataFilterList
from .unification.subtyping import UnifySubTypesFilter
from .unification.union import UnionFilter
from .unification.drop_min_threshold import MinThresholdFilter
from .unification.keep_only_first import KeepOnlyFirstFilter

from .strats.stub import StubFileGenerator
from .strats.inline import InlineGenerator
from .strats.eval_inline import EvaluationInlineGenerator
from .strats.gen import TypeHintGenerator

__all__ = [
    DataFileCollector.__name__,
    TraceDataFileCollector.__name__,
    DropDuplicatesFilter.__name__,
    DropTestFunctionDataFilter.__name__,
    DropVariablesOfMultipleTypesFilter.__name__,
    UnifySubTypesFilter.__name__,
    MinThresholdFilter.__name__,
    UnionFilter.__name__,
    KeepOnlyFirstFilter.__name__,
]


@click.command(name="typegen", help="Generate type hinted files using trace data")
@click.option(
    "-p",
    "--path",
    type=click.Path(
        exists=True,
        dir_okay=True,
        writable=False,
        readable=True,
        path_type=pathlib.Path,
    ),
    help="Path to project directory",
    required=True,
)
@click.option(
    "-u",
    "--unifiers",
    help=f"Unifier to apply, as given by `name` in {CONFIG_FILE_NAME} under [[unifier]]",
    multiple=True,
    required=False,
)
@click.option(
    "-g",
    "--gen-strat",
    help="Select a strategy for generating type hints",
    type=click.Choice(
        [StubFileGenerator.ident, InlineGenerator.ident, EvaluationInlineGenerator.ident], case_sensitive=False
    ),
    required=True,
)
@click.option(
    "-v",
    "--verbose",
    help="DEBUG if not given, else CRITICAL",
    is_flag=True,
    callback=lambda ctx, _, val: logging.DEBUG if val else logging.INFO,
    required=False,
    default=False,
)
def main(**params):
    projpath, verb, strat_name, unifiers = (
        params["path"],
        params["verbose"],
        params["gen_strat"],
        params["unifiers"],
    )

    logging.basicConfig(level=verb)
    logging.debug(f"{projpath=}, {verb=}, {strat_name=} {unifiers=}")

    # Load config
    pytypes_cfg = ptconfig.load_config(projpath / CONFIG_FILE_NAME)

    unifier_lookup: dict[str, ptconfig.Unifier]
    if pytypes_cfg.unifier is not None:
        unifier_lookup = {u.name: u for u in pytypes_cfg.unifier}
        print(pytypes_cfg.unifier)
    else:
        logging.warning(f"No unifiers were found in {CONFIG_FILE_NAME}")
        unifier_lookup = dict()

    filters: list[TraceDataFilter] = list()

    for name in unifiers:
        attrs = unifier_lookup[name]
        impl = TraceDataFilter(
            ident=attrs.kind,
            **attrs.__dict__,
            stdlib_path=pytypes_cfg.pytypes.stdlib_path,
            proj_path=pytypes_cfg.pytypes.proj_path,
            venv_path=pytypes_cfg.pytypes.venv_path,
        )

        filters.append(impl)

    traced_df_folder = pathlib.Path(pytypes_cfg.pytypes.proj_path)
    collector = TraceDataFileCollector()
    collector.collect_data(traced_df_folder, include_also_files_in_subdirectories=True)

    td_df = collector.trace_data
    print(td_df)

    filter_list = TraceDataFilter(ident=TraceDataFilterList.ident, filters=filters)
    filtered = filter_list.apply(collector.trace_data)

    typegen = TypeHintGenerator(ident=strat_name, types=filtered)
    typegen.apply(pytypes_cfg.pytypes.proj_path)
