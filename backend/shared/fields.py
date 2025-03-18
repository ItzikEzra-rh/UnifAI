from typing import Type

class FieldDefinition:
    def __init__(self, name: str, field_type: Type):
        self.name = name
        self.field_type = field_type

    def __str__(self):
        return self.name

class FormFields:
    STATUS = FieldDefinition("status", str)
    PROJECT_NAME = FieldDefinition("projectName", str)
    TRAINING_NAME = FieldDefinition("trainingName", str)
    GIT_URL = FieldDefinition("gitUrl", str)
    GIT_CREDENTIAL_KEY = FieldDefinition("gitCredentialKey", str)
    GIT_FOLDER_PATH = FieldDefinition("gitFolderPath", str)
    GIT_BRANCH_NAME = FieldDefinition("gitBranchName", str)
    TESTS_CODE_FRAMEWORK = FieldDefinition("testsCodeFramework", str)
    NUMBER_OF_TESTS = FieldDefinition("numberOfTests", int)
    DATASET_GRADING_UPGRADE = FieldDefinition("datasetGradingUpgrade", bool)
    FILES_PATH = FieldDefinition("filesPath", list)
