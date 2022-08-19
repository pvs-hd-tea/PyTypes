import pathlib
import typing
from pathlib import Path
from pathlib import PosixPath, WindowsPath
import numpy as np
from typegen import evaluation
from tests.resource.typegen.evaluation.file_type_hints_collector.sample_to_import import FileTypeHintsCollector
from typegen.evaluation import FileTypeHintsCollector
from tests.resource.typegen.evaluation.file_type_hints_collector import MetricDataCalculator
from typing import Optional


class MetricDataCalculator:
    pass

from typegen.evaluation.metric_data_calculator import MetricDataCalculator


class A:
    def __init__(self):
        self.string: WindowsPath = WindowsPath("string")
        self.array: np.ndarray = np.zeros((3, 3))
        self.not_annotated_member = False

        w: MetricDataCalculator.A = ...
        x: evaluation.FileTypeHintsCollector = ...
        y: MetricDataCalculator = MetricDataCalculator()
        z: FileTypeHintsCollector = FileTypeHintsCollector()

    def function(self, a: pathlib.Path, b: Path) -> bool:
        c: Optional[bool]; d = a == b, 10
        e: dict[str, evaluation.FileTypeHintsCollector] = ...
        if True:
            e: int | str | float | None = 12
        e: typing.Union[bool | np.ndarray, typing.Optional[str]] = False
        f: object = None; g: float = 3.14
        h: typing.Union[list[str], dict[None | evaluation.FileTypeHintsCollector, dict[float, Optional[bool | int]]]] = ...
        return c


class B(A):
    def function(self, a: pathlib.Path, b: Path) -> bool:
        return not super().function(a, b)


def evaluate(instance: A) -> None:
    pass


def main():
    instance1: A = A()
    instance2: B = B()
    evaluate(instance1)
    evaluate(instance2)
    assert instance1.function(Path("a"), PosixPath("a"))
    assert not instance2.function(Path("a"), PosixPath("a"))
