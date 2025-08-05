import hashlib
import hmac
import json
from flask import Blueprint, request, jsonify
from shared.logger import logger
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from config.constants import DataSource, PipelineStatus

slack_webhook_bp = Blueprint("slack_webhook", __name__)

def verify_slack_signature(timestamp: str, body: str, signature: str, signing_secret: str) -> bool:
    """
    Verify that the request is from Slack using the signing secret.
    
    Args:
        timestamp: X-Slack-Request-Timestamp header
        body: Raw request body
        signature: X-Slack-Signature header
        signing_secret: Slack app signing secret
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not all([timestamp, body, signature, signing_secret]):
        return False
    
    # Create expected signature
    sig_basestring = f"v0:{timestamp}:{body}"
    expected_signature = "v0=" + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures securely
    return hmac.compare_digest(expected_signature, signature)

@slack_webhook_bp.route("/events", methods=["POST"])
def handle_slack_events():
    """
    Handle incoming Slack events via webhook.
    
    This endpoint:
    1. Verifies the request is from Slack
    2. Handles URL verification challenge
    3. Processes message events by incrementing counters
    """
    try:
        # Get request headers and body
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")
        body = request.get_data(as_text=True)
        
        # Verify Slack signature (uncomment when you have signing secret configured)
        from config.slack_config import SlackConfig
        
        if SlackConfig.is_webhook_verification_enabled():
            signing_secret = SlackConfig.get_signing_secret()
            if signing_secret and not verify_slack_signature(timestamp, body, signature, signing_secret):
                logger.warning("Invalid Slack signature")
                return jsonify({"error": "Invalid signature"}), 401
        
        # Parse JSON payload
        try:
            payload = request.get_json()
        except Exception as e:
            logger.error(f"Failed to parse JSON payload: {str(e)}")
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Handle URL verification challenge
        if payload.get("type") == "url_verification":
            logger.info("Handling Slack URL verification challenge")
            return jsonify({"challenge": payload.get("challenge")})
        
        # Handle event callbacks
        if payload.get("type") == "event_callback":
            event = payload.get("event", {})
            return handle_slack_event(event)
        
        # Handle other event types
        logger.info(f"Received unhandled Slack event type: {payload.get('type')}")
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling Slack webhook: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

def handle_slack_event(event: dict) -> tuple:
    """
    Process specific Slack events and update message counters.
    
    Args:
        event: Slack event data
        
    Returns:
        Flask response tuple
    """
    event_type = event.get("type")
    
    if event_type == "message":
        return handle_message_event(event)
    
    elif event_type in ["message.channels", "message.groups", "message.mpim"]:
        return handle_message_event(event)
    
    else:
        logger.debug(f"Ignoring event type: {event_type}")
        return jsonify({"status": "ignored"}), 200

def handle_message_event(event: dict) -> tuple:
    """
    Handle message events by incrementing the counter for active channels.
    
    Args:
        event: Message event data
        
    Returns:
        Flask response tuple
    """
    try:
        channel_id = event.get("channel")
        message_ts = event.get("ts")
        
        if not channel_id:
            logger.warning("Message event missing channel ID")
            return jsonify({"status": "ignored"}), 200
        
        # Ignore bot messages and system messages
        if event.get("bot_id") or event.get("subtype"):
            logger.debug(f"Ignoring bot/system message in channel {channel_id}")
            return jsonify({"status": "ignored"}), 200
        
        # Check if this channel is active and monitored
        mongo_storage = get_mongo_storage()
        
        # Get channel info from MongoDB
        source_response = mongo_storage.get_source_info(channel_id)
        if not source_response.get("success") or not source_response.get("source_info"):
            logger.debug(f"Channel {channel_id} not found in database, ignoring message")
            return jsonify({"status": "ignored"}), 200
        
        source_info = source_response["source_info"]
        
        # Check if channel is active (has DONE status) and webhook monitoring is enabled
        if source_info.get("status") != PipelineStatus.DONE.value:
            logger.debug(f"Channel {channel_id} is not active (status: {source_info.get('status')}), ignoring message")
            return jsonify({"status": "ignored"}), 200
        
        type_data = source_info.get("type_data", {})
        if not type_data.get("webhook_active", False):
            logger.debug(f"Webhook monitoring not active for channel {channel_id}, ignoring message")
            return jsonify({"status": "ignored"}), 200
        
        # Increment the message counter
        current_count = type_data.get("new_messages_since_last_embedding", 0)
        new_count = current_count + 1
        
        # Update the counter in MongoDB
        type_data.update({
            "new_messages_since_last_embedding": new_count,
            "last_webhook_message_ts": message_ts,
            "last_webhook_update": f"{__import__('datetime').datetime.now().isoformat()}"
        })
        
        # Update the source in MongoDB
        mongo_storage.upsert_source_summary(
            source_id=channel_id,
            source_name=source_info.get("source_name", ""),
            source_type=source_info.get("source_type", DataSource.SLACK.upper_name),
            upload_by=source_info.get("upload_by", "system"),
            pipeline_id=source_info.get("pipeline_id", ""),
            type_data=type_data
        )
        
        logger.info(f"Incremented message counter for channel {channel_id}: {current_count} → {new_count}")
        
        return jsonify({
            "status": "processed",
            "channel_id": channel_id,
            "new_count": new_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing message event: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to process message"}), 500

@slack_webhook_bp.route("/status", methods=["GET"])
def webhook_status():
    """
    Get webhook status and monitored channels.
    
    Returns:
        JSON with webhook status information
    """
    try:
        mongo_storage = get_mongo_storage()
        
        # Get all Slack channels with webhook monitoring enabled
        all_sources = mongo_storage.get_all_sources(DataSource.SLACK.upper_name)
        
        active_channels = []
        total_pending_messages = 0
        
        for source in all_sources:
            type_data = source.get("type_data", {})
            if type_data.get("webhook_active", False) and source.get("status") == PipelineStatus.DONE.value:
                pending_count = type_data.get("new_messages_since_last_embedding", 0)
                total_pending_messages += pending_count
                
                active_channels.append({
                    "channel_id": source.get("source_id"),
                    "channel_name": source.get("source_name"),
                    "pending_messages": pending_count,
                    "last_webhook_update": type_data.get("last_webhook_update"),
                    "last_embedding_timestamp": type_data.get("last_embedding_timestamp")
                })
        
        return jsonify({
            "status": "active",
            "monitored_channels": len(active_channels),
            "total_pending_messages": total_pending_messages,
            "channels": active_channels
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting webhook status: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to get status"}), 500

@slack_webhook_bp.route("/manage/<channel_id>", methods=["POST"])
def manage_webhook_monitoring(channel_id: str):
    """
    Enable or disable webhook monitoring for a specific channel.
    
    Args:
        channel_id: Slack channel ID
        
    Request body:
        {
            "webhook_active": true/false,
            "reset_counter": true/false (optional)
        }
    
    Returns:
        JSON with operation result
    """
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "JSON payload required"}), 400
        
        webhook_active = payload.get("webhook_active")
        reset_counter = payload.get("reset_counter", False)
        
        if webhook_active is None:
            return jsonify({"error": "webhook_active field is required"}), 400
        
        mongo_storage = get_mongo_storage()
        
        # Get current channel info
        source_response = mongo_storage.get_source_info(channel_id)
        if not source_response.get("success") or not source_response.get("source_info"):
            return jsonify({"error": "Channel not found"}), 404
        
        source_info = source_response["source_info"]
        type_data = source_info.get("type_data", {})
        
        # Update webhook settings
        updates = {
            "webhook_active": webhook_active,
            "webhook_updated": f"{__import__('datetime').datetime.now().isoformat()}"
        }
        
        if reset_counter:
            updates["new_messages_since_last_embedding"] = 0
        
        type_data.update(updates)
        
        # Update the source
        mongo_storage.upsert_source_summary(
            source_id=channel_id,
            source_name=source_info.get("source_name", ""),
            source_type=source_info.get("source_type", DataSource.SLACK.upper_name),
            upload_by=source_info.get("upload_by", "system"),
            pipeline_id=source_info.get("pipeline_id", ""),
            type_data=type_data
        )
        
        action = "enabled" if webhook_active else "disabled"
        logger.info(f"Webhook monitoring {action} for channel {channel_id}")
        
        return jsonify({
            "status": "success",
            "channel_id": channel_id,
            "webhook_active": webhook_active,
            "counter_reset": reset_counter,
            "message": f"Webhook monitoring {action}"
        }), 200
        
    except Exception as e:
        logger.error(f"Error managing webhook for channel {channel_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to update webhook settings"}), 500