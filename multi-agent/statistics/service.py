from blueprints.service import BlueprintService
from session.service import SessionService
from resources.service import ResourcesService
from .models import StatisticsResponse, ResourceCategoryStats


class StatisticsService:
    """
    Service for aggregating statistics for all features.
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

    def get_all(self, user_id: str) -> StatisticsResponse:
        """
        Get aggregated statistics for all features.
        Returns all stats in a single response for optimal performance.

        Args:
            user_id: The user ID to get statistics for

        Returns:
            StatisticsResponse: Pydantic model containing all statistics
        """
        # Get available blueprint IDs for this user
        available_blueprint_ids = set(self._blueprint_service.list_ids(user_id=user_id))
        total_workflows = len(available_blueprint_ids)
        
        # Get blueprint IDs that have sessions
        blueprints_with_sessions = set(self._session_service.get_user_blueprints(user_id))
        
        # Count only blueprints that exist AND have sessions
        active_sessions = len(available_blueprint_ids & blueprints_with_sessions)
        
        # Get session counts, filtered to only include existing blueprints
        all_session_counts = self._session_service.get_user_blueprint_session_counts(user_id)
        blueprint_session_counts = {
            bp_id: count for bp_id, count in all_session_counts.items()
            if bp_id in available_blueprint_ids
        }

        # Get resource aggregation
        resource_repo = self._resources_service._store._repo
        resources_by_category_raw = resource_repo.aggregate_by_category(user_id)

        # Convert to Pydantic models
        resources_by_category = [
            ResourceCategoryStats(**item) for item in resources_by_category_raw
        ]

        # Get total resources count
        total_resources = resource_repo.count(user_id, {})

        return StatisticsResponse(
            totalWorkflows=total_workflows,
            activeSessions=active_sessions,
            totalResources=total_resources,
            categoriesInUse=len(resources_by_category),
            blueprintSessionCounts=blueprint_session_counts,
            resourcesByCategory=resources_by_category
        )

