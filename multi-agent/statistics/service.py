from typing import Dict, Any
from blueprints.service import BlueprintService
from session.service import SessionService
from resources.service import ResourcesService


class StatisticsService:
    """
    Service for aggregating statistics for agentic features.
    Centralizes the logic for collecting and formatting workflow, session, and resource statistics.
    """

    def __init__(
        self,
        blueprint_service: BlueprintService,
        session_service: SessionService,
        resources_service: ResourcesService
    ):
        """
        Initialize the StatisticsService.

        Args:
            blueprint_service: Service for blueprint operations
            session_service: Service for session operations
            resources_service: Service for resource operations
        """
        self._blueprint_service = blueprint_service
        self._session_service = session_service
        self._resources_service = resources_service

    def get_agentic_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for agentic features.
        Returns all stats in a single response for optimal performance.

        Args:
            user_id: The user ID to get statistics for

        Returns:
            Dictionary containing:
                - totalWorkflows: Total number of workflows/blueprints
                - activeSessions: Number of active sessions
                - totalResources: Total number of resources
                - blueprintSessionCounts: Dictionary mapping blueprint_id to session count
                - resourcesByCategory: List of resource statistics grouped by category
        """
        # Get counts using optimized queries
        total_workflows = self._blueprint_service.count(user_id=user_id)
        active_sessions = len(self._session_service.get_user_blueprints(user_id))
        blueprint_session_counts = self._session_service.get_user_blueprint_session_counts(user_id)

        # Get resource aggregation using MongoDB aggregation
        resource_repo = self._resources_service._store._repo
        resources_by_category = resource_repo.aggregate_by_category(user_id)

        # Get total resources count
        total_resources = resource_repo.count(user_id, {})

        return {
            "totalWorkflows": total_workflows,
            "activeSessions": active_sessions,
            "totalResources": total_resources,
            "blueprintSessionCounts": blueprint_session_counts,
            "resourcesByCategory": resources_by_category
        }

