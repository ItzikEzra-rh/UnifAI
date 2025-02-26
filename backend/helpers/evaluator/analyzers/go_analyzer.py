import os
from typing import Dict, Set, List
import re

class GoCodeAnalyzer:
    def __init__(self):
        self.symbol_database = {
            'functions': set(),      # standalone functions
            'methods': set(),        # methods belonging to types
            'interfaces': set(),
            'structs': set(),
            'packages': set()
        }
        
        # Ginkgo test framework functions to ignore
        self.ginkgo_functions = {
            # Test Definitions
            'Describe', 'Context', 'It', 'DescribeTable', 'Entry',
            # Setup and Teardown
            'BeforeEach', 'AfterEach', 'JustBeforeEach', 'JustAfterEach',
            'BeforeSuite', 'AfterSuite',
            'BeforeAll', 'AfterAll', 'By',
            # Assertions
            'Expect', 'Eventually', 'Consistently', 'Should',
            # Helpers & Matchers
            'ContainSubstring', 'HaveOccurred', 'BeEmpty', 'BeNil',
            'BeTrue', 'BeFalse', 'Equal', 'HaveLen', 'BeEquivalentTo',
            'ContainElement', 'BeZero', 'BeClosed', 'NotTo'
        }
        
        # Common Go built-in functions and methods to ignore
        self.go_builtins = {
            # Built-in functions
            'make', 'new', 'len', 'cap', 'append', 'copy', 'delete',
            'close', 'complex', 'real', 'imag', 'panic', 'recover',
            'print', 'println', 'import', 'func',
            # Common standard library method names
            'String', 'Error', 'Read', 'Write', 'Close', 'Open',
            'Init', 'Scan', 'Print', 'Printf', 'Println',
            # Context methods
            'Done', 'Err', 'Deadline', 'Value',
            # Common interface methods
            'Marshal', 'Unmarshal', 'MarshalJSON', 'UnmarshalJSON',
            # Testing related
            'Fatal', 'Fatalf', 'Log', 'Logf'
        }
        
        # Common Go types to ignore
        self.go_builtin_types = {
            'string', 'int', 'int64', 'int32', 'uint', 'uint64', 'uint32',
            'byte', 'rune', 'float64', 'float32', 'bool', 'error',
            'interface', 'struct', 'map', 'chan', 'func'
        }
    
    def parse_go_file(self, file_path: str) -> Dict[str, Set[str]]:
        """Parse a Go file and extract all symbol definitions"""
        with open(file_path, 'r') as f:
            content = f.read()

        file_symbols = {
            'functions': set(),
            'methods': set(),
            'interfaces': set(),
            'structs': set(),
            'packages': set()
        }
        
        # Extract package name
        package_match = re.search(r'package\s+(\w+)', content)
        if package_match:
            file_symbols['packages'].add(package_match.group(1))
        # Extract interface definitions
        interface_matches = re.finditer(r'type\s+(\w+)\s+interface\s*{', content)
        for match in interface_matches:
            file_symbols['interfaces'].add(match.group(1))
            
        # Extract struct definitions
        struct_matches = re.finditer(r'type\s+(\w+)\s+struct\s*{', content)
        for match in struct_matches:
            struct_name = match.group(1)
            if struct_name not in self.go_builtin_types:
                file_symbols['structs'].add(struct_name)

        # Extract method definitions
        method_matches = re.finditer(r'func\s*\([\w\s*]*\s*(\w+)\s+[*]?(\w+)\)\s*(\w+)\s*\(', content)
        for match in method_matches:
            receiver_var, receiver_type, method_name = match.groups()
            if method_name not in self.ginkgo_functions and method_name not in self.go_builtins:
                # file_symbols['methods'].add(f"{receiver_type}.{method_name}")
                file_symbols['methods'].add(f"{method_name}")

        # Extract standalone function definitions
        function_matches = re.finditer(r'func\s+(\w+)\s*\((?![^)]*\)\s*\w+\s*\()', content)
        for match in function_matches:
            func_name = match.group(1)
            if func_name not in self.ginkgo_functions and func_name not in self.go_builtins:
                file_symbols['functions'].add(func_name)
            
        return file_symbols
    
    def analyze_repository(self, repo_path: str):
        """Analyze entire repository and build symbol database"""
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.go'):
                    file_path = os.path.join(root, file)
                    file_symbols = self.parse_go_file(file_path)
                    
                    # Update global symbol database
                    for symbol_type, symbols in file_symbols.items():
                        self.symbol_database[symbol_type].update(symbols)

    def extract_imports(self, code: str) -> set:
        """
        Extract imports from GO code and normalize them to their usage names.
        Handles both single imports and import blocks.
        Returns a set of import names as they would be used in the code.
        """
        imports = set()
        
        # Find the import block or single imports
        import_block_match = re.search(r'import\s*\((.*?)\)', code, re.DOTALL)
        if import_block_match:
            # Handle multi-line import block
            block = import_block_match.group(1).strip()
            for line in block.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Handle aliased import
                alias_match = re.match(r'(\w+)\s+"([^"]+)"', line)
                if alias_match:
                    imports.add(alias_match.group(1))  # Add the alias
                    continue
                    
                # Handle regular import
                regular_match = re.match(r'"([^"]+)"', line)
                if regular_match:
                    import_path = regular_match.group(1)
                    # Get the last component of the path
                    import_name = import_path.split('/')[-1]
                    imports.add(import_name)
        else:
            # Handle single-line imports
            single_imports = re.finditer(r'import\s+(?:(\w+)\s+)?"([^"]+)"', code)
            for match in single_imports:
                if match.group(1):  # Aliased import
                    imports.add(match.group(1))
                else:  # Regular import
                    import_path = match.group(2)
                    import_name = import_path.split('/')[-1]
                    imports.add(import_name)
        
        return imports
    
    def is_chained_function_call(self, code: str, start_pos: int) -> bool:
        """
        Check if a function call is chained (appears directly after another function/method call).
        
        Args:
            code: The full code string
            start_pos: Starting position of the current function match
            
        Returns:
            bool: True if the function is chained, False otherwise
        """
        # Look backwards from the current position
        before_function = code[:start_pos].rstrip()
        
        # Check if the previous character is a dot (indicating method chain)
        if before_function.endswith('.'):
            return True
            
        # Check if we're inside a function/method call parentheses
        open_count = 0
        for i in range(len(before_function) - 1, -1, -1):
            if before_function[i] == ')':
                open_count += 1
            elif before_function[i] == '(':
                open_count -= 1
            elif before_function[i] == '.' and open_count == 0:
                # Found a dot outside of parentheses
                # E.G. someFunc(obj.Method()).otherFunc() - When analyzing otherFunc, we need to know if the dot before it is outside any parentheses
                # When open_count is 0, we're outside all parentheses
                # If we find a dot when open_count is 0, it means we have a true chain
                return True
            elif before_function[i] in {';', '{', '}', '\n'} and open_count == 0:
                # Found a statement boundary without finding a dot
                return False
                
        return False
    
    def verify_code_snippet(self, code: str) -> Dict[str, List[Dict[str, bool]]]:
        """Verify if project-specific symbols used in a code snippet exist"""
        verification_results = {
            'functions': [],
            'methods': [],
            'interfaces': [],
            'structs': [],
            'packages': []
        }
        
        # Clean the code (remove escape characters and extra spaces)
        code = code.replace('\\', '').strip()

        # Extract available imports
        available_imports = self.extract_imports(code)
        
        # Extract function calls using patterns
        function_patterns = [
            r'(\w+)\s*\(',  # Basic function calls
            r'(\w+)\s*:=\s*\w+\.',  # Function assignments
            r'func\s+(\w+)\s*\(',  # Function definitions
            r'return\s+(\w+)\s*\(',  # Return statements with function calls
        ]

        # Extract method calls
        method_patterns = [
            r'(\w+)\.(\w+)\([^)]*\)',  # Basic method call: obj.Method()
            r'(\w+)\.(\w+)\([^)]*\)\.',  # Chained calls: obj.Method1().Method2()
        ]

        # Extract and verify struct instantiations
        struct_patterns = [
            r':\s*=\s*(\w+){',  # x := TypeName{}
            r':\s*=\s*&?(\w+){',  # x := &TypeName{}
            r'var\s+\w+\s+(\w+)\s*{?',  # var x TypeName
        ]

        # Extract and verify interface usage patterns
        interface_patterns = [
            r'interface\{(\s*\w+\s*)+\}',  # Basic interface implementation
            r'(\w+)\s*interface\s*{',      # Named interface declaration
            r'implements\s+(\w+)',         # explicit implements keyword (if used)
            r'var\s+\w+\s+(\w+)er\b',     # Common interface naming convention with 'er' suffix
            r'func\s*\([^)]+\)\s*(\w+)er\b', # Method receivers using interface types
            r'func\s*\([^)]+\)\s*(\w+)Interface\b', # Interface types with 'Interface' suffix
            r'type\s+\w+\s+interface\s*{', # Interface type declarations
            r'type\s+(\w+)\s*interface\s*{',  # More specific interface declaration
            r'func\s*\([^)]+\)\s*(\w+)able\b',  # Interfaces ending with 'able'
            r'interface\s*{\s*(\w+)\s*}',       # Single method interfaces
        ]

        method_names_to_exclude = set()  # Track methods to exclude from functions
        used_methods = set()  # Track unique methods
        method_parents = {}  # Hash table for method -> parent mapping

        def find_method_calls(code):
            for pattern in method_patterns:
                matches = re.findall(pattern, code)
                for parent, method_name in matches:
                    if (method_name not in self.ginkgo_functions and 
                        method_name not in self.go_builtins):
                        # Store the parent-method relationship
                        method_parents[method_name] = parent

                        used_methods.add(method_name)
                        method_names_to_exclude.add(method_name)  # Add to exclusion set

                    # Recursively search inside method arguments
                    args_match = re.search(r'\((.*)\)', code)
                    if args_match:
                        find_method_calls(args_match.group(1))

            return used_methods, method_parents
        
        # Get all method names and their parents
        used_methods, method_parents = find_method_calls(code)

        # Now handle functions, excluding any methods we found and chained calls
        used_functions = set()

        for pattern in function_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                func_name = match.group(1)
                # Skip if it's a method we already found or a builtin
                if (func_name in method_names_to_exclude or 
                    func_name in self.ginkgo_functions or 
                    func_name in self.go_builtins):
                    continue
                    
                # Skip if it's a chained function call
                if self.is_chained_function_call(code, match.start(1)):
                    continue
                    
                used_functions.add(func_name)
        
        # Add unique methods to verification results
        for method in used_methods:
            # Check if method exists in symbol database OR if its parent is in available imports
            exists_in_db = method in self.symbol_database['methods']
            parent = method_parents.get(method, '')
            exists_in_imports = parent in available_imports
            
            verification_results['methods'].append({
                'name': method,
                'exists': exists_in_db or exists_in_imports,
                # 'parent': parent  # Optional: include parent information
            })

        # Add verified functions
        for func in used_functions:
            verification_results['functions'].append({
                'name': func,
                'exists': func in self.symbol_database['functions']
            })
        
        used_structs = set()  # Track unique structs
        used_interfaces = set() # Track unique interfaces
        
        # struct instantiations section:
        for pattern in struct_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                struct_name = match.group(1)
                used_structs.add(struct_name)  # Add to set instead of directly to results

        # Interface usage section:
        for pattern in interface_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                interface_name = match.group(1)
                if interface_name:
                    # Clean up the interface name (remove potential whitespace/special chars)
                    interface_name = interface_name.strip()
                    # Add to set if it looks like a valid interface name
                    if interface_name.isidentifier() and interface_name not in self.go_builtin_types:
                        used_interfaces.add(interface_name)
        
        # Add unique structs to verification results
        for struct in used_structs:
            verification_results['structs'].append({
                'name': struct,
                'exists': struct in self.symbol_database['structs'] or struct in available_imports
            })

        for interface in used_interfaces:
            verification_results['interfaces'].append({
                'name': interface,
                'exists': interface in self.symbol_database['interfaces'] or interface in available_imports
            })
    
        # Extract and verify package imports
        # package_uses = re.finditer(r'import\s+(?:"([^"]+)"|`([^`]+)`)', code)
        package_uses = re.finditer(r'package\s+(\w+)', code) 

        for match in package_uses:
            package = match.group(1) or match.group(2)
            verification_results['packages'].append({
                'name': package,
                'exists': package in self.symbol_database['packages']
            })
            
        return verification_results