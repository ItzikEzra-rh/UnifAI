from enum import Enum

class FormStatus(Enum):
    PARSING = "parsing"
    CLONING = "cloning"
    UPLOADHF = "uploading to Hugging Face"
    DONE = "done"
    FAILED = "failed"


