from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Tuple

from config.app_config import AppConfig
from config.constants import DataSource
from services.documents.duplicate_checker import DocumentDuplicateChecker
from shared.logger import logger
from shared.source_types import DocumentMetadata, DocumentTypeData
from utils.file_hash import compute_file_md5
from validator.validator import Validator, build_doc_validators

from .base import RegistrationBase

app_config = AppConfig.get_instance()
upload_folder = app_config.upload_folder

class DocumentRegistration(RegistrationBase):
    """Registration flow for Document sources."""

    def __init__(self, mongo_storage: Any, upload_by: str, instance: Dict[str, Any]) -> None:
        super().__init__(mongo_storage, upload_by, instance)
        self.upload_folder = upload_folder
        self._validator = Validator(build_doc_validators())
        self._duplicate_checker = DocumentDuplicateChecker(self.mongo_storage)
        self.source_name = self._extract_source_name()
        self.doc_path = self._compute_doc_path()
        self.md5 = self._compute_md5()
        self.source_id = str(uuid.uuid4())

    def register(self) -> Tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
        user_metadata = self._extract_user_metadata()
        pipeline_id = self._get_pipeline_id()
        metadata = self._build_metadata()
        type_data = self._build_type_data(user_metadata)
        self._persist_common(
            source_id=self.source_id,
            source_name=self.source_name,
            source_type_upper=DataSource.DOCUMENT.upper_name,
            pipeline_id=pipeline_id,
            type_data=type_data,
        )
        registered_source = self._build_registered_source_common(
            pipeline_id=pipeline_id,
            metadata=metadata,
            source_type_upper=DataSource.DOCUMENT.upper_name,
            type_data=type_data,
        )
        self._log_registered_common(
            source_type_upper=DataSource.DOCUMENT.upper_name,
            source_name=self.source_name,
            pipeline_id=pipeline_id,
            user_metadata=user_metadata,
        )
        return registered_source, None

    def run_validator(self) -> Tuple[bool, Dict[str, Any] | None]:
        context = {"duplicate_checker": self._duplicate_checker}

        validation_args = {
            "doc_path": self.doc_path,
            "source_name": self.source_name,
            "md5": self.md5
        }
        import asyncio as _asyncio
        is_valid, issue = _asyncio.run(self._validator.validate(validation_args, context))

        if not is_valid:
            # Adapt to structured ValidationIssue dict shape used by callers
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

    def _get_pipeline_id(self) -> str:
        return f"{DataSource.DOCUMENT.value}_{self.source_id}"

    def _extract_source_name(self) -> str:
        return self.instance.get("source_name", "")

    def _compute_doc_path(self) -> str:
        return os.path.join(self.upload_folder, self.instance.get("source_name", ""))

    def _compute_md5(self) -> str:
        return compute_file_md5(self.doc_path)

    def _extract_user_metadata(self) -> Dict[str, Any]:
        user_metadata = self.instance.get("metadata", {})
        if user_metadata:
            logger.info(f"Processing user metadata: {user_metadata}")
        return user_metadata

    def _build_metadata(self) -> DocumentMetadata:
        return DocumentMetadata(
            doc_id=self.source_id,
            doc_name=self.source_name,
            doc_path=self.doc_path,
            upload_by=self.upload_by,
        )

    def _build_type_data(self, user_metadata: Dict[str, Any]) -> Dict[str, Any]:
        doc_type_data = DocumentTypeData(
            file_type=self.source_name.rsplit(".", 1)[-1].lower(),
            doc_path=self.doc_path,
            page_count=0,
            full_text="",
            file_size=0,
            md5=self.md5,
            **user_metadata,
        )
        return doc_type_data.model_dump()
