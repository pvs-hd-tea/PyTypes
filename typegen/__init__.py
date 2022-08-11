import logging

import click
import pathlib

import constants

from tracing import ptconfig

from typegen.unification import TraceDataFilter
from typegen.unification.drop_dupes import DropDuplicatesFilter
from typegen.unification.drop_test_func import DropTestFunctionDataFilter
from typegen.unification.drop_vars import DropVariablesOfMultipleTypesFilter
from typegen.unification.subtyping import ReplaceSubTypesFilter
from typegen.trace_data_file_collector import TraceDataFileCollector

from .strats.stub import StubFileGenerator
from .strats.inline import InlineGenerator

__all__ = [
    TraceDataFileCollector.__name__,
    DropDuplicatesFilter.__name__,
    DropTestFunctionDataFilter.__name__,
    DropVariablesOfMultipleTypesFilter.__name__,
    ReplaceSubTypesFilter.__name__,
]


@click.command(name="typegen", help="Collects trace data files in directories")
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
    "-s",
    "--subdirs",
    help="Go down the directory tree of the tests, instead of staying in the first level",
    is_flag=True,
    required=False,
    default=True,
)
@click.option(
    "-u",
    "--unifiers",
    help=f"Unifier to apply, as given by `name` in {constants.CONFIG_FILE_NAME} under [[unifier]]",
    multiple=True,
    required=True,
)
@click.option(
    "-g",
    "--gen-strat",
    help="Select a strategy for generating type hints",
    type=click.Choice(
        [StubFileGenerator.ident, InlineGenerator.ident], case_sensitive=False
    ),
    required=True,
)
@click.option(
    "-v",
    "--verbose",
    help="INFO if not given, else CRITICAL",
    is_flag=True,
    callback=lambda ctx, _, val: logging.DEBUG if val else logging.INFO,
    required=False,
    default=False,
)
def main(**params):
    projpath, verb, strat_name, subdirs, unifiers = (
        params["path"],
        params["verbose"],
        params["gen_strat"],
        params["subdirs"],
        params["unifiers"],
    )

    logging.basicConfig(level=verb)
    logging.debug(f"{projpath=}, {verb=}, {strat_name=} {subdirs=} {unifiers=}")

    # Load config
    pytypes_cfg = ptconfig.load_config(projpath / constants.CONFIG_FILE_NAME)

    unifier_lookup: dict[str, ptconfig.Unifier]
    if pytypes_cfg.unifier is not None:
        unifier_lookup = {u.name: u for u in pytypes_cfg.unifier}
    else:
        logging.warning(f"No unifiers were found in {constants.CONFIG_FILE_NAME}")
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

    traced_df_folder = pathlib.Path(pytypes_cfg.pytypes.project)
    collector = TraceDataFileCollector()
    collector.collect_trace_data(traced_df_folder, subdirs)

    print(collector.trace_data)
    return
