import os
import json
from abc import ABC, abstractmethod
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# Initialize Tree Sitter for Python
PY_LANGUAGE = Language(tspython.language())

parser = Parser(PY_LANGUAGE)


# Base class for analyzers
class BaseAnalyzer(ABC):
    def __init__(self, file_path, source_dir, file_imports=None, file_content=None):
        self.file_path = file_path
        self.source_dir = source_dir
        self.file_location = os.path.abspath(os.path.join(self.source_dir, self.file_path))  # Full path from source dir
        self.file_imports = file_imports or []  # Store all imports at the file level
        self.imported_names = [imp.split()[-1] for imp in self.file_imports]  # Extract the names for tracking
        self.file_content = file_content  # Entire file content

    @abstractmethod
    def analyze(self, root_node):
        pass

    def _get_node_text(self, node):
        return self.file_content[node.start_byte:node.end_byte]

    def _extract_function_calls(self, node):
        """
        Recursively traverse all the child nodes within the function's scope
        to find all function calls.
        """
        calls = []

        # Recursive helper function to traverse nodes
        def traverse(node):
            for child in node.children:
                if child.type == 'call':  # Check if the node represents a function call
                    function_name_node = child.child_by_field_name('function')
                    if function_name_node:
                        function_name = self._get_node_text(function_name_node)
                        calls.append(function_name)
                # Recursively traverse the children of the current node
                traverse(child)

        # Start traversing from the given node
        traverse(node)

        return calls

    def _is_import_used(self, node, import_name):
        """Check if the given import name is used in the entire node tree."""

        def traverse(node):
            # Look for identifiers and attribute accesses throughout the node tree
            for child in node.children:
                if child.type == 'identifier' or child.type == 'attribute':
                    identifier_name = self._get_node_text(child)

                    # Check if the identifier starts with the import name
                    if identifier_name == import_name:
                        # Check if it's followed by a dot (for attribute access) or a parenthesis (for function calls)
                        next_sibling = child.next_sibling
                        if next_sibling and (next_sibling.type == 'attribute' or next_sibling.type == '('):
                            return True
                        # If there's no next sibling or no dot/parenthesis, it's an exact match
                        return True

                    # For imports like "import foo as bar", check if the alias is used
                    if identifier_name.startswith(import_name + '.'):
                        return True

                # Recursively traverse the children of the current node
                if traverse(child):
                    return True
            return False

        # Start traversing the node to check for the import name
        return traverse(node)

    def _extract_used_imports(self, node):
        """Check which file-level imports are used in the provided code's syntax tree."""
        used_imports = []
        for import_stmt in self.file_imports:
            # Get the imported name (last part of the import statement)
            imported_name = import_stmt.split()[-1]
            if self._is_import_used(node, imported_name):
                used_imports.append(import_stmt)
        return used_imports

    def _extract_used_components(self, node):
        # This will extract components used within a method or function
        used_components = []
        for child in node.children:
            if child.type == 'attribute':
                attribute_name = self._get_node_text(child)
                used_components.append(attribute_name)
        return used_components


# Analyzer for class definitions
class ClassAnalyzer(BaseAnalyzer):
    def analyze(self, root_node):
        class_definitions = []

        for node in root_node.children:
            if node.type == 'class_definition':
                class_name = self._get_node_text(node.child_by_field_name('name'))
                class_methods = []

                block_node = node.child_by_field_name('body')

                if block_node:
                    # Use MethodAnalyzer to analyze methods inside the class
                    method_analyzer = MethodAnalyzer(self.file_path, self.source_dir, self.file_imports,
                                                     self.file_content)
                    class_methods = method_analyzer.analyze(block_node, class_name)  # Pass class name for methods

                class_data = {
                    "class_name": class_name,
                    "code": self._get_node_text(node),
                    "file_location": self.file_location,  # Full file location
                    "methods": class_methods,
                    "dependencies": {
                        "imports": self._extract_used_imports(node)  # Class-level imports
                    }
                }
                class_definitions.append(class_data)

        return class_definitions


# Analyzer for method definitions (inside classes)
class MethodAnalyzer(BaseAnalyzer):
    def analyze(self, block_node, class_name):
        methods = []

        for node in block_node.children:
            if node.type == 'function_definition':
                method_name = self._get_node_text(node.child_by_field_name('name'))
                method_code = self._get_node_text(node)
                methods.append({
                    "method_name": method_name,
                    "code": method_code,
                    "class_name": class_name,  # Name of the class containing this method
                    "file_location": self.file_location,  # Full file location
                    "calls": self._extract_function_calls(node),
                    "used_components": self._extract_used_components(node),
                    "dependencies": {
                        "imports": self._extract_used_imports(node)  # Method-level imports
                    }
                })
        return methods


# Analyzer for standalone functions (functions outside classes)
class FunctionAnalyzer(BaseAnalyzer):
    def analyze(self, root_node):
        functions = []

        for node in root_node.children:
            if node.type == 'function_definition':
                function_name = self._get_node_text(node.child_by_field_name('name'))
                function_code = self._get_node_text(node)
                functions.append({
                    "function_name": function_name,
                    "code": function_code,
                    "file_location": self.file_location,  # Full file location for the function
                    "calls": self._extract_function_calls(node),
                    "dependencies": {
                        "imports": self._extract_used_imports(node)  # Function-level imports
                    }
                })
        return functions


# Main analyzer that uses different analyzers
class ProjectFileAnalyzer:
    def __init__(self, file_path, source_dir):
        self.file_path = file_path
        self.source_dir = source_dir
        self.file_location = os.path.abspath(os.path.join(self.source_dir, self.file_path))
        self.file_content = None
        self.file_imports = []

    def _extract_file_imports(self, root_node):
        """Extract file-level imports once, then pass them to analyzers."""
        imports = []
        for node in root_node.children:
            if node.type == 'import_statement' or node.type == 'import_from_statement':
                import_statement = self.file_content[node.start_byte:node.end_byte]
                imports.append(import_statement)
        return imports

    def analyze_file(self):
        # Open and parse the file using Tree Sitter, and store the file content
        with open(self.file_path, 'r') as file:
            self.file_content = file.read()
            tree = parser.parse(bytes(self.file_content, "utf8"))
            root_node = tree.root_node

        # Extract file-level imports
        self.file_imports = self._extract_file_imports(root_node)

        # Use different analyzers for classes, methods, and functions
        class_analyzer = ClassAnalyzer(self.file_path, self.source_dir, self.file_imports, self.file_content)
        function_analyzer = FunctionAnalyzer(self.file_path, self.source_dir, self.file_imports, self.file_content)

        classes_data = class_analyzer.analyze(root_node)
        functions_data = function_analyzer.analyze(root_node)

        return {
            "classes": classes_data,
            "functions": functions_data
        }

    def output_to_json(self, data, output_file):
        with open(output_file, 'w') as json_file:
            json.dump(data, json_file, indent=4)


# Example Usage:
source_dir = '/home/instruct/testgenie/llm-backend/parser'
file_path = '/home/instruct/testgenie/llm-backend/parser/test_python_code/start_sample.py'

analyzer = ProjectFileAnalyzer(file_path, source_dir)
data = analyzer.analyze_file()
analyzer.output_to_json(data, 'output_file.json')

print(f"Analysis Complete. Data saved in 'output_file.json'.")
