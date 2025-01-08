from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
import ast
import networkx as nx
import subprocess
import json
import os

@dataclass
class FunctionContext:
    name: str
    file_path: str
    signature: str
    calls: List[str]
    called_by: List[str]
    source_code: str
    language: str
    package_name: Optional[str] = None  # Particularly useful for Go

class LanguageParser(ABC):
    @abstractmethod
    def parse_file(self, file_path: Path) -> List[Tuple[str, FunctionContext]]:
        """Parse a single file and return list of (qualified_name, FunctionContext) tuples"""
        pass

    @abstractmethod
    def get_file_pattern(self) -> str:
        """Return the file pattern to match for this language"""
        pass