
from typing import Dict, List, Tuple
from pathlib import Path
from dataclasses import asdict
import networkx as nx
import matplotlib.pyplot as plt
from rag.code_graph.language_parsers.language_parser import FunctionContext, LanguageParser
from rag.code_graph.language_parsers.go_parser import GoParser
from rag.code_graph.language_parsers.python_parser import PythonParser
from be_utils.db.db import mongo, Collections, db

class CodeContextExtractor:
    def __init__(self, project_name: str, repo_path: str = '', languages: List[str] = [], project_repo_path: str = ''):
        self.project_name = project_name
        self.repo_path = Path(repo_path)
        self.project_repo_path = project_repo_path
        self.function_graph = nx.DiGraph()
        self.function_contexts: Dict[str, FunctionContext] = {}
        self.init_parsers(languages)

    def init_parsers(self, languages: List[str]):
        # Initialize language parsers
        self.parsers: Dict[str, LanguageParser] = {
            'python': PythonParser(project_name=self.project_name),
            'go': GoParser(project_name=self.project_name)
        }
        
        # Validate requested languages
        for lang in languages:
            if lang.lower() not in self.parsers:
                raise ValueError(f"Unsupported language: {lang}")
        
        self.active_parsers = {
            lang.lower(): self.parsers[lang.lower()] 
            for lang in languages
        }

    def parse_repository(self):
        """Parse the entire repository for all specified languages."""
        for lang, parser in self.active_parsers.items():
            for file_path in self.repo_path.rglob(parser.get_file_pattern()):
                try:
                    parsed_functions = parser.parse_file(file_path)
                    
                    for qualified_name, func_context in parsed_functions:
                        self.function_contexts[qualified_name] = func_context
                        self.function_graph.add_node(qualified_name)
                        
                        # Add edges for function calls
                        for call in func_context.calls:
                            self.function_graph.add_edge(qualified_name, call)
                            
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

        # Update called_by relationships
        self._update_caller_relationships()
    
    @mongo
    def upload_to_db(self):
        elements_mapping = []
        for location, element_mapping in self.function_contexts.items():
            db_element_general_details = {
                "project_name": self.project_name,
                "project_repo_path": self.project_repo_path,
            }

            # Convert the dataclass to a dictionary before merging
            db_element_mapping = {**db_element_general_details,**asdict(element_mapping)}
            elements_mapping.append(db_element_mapping)

        Collections.by_name('code_graph').insert_many(elements_mapping)

    def function_contexts_dict_builder(self):
        """
        Converts a list of dictionaries into a dict where the file_path (from hidden keys) 
        is used as the key, and the rest of the key-value pairs form the value.

        Args:
            objects (list): List of dictionaries with keys including '_id', 'project_name',
                            'project_repo_path', and others.

        Returns:
            dict: A dictionary with file_path as the key and the rest of the keys/values as the value.
        """
        result = {}
        elements = list(Collections.by_name('code_graph').find({"project_name": self.project_name}))

        for obj in elements:
            # Extract the file_path from the object's hidden keys
            file_path = obj.get("file_path")
            element_name = obj.get("name", "")
            
            if not file_path:
                raise KeyError("Missing 'file_path' key in one of the objects.")
            
            # Create a new dictionary excluding the 'file_path'
            filtered_obj = {key: value for key, value in obj.items() if key != "_id" and key != "project_name" and key != "project_repo_path"}
            func_context = FunctionContext(**filtered_obj)
            
            # Assign the rest of the object to the file_path key
            qualified_name = f"{file_path} : {element_name}"
            result[qualified_name] = func_context

            self.function_graph.add_node(qualified_name)
                    
            # Add edges for function calls
            for call in func_context.calls:
                self.function_graph.add_edge(qualified_name, call)

        # Update called_by relationships
        self._update_caller_relationships()
        return result 

    def _update_caller_relationships(self):
        """Update the called_by lists for all functions based on the graph."""
        for func_name in self.function_contexts:
            callers = list(self.function_graph.predecessors(func_name))
            self.function_contexts[func_name].called_by = callers

    def _print_graph(self):
        # Modify the labels to use the last 15 characters
        labels = {node: node[-15:] for node, data in self.function_graph.nodes(data=True)}

        # Draw the graph
        plt.figure(figsize=(12, 10))  # Optional: Set figure size
        
        pos = nx.spring_layout(self.function_graph)  # Layout for nodes

        nx.draw(self.function_graph, pos, with_labels=True, labels=labels,
                node_color='lightblue', edge_color='gray', node_size=1500, font_size=8)

        # Save the plot
        plt.savefig("graph_with_short_labels.png")

        # print("Nodes:", self.function_graph.nodes())
        # print("Edges:", self.function_graph.edges())
        
    @mongo
    def get_context_for_functions(self, function_names: List[Tuple[str, str]]) -> Dict[str, FunctionContext]:
        """
        Get context for specified functions and their immediate neighbors.
        
        Args:
            function_names: List of (function_name, file_path) tuples from keyword search
        """
        context = {}
        retreived_function_contexts = self.function_contexts if self.function_contexts else self.function_contexts_dict_builder()
        
        for func_name, file_path in function_names:
            qualified_name = f"{file_path}:{func_name}"
            
            if qualified_name in retreived_function_contexts:
                # Get the main function context
                context[qualified_name] = retreived_function_contexts[qualified_name]

                # Get immediate neighbors
                neighbors = list(self.function_graph.predecessors(qualified_name))
                neighbors.extend(self.function_graph.successors(qualified_name))
                
                for neighbor in neighbors:
                    if neighbor in retreived_function_contexts:
                        context[neighbor] = retreived_function_contexts[neighbor]
        
        return context