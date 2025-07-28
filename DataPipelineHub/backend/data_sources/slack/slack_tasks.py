from global_utils.celery_app import CeleryApp
from providers.slack.slack import embed_slack_channel
from shared.logger import logger

@CeleryApp().app.task(bind=True, max_retries=3, default_retry_delay=60)
def embed_slack_channels_task(self, channel_list, upload_by="default"):
    """
    Embed multiple Slack channels with individual error handling.
    This prevents one failing channel from causing the entire batch to retry.
    """
    results = []
    failed_channels = []
    
    for channel in channel_list:
        try:
            # Process each channel individually
            channel_id = channel.get('channel_id', str(channel))
            logger.info(f"Processing Slack channel: {channel_id}")
            
            result = embed_slack_channel([channel], upload_by)
            results.append({
                "channel_id": channel_id,
                "status": "success",
                "result": result
            })
            logger.info(f"Successfully processed channel: {channel_id}")
            
        except Exception as e:
            # Log individual channel failure but continue processing others
            channel_id = channel.get('channel_id', str(channel)) if isinstance(channel, dict) else str(channel)
            error_msg = str(e)
            
            logger.error(f"Failed to process channel {channel_id}: {error_msg}", exc_info=True)
            
            failed_channels.append({
                "channel_id": channel_id,
                "error": error_msg
            })
            
            results.append({
                "channel_id": channel_id,
                "status": "failed",
                "error": error_msg
            })
    
    # Only retry the task if ALL channels failed (indicating a systematic issue)
    if failed_channels and len(failed_channels) == len(channel_list):
        logger.error(f"All {len(channel_list)} channels failed. Retrying task...")
        raise self.retry(exc=Exception(f"All channels failed: {[fc['error'] for fc in failed_channels]}"))
    
    # Return summary of results
    summary = {
        "total_channels": len(channel_list),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len(failed_channels),
        "results": results
    }
    
    if failed_channels:
        logger.warning(f"Task completed with {len(failed_channels)} failed channels out of {len(channel_list)} total")
    else:
        logger.info(f"All {len(channel_list)} channels processed successfully")
    
    return summary