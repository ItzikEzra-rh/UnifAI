"""
Pipeline module initialization.

This module imports all pipeline factory subclasses to ensure they are
automatically registered in the PipelineFactory registry when the pipeline
module is imported. This prevents bugs where subclasses aren't registered
because they weren't imported elsewhere.
"""

# Import all pipeline factory subclasses to trigger their registration
from .pipeline_factory import PipelineFactory
from .doc_pipeline_factory import DocumentPipelineFactory
from .slack_pipeline_factory import SlackPipelineFactory

# Re-export the main factory class for convenient access
__all__ = [
    "PipelineFactory",
    "DocumentPipelineFactory", 
    "SlackPipelineFactory"
] 