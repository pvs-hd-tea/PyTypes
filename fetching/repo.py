from abc import ABC, abstractmethod

import logging
import requests
import pathlib
import tempfile
import typing
import shutil

import git
import tqdm  # type: ignore

from .projio import Project


class Repository(ABC):
    def __init__(self, project_url: str):
        self.project_url = project_url

    def fetch(self, output: pathlib.Path) -> Project:
        """
        Download the project from the URL specified in the constructor
        and store it in the path specified by output
        """
        td = self._fetch()
        self._write_to(td, output)

        return Project(output)

    @property
    @abstractmethod
    def fmt(self) -> str:
        """
        Attribute indicating format of repository.
        Implement using `fmt = "THIS_REPOS_FORMAT"` in the derived class.
        """
        pass

    @abstractmethod
    def _fetch(self) -> tempfile.TemporaryDirectory:
        """
        Fetch the project at the specified URL, and store it under a temporary directory
        """
        pass

    def _write_to(
        self, intermediary: tempfile.TemporaryDirectory, output: pathlib.Path
    ):
        output.mkdir(parents=True, exist_ok=True)

        inter_path = pathlib.Path(intermediary.name)
        for inpath in inter_path.iterdir():
            relpath = inpath.relative_to(inter_path)
            outpath = output / relpath

            shutil.move(inpath, outpath)


class GitRepository(Repository):
    def __init__(self, project_url: str):
        super().__init__(project_url)
        self.pbar = None

    fmt = "Git"

    def _fetch(self) -> tempfile.TemporaryDirectory:
        td = tempfile.TemporaryDirectory()
        git.Repo.clone_from(self.project_url, td.name, progress=self._progress())
        return td

    def _progress(self) -> typing.Callable:
        if logging.root.isEnabledFor(logging.INFO):
            self.pbar = tqdm.tqdm()
            return self._info_progress

        return self._sentinel_progress

    def _info_progress(self, _, cur_count: int, max_count: int, message: str) -> None:
        assert self.pbar is not None

        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.desc = message
        self.pbar.refresh()

    def _sentinel_progress(
        self, _, cur_count: int, max_count: int, message: str
    ) -> None:
        return None


class ArchiveRepository(Repository):
    def __init__(self, project_url: str):
        super().__init__(project_url)

    fmt = "Archive"

    def _fetch(self) -> tempfile.TemporaryDirectory:
        td = tempfile.TemporaryDirectory()
        git.Repo.clone_from(self.project_url, td.name, depth=1)
        return td


def repository_factory(project_url: str, fmt: str | None) -> Repository:
    if fmt == GitRepository.fmt or project_url.endswith(".git"):
        logging.info(f"Interpreted {project_url} as Git repository")
        return GitRepository(project_url)

    if fmt == ArchiveRepository.fmt or project_url.endswith((".tar.gz", ".zip")):
        logging.info(f"Interpreted {project_url} as an URL to an archive")
        return ArchiveRepository(project_url)

    raise LookupError(f"Unsupported repository format: {project_url}")
