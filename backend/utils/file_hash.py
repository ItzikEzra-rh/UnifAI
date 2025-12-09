import hashlib
import os
from typing import Final, Optional
from shared.logger import logger


_DEFAULT_CHUNK_SIZE: Final[int] = 1024 * 1024  # 1MB


def compute_file_md5(file_path: str, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> str:
    """
    Compute the MD5 checksum of a file by streaming in chunks.

    Args:
        file_path: Absolute path to the file on disk
        chunk_size: Read size per iteration (bytes)

    Returns:
        Hexadecimal MD5 digest string
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as file_handle:
        while True:
            chunk = file_handle.read(chunk_size)
            if not chunk:
                break
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def cleanup_file(file_path: Optional[str], context: str = "") -> bool:
    """
    Safely remove a file from disk.

    Args:
        file_path: Path to the file to remove
        context: Optional context for logging (e.g., "after validation failure")

    Returns:
        True if file was removed, False otherwise
    """
    if not file_path:
        return False
        
    if not os.path.exists(file_path):
        return False
        
    try:
        os.remove(file_path)
        context_msg = f" {context}" if context else ""
        logger.info(f"Cleaned up file{context_msg}: {file_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to clean up file {file_path}: {e}")
        return False
