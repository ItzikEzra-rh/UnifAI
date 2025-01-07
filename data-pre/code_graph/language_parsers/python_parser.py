from typing import Dict, List, Tuple
from pathlib import Path
import ast
import networkx as nx
import subprocess
import json
import os
from code_graph.language_parsers.language_parser import FunctionContext, LanguageParser

class PythonParser(LanguageParser):
    def get_file_pattern(self) -> str:
        return "*.py"

    def parse_file(self, file_path: Path) -> List[Tuple[str, FunctionContext]]:
        with open(file_path, 'r') as f:
            content = f.read()
            tree = ast.parse(content)

        visitor = PythonFunctionVisitor(file_path, content)
        visitor.visit(tree)
        return visitor.get_functions()

class PythonFunctionVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path, source: str):
        self.file_path = file_path
        self.source = source
        self.functions: Dict[str, FunctionContext] = {}
        self.current_function = None

    def visit_FunctionDef(self, node):
        qualified_name = f"{self.file_path}:{node.name}"
        self.current_function = qualified_name

        # Extract function signature
        args = []
        for arg in node.args.args:
            annotation = ""
            if arg.annotation:
                annotation = f": {ast.unparse(arg.annotation)}"
            args.append(f"{arg.arg}{annotation}")

        signature = f"def {node.name}({', '.join(args)})"
        if node.returns:
            signature += f" -> {ast.unparse(node.returns)}"

        if ast.get_docstring(node):
            signature += f"\n'''{ast.get_docstring(node)}'''"

        # Get source code
        source_code = ast.get_source_segment(self.source, node)

        self.functions[qualified_name] = FunctionContext(
            name=node.name,
            file_path=str(self.file_path),
            signature=signature,
            calls=[],
            called_by=[],
            source_code=source_code,
            language="python"
        )

        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        if self.current_function and isinstance(node.func, ast.Name):
            self.functions[self.current_function].calls.append(node.func.id)
        self.generic_visit(node)

    def get_functions(self) -> List[Tuple[str, FunctionContext]]:
        return list(self.functions.items())