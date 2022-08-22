import logging
import pathlib

import click

from .repo import LocalFolder, Repository, GitRepository, ArchiveRepository
from .detector import TestDetector

__all__ = [Repository.__name__]
ORIGINAL_REPOSITORY_FOLDER_NAME = "Original"


@click.command(name="fetch", help="download repositories and apply tracing decorators")
@click.option(
    "-u",
    "--uri",
    type=str,
    help="URI to code resource",
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
    type=click.Choice([GitRepository.fmt, ArchiveRepository.fmt, LocalFolder.fmt], case_sensitive=False),
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
    "-e",
    "--eval",
    help="Instead of generating one copy, generate two copies: The original & the repository for tracing",
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
    url, fmt, out, verb, notraverse, evaluate = (
        params["uri"],
        params["format"],
        params["output"],
        params["verbose"],
        params["no_traverse"],
        params["eval"]
    )
    logging.basicConfig(level=verb)

    logging.debug(f"{url=}, {fmt=}, {out=}, {verb=}, {notraverse=}")

    repo = Repository.factory(project_uri=url, fmt=fmt)

    traceable_output_path = out
    if evaluate:
        original_repo_path = out / ORIGINAL_REPOSITORY_FOLDER_NAME
        repo.fetch(original_repo_path)
        traceable_output_path /= traceable_output_path.name

    project = repo.fetch(traceable_output_path)

    detector = TestDetector.factory(proj=project)
    strategy = detector.create_strategy(recurse_into_subdirs=not notraverse)
    strategy.apply(project)
