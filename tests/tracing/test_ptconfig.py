import pathlib

from tracing import ptconfig



def test_full():
    config_path = pathlib.Path("tests", "resource", "configs", "example.toml")
    config = ptconfig.load_config(config_path)

    assert config.pytypes.project == "PyTypes"
    assert config.pytypes.stdlib_path == pathlib.Path("/", "usr", "lib", "python3.10")
    assert config.pytypes.proj_path == pathlib.Path(
        "/", "home", "benji", "Documents", "Uni", "heidelberg", "04", "pytype", "repo"
    )
    assert config.pytypes.venv_path == pathlib.Path(
        "/", "home", "benji", ".cache", "pypoetry", "virtualenvs", "pytypes-xvtnrWJT-py3.10"
    )

    assert len(config.unifier) == 6

    assert config.unifier[0].kind == "dedup"

    assert config.unifier[1].kind == "drop_test"
    assert config.unifier[1].test_name_pat == "test_"

    assert config.unifier[2].kind == "drop_mult_var"
    assert config.unifier[2].min_amount_types_to_drop == 2

    assert config.unifier[3].kind == "drop_mult_var"
    assert config.unifier[3].min_amount_types_to_drop == 5

    assert config.unifier[4].kind ==  "repl_subty"
    assert config.unifier[4].only_replace_if_base_was_traced == False

    assert config.unifier[5].kind ==  "repl_subty"
    assert config.unifier[5].only_replace_if_base_was_traced == True


def test_simple():
    config_path = pathlib.Path("tests", "resource", "configs", "simple.toml")
    config = ptconfig.load_config(config_path)

    assert config.pytypes.project == "PyTypes"
    assert config.pytypes.stdlib_path == pathlib.Path("/", "usr", "lib", "python3.10")
    assert config.pytypes.proj_path == pathlib.Path(
        "/", "home", "benji", "Documents", "Uni", "heidelberg", "04", "pytype", "repo"
    )
    assert config.pytypes.venv_path == pathlib.Path(
        "/", "home", "benji", ".cache", "pypoetry", "virtualenvs", "pytypes-xvtnrWJT-py3.10"
    )

    assert len(config.unifier) == 0