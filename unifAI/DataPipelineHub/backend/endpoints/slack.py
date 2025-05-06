from flask import Blueprint, jsonify, request
from webargs import fields
from shared.logger import logger
from global_utils.helpers.apiargs import from_query, from_body
from global_utils.celery_app.helpers import send_task
from providers.slack import (
    get_available_slack_channels,
    embed_slack_channels_flow,
    count_channel_chunks,
)

slack_bp = Blueprint("slack", __name__)

@slack_bp.route("/available.slack.channels.get", methods=["GET"])
@from_query({
    "types": fields.Str(required=True, data_key='types')
})
def available_slack_channels(types):
    try:
        channels = get_available_slack_channels(types)
        return jsonify({"channels": channels}), 200
    except Exception as e:
        logger.error(f"Failed to get available Slack channels: {str(e)}")
        return jsonify({"error": str(e)}), 500


@slack_bp.route("/embed.channels", methods=["PUT"])
@from_body({
    "channels": fields.List(fields.Dict(), required=True)
})
def embed_channels(channels):
    try:
        send_task(
            task_name="data_sources.slack.slack_tasks.embed_slack_channels_task",
            celery_queue="slack_queue",  # or whatever queue name you're using
            channel_list=channels
        )
        return jsonify({"status": "task submitted"}), 202
    except Exception as e:
        logger.error(f"Failed to submit Slack embedding task: {str(e)}")
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
