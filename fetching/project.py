from abc import abstractmethod

import pathlib
import tempfile
import shutil

from .repositories import gitrepo


class Repository:
    def __init__(self, project_url: str):
        self.project_url = project_url

    @abstractmethod
    def fetch(self) -> tempfile.TemporaryDirectory:
        """
        Fetch the project at the specified URL, and store it under a temporary directory
        """
        pass

    def write_to(self, intermediary: tempfile.TemporaryDirectory, output: pathlib.Path, copy=False):
        method = shutil.copy if copy else shutil.move

        output.mkdir(parents=True, exist_ok=True)

        inter_path = pathlib.Path(intermediary.name)
        for inpath in inter_path.iterdir():
            relpath = each_file.relative_to(each_file)
            outpath = output / relpath

            method(inpath, outpath)


class GitRepository(Repository):
    def __init__(self, project_url: str):
        super().__init__(project_url)

    def fetch(self):


def repository_factory(project_url: str) -> Repository:
    if project_url.endswith(".git"):
        return GitRepository(project_url)

    raise LookupError(f"Unsupported repository format: {project_url}")