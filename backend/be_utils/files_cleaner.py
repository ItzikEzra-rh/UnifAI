import os
import shutil

class FileCleaner:
    """
    Utility class for deleting files and directories safely.
    """

    @staticmethod
    def delete_path(path: str) -> bool:
        """
        Deletes a file or directory if it exists.
        
        :param path: Path to the file or directory to be deleted.
        :return: True if deletion was successful, False otherwise.
        """
        if not os.path.exists(path):
            print(f"Path does not exist: {path}")
            return False

        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
                print(f"Deleted file: {path}")
            elif os.path.isdir(path):
                shutil.rmtree(path)
                print(f"Deleted directory: {path}")
            return True
        except Exception as e:
            print(f"Error deleting {path}: {e}")
            return False
