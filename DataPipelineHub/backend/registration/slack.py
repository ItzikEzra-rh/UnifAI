from __future__ import annotations
from typing import Any, Dict, Tuple
from functools import cached_property
from config.constants import DataSource
from global_utils.helpers.helpers import calculate_date_range
from shared.source_types import SlackMetadata, SlackTypeData
from .base import RegistrationBase


class SlackRegistration(RegistrationBase):
    """Registration flow for Slack sources."""
    DATA_SOURCE_TYPE = DataSource.SLACK.upper_name

    def __init__(self, mongo_storage: Any, upload_by: str, instance: Dict[str, Any]) -> None:
        super().__init__(mongo_storage, upload_by, instance)

    @property
    def source_id(self) -> str:
        return self.instance.get("channel_id", "")

    @cached_property
    def pipeline_id(self) -> str:
        return f"{DataSource.SLACK.value}_{self.source_id}"

    def run_validator(self) -> Tuple[bool, Dict[str, Any] | None]:
        # No validator yet for Slack; always pass.
        return True, None

    def _build_metadata(self) -> SlackMetadata:
        return SlackMetadata(
            channel_id=self.source_id,
            channel_name=self.source_name,
            is_private=self.instance.get("is_private", False),
            upload_by=self.upload_by,
        )

    def _build_type_data(self) -> Dict[str, Any]:
        date_range = self.form_data.get("dateRange")
        start_datetime, end_datetime = calculate_date_range(date_range)
        slack_type_data = SlackTypeData(
            is_private=self.instance.get("is_private", False),
            start_timestamp=start_datetime,
            end_timestamp=end_datetime,
            **self.form_data,
        )
        return slack_type_data.model_dump()


