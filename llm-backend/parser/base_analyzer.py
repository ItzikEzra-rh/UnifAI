import os
import json
from abc import ABC, abstractmethod
import tree_sitter_python as tspython
from tree_sitter import Language, Parser


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

    def _extract_function_info(self, node, class_name=None):
        """
        Extract function or method information from a node, including decorators.
        Handles both decorated and non-decorated functions/methods.
        """
        # Check if it's a decorated definition
        if node.type == 'decorated_definition':
            decorators = self._extract_decorators_from_decorated_definition(node)
            # Find the inner function_definition within the decorated_definition
            function_node = next((child for child in node.children if child.type == 'function_definition'), None)

            # Extract the full text of the decorated definition (including decorators and the function)
            full_code = self._get_node_text(node)
        else:
            # No decorators, so the node is directly a function_definition
            function_node = node
            decorators = []
            full_code = self._get_node_text(node)  # Get the function code

        if function_node:
            function_name = self._get_node_text(function_node.child_by_field_name('name'))

            return {
                "function_name": function_name,
                "code": full_code,  # Include both function and decorator code
                "class_name": class_name,  # Optional, for methods in classes
                "file_location": self.file_path,
                "decorators": decorators,
                "calls": self._extract_function_calls(function_node),
                # "used_components": self._extract_used_components(function_node),
                "dependencies": {
                    "imports": self._extract_used_imports(function_node)  # Function/method-level imports
                }
            }
        return None

    def _extract_decorators_from_decorated_definition(self, node):
        """
        Extract decorators from the decorated_definition node, handling both
        identifier-based and call-based decorators.
        """
        decorators = []

        for child in node.children:
            if child.type == 'decorator':  # Decorators are of type 'decorator'
                # Handle identifier-based decorators (e.g., @staticmethod, @mongo)
                identifier_node = next((gc for gc in child.children if gc.type == 'identifier'), None)
                if identifier_node:
                    decorator_name = self._get_node_text(identifier_node)
                    decorators.append({
                        "decorator_function": decorator_name,
                        "arguments": None  # No arguments for identifier-based decorators
                    })

                # Handle call-based decorators (e.g., @route(...))
                for grandchild in child.children:
                    if grandchild.type == 'call':  # The call node represents the decorator function
                        # Extract the function node (which is an attribute)
                        function_node = grandchild.child_by_field_name('function')
                        if function_node is None:
                            # In some cases, function can be an attribute
                            function_node = next((gc for gc in grandchild.children if gc.type == 'attribute'), None)
                        function_name = self._get_node_text(function_node) if function_node else None

                        # Extract arguments to the decorator function
                        arguments_node = next((gc for gc in grandchild.children if gc.type == 'argument_list'), None)
                        arguments_text = self._get_node_text(arguments_node) if arguments_node else None

                        # Store the decorator with its function name and arguments
                        decorators.append({
                            "decorator_function": function_name,
                            "arguments": arguments_text
                        })

        return decorators


class ClassAnalyzer(BaseAnalyzer):
    def analyze(self, root_node):
        class_definitions = []
        method_count = 0  # Track number of methods in this file

        for node in root_node.children:
            if node.type == 'class_definition':
                class_name = self._get_node_text(node.child_by_field_name('name'))
                block_node = node.child_by_field_name('body')
                class_methods = []

                if block_node:
                    method_analyzer = MethodAnalyzer(self.file_path, self.source_dir, self.file_imports,
                                                     self.file_content)
                    class_methods = method_analyzer.analyze(block_node, class_name)
                    method_count += len(class_methods)  # Add method count for this class

                class_data = {
                    "class_name": class_name,
                    "code": self._get_node_text(node),
                    "file_location": self.file_path,
                    "methods": class_methods,
                    "dependencies": {
                        "imports": self._extract_used_imports(node)
                    }
                }
                class_definitions.append(class_data)

        return class_definitions, method_count


# Analyzer for method definitions (inside classes)
class MethodAnalyzer(BaseAnalyzer):
    def analyze(self, block_node, class_name):
        methods = []

        for node in block_node.children:
            if node.type in ['decorated_definition', 'function_definition']:
                method_info = self._extract_function_info(node, class_name=class_name)
                if method_info:
                    methods.append(method_info)

        return methods


# Analyzer for standalone functions (functions outside classes)
class FunctionAnalyzer(BaseAnalyzer):
    def analyze(self, root_node):
        functions = []

        for node in root_node.children:
            if node.type in ['decorated_definition', 'function_definition']:
                function_info = self._extract_function_info(node)
                if function_info:
                    functions.append(function_info)

        return functions


# Main analyzer that uses different analyzers
class ProjectFileAnalyzer:
    PY_LANGUAGE = Language(tspython.language())

    def __init__(self, source_dir):
        self.source_dir = source_dir
        self.parser = Parser(self.PY_LANGUAGE)

    def _extract_file_imports(self, root_node, file_content):
        """Extract file-level imports once, then pass them to analyzers."""
        imports = []
        for node in root_node.children:
            if node.type == 'import_statement' or node.type == 'import_from_statement':
                import_statement = file_content[node.start_byte:node.end_byte]
                imports.append(import_statement)
        return imports

    def analyze_file(self, file_path):
        relative_file_path = os.path.relpath(file_path, self.source_dir)

        with open(file_path, 'r') as file:
            file_content = file.read()
            tree = self.parser.parse(bytes(file_content, "utf8"))
            root_node = tree.root_node

        file_imports = self._extract_file_imports(root_node, file_content)
        class_analyzer = ClassAnalyzer(relative_file_path, self.source_dir, file_imports, file_content)
        function_analyzer = FunctionAnalyzer(relative_file_path, self.source_dir, file_imports, file_content)

        classes_data, method_count = class_analyzer.analyze(root_node)
        functions_data = function_analyzer.analyze(root_node)

        return {
            "file_path": relative_file_path,
            "classes": classes_data,
            "functions": functions_data,
            "methods": method_count  # Keep track of method counts
        }

    def analyze_project(self):
        """
        Analyze all .py files in the given directory and its subdirectories.
        """
        all_data = {
            "classes": [],
            "functions": [],
            "methods_count": 0  # Initialize method count
        }

        # Walk through all .py files in the directory
        for root, _, files in os.walk(self.source_dir):
            for file_name in files:
                if file_name.endswith(".py"):
                    file_path = os.path.join(root, file_name)
                    file_data = self.analyze_file(file_path)

                    # Accumulate class and function data
                    all_data["classes"].extend(file_data["classes"])
                    all_data["functions"].extend(file_data["functions"])
                    all_data["methods_count"] += file_data["methods"]

        return all_data

    def output_to_json(self, data, output_file):
        with open(output_file, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def count_elements(self, data):
        """Print the count of classes, functions, and methods."""
        num_classes = len(data["classes"])
        num_functions = len(data["functions"])
        num_methods = data["methods_count"]

        print(f"Number of classes: {num_classes}")
        print(f"Number of methods: {num_methods}")
        print(f"Number of functions: {num_functions}")
        print(f"Total elements: {num_classes + num_methods + num_functions}")


if __name__ == "__main__":
    source_dir = '/home/instruct/nova/'
    output_file = 'nova_output_project_analysis.json'

    analyzer = ProjectFileAnalyzer(source_dir)
    project_data = analyzer.analyze_project()

    # Save the aggregated data to a JSON file
    analyzer.output_to_json(project_data, output_file)

    # Print the total number of elements (classes/methods/functions)
    analyzer.count_elements(project_data)

    print(f"Analysis Complete. Data saved in '{output_file}'.")
