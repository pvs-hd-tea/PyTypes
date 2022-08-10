import ast
from abc import ABC, abstractmethod
import pathlib
import re
from re import Pattern

from .projio import Project
import constants
from tracing.ptconfig import write_config, TomlCfg, PyTypes


class ApplicationStrategy(ABC):
    """
    Implement for a specific test framework;
    When given a file that uses the specified framework,
    parse this file and insert code that will cause the test
    functions to be traced upon execution.
    """

    def __init__(self, overwrite_tests: bool = True, recurse_into_subdirs: bool = True):
        self.overwrite_tests = overwrite_tests
        self.globber = pathlib.Path.rglob if recurse_into_subdirs else pathlib.Path.glob

    def apply(self, project: Project):
        assert project.test_directory is not None
        for path in filter(
            self._is_test_file, self.globber(project.test_directory, "*")
        ):
            self._apply(path)

        cfg_path = project.root / constants.CONFIG_FILE_NAME
        toml = TomlCfg(pytypes=PyTypes(project=project.root.name))
        write_config(cfg_path, toml)

    @abstractmethod
    def _apply(self, path: pathlib.Path) -> None:
        """Perform IO operation to modify the file pointed to by path"""
        pass

    @abstractmethod
    def _is_test_file(self, path: pathlib.Path) -> bool:
        """True iff path is a file / folder that will be executed by the framework"""
        pass


class PyTestStrategy(ApplicationStrategy):
    FUNCTION_PATTERN = constants.PYTEST_FUNCTION_PATTERN
    SYS_IMPORT = "import sys"
    PYTYPE_IMPORTS = "from tracing import register, entrypoint"
    SUFFIX = "_decorator_appended.py"
    ENTRYPOINT = "@entrypoint()\ndef main():\n  ...\n"

    def __init__(
        self,
        pytest_root: pathlib.Path,
        overwrite_tests: bool = True,
        recurse_into_subdirs: bool = True,
    ):
        super().__init__(overwrite_tests, recurse_into_subdirs)

        self.pytest_root = pytest_root
        self.decorator_appended_file_paths: list[pathlib.Path] = []
        sys_path_ext = f"sys.path.append('{self.pytest_root}')\n"

        self.sys_import_node = ast.parse(PyTestStrategy.SYS_IMPORT)
        self.pytype_imports_node = ast.parse(PyTestStrategy.PYTYPE_IMPORTS)
        self.entrypoint_node = ast.parse(PyTestStrategy.ENTRYPOINT)
        self.sys_path_ext_node = ast.parse(sys_path_ext)
        self.append_register_decorator_transformer = AppendRegisterDecoratorTransformer(
            PyTestStrategy.FUNCTION_PATTERN
        )

    def _apply(self, path: pathlib.Path) -> None:
        with path.open() as file:
            file_content = file.read()

        file_ast = ast.parse(file_content)
        file_ast = self.append_register_decorator_transformer.visit(file_ast)
        self._append_nodes_necessary_for_tracing(file_ast)
        file_content = ast.unparse(file_ast)

        if self.overwrite_tests:
            output = path
        else:
            output = path.parent / f"{path.stem}{PyTestStrategy.SUFFIX}"

        # logging.debug(f"{path} -> {output}")

        with output.open("w") as file:
            file.write(file_content)

        self.decorator_appended_file_paths.append(output)

    def _is_test_file(self, path: pathlib.Path) -> bool:
        if path.name.startswith("test_") and path.name.endswith(".py"):
            return not path.name.endswith(PyTestStrategy.SUFFIX)

        return path.name.endswith("_test.py")

    def _append_nodes_necessary_for_tracing(
        self, abstract_syntax_tree: ast.Module
    ) -> None:
        """Appends the imports, sys path extension statement and the entrypoint to the provided AST."""
        abstract_syntax_tree.body.insert(0, self.sys_import_node)  # type: ignore
        abstract_syntax_tree.body.insert(1, self.sys_path_ext_node)  # type: ignore
        abstract_syntax_tree.body.insert(2, self.pytype_imports_node)  # type: ignore
        abstract_syntax_tree.body.append(self.entrypoint_node)  # type: ignore


class AppendRegisterDecoratorTransformer(ast.NodeTransformer):
    """
    Transforms an AST such that the register decorator is appended on each test function.
    """

    REGISTER = "register()"

    def __init__(self, test_function_name_pattern: Pattern[str]):
        self.test_function_name_pattern: Pattern[str] = test_function_name_pattern
        self.register_decorator_node = ast.Name(
            AppendRegisterDecoratorTransformer.REGISTER
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Called on visiting a function definition node.
        Adds the register decorator to the decorator list if function name matches test function name pattern."""
        if re.match(self.test_function_name_pattern, node.name):
            node.decorator_list.append(self.register_decorator_node)
        return node
