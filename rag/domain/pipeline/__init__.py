"""Pipeline aggregate - domain model, repository port, and source pipeline port."""
from domain.pipeline.model import PipelineRecord, PipelineStatus, PipelineStats
from domain.pipeline.repository import PipelineRepository
from domain.pipeline.port import SourcePipelinePort, PipelineContext
from domain.pipeline.dispatcher import PipelineTaskDispatcher, TaskResult

__all__ = [
    "PipelineRecord",
    "PipelineStatus",
    "PipelineStats",
    "PipelineRepository",
    "SourcePipelinePort",
    "PipelineContext",
    "PipelineTaskDispatcher",
    "TaskResult",
]
