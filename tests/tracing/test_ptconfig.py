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
        "/",
        "home",
        "benji",
        ".cache",
        "pypoetry",
        "virtualenvs",
        "pytypes-xvtnrWJT-py3.10",
    )

    assert len(config.unifier) == 6

    assert isinstance(config.unifier[0], ptconfig.Dedup)
    assert config.unifier[0].name == "remove_dups"
    assert config.unifier[0].kind == "dedup"

    assert isinstance(config.unifier[1], ptconfig.DropTest)
    assert config.unifier[1].name == "ignore_test"
    assert config.unifier[1].kind == "drop_test"
    assert config.unifier[1].test_name_pat == "test_"

    assert isinstance(config.unifier[2], ptconfig.DropVars)
    assert config.unifier[2].name == "drop_implicit_2"
    assert config.unifier[2].kind == "drop_mult_var"
    assert config.unifier[2].min_amount_types_to_drop == 2

    assert isinstance(config.unifier[3], ptconfig.DropVars)
    assert config.unifier[3].name == "drop_explicit_5"
    assert config.unifier[3].kind == "drop_mult_var"
    assert config.unifier[3].min_amount_types_to_drop == 5

    assert isinstance(config.unifier[4], ptconfig.ReplaceSubtypes)
    assert config.unifier[4].name == "replace_subtypes_relaxed"
    assert config.unifier[4].kind == "repl_subty"
    assert config.unifier[4].only_replace_if_base_was_traced == False

    assert isinstance(config.unifier[5], ptconfig.ReplaceSubtypes)
    assert config.unifier[5].name == "replace_subtypes_strict"
    assert config.unifier[5].kind == "repl_subty"
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
        "/",
        "home",
        "benji",
        ".cache",
        "pypoetry",
        "virtualenvs",
        "pytypes-xvtnrWJT-py3.10",
    )

    assert len(config.unifier) == 0
