from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import os

@dataclass
class FileMetadata:
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    last_modified: float

class FileHandler:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.metadata = self._get_file_metadata()
        self.content: Optional[str] = None

    def _get_file_metadata(self) -> FileMetadata:
        stats = os.stat(self.file_path)
        return FileMetadata(
            file_path=str(self.file_path),
            file_name=self.file_path.name,
            file_size=stats.st_size,
            file_type=self.file_path.suffix,
            last_modified=stats.st_mtime
        )

    def read_content(self) -> str:
        """Read and store file content"""
        if not self.content:
            with open(self.file_path, 'r') as file:
                self.content = file.read()
                
            # # Try to decode the content with various encodings
            # for encoding in ['utf-8', 'latin-1', 'utf-16']:
            #     try:
            #         self.content = content.decode(encoding, errors='replace')
            #         break
            #     except UnicodeDecodeError:
            #         pass
            # else:
            #     # If all decoding attempts fail, use a replacement character
            #     self.content = content.decode('utf-8', 'replace')
        
        return self.content