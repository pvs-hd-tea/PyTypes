import logging
import click
import pathlib
from typegen.trace_data_file_collector import TraceDataFileCollector

__all__ = [
    TraceDataFileCollector.__name__,
]


@click.command(name="typegen", help="Collects trace data files in directories")
@click.option(
    "-p",
    "--path",
    type=click.Path(exists=True, dir_okay=True, writable=False, readable=True, path_type=pathlib.Path),
    help="Path to directory",
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
    "-v",
    "--verbose",
    help="INFO if not given, else CRITICAL",
    is_flag=True,
    callback=lambda ctx, _, val: logging.INFO if val else logging.CRITICAL,
    required=False,
    default=False,
)
def main(**params):
    path, verb, subdirs = (
        params["path"],
        params["verbose"],
        params["subdirs"],
    )

    logging.basicConfig(level=verb)

    logging.debug(f"{path=}, {verb=}, {subdirs=}")

    collector = TraceDataFileCollector()
    collector.collect_trace_data(path, subdirs)
    print(collector.trace_data)
