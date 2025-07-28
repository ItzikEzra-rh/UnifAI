"""
General privacy filtering utilities for data sources.

This module provides reusable functions to filter data sources based on community privacy settings.
Community privacy controls whether data is shared publicly or kept private to the uploader.

Example usage in endpoints:
    # For Slack channels
    filtered_channels = get_filtered_sources_by_type(service, 'SLACK', current_user)
    
    # For documents  
    filtered_docs = get_filtered_sources_by_type(service, 'DOCUMENT', current_user)
    
    # For single source check
    if is_source_accessible_to_user(source, current_user):
        # Process the source
"""

from typing import List, Dict, Any, Optional
from shared.logger import logger


def filter_sources_by_community_privacy(
    sources: List[Dict[str, Any]], 
    current_user: str
) -> List[Dict[str, Any]]:
    """
    Filter sources based on community privacy settings.
    Private community sources are only visible to the user who uploaded them.
    
    Args:
        sources: List of source objects from the database
        current_user: Username of the current user
        
    Returns:
        Filtered list of sources that the current user is authorized to see
    """
    filtered_sources = []
    
    for source in sources:
        # Get community privacy from type_data (defaulting to 'public' if not set)
        type_data = source.get('type_data', {})
        community_privacy = type_data.get('communityPrivacy', 'public')
        source_uploader = source.get('upload_by', 'default')
        source_name = source.get('source_name', 'unknown')
        source_type = source.get('source_type', 'unknown')
        
        # Include source if:
        # 1. Community privacy is 'public', OR
        # 2. Community privacy is 'private' AND current user is the uploader
        if community_privacy == 'public' or (community_privacy == 'private' and source_uploader == current_user):
            filtered_sources.append(source)
        else:
            logger.info(f"Filtering out private community {source_type} '{source_name}' "
                       f"uploaded by '{source_uploader}' from user '{current_user}'")
    
    logger.info(f"Privacy filter: Returning {len(filtered_sources)} of {len(sources)} sources for user '{current_user}'")
    return filtered_sources


def get_filtered_sources_by_type(
    source_service, 
    source_type: str, 
    current_user: str
) -> List[Dict[str, Any]]:
    """
    Get all sources of a specific type, filtered by community privacy settings.
    
    Args:
        source_service: Service instance that provides list_sources method
        source_type: Type of sources to retrieve (e.g., 'SLACK', 'DOCUMENT')
        current_user: Username of the current user
        
    Returns:
        Filtered list of sources that the current user is authorized to see
    """
    all_sources = source_service.list_sources(source_type)
    return filter_sources_by_community_privacy(all_sources, current_user)


def is_source_accessible_to_user(
    source: Dict[str, Any], 
    current_user: str
) -> bool:
    """
    Check if a specific source is accessible to the current user based on community privacy.
    
    Args:
        source: Source object from the database
        current_user: Username of the current user
        
    Returns:
        True if the user can access the source, False otherwise
    """
    type_data = source.get('type_data', {})
    community_privacy = type_data.get('communityPrivacy', 'public')
    source_uploader = source.get('upload_by', 'default')
    
    return community_privacy == 'public' or (community_privacy == 'private' and source_uploader == current_user) 