import functools

def pipeline_step(status: str):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            self.repo.update_pipeline_status(status)

            try:
                return fn(self, *args, **kwargs)
            except Exception as e:
                self.pipeline.monitor.record_error(
                    pipeline_id=self.pipeline_id,
                    error_details=status,
                    error_message=str(e)
                )
                raise
        return wrapper
    return decorator
