import functools
from typing import Callable, Any
from pipeline.pipeline_repository import PipelineRepository
from config.constants import PipelineStatus

def inject(*dep_names: str) -> Callable:
    """
    Decorator to inject dependencies from instance attributes into method arguments.

    Usage:
        @inject('connector', 'processor')
        def _create_processor(self, data, connector, processor):
            # connector and processor are pulled from self.connector, self.processor
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs) -> Any:
            for name in dep_names:
                if name not in kwargs:
                    if not hasattr(self, name):
                        raise AttributeError(f"Dependency '{name}' not found on {{self}}")
                    kwargs[name] = getattr(self, name)
            return fn(self, *args, **kwargs)
        return wrapper
    return decorator

def pipeline_step(status: str):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            self.repo.update_pipeline_status(self.pipeline_id, status)

            try:
                return fn(self, *args, **kwargs)
            except Exception as e:
                self.monitor.record_error(
                    pipeline_id=self.pipeline_id,
                    step=status,
                    error=str(e)
                )
                raise
        return wrapper
    return decorator

def monitor_pipeline(exec_cls):
    """
    Class decorator for PipelineExecutor classes.
    - On __init__: instantiate PipelineRepository, register (PENDING) then mark ACTIVE.
    - On run(): after everything finishes, mark DONE.
    """
    orig_init = exec_cls.__init__
    @functools.wraps(orig_init)
    def __init__(self, factory, pipeline_id, *args, **kwargs):
        
        self.factory     = factory
        self.pipeline_id = pipeline_id
        self.repo        = PipelineRepository()

        self.repo.register_pipeline(
            pipeline_id=self.pipeline_id,
            source_type=self.factory.SOURCE_TYPE
        )
        self.pipeline.storage_manager.mstore.upsert_source_summary(
            source_id=self.factory._get_source_id(),
            source_name=self.factory._get_source_name(),
            source_type=self.factory.SOURCE_TYPE,
            pipeline_id=self.pipeline_id,
            summary=self.factory._create_summary()
        )
        orig_init(self, factory, pipeline_id, *args, **kwargs)
    exec_cls.__init__ = __init__

    orig_run = exec_cls.run
    @functools.wraps(orig_run)
    def run(self, *args, **kwargs):
        try:
            return orig_run(self, *args, **kwargs)
        finally:
            self.repo.update_pipeline_status(
                pipeline_id=self.pipeline_id,
                new_status=PipelineStatus.DONE.value
            )
    exec_cls.run = run
    return exec_cls