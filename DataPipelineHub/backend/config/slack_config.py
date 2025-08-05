import os
from typing import Optional

class SlackConfig:
    """Configuration for Slack webhook integration"""
    
    @staticmethod
    def get_signing_secret() -> Optional[str]:
        """Get Slack app signing secret from environment variables"""
        return os.getenv('SLACK_SIGNING_SECRET')
    
    @staticmethod
    def get_bot_token() -> Optional[str]:
        """Get Slack bot user OAuth token from environment variables"""
        return os.getenv('SLACK_BOT_TOKEN')
    
    @staticmethod
    def get_verification_token() -> Optional[str]:
        """Get Slack verification token (legacy, for older apps)"""
        return os.getenv('SLACK_VERIFICATION_TOKEN')
    
    @staticmethod
    def is_webhook_verification_enabled() -> bool:
        """Check if webhook signature verification should be enabled"""
        return os.getenv('SLACK_VERIFY_WEBHOOKS', 'true').lower() == 'true'

# Example environment variables you need to set:
"""
export SLACK_SIGNING_SECRET="your_signing_secret_here"
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
export SLACK_VERIFY_WEBHOOKS="true"
"""