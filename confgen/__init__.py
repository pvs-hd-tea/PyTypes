import constants
import pathlib
import os
from tracing import ptconfig

import click


@click.command(name="confgen", help="generate pytypes.toml")
@click.option(
    "-p",
    "--project",
    type=click.Path(exists=False, dir_okay=True, writable=True, path_type=pathlib.Path),
    help="Project path (also used as output path)",
    required=True,
)
def main(**params):
    project: pathlib.Path = params["project"]
    stdlib = pathlib.Path(pathlib.__file__).parent
    venv = pathlib.Path(os.environ["VIRTUAL_ENV"])

    assert not stdlib.is_relative_to(project), "stdlib must be outside of pytypes"
    assert not venv.is_relative_to(project), "venv must be outside of pytypes"

    cfg = ptconfig.TomlCfg(
        pytypes=ptconfig.PyTypes(
            project=project.stem,
            proj_path=project.resolve(),
            stdlib_path=stdlib.resolve(),
            venv_path=venv.resolve(),
        ),
        unifier=[],
    )

    ptconfig.write_config(project / constants.CONFIG_FILE_NAME, cfg)
