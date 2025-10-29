from __future__ import annotations

from typing import Any, Dict, Tuple

from config.constants import DataSource
from global_utils.helpers.helpers import calculate_date_range
from shared.logger import logger
from shared.source_types import SlackMetadata, SlackTypeData

from .base import RegistrationBase


class SlackRegistration(RegistrationBase):
    """Registration flow for Slack sources."""

    def __init__(self, mongo_storage: Any, upload_by: str, instance: Dict[str, Any]) -> None:
        super().__init__(mongo_storage, upload_by, instance)
        self.user_metadata = self._extract_user_metadata()
        self.source_id = self._extract_channel_id()
        self.source_name = self._extract_channel_name()
        self.pipeline_id = self._compute_pipeline_id()

    def register(self) -> Tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
        metadata = self._build_metadata()
        type_data = self._build_type_data()
        self._persist_common(
            source_id=self.source_id,
            source_name=self.source_name,
            source_type_upper=DataSource.SLACK.upper_name,
            pipeline_id=self.pipeline_id,
            type_data=type_data,
        )
        registered = self._build_registered_source_common(
            pipeline_id=self.pipeline_id,
            metadata=metadata,
            source_type_upper=DataSource.SLACK.upper_name,
            type_data=type_data,
        )
        self._log_registered_common(
            source_type_upper=DataSource.SLACK.upper_name,
            source_name=self.source_name,
            pipeline_id=self.pipeline_id,
            user_metadata=self.user_metadata,
        )
        return registered, None

    def run_validator(self) -> Tuple[bool, Dict[str, Any] | None]:
        # No validator yet for Slack; always pass.
        return True, None

    def _extract_channel_id(self) -> str:
        return self.instance.get("channel_id", "")

    def _extract_channel_name(self) -> str:
        return self.instance.get("channel_name", "")

    def _compute_pipeline_id(self) -> str:
        return f"{DataSource.SLACK.value}_{self.source_id}"

    def _build_metadata(self) -> SlackMetadata:
        return SlackMetadata(
            channel_id=self.source_id,
            channel_name=self.source_name,
            is_private=self.instance.get("is_private", False),
            upload_by=self.upload_by,
        )

    def _build_type_data(self) -> Dict[str, Any]:
        date_range = self.user_metadata.get("dateRange")
        start_datetime, end_datetime = calculate_date_range(date_range)
        slack_type_data = SlackTypeData(
            is_private=self.instance.get("is_private", False),
            start_timestamp=start_datetime,
            end_timestamp=end_datetime,
            **self.user_metadata,
        )
        return slack_type_data.model_dump()


