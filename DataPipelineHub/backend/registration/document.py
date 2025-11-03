from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Tuple
from functools import cached_property
from config.app_config import AppConfig
from config.constants import DataSource
from services.documents.duplicate_checker import DocumentDuplicateChecker
from shared.source_types import DocumentMetadata, DocumentTypeData
from utils.file_hash import compute_file_md5
from validator.validator import Validator, build_doc_validators
from .base import RegistrationBase

app_config = AppConfig.get_instance()
upload_folder = app_config.upload_folder

class DocumentRegistration(RegistrationBase):
    """Registration flow for Document sources."""
    DATA_SOURCE_TYPE = DataSource.DOCUMENT.upper_name

    def __init__(self, mongo_storage: Any, upload_by: str, instance: Dict[str, Any]) -> None:
        super().__init__(mongo_storage, upload_by, instance)
        self.upload_folder = upload_folder
        self._validator = Validator(build_doc_validators())
        self._duplicate_checker = DocumentDuplicateChecker(self.mongo_storage)

    @cached_property
    def doc_path(self) -> str:
        return os.path.join(self.upload_folder, self.source_name)

    @cached_property
    def md5(self) -> str:
        return compute_file_md5(self.doc_path)

    @cached_property
    def source_id(self) -> str:
        return str(uuid.uuid4())

    @cached_property
    def pipeline_id(self) -> str:
        return f"{DataSource.DOCUMENT.value}_{self.source_id}"

    def run_validator(self) -> Tuple[bool, Dict[str, Any] | None]:
        context = {"duplicate_checker": self._duplicate_checker}

        validation_args = {
            "doc_path": self.doc_path,
            "source_name": self.source_name,
            "md5": self.md5
        }
        is_valid, issue = self._validator.validate(validation_args, context)

        if not is_valid:
            issue_key = (issue or {}).get("issue_key", "ValidationError")
            message = (issue or {}).get("message", "Validation error")
            validator_name = (issue or {}).get("validator_name", "Validator")
            return False, {
                "doc_name": self.source_name,
                "issue_type": issue_key,
                "message": message,
                "validator": validator_name,
            }

        return True, None

    def _build_metadata(self) -> DocumentMetadata:
        return DocumentMetadata(
            doc_id=self.source_id,
            doc_name=self.source_name,
            doc_path=self.doc_path,
            upload_by=self.upload_by,
        )

    def _build_type_data(self) -> Dict[str, Any]:
        doc_type_data = DocumentTypeData(
            file_type=self.source_name.rsplit(".", 1)[-1].lower(),
            doc_path=self.doc_path,
            page_count=0,
            full_text="",
            file_size=0,
            md5=self.md5,
            **self.form_data,
        )
        return doc_type_data.model_dump()
