from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple
from shared.logger import logger
from shared.source_types import RegisteredSource


class RegistrationBase(ABC):
    """
    Abstract base for source registration flows.

    Implementations should orchestrate validation and persistence while preserving
    the existing behavior for their specific source type.
    """

    def __init__(self, mongo_storage: Any, upload_by: str, instance: Dict[str, Any]) -> None:
        self.mongo_storage = mongo_storage
        self.upload_by = upload_by
        self.instance = instance
        
    def run_registration(self) -> Tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
        """
        Orchestrate the single-item registration flow:
        1) validate the instance
        2) register (persist) if valid
        Returns (registered_source_dict, issue_dict)
        """
        is_valid, issue = self.run_validator()
        if not is_valid:
            return None, issue
        return self.register()

    @abstractmethod
    def register(self) -> Tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
        """
        Register a single instance. Returns (registered_source_dict, issue_dict).
        If registration is successful, issue_dict should be None. If validation fails,
        registered_source_dict should be None and issue_dict should contain structured info.
        """
        raise NotImplementedError

    @abstractmethod
    def run_validator(self) -> Tuple[bool, Dict[str, Any] | None]:
        """Run source-specific validation for a single instance and return (is_valid, issue)."""
        raise NotImplementedError

    def _extract_user_metadata(self) -> Dict[str, Any]:
        user_metadata = self.instance.get("metadata", {})
        if user_metadata:
            logger.info(f"Processing user metadata: {user_metadata}")
        return user_metadata

    def _persist_common(
        self,
        *,
        source_id: str,
        source_name: str,
        source_type_upper: str,
        pipeline_id: str,
        type_data: Dict[str, Any],
    ) -> None:
        self.mongo_storage.upsert_source_summary(
            source_id=source_id,
            source_name=source_name,
            source_type=source_type_upper,
            upload_by=self.upload_by,
            pipeline_id=pipeline_id,
            type_data=type_data,
        )

    def _build_registered_source_common(
        self,
        *,
        pipeline_id: str,
        metadata: Any,
        source_type_upper: str,
        type_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        registered_source = RegisteredSource(
            pipeline_id=pipeline_id,
            metadata=metadata.__dict__,
            source_type=source_type_upper,
            upload_by=self.upload_by,
            type_data=type_data,
        )
        return registered_source.model_dump()

    def _log_registered_common(
        self,
        *,
        source_type_upper: str,
        source_name: str,
        pipeline_id: str,
        user_metadata: Dict[str, Any],
    ) -> None:
        metadata_info = f" with user settings: {user_metadata}" if user_metadata else ""
        logger.info(
            f"Registered {source_type_upper} source: {source_name} with pipeline_id: {pipeline_id}{metadata_info}"
        )


