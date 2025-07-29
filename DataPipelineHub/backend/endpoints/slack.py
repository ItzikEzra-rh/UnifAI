from flask import Blueprint, jsonify, session
from providers.slack.stats import SlackStatsProvider
from providers.privacy_filter import get_filtered_sources_by_type
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from webargs import fields
from shared.logger import logger
from global_utils.helpers.apiargs import from_query, from_body
from global_utils.celery_app.helpers import send_task
from config.constants import DataSource
from providers.slack.slack import (
    get_available_slack_channels,
    count_channel_chunks,
    get_best_match_results,
    delete_slack_channel,
    fetch_available_slack_channels,
)

slack_bp = Blueprint("slack", __name__)

@slack_bp.route("/fetch.available.slack.channels", methods=["PUT"])
def fetch_slack_channels():
    try:
        channels = fetch_available_slack_channels()
        return jsonify({"status": "channels fetched and cached", "count": len(channels)}), 200
    except Exception as e:
        logger.error(f"Failed to fetch available Slack channels: {str(e)}")
        return jsonify({"error": str(e)}), 500


@slack_bp.route("/available.slack.channels.get", methods=["GET"])
@from_query({
    "types": fields.Str(required=True, data_key='types'),
    "cursor": fields.Str(required=False, data_key='cursor', load_default=""),
    "limit": fields.Int(required=False, data_key='limit', load_default=50)
})
def available_slack_channels(types, cursor="", limit=50):
    try:
        result = get_available_slack_channels(types, cursor=cursor, limit=limit)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Failed to get available Slack channels: {str(e)}")
        return jsonify({"error": str(e)}), 500


# @slack_bp.route("/embed.channels.direct", methods=["PUT"])
# @from_body({
#     "channels": fields.List(fields.Dict(), required=True)
# })
# def embed_channels(channels):
#     try:
#         results = embed_slack_channels_flow(channels)
#         return jsonify({"status": "success", "details": results}), 200
#     except Exception as e:
#         logger.error(f"Embedding Slack channels failed: {str(e)}")
#         return jsonify({"error": str(e)}), 500


@slack_bp.route("/slack.channel.chunks", methods=["GET"])
@from_query({
    "channel_name": fields.Str(required=True)
})
def slack_channel_chunks(channel_name):
    try:
        count = count_channel_chunks(channel_name)
        return jsonify({"channel_name": channel_name, "chunk_count": count}), 200
    except Exception as e:
        logger.error(f"Counting chunks failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    
@slack_bp.route("/query.match", methods=["GET"])
@from_query({
    "query": fields.Str(required=True),
    "top_k_results": fields.Int(required=False),
    "scope": fields.Str(required=False, load_default="public"),
    "logged_in_user": fields.Str(required=False, load_default="default", data_key="loggedInUser")
})
def best_match_results(query, top_k_results, scope, logged_in_user):
    try:
        search_results = get_best_match_results(query, top_k_results, scope, logged_in_user)
        return jsonify({"search_results": search_results}), 200
    except Exception as e:
        logger.error(f"Failed to find best match for user query: {str(e)}")
        return jsonify({"error": str(e)}), 500


@slack_bp.route('/embed.channels', methods=['GET'])
def get_embed_channels():
    """
    Returns all stored channels, filtered by source_type and community privacy.
    Private community channels are only visible to the user who uploaded them.
    """
    source_type = DataSource.SLACK.upper_name
    svc = get_mongo_storage()
    current_user = session.get('user', {}).get('username', 'default')
    
    # Use the privacy filter provider to get filtered channels
    filtered_channels = get_filtered_sources_by_type(svc, source_type, current_user)
    
    return jsonify(filtered_channels), 200

@slack_bp.route("/stats", methods=["GET"])
def system_stats():
    provider = SlackStatsProvider()
    stats    = provider.get_stats()
    return jsonify(stats), 200

@slack_bp.route("/embed.channels/<channel_id>", methods=["DELETE"])
def delete_embed_channel(channel_id):
    """
    Delete a slack channel from both MongoDB and Qdrant storage.
    """
    try:
        result = delete_slack_channel(channel_id)
        return jsonify({"status": "success", "message": f"Channel {channel_id} deleted successfully", "result": result}), 200
    except Exception as e:
        logger.error(f"Failed to delete Slack channel {channel_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500