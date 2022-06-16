import pathlib


class Project:
    """
    Represents a downloaded Python repository.
    Use for more intuitive navigation of the project
    """

    def __init__(self, root: pathlib.Path):
        self.root = root

    @property
    def test_directory(self) -> pathlib.Path | None:
        if (p := self.root / "tests").is_dir():
            return p

        return None