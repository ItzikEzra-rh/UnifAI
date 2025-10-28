import functools
from config.constants import PipelineStatus

def pipeline_step(status: str):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            self.repo.update_pipeline_status(self.pipeline, status)

            try:
                return fn(self, *args, **kwargs)
            except Exception as e:
                self.pipeline.monitor.record_error(
                    pipeline_id=self.pipeline.get_pipeline_id(),
                    error_details=status,
                    error_message=str(e)
                )
                # If it's a Slack rate limit, do not mark as FAILED; let outer retry handle it
                msg = str(e).lower()
                is_rate_limit = (
                    "rate limit" in msg or 
                    "Rate limit" in msg or 
                    "ratelimited" in msg or 
                    "too many requests" in msg or 
                    "429" in msg
                )
                if not is_rate_limit:
                    self.repo.update_pipeline_status(self.pipeline, PipelineStatus.FAILED.value)
                self.repo.register_data_source(
                    pipeline=self.pipeline,
                    summary={
                        "last_error": str(e),
                        "failed_at": status,
                    }
                )
                raise
        return wrapper
    return decorator
