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

    def __init__(self, recurse_into_subdirs: bool = True):
        self.globber = pathlib.Path.rglob if recurse_into_subdirs else pathlib.Path.glob

    def apply(self, project: Project):
        assert project.test_directory is not None

        for path in filter(
            self._is_test_file, self.globber(project.test_directory, "*")
        ):
            self._apply(path)

        cfg_path = project.root / constants.CONFIG_FILE_NAME
        pts = PyTypes(
            project=project.root.name,
            proj_path=project.root,
            stdlib_path=pathlib.Path("stdlib", "goes", "here"),
            venv_path=pathlib.Path("venv", "goes", "here"),
        )

        toml = TomlCfg(pts, unifier=None)  # type: ignore
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
    SYS_IMPORT = ast.parse("import sys").body[0]
    PYTYPE_IMPORTS = ast.parse("from tracing import decorators").body[0]

    def __init__(self, pytest_root: pathlib.Path, recurse_into_subdirs: bool = True):
        super().__init__(recurse_into_subdirs)

        self.pytest_root = pytest_root
        self.decorator_appended_file_paths: list[pathlib.Path] = []

        self.sys_path_ext_node = ast.parse(f"sys.path.append('{self.pytest_root}')\n").body[0]
        self.append_register_decorator_transformer = AppendDecoratorTransformer(
            PyTestStrategy.FUNCTION_PATTERN
        )

    def _apply(self, path: pathlib.Path) -> None:
        with path.open() as file:
            file_content = file.read()

        file_ast = ast.parse(file_content)
        file_ast = self.append_register_decorator_transformer.visit(file_ast)
        self._add_nodes_necessary_for_tracing(file_ast)
        file_content = ast.unparse(file_ast)

        output = path
        with output.open("w") as file:
            file.write(file_content)

        self.decorator_appended_file_paths.append(output)

    def _is_test_file(self, path: pathlib.Path) -> bool:
        if path.name.startswith("test_"):
            return path.name.endswith(".py")

        return path.name.endswith("_test.py")

    def _add_nodes_necessary_for_tracing(
        self, abstract_syntax_tree: ast.Module
    ) -> None:
        """Appends the imports, sys path extension statement and the entrypoint to the provided AST."""
        abstract_syntax_tree.body.insert(0, PyTestStrategy.SYS_IMPORT)
        abstract_syntax_tree.body.insert(1, self.sys_path_ext_node)
        abstract_syntax_tree.body.insert(2, PyTestStrategy.PYTYPE_IMPORTS)


class AppendDecoratorTransformer(ast.NodeTransformer):
    """
    Transforms an AST such that the register decorator is appended on each test function.
    """

    TRACE = "decorators.trace"

    def __init__(self, test_function_name_pattern: Pattern[str]):
        self.test_function_name_pattern: Pattern[str] = test_function_name_pattern
        self.register_decorator_node = ast.Name(
            AppendDecoratorTransformer.TRACE
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Called on visiting a function definition node.
        Adds the register decorator to the decorator list if function name matches test function name pattern."""
        if re.match(self.test_function_name_pattern, node.name):
            node.decorator_list.append(self.register_decorator_node)
        return node
