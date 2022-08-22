from abc import ABC, abstractmethod
import logging
import os
import requests
import pathlib
import tempfile
import typing
import shutil
import zipfile

import git
import tqdm

from .projio import Project


class Repository(ABC):
    def __init__(self, project_uri: str):
        self.project_uri = project_uri

    def fetch(self, output: pathlib.Path) -> Project:
        """
        Download the project from the URL specified in the constructor
        and store it in the path specified by output
        """
        td = self._fetch()
        self._write_to(td, output)

        return Project(output)

    @staticmethod
    def factory(project_uri: str, fmt: str | None = None) -> "Repository":
        if fmt == GitRepository.fmt or project_uri.endswith(".git"):
            logging.info(f"Interpreted {project_uri} as Git repository")
            return GitRepository(project_uri)

        if fmt == ArchiveRepository.fmt or project_uri.endswith((".tar.gz", ".zip")):
            logging.info(f"Interpreted {project_uri} as an URL to an archive")
            return ArchiveRepository(project_uri)

        if fmt == LocalFolder.fmt or pathlib.Path(project_uri).is_dir():
            logging.info(f"Interpreted {project_uri} as a path to a local directory")
            return LocalFolder(project_uri)

        raise LookupError(f"Unsupported repository format: {project_uri}")

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
        if output.is_dir():
            shutil.rmtree(str(output))
        output.mkdir(parents=True, exist_ok=True)
        shutil.copytree(intermediary.name, str(output), dirs_exist_ok=True)


class GitRepository(Repository):
    def __init__(self, project_uri: str):
        super().__init__(project_uri)
        self.pbar = None

    fmt = "Git"

    def _fetch(self) -> tempfile.TemporaryDirectory:
        td = tempfile.TemporaryDirectory()

        # https://stackoverflow.com/questions/28291909/gitpython-and-ssh-keys
        git_ssh_cmd = f"ssh -i {os.path.expanduser('~/.ssh/id_rsa')}"

        with git.Git().custom_environment(GIT_SSH_CMD=git_ssh_cmd):
            git.Repo.clone_from(
                self.project_uri,
                td.name,
                progress=self._progress(),
                env={"GIT_SSH_COMMAND": git_ssh_cmd},
                depth=1,
            )
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
    def __init__(self, project_uri: str):
        super().__init__(project_uri)

    fmt = "Archive"

    def _fetch(self) -> tempfile.TemporaryDirectory:
        td = tempfile.TemporaryDirectory()
        if (r := requests.get(self.project_uri, stream=True)).status_code == 200:
            output = pathlib.Path(td.name) / "repo.zip"
            logging.debug(f"Storing in {output}")

            with output.open("wb") as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)

            zf = zipfile.ZipFile(output)
            zf.extractall(td.name)

            paths = list(map(pathlib.Path, zf.namelist()))

            logging.debug(f"Removing intermediary archive {output}")
            output.unlink()

            self._handle_singledir(td, paths)

        else:
            logging.error(f"Failed to download archive from {self.project_uri}")
            raise RuntimeError(r.content)

        return td

    def _handle_singledir(
        self, temp_output: tempfile.TemporaryDirectory, paths: list[pathlib.Path]
    ):
        logging.debug("Extracted files from archive")
        if paths and all(paths[0].parts[0] == path.parts[0] for path in paths):
            logging.debug("Detected singular folder in archive; exploding archive")

            # Skip moving the root folder into itself
            output_path = pathlib.Path(temp_output.name)
            in_path = output_path / paths[0].parts[0]

            for subdir in in_path.iterdir():
                relpath = subdir.relative_to(in_path)
                to_path = output_path / pathlib.Path(*relpath.parts[1:])
                shutil.move(subdir, to_path)


class LocalFolder(Repository):
    fmt = "Local"

    def __init__(self, filepath: str):
        super().__init__(filepath)

    def _fetch(self) -> tempfile.TemporaryDirectory:
        td = tempfile.TemporaryDirectory()
        shutil.copytree(self.project_uri, td.name, dirs_exist_ok=True)
        return td
