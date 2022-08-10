from dataclasses import dataclass, field, asdict
import pathlib
import typing

import dacite
from dacite.exceptions import DaciteError
import toml

import constants


@dataclass
class PyTypes:
    project: str

    stdlib_path: pathlib.Path
    proj_path: pathlib.Path
    venv_path: pathlib.Path

    output_template: str = field(
        default="pytypes/{project}/{func_name}" + constants.TRACE_DATA_FILE_ENDING
    )


@dataclass
class Dedup:
    kind: typing.Literal["dedup"] = "dedup"


@dataclass
class DropTest:
    test_name_pat: str
    kind: typing.Literal["drop_test"] = "drop_test"


@dataclass
class DropVars:
    kind: typing.Literal["drop_mult_var"] = "drop_mult_var"
    min_amount_types_to_drop: int | None = 2


@dataclass
class ReplaceSubtypes:
    kind: typing.Literal["repl_subty"] = "repl_subty"
    only_replace_if_base_was_traced: bool | None = False


# https://github.com/konradhalas/dacite/pull/184
# the cooler union syntax is not supported
Unifier = typing.Union[Dedup, DropTest, DropVars, ReplaceSubtypes]


@dataclass
class TomlCfg:
    pytypes: PyTypes
    unifier: list[Unifier] = field(default_factory=list)


def load_config(config_path: pathlib.Path) -> TomlCfg:
    cfg = toml.load(config_path.open())

    try:
        return dacite.from_dict(
            data_class=TomlCfg,
            data=cfg,
            config=dacite.Config(
                cast=[pathlib.Path],
                strict=True,
                strict_unions_match=True,
            ),
        )

    except DaciteError as e:
        print(f"Failed to load config from {config_path}. Here is the schema:\n")
        raise e


def write_config(config_path: pathlib.Path, pttoml: TomlCfg):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    ad = asdict(pttoml)
    ad["pytypes"].pop("output_template")
    toml.dump(ad, config_path.open("w"))
