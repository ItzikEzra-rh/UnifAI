from .meta_data_extractor import MetaDataExtractorBase
from .kubevirt_meta_data_extractor import KubevirtMetaDataExtractor
from .eco_go_meta_data_extractor import EcogoMetaDataExtractor
from .oadp_meta_data_extractor import OadpMetaDataExtractor

# Register the KubevirtMetaDataExtractor, EcogoMetaDataExtractor 
MetaDataExtractorBase.register_extractor("kubevirt", KubevirtMetaDataExtractor)
MetaDataExtractorBase.register_extractor("eco-gotests", EcogoMetaDataExtractor)
MetaDataExtractorBase.register_extractor("oadp", OadpMetaDataExtractor)

# This ensures all extractors are properly registered
__all__ = ['MetaDataExtractorBase', 'KubevirtMetaDataExtractor', 'EcogoMetaDataExtractor', 'OadpMetaDataExtractor']