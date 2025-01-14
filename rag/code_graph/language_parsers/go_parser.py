from typing import List, Tuple
from pathlib import Path
import networkx as nx
import subprocess
import json
import os

from .language_parser import FunctionContext, LanguageParser
class GoParser(LanguageParser):
    def __init__(self, project_name: str):
        super().__init__()
        self.project_name = project_name
        self.compile_go_parser()

    def get_file_pattern(self) -> str:
        return "*.go"
    
    def compile_go_parser(self):
        subprocess.run(["go", "build", "-o", "goparser", "../rag/code_graph/language_parsers/go_parser.go"])

    def parse_file(self, file_path: Path) -> List[Tuple[str, FunctionContext]]:
        # Run the parser
        result = subprocess.run(["./goparser", str(file_path)], 
                              capture_output=True, text=True)
        
        # Clean up
        os.remove("temp_parser.go")
        os.remove("goparser")
        
        functions_info = json.loads(result.stdout)
        parsed_functions = []
        
        for func_info in functions_info:
            realtive_file_path = str(Path(*file_path.parts[file_path.parts.index(self.project_name) + 1:]))
            qualified_name = f"{realtive_file_path}:{func_info['name']}"
            # print(f"Qualified_name: {qualified_name}")
            context = FunctionContext(
                name=func_info['name'],
                file_path=realtive_file_path,
                signature=func_info['signature'],
                calls=func_info['calls'],
                called_by=[],
                source_code=func_info['source_code'],
                language="go",
                package_name=func_info['package'],
                is_test=func_info.get('is_test', False),
                test_type=func_info.get('test_type', ''),
                test_parent=func_info.get('test_parent', '')
            )
            parsed_functions.append((qualified_name, context))
            
        return parsed_functions