# pipelines/slack_pipeline.py

from typing import List, Dict, Tuple, Optional
from data_sources.slack.slack_data_processor import SlackProcessor
from data_sources.slack.slack_connector import SlackConnector
from data_sources.slack.slack_chunker_strategy import SlackChunkerStrategy
from shared.source_types import SlackMetadata
from config.constants import DataSource
from pipeline.pipeline import Pipeline
from utils.embedding.embedding_generator import EmbeddingGenerator
from utils.monitor.pipeline_monitor import PipelineMonitor
from utils.storage.vector_storage import VectorStorage
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from shared.logger import logger
from datetime import datetime


class SlackPipeline(Pipeline):
    SOURCE_TYPE = DataSource.SLACK.upper_name
    def __init__(
        self,
        collector: SlackConnector,
        processor: SlackProcessor,
        chunker: SlackChunkerStrategy,
        embedder: EmbeddingGenerator,
        storage: VectorStorage,
        metadata: SlackMetadata,
        monitor: PipelineMonitor,
    ):
        self.collector = collector
        self.slack_processor = processor
        self.slack_chunker = chunker
        self.embedder = embedder
        self.metadata = metadata
        
        super().__init__(
            collector=collector,
            processor=processor,
            chunker=chunker,
            embedder=embedder,
            storage=storage,
            monitor=monitor,
            metadata=metadata
        )

    def get_source_id(self) -> str:
        return self.metadata.channel_id

    def get_source_name(self) -> str:
        return self.metadata.channel_name
        
    def summary(self) -> Dict:
        return {
            "is_private": self.metadata.is_private,
        }
        
    def collect_data(self) -> Tuple[List[Dict], List[List[Dict]]]:
        oldest, latest = self._get_time_range_bounds()
        if oldest or latest:
            logger.info(
                f"Fetching messages for channel {self.metadata.channel_name} in range oldest={oldest}, latest={latest}"
            )
            return self.collector.get_conversations_history(
                channel_id=self.metadata.channel_id,
                oldest=oldest,
                latest=latest,
            )
        logger.info(
            f"Fetching all messages for channel {self.metadata.channel_name} (no time range specified)"
        )
        return self.collector.get_conversations_history(
            channel_id=self.metadata.channel_id
        )

    def _get_time_range_bounds(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Read start_timestamp and end_timestamp from Mongo type_data, return Slack timestamp strings.
        """
        try:
            mongo_storage = get_mongo_storage()
            source_response = mongo_storage.get_source_info(self.metadata.channel_id)

            if not source_response.get("success") or not source_response.get("source_info"):
                logger.warning(
                    f"Could not get source info for channel {self.metadata.channel_id}"
                )
                return None, None

            source_info = source_response["source_info"]
            type_data = source_info.get("type_data", {})

            start_timestamp_obj = type_data.get("start_timestamp")
            end_timestamp_obj = type_data.get("end_timestamp")

            oldest_ts: Optional[str] = None
            latest_ts: Optional[str] = None

            if start_timestamp_obj:
                if isinstance(start_timestamp_obj, str):
                    start_dt = datetime.fromisoformat(start_timestamp_obj.replace('Z', '+00:00'))
                else:
                    start_dt = start_timestamp_obj
                oldest_ts = str(start_dt.timestamp())
                logger.info(f"Using stored start timestamp: {start_dt.isoformat()} → {oldest_ts}")

            if end_timestamp_obj:
                if isinstance(end_timestamp_obj, str):
                    end_dt = datetime.fromisoformat(end_timestamp_obj.replace('Z', '+00:00'))
                else:
                    end_dt = end_timestamp_obj
                latest_ts = str(end_dt.timestamp())
                logger.info(f"Using stored end timestamp: {end_dt.isoformat()} → {latest_ts}")

            return oldest_ts, latest_ts

        except Exception as e:
            logger.warning(
                f"Failed to get time range for channel {self.metadata.channel_id}: {str(e)}"
            )
            return None, None

    def process_data(
        self, data: Tuple[List[Dict], List[List[Dict]]]
    ) -> Tuple[List[Dict], List[List[Dict]]]:
        messages, threads = data
        main = self.slack_processor.process(
            messages, channel_name=self.metadata.channel_name
        )
        thrs = [
            self.slack_processor.process(t, channel_name=self.metadata.channel_name)
            for t in threads
        ]
        return main, thrs

    def chunk_and_embed(
        self, processed: Tuple[List[Dict], List[List[Dict]]]
    ) -> List[Dict]:
        main, threads = processed
        chunks = self.slack_chunker.chunk_content(main)
        for t in threads:
            chunks.extend(self.slack_chunker.chunk_content(t))

        for idx, c in enumerate(chunks):
            md = c.setdefault("metadata", {})
            md.update({
                "source_id": self.metadata.channel_id,
                "chunk_index": idx,
                "source_type": DataSource.SLACK.upper_name,
            })

        return self.embedder.generate_embeddings(chunks)
