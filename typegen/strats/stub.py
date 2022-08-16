import pathlib
import libcst as cst
from mypy import stubgen
import constants
from tracing.ptconfig import load_config
from typegen.strats.inline import InlineGenerator


def _get_temp_folder_path(root: pathlib.Path) -> pathlib.Path:
    cfg = load_config(root / constants.CONFIG_FILE_NAME)
    if cfg.pytypes.proj_path != root:
        raise RuntimeError(
            f"Invalid config file: wrong project root: Program has been executed in {root}, "
            f"but config file has {cfg.pytypes.proj_path} set"
        )

    return root / StubFileGenerator.RELATIVE_TEMP_FOLDER_PATH


def validate_temp_file_path(temp_file_path: pathlib.Path) -> None:
    if temp_file_path.exists():
        assert temp_file_path.is_file()
        assert temp_file_path.stat().st_size == 0, f"{temp_file_path} is not empty!"


class StubFileGenerator(InlineGenerator):
    """Generates stub files using mypy.stubgen."""
    RELATIVE_TEMP_FOLDER_PATH = pathlib.Path("pytypes") / "typegen" / "stub" / "temp"
    TEMP_PY_FILENAME = "temp.py"
    ident = "stub"

    def _store_hinted_ast(self, source_file: pathlib.Path, hinting: cst.Module) -> None:
        # Stub means generating a stub without overwriting the original
        root = pathlib.Path.cwd()

        temp_folder_path = _get_temp_folder_path(root)
        temp_folder_path.mkdir(parents=True, exist_ok=True)

        temp_py_file_path = temp_folder_path / StubFileGenerator.TEMP_PY_FILENAME

        validate_temp_file_path(temp_py_file_path)

        super()._store_hinted_ast(temp_py_file_path, hinting)

        options = stubgen.parse_options([str(temp_py_file_path)])
        mypy_opts = stubgen.mypy_options(options)

        module = stubgen.StubSource("temp", str(temp_py_file_path))

        stubgen.generate_asts_for_modules([module], False, mypy_opts, options.verbose)
        assert module.path is not None, "Not found module was not skipped"
        relative_source_file_path = str(source_file.relative_to(root).with_suffix(".pyi"))

        with stubgen.generate_guarded(module.module, relative_source_file_path):
            stubgen.generate_stub_from_ast(module, relative_source_file_path, False, options.pyversion)

        temp_py_file_path.open("w").close()
