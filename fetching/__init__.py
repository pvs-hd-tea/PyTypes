import logging
import pathlib

import click

from .repo import repository_factory, Repository, GitRepository, ArchiveRepository
from .detector import detector_factory

__all__ = [repository_factory.__name__, Repository.__name__]


@click.command(name="fetch", help="download repositories and apply tracing decorators")
@click.option(
    "-u",
    "--url",
    type=str,
    help="URL to a repository",
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
    "-o",
    "--output",
    type=click.Path(exists=False, dir_okay=True, writable=True, path_type=pathlib.Path),
    help="Download output path",
    required=True,
)
@click.option(
    "-v",
    "--verbose",
    help="Each occurrence increases the logging level from NOTSET to CRITICAL",
    is_flag=True,
    callback=lambda ctx, _, val: logging.INFO if val else logging.CRITICAL,
    required=False,
    default=False,
)
def main(**params):
    url, fmt, out, verb = (
        params["url"],
        params["format"],
        params["output"],
        params["verbose"],
    )
    logging.basicConfig(level=verb)

    repo = repository_factory(project_url=url, fmt=fmt)
    project = repo.fetch(out)

    detector = detector_factory(proj=project)
    strategy = detector.create_strategy()
    strategy.apply(project)
