import pytest

import fetching

import repoutils


# TODO: Convert to setup / teardown
def test_numpy_repo_is_git():
    np_path = repoutils.create_repo("numpy")

    np_repo = fetching.Repository.factory(r"https://github.com/numpy/numpy.git")
    assert isinstance(np_repo, fetching.GitRepository), f"Failed to detect numpy GitHub URL as such"

    np_repo.fetch(np_path)

    # Basic check for contents of repo, requires knowledge thereof
    assert (np_path / "pyproject.toml").is_file()

    repoutils.delete_repo(np_path)


def test_pandas_repo_is_git():
    pandas_path = repoutils.create_repo("pandas")

    np_repo = fetching.Repository.factory(r"https://github.com/pandas-dev/pandas.git")
    assert isinstance(np_repo, fetching.GitRepository), f"Failed to detect pandas GitHub URL as such"

    np_repo.fetch(pandas_path)

    # Basic check for contents of repo, requires knowledge thereof
    assert (pandas_path / "pyproject.toml").is_file()

    repoutils.delete_repo(pandas_path)


""" class NumpyTest(repotest.RepoTest):
    @pytest.mark.dependency
    def test_factory(self, setUp):
        self.np_repo = fetching.Repository.factory(
            r"https://github.com/numpy/numpy.git"
        )
        assert isinstance(
            np_repo, GitRepository
        ), f"Failed to detect numpy GitHub URL as such"

    @pytest.mark.dependency(depends=["test_factory"])
    def test_fetch(self, setUp):
        project = self.np_repo.fetch(self.repo_path) """
