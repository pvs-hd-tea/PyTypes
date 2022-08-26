import typing
from typing import Optional
import numpy as np
from typegen import evaluation

a: Optional[bool] = ...
b: dict[str, evaluation.FileTypeHintsCollector] = ...
c: int | str | float | None = 12
d: typing.Union[bool | np.ndarray, typing.Optional[str]] = False
e: typing.Union[list[str], dict[None | evaluation.FileTypeHintsCollector, dict[float, Optional[bool | int]]]] = ...
e: str | typing.Optional[object] = "a"
