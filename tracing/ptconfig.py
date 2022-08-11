from dataclasses import dataclass, field, asdict
import pathlib

import dacite
import toml

import constants


@dataclass
class Config:
    project: str
    output_template: str = field(
        default="pytypes/{project}/{func_name}" + constants.TRACE_DATA_FILE_ENDING
    )


@dataclass
class PyTypesToml:
    pytypes: Config


def _load_config(config_path: pathlib.Path) -> PyTypesToml:
    cfg = toml.load(config_path.open())
    return dacite.from_dict(
        data_class=PyTypesToml, data=cfg, config=dacite.Config(strict=True)
    )


def _write_config(config_path: pathlib.Path, pttoml: PyTypesToml):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    toml.dump(asdict(pttoml), config_path.open("w"))
