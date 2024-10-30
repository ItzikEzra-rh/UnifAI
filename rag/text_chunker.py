from typing import List
from handlers.file_handler import FileHandler

class TextChunker:
    def __init__(self, max_chunk_size: int = 512):
        self.max_chunk_size = max_chunk_size

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks based on max_chunk_size"""
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= self.max_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def chunk_file(self, file_handler: FileHandler) -> List[str]:
        """Convenience method to chunk a file directly"""
        content = file_handler.read_content()
        return self.chunk_text(content)