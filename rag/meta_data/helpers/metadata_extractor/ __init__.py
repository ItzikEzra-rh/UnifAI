from .meta_data_extractor import MetaDataExtractorBase
from .kubevirt_meta_data_extractor import KubevirtMetaDataExtractor

# Register the KubevirtMetaDataExtractor
MetaDataExtractorBase.register_extractor("kubevirt", KubevirtMetaDataExtractor)

# This ensures all extractors are properly registered
__all__ = ['MetaDataExtractorBase', 'KubevirtMetaDataExtractor']