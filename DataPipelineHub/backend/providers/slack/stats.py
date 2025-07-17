from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.storage.mongo.mongo_helpers import get_source_service
from config.constants import DataSource


class SlackStatsProvider:
    def __init__(self):
        # source_service implements both SourceRepository & PipelineRepository
        self._service = get_source_service()

    def _fetch_slack_sources(self) -> List[Dict[str, Any]]:
        """Fetch all SLACK sources enriched with their last pipeline status."""
        return self._service.list_sources_with_status(source_type=DataSource.SLACK.upper_name)

    def _aggregate_counts(
        self, sources: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Compute channel counts, message totals, and api calls."""
        total_channels  = len(sources)
        active_channels = sum(1 for s in sources if s.get("status") == "ACTIVE")
        total_messages  = sum(
            s.get("type_data", {}).get("message_count", 0) for s in sources
        )
        api_calls_count = sum(
            s.get("type_data", {}).get("api_calls", 0) for s in sources
        )
        return {
            "totalChannels":   total_channels,
            "activeChannels":  active_channels,
            "totalMessages":   total_messages,
            "apiCallsCount":   api_calls_count,
        }

    def _get_last_sync_at(self, sources: List[Dict[str, Any]]) -> Optional[str]:
        """Return the most recent last_sync_at timestamp (ISO string)."""
        timestamps = []
        for s in sources:
            last_sync = s.get("last_sync_at")
            if last_sync is not None:
                timestamps.append(last_sync)
        return max(timestamps) if timestamps else None

    def _get_total_embeddings(self) -> int:
        """Get total number of SLACK sources in the database."""
        try:
            # Fetch all SLACK sources (reusing existing method)
            sources = self._fetch_slack_sources()
            
            # Return the count of SLACK sources
            return len(sources)
        except Exception:
            # Return 0 if unable to connect to storage
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Public method: gather everything into a single dict."""
        sources = self._fetch_slack_sources()
        counts = self._aggregate_counts(sources)
        last_sync = self._get_last_sync_at(sources)
        total_embeddings = self._get_total_embeddings()
        return {
            "id":               1,
            **counts,
            "lastSyncAt":       last_sync,
            "totalEmbeddings":  total_embeddings,
            "updatedAt":        datetime.utcnow().isoformat() + "Z",
        }
