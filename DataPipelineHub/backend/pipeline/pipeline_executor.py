from typing import Any
from pipeline.pipeline_repository import PipelineRepository
from config.constants import PipelineStatus
from pipeline.decorators import pipeline_step
from pipeline.pipeline_factory import Pipeline

class PipelineExecutor:
    """
    Given a PipelineFactory (with its five steps already created),
    .run() will invoke:
      1. orchestrator()
      2. collector()
      3. processor(collected)
      4. chunker_and_embedder(processed)
      5. storage(embeddings)
    and return whatever the storage step produces.
    """
    def __init__(
        self,
        pipeline: Pipeline,
        pipeline_id: str
    ):
        self.pipeline     = pipeline
        self.pipeline_id = pipeline_id
        self.repo = self._initialize_repo()
        self.repo.register_pipeline()
        
    def _initialize_repo(self) -> PipelineRepository:
        return PipelineRepository(
            pipeline_id=self.pipeline_id,
            source_type=self.pipeline.source_type,
            source_id=self.pipeline.get_source_id(),
            source_name=self.pipeline.get_source_name()
        )
        
    def _orchestrate(self):
        return self.pipeline.orchestrator()

    @pipeline_step(PipelineStatus.COLLECTING.value)
    def _collect(self):
        return self.pipeline.collector()

    @pipeline_step(PipelineStatus.PROCESSING.value)
    def _process(
        self,
        collected: Any
    ) -> Any:
        return self.pipeline.processor(collected)

    @pipeline_step(PipelineStatus.CHUNKING_AND_EMBEDDING.value)
    def _chunk_and_embed(
        self,
        processed: Any
    ) -> Any:
        return self.pipeline.chunker_and_embedder(processed)

    @pipeline_step(PipelineStatus.STORING.value)
    def _store(
        self,
        embeddings: Any
    ) -> Any:
        return self.pipeline.storage(embeddings)

    def _clean_orchestrator(self):
        self.pipeline.clean_orchestrator()

    def run(self) -> Any:
        self._orchestrate()
        
        collected   = self._collect()          
        processed   = self._process(collected)   
        embeddings  = self._chunk_and_embed(processed)
        stored      = self._store(embeddings)
        
        self._clean_orchestrator()
        self.repo.update_pipeline_status(
            new_status=PipelineStatus.DONE.value
        )
        self.repo.register_data_source(
            summary=self.pipeline.summary()
        )
        return stored
