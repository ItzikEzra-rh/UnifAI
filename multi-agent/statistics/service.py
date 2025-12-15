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

        Uses generic group_count() methods for efficient database aggregations
        instead of N+1 queries or Python-side grouping.

        Args:
            user_id: The user ID to get statistics for

        Returns:
            StatisticsResponse: Pydantic model containing all statistics
        """
        # Get available blueprint IDs that belong to this user
        available_blueprint_ids = set(self._blueprint_service.list_ids(user_id=user_id))
        total_workflows = len(available_blueprint_ids)
        
        # Get blueprints that have sessions for this user
        blueprints_with_sessions = set(self._session_service.get_user_blueprints(user_id))
        
        # Active = blueprints the user owns AND has sessions for
        active_blueprint_ids = available_blueprint_ids & blueprints_with_sessions
        active_sessions = len(active_blueprint_ids)
        
        # Get session counts using generic group_count() - 1 query instead of N+1
        session_counts_raw = self._session_service.group_count(
            user_id, 
            group_by=["blueprint_id"]
        )
        # Convert aggregation result to dict, filtered to user's own blueprints
        blueprint_session_counts = {
            item["_id"]["blueprint_id"]: item["count"] 
            for item in session_counts_raw
            if item["_id"].get("blueprint_id") in available_blueprint_ids
        }

        # Get resource aggregation using generic group_count() - uses service layer (DIP)
        resources_grouped = self._resources_service.group_count(
            user_id, 
            group_by=["category", "type"]
        )
        
        # Transform aggregation results to ResourceCategoryStats format
        # Group by category and collect types within each category
        category_data = {}
        for item in resources_grouped:
            category = item["_id"].get("category")
            type_name = item["_id"].get("type")
            count = item["count"]
            
            if not category:
                continue
                
            if category not in category_data:
                category_data[category] = {"count": 0, "types": {}}
            
            category_data[category]["count"] += count
            if type_name:
                category_data[category]["types"][type_name] = count
        
        resources_by_category = [
            ResourceCategoryStats(category=cat, count=data["count"], types=data["types"])
            for cat, data in category_data.items()
        ]

        # Get total resources count using service layer
        total_resources = self._resources_service.count(user_id)

        return StatisticsResponse(
            totalWorkflows=total_workflows,
            activeSessions=active_sessions,
            totalResources=total_resources,
            categoriesInUse=len(resources_by_category),
            blueprintSessionCounts=blueprint_session_counts,
            resourcesByCategory=resources_by_category
        )

