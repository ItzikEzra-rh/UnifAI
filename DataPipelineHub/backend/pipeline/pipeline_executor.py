from typing import Any
from config.constants import PipelineStatus
from pipeline.decorators import pipeline_step, monitor_pipeline
from pipeline.pipeline_factory import PipelineFactory

@monitor_pipeline
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
        factory: PipelineFactory,
        pipeline_id: str
    ):
        
        self.factory     = factory
        self.pipeline_id = pipeline_id

    @pipeline_step(PipelineStatus.ORCHESTRATING.value)
    def _orchestrate(self):
        return self.factory.orchestrator()

    @pipeline_step(PipelineStatus.COLLECTING.value)
    def _collect(self):
        return self.factory.collector()

    @pipeline_step(PipelineStatus.PROCESSING.value)
    def _process(
        self,
        collected: Any
    ) -> Any:
        return self.factory.processor(collected)

    @pipeline_step(PipelineStatus.CHUNKING_AND_EMBEDDING.value)
    def _chunk_and_embed(
        self,
        processed: Any
    ) -> Any:
        return self.factory.chunker_and_embedder(processed)

    @pipeline_step(PipelineStatus.STORING.value)
    def _store(
        self,
        embeddings: Any
    ) -> Any:
        return self.factory.storage(self.pipeline_id, embeddings)

    def run(self) -> Any:
       
        orchestrated = self._orchestrate()
        collected    = self._collect()            # status → "collecting"
        processed    = self._process(collected)   # status → "processing"
        embeddings   = self._chunk_and_embed(processed)
        stored       = self._store(embeddings)
        
        return stored       
      
