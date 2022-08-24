import enum
import logging
import libcst as cst
import libcst.matchers as m
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

    def __init__(self, pytest_root: pathlib.Path, recurse_into_subdirs: bool = True):
        super().__init__(recurse_into_subdirs)

        self.pytest_root = pytest_root

        self.sys_path_ext_node = cst.Expr(
            cst.parse_expression(f"sys.path.append('{self.pytest_root}')")
        )

    def _apply(self, path: pathlib.Path) -> None:
        # transformer is stateful, meaning it must be reinstantiated
        dec_trans = AppendDecoratorTransformer(
            PyTestStrategy.FUNCTION_PATTERN, self.sys_path_ext_node
        )

        with path.open() as f:
            content = f.read()
            file_ast = cst.parse_module(content)
            file_ast = file_ast.visit(dec_trans)

        with path.open("w") as f:
            f.write(file_ast.code)

    def _is_test_file(self, path: pathlib.Path) -> bool:
        if path.name.startswith("test_"):
            return path.name.endswith(".py")

        return path.name.endswith("_test.py")


ADT_LOGGER = logging.getLogger("AppendDecoratorTransformer")


class AppendDecoratorTransformer(cst.CSTTransformer):
    """
    Transforms an AST such that the trace decorator is appended on each test function.
    Additionally, imports are generated in the correct locations so that using
    the decorator is possible
    """

    TRACE_DECORATOR = cst.Decorator(
        decorator=cst.Attribute(value=cst.Name("decorators"), attr=cst.Name("trace"))
    )
    _FUTURE_IMPORT_MATCH = m.ImportFrom(module=m.Name(value="__future__"))

    SYS_IMPORT = cst.Import(names=[cst.ImportAlias(name=cst.Name("sys"))])
    PYTYPE_IMPORT = cst.ImportFrom(
        module=cst.Name("tracing"), names=[cst.ImportAlias(name=cst.Name("decorators"))]
    )

    class ImportStatus(enum.IntEnum):
        INVALID = 0

        # No preamble has been generated, and no
        # viable preamble insertion point has been found.
        # If the import-from is from __future__, the insertion point is not viable.
        CAN_NOT_ADD = 1
        # A fitting preamble insertion point has been found
        CAN_ADD = 2
        # The preamble has been added to the AST
        ALREADY_ADDED = 3

    def __init__(
        self,
        test_function_name_pattern: Pattern[str],
        sys_path_ext: cst.BaseSmallStatement,
    ):
        self.test_function_name_pattern: Pattern[str] = test_function_name_pattern
        self.nodes_to_add = [AppendDecoratorTransformer.SYS_IMPORT,
                        sys_path_ext,
                        AppendDecoratorTransformer.PYTYPE_IMPORT
                    ]
        self._import_status: AppendDecoratorTransformer.ImportStatus = (
            AppendDecoratorTransformer.ImportStatus.CAN_NOT_ADD
        )

    def leave_Module(self, _: cst.Module, updated_node: cst.Module) -> cst.Module:
        if self._import_status != AppendDecoratorTransformer.ImportStatus.ALREADY_ADDED:
            ADT_LOGGER.debug("Preamble has not yet been added: There aren't any tests.")
            self._import_status = AppendDecoratorTransformer.ImportStatus.ALREADY_ADDED
        return updated_node

    def visit_Import(self, node: cst.Import) -> bool | None:
        if self._import_status == AppendDecoratorTransformer.ImportStatus.CAN_NOT_ADD:
            self._import_status == AppendDecoratorTransformer.ImportStatus.CAN_ADD
        return True

    def leave_Import(
        self, _: cst.Import, updated_node: cst.Import
    ) -> cst.FlattenSentinel[cst.BaseSmallStatement]:
        return self._get_updated_node(updated_node)

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
        if self._import_status == AppendDecoratorTransformer.ImportStatus.CAN_NOT_ADD:
            if m.matches(node, AppendDecoratorTransformer._FUTURE_IMPORT_MATCH):
                ADT_LOGGER.debug(
                    "Detected from __future__ import ..., continuing search for insertion point"
                )
                assert (
                    self._import_status
                    == AppendDecoratorTransformer.ImportStatus.CAN_NOT_ADD
                )

            else:
                ADT_LOGGER.debug("ImportFrom detected that is unrelated to __future__")
                self._import_status = AppendDecoratorTransformer.ImportStatus.CAN_ADD

        return True

    def leave_ImportFrom(
        self, _: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.FlattenSentinel[cst.BaseSmallStatement] | cst.BaseSmallStatement:
        return self._get_updated_node(updated_node)

    def leave_FunctionDef(
        self, _: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FlattenSentinel[cst.BaseStatement] | cst.FunctionDef:
        """
        Called on visiting a function definition node.
        Adds the trace decorator to the decorator list if function name matches test function name pattern.

        Also acts as a breaker for AppendDecoratorTransformer.State.FUTURE_IMPORT_FROM_FOUND,
        i.e. if only imports so far have been from __future__ import ..., then insert the preamble before the function
        """
        if re.match(self.test_function_name_pattern, updated_node.name.value):
            ADT_LOGGER.debug(f"Adding decorator to {updated_node.name.value}")
            new_decs = list(updated_node.decorators) + [
                AppendDecoratorTransformer.TRACE_DECORATOR
            ]
            updated_node = updated_node.with_changes(decorators=new_decs)

        else:
            ADT_LOGGER.debug(f"Skipping adding decorator to {updated_node.name.value}")

        if self._import_status == AppendDecoratorTransformer.ImportStatus.CAN_NOT_ADD:
            ADT_LOGGER.debug(
                "ONLY_FUTURE_IMPORT_FOUND breaker activated; does not match pattern"
            )

            self._import_status = AppendDecoratorTransformer.ImportStatus.CAN_ADD
        return self._get_updated_node(updated_node)

    def _get_updated_node(
        self, updated_node: cst.CSTNode
    ) -> cst.FlattenSentinel[cst.BaseSmallStatement]:
        if self._import_status == AppendDecoratorTransformer.ImportStatus.CAN_ADD:
            self._import_status = AppendDecoratorTransformer.ImportStatus.ALREADY_ADDED
            returned_nodes = self.nodes_to_add + [updated_node]
            if isinstance(updated_node, cst.FunctionDef):
                returned_nodes = [cst.SimpleStatementLine(self.nodes_to_add), updated_node]
            return cst.FlattenSentinel(returned_nodes)

        return updated_node
