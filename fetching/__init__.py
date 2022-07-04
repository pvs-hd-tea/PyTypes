from email.policy import default
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
    "--nooverwrite",
    help="Instead of overwriting tests, create new ones with a new suffix",
    is_flag=True,
    required=False,
    default=False,
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
    url, fmt, out, verb, no, subdirs = (
        params["url"],
        params["format"],
        params["output"],
        params["verbose"],
        params["nooverwrite"],
        params["subdirs"],
    )
    logging.basicConfig(level=verb)

    repo = Repository.factory(project_url=url, fmt=fmt)
    project = repo.fetch(out)

    detector = TestDetector.factory(proj=project)
    strategy = detector.create_strategy(
        overwrite_tests=no, recurse_into_subdirs=subdirs
    )
    strategy.apply(project)
