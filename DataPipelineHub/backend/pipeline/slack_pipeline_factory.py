from functools import cached_property
from typing import Dict, List, Tuple
from pipeline.pipeline_factory import PipelineFactory
from pipeline.decorators import inject
from data_sources.slack.types import SlackMetadata
from data_sources.slack.slack_config_manager import SlackConfigManager
from data_sources.slack.slack_connector import SlackConnector
from data_sources.slack.slack_pipeline_scheduler import SlackDataPipeline
from data_sources.slack.slack_data_processor import SlackProcessor
from data_sources.slack.slack_chunker_strategy import SlackChunkerStrategy
from pipeline.config import ChunkerConfig
from shared.logger import logger
from config.constants import DataSource

class SlackPipelineFactory(PipelineFactory):
    SOURCE_TYPE = DataSource.SLACK.upper_name
    
    def __init__(
        self,
        metadata: SlackMetadata,
    ):
        super().__init__(metadata)

    def _get_configured_connector(self) -> SlackConnector:
        config_manager = SlackConfigManager()
        config_manager.set_project_tokens(
            project_id="example-project",
            bot_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb",
            user_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb"
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
    def slack_processor(self) -> SlackProcessor:
        return SlackProcessor()

    @cached_property
    def slack_chunker(self) -> SlackChunkerStrategy:
        cfg = ChunkerConfig()
        return SlackChunkerStrategy(
            max_tokens_per_chunk=cfg.max_tokens_per_chunk,
            overlap_tokens=cfg.overlap_tokens,
            time_window_seconds=300
        )

    def _get_source_id(self) -> str:
        return self.metadata.channel_id

    def _get_source_name(self) -> str:
        return self.metadata.channel_name
        
    def _create_summary(self) -> Dict:
        return {
            "is_private": self.metadata.is_private,
        }
        
    def _create_orchestrator(self):
        self._get_monitor().start_log_monitoring(target_logger=logger, pipeline_id=f"slack_{self.metadata.channel_id}")
 
    @inject('connector')
    def _create_collector(self, connector) -> Tuple[List[Dict], List[List[Dict]]]:
        return connector.get_conversations_history(
            channel_id=self.metadata.channel_id
        )

    @inject('slack_processor')
    def _create_processor(
        self,
        data: Tuple[List[Dict], List[List[Dict]]],
        slack_processor
    ) -> Tuple[List[Dict], List[List[Dict]]]:
        messages, threads = data
        main = slack_processor.process(
            messages, channel_name=self.metadata.channel_name
        )
        thrs = [
            slack_processor.process(t, channel_name=self.metadata.channel_name)
            for t in threads
        ]
        return main, thrs

    @inject('slack_chunker', 'embedder')
    def _create_chunker_and_embedder(
        self,
        processed: Tuple[List[Dict], List[List[Dict]]],
        slack_chunker,
        embedder
    ) -> List[Dict]:
        main, threads = processed
        chunks = slack_chunker.chunk_content(main)
        for t in threads:
            chunks.extend(slack_chunker.chunk_content(t))

        for idx, c in enumerate(chunks):
            md = c.setdefault("metadata", {})
            md.update({
                "source_id":    self.metadata.channel_id,
                "chunk_index":  idx,
                "source_type":  DataSource.SLACK.upper_name,
            })

        return embedder.generate_embeddings(chunks)

    def _clean_orchestrator(self):
        self._get_monitor().finish_log_monitoring()