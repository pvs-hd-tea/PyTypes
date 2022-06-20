import pytest

import fetching

import repoutils


def test_numpy_zip_is_archive():
    np_path = repoutils.create_repo("numpy-zip")

    np_repo = fetching.Repository.factory(
        r"https://github.com/numpy/numpy/archive/refs/heads/main.zip"
    )
    assert isinstance(
        np_repo, fetching.ArchiveRepository
    ), f"Failed to detect numpy archive URL as such"

    np_repo.fetch(np_path)

    # Basic check for contents of repo, requires knowledge thereof
    assert (np_path / "pyproject.toml").is_file()

    repoutils.delete_repo(np_path)
