import pathlib

import pytest

_REPO_DUMP_ROOT = pathlib.Path("tests", "fetching", "repos")


def create_repo(project_name: str) -> pathlib.Path:
    repo_path = _REPO_DUMP_ROOT / project_name
    repo_path.mkdir(parents=True, exist_ok=True)

    return repo_path

def delete_repo(p: pathlib.Path):
    _delete_tree(p)

def _delete_tree(p: pathlib.Path):
    if p.is_file():
        p.unlink()
    else:
        for child in p.iterdir():
            _delete_tree(child)
        p.rmdir()
