from typing import Optional, Dict, Any, Tuple, List
from services.slack.channel_bot_installation_checker import ChannelBotInstallationChecker
from common.interfaces import DataSourceValidator, ValidationIssue
from shared.logger import logger


class ChannelBotInstallationValidator(DataSourceValidator):
    name = "ChannelBotInstallationValidator"
    error_message = "Invite the TAG-001 app user to this channel to enable embedding. Channel: {channel_name}"
    error_message_key = "Channel bot not installed"

    def __init__(self) -> None:
        self._checker = ChannelBotInstallationChecker()

    def validate(self, **kwargs: Any) -> Tuple[bool, Optional[ValidationIssue]]:
        """
        Validate that the Slack app (bot user) is a member of the provided channel.
        Falls back to Slack API if cache is missing/unknown.
        Expected kwargs:
          - channel_id: str (required)
          - channel_name: str (optional, for nicer messaging)
        """
        channel_id = kwargs.get("channel_id")
        channel_name = kwargs.get("channel_name") or ""

        if not isinstance(channel_id, str) or not channel_id:
            # Without a channel_id we cannot validate; do not block
            return True, None

        try:
            # Always check with Slack API via the checker, regardless of cached is_app_member
            is_member = self._checker.is_bot_installed_in_channel(channel_id)
            if not is_member:
                return False, self.build_issue(
                    self.error_message.format(channel_name=channel_name or channel_id)
                )

            return True, None

        except Exception as e:
            # Any unexpected error should not block the flow
            logger.error(f"SlackAppInstalledValidator: unexpected error validating {channel_id}: {e}")
            return True, None


def build_slack_validators(_mongo_storage: Any) -> List[DataSourceValidator]:
    """
    Build the list of Slack-specific validators.
    """
    return [
        ChannelBotInstallationValidator(),
    ]


