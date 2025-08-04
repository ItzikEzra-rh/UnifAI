from functools import cached_property
from typing import Dict, List, Tuple
from pipeline.pipeline_factory import PipelineFactory
from shared.source_types import SlackMetadata
from data_sources.slack.slack_config_manager import SlackConfigManager
from data_sources.slack.slack_connector import SlackConnector
from data_sources.slack.slack_data_processor import SlackProcessor
from data_sources.slack.slack_chunker_strategy import SlackChunkerStrategy
from shared.config import ChunkerConfig
from config.constants import DataSource
from config.app_config import AppConfig

class SlackPipelineFactory(PipelineFactory):
    SOURCE_TYPE = DataSource.SLACK.upper_name
    
    def __init__(
        self,
        metadata: SlackMetadata,
    ):
        super().__init__(metadata)
        self.app_config = AppConfig()

    def _get_configured_connector(self) -> SlackConnector:
        config_manager = SlackConfigManager()
        config_manager.set_project_tokens(
            project_id="example-project",
            bot_token=self.app_config.default_slack_bot_token,
            user_token=self.app_config.default_slack_user_token
        )
        config_manager.set_default_project("example-project")
        return SlackConnector(config_manager) 
    
    @cached_property
    def connector(self) -> SlackConnector:
        connector = self._get_configured_connector()
        if not connector.authenticate():
            raise RuntimeError("Slack authentication failed")
        return connector

    @cached_property
    def slack_chunker(self) -> SlackChunkerStrategy:
        cfg = ChunkerConfig()
        return SlackChunkerStrategy(
            max_tokens_per_chunk=cfg.max_tokens_per_chunk,
            overlap_tokens=cfg.overlap_tokens,
            time_window_seconds=300
        )

    def get_source_id(self) -> str:
        return self.metadata.channel_id

    def get_source_name(self) -> str:
        return self.metadata.channel_name
        
    def _create_summary(self) -> Dict:
        return {
            "is_private": self.metadata.is_private,
        }
        
    def _create_collector(self) -> Tuple[List[Dict], List[List[Dict]]]:
        return self.connector.get_conversations_history(
            channel_id=self.metadata.channel_id
        )

    def _create_processor(
        self,
        data: Tuple[List[Dict], List[List[Dict]]],
    ) -> Tuple[List[Dict], List[List[Dict]]]:
        messages, threads = data
        slack_processor = SlackProcessor()
        main = slack_processor.process(
            messages, channel_name=self.metadata.channel_name
        )
        thrs = [
            slack_processor.process(t, channel_name=self.metadata.channel_name)
            for t in threads
        ]
        return main, thrs

    def _create_chunker_and_embedder(
        self,
        processed: Tuple[List[Dict], List[List[Dict]]],
    ) -> List[Dict]:
        main, threads = processed
        chunks = self.slack_chunker.chunk_content(main)
        chunker = self.slack_chunker
        for t in threads:
            chunks.extend(chunker.chunk_content(t))

        for idx, c in enumerate(chunks):
            md = c.setdefault("metadata", {})
            md.update({
                "source_id":    self.metadata.channel_id,
                "chunk_index":  idx,
                "source_type":  DataSource.SLACK.upper_name,
            })

        return self.embedder.generate_embeddings(chunks)
