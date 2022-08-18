import logging
import pathlib

import click

from .repo import Repository, GitRepository, ArchiveRepository
from .detector import TestDetector

__all__ = [Repository.__name__]


@click.command(name="fetch", help="download repositories and apply tracing decorators")
@click.option(
    "-u",
    "--url",
    type=str,
    help="URL to a repository",
    required=True,
)
@click.option(
    "-o",
    "--output",
    type=click.Path(exists=False, dir_okay=True, writable=True, path_type=pathlib.Path),
    help="Download output path",
    required=True,
)
@click.option(
    "-f",
    "--format",
    type=click.Choice([GitRepository.fmt, ArchiveRepository.fmt], case_sensitive=False),
    help="Indicate repository format explicitly",
    required=False,
    default=None,
)
@click.option(
    "-n",
    "--no-traverse",
    help="Do not go down the directory tree of the tests, instead stay in the first level",
    is_flag=True,
    required=False,
    default=False,
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
    url, fmt, out, verb, notraverse = (
        params["url"],
        params["format"],
        params["output"],
        params["verbose"],
        params["no_traverse"]
    )
    logging.basicConfig(level=verb)

    logging.debug(f"{url=}, {fmt=}, {out=}, {verb=}, {notraverse=}")

    repo = Repository.factory(project_url=url, fmt=fmt)
    project = repo.fetch(out)

    detector = TestDetector.factory(proj=project)
    strategy = detector.create_strategy(recurse_into_subdirs=not notraverse)
    strategy.apply(project)
