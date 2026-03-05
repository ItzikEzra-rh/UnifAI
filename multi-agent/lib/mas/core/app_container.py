from mas.catalog.element_registry import ElementRegistry
from mas.catalog.service import CatalogService
from outbound.mongo import MongoBlueprintRepository
from mas.blueprints.service import BlueprintService
from mas.blueprints.resolver import BlueprintResolver
from mas.session.building import WorkflowSessionFactory
from outbound.mongo import MongoSessionRepository
from mas.session.management import UserSessionManager
from mas.session.execution import SessionLifecycle, ForegroundSessionRunner
from mas.session.service import SessionService
from mas.resources.registry import ResourcesRegistry
from mas.resources.service import ResourcesService
from outbound.mongo import MongoResourceRepository
from mas.graph.service import GraphService
from mas.graph.validation.service import GraphValidationService
from mas.actions.service import ActionsService
from outbound.mongo import MongoShareRepository
from mas.sharing.cloner import ShareCloner
from mas.sharing.service import ShareService
from mas.statistics.service import StatisticsService
from mas.validation.service import ElementValidationService
from outbound.mongo import MongoTemplateRepository
from mas.templates.service import TemplateService
from mas.config.app_config import AppConfig
from global_utils.utils.singleton import SingletonMeta


class AppContainer(metaclass=SingletonMeta):
    """
    Central composition root.  All wiring lives here, but no magic strings:
      • reads collection names   from AppConfig
      • reads engine_name        from AppConfig
      • reads mongo_uri & db     from AppConfig
    """

    def __init__(self, cfg: AppConfig):
        # idempotent guard
        if getattr(self, "_initialized", False):
            return

        # plugin discovery
        self.element_registry = ElementRegistry()
        self.element_registry.auto_discover()

        # actions service (independent of element registry)
        self.actions_service = ActionsService()
        # auto-discover and register all actions
        self.actions_service.auto_discover_actions()

        # catalog service
        self.catalog_service = CatalogService(self.element_registry)

        # Graph service (building only)
        self.graph_service = GraphService(self.element_registry)
        
        # Graph validation service (validation only)
        self.graph_validation_service = GraphValidationService(self.element_registry)

        # Element validation service
        self.validation_service = ElementValidationService(
            element_registry=self.element_registry
        )

        # blueprint catalog
        self.blueprint_repo = MongoBlueprintRepository(
            db_name=cfg.mongo_db,
            coll_name=cfg.blueprint_coll
        )

        # resource registry
        resource_registry = ResourcesRegistry(repo=MongoResourceRepository(cfg.mongodb_port,
                                                                           mongodb_ip=cfg.mongodb_ip,
                                                                           db_name=cfg.mongo_db,
                                                                           coll_name=cfg.resources_coll),
                                              bp_repo=self.blueprint_repo)

        # resources service (with validation)
        self.resources_service = ResourcesService(
            resource_registry=resource_registry,
            element_registry=self.element_registry,
            validation_service=self.validation_service,
        )
        
        # blueprint resolver
        self.blueprint_resolver = BlueprintResolver(
            resource_registry=resource_registry,
            element_registry=self.element_registry
        )

        # blueprint service (with validation)
        self.blueprint_service = BlueprintService(
            self.blueprint_repo,
            resolver=self.blueprint_resolver,
            validation_service=self.validation_service,
        )

        # session orchestration
        self.session_factory = WorkflowSessionFactory(
            element_registry=self.element_registry,
            engine_name=cfg.engine_name
        )
        self.session_repo = MongoSessionRepository(
            mongodb_port=cfg.mongodb_port,
            mongodb_ip=cfg.mongodb_ip,
            db_name=cfg.mongo_db,
            collection_name=cfg.session_coll
        )
        self.session_manager = UserSessionManager(
            repository=self.session_repo,
            session_factory=self.session_factory,
            blueprint_service=self.blueprint_service
        )
        # Session lifecycle — portable state-machine transitions.
        self.session_lifecycle = SessionLifecycle(repository=self.session_repo)

        # Streaming / HITL channel factory — single resolution for all processes.
        self.channel_factory = self._create_channel_factory(cfg)

        foreground_runner = ForegroundSessionRunner(
            lifecycle=self.session_lifecycle,
            channel_factory=self.channel_factory,
        )

        # Background submitter — only wired when engine supports it.
        background_submitter = self._create_background_submitter(cfg.engine_name)

        self.session_service = SessionService(
            manager=self.session_manager,
            foreground_runner=foreground_runner,
            background_submitter=background_submitter,
        )

        # sharing service
        self.share_repo = MongoShareRepository(
            db_name=cfg.mongo_db,
            coll_name=cfg.shares_coll
        )
        self.share_cloner = ShareCloner(
            resources_registry=resource_registry,
            blueprint_service=self.blueprint_service,
            element_registry=self.element_registry
        )
        self.share_service = ShareService(
            share_repository=self.share_repo,
            cloner=self.share_cloner
        )

        # Statistics service (user-specific dashboard stats AND system-wide analytics)
        # System-wide analytics uses session_service's system-wide methods
        # No separate analytics repository needed - follows composition pattern
        self.statistics_service = StatisticsService(
            blueprint_service=self.blueprint_service,
            session_service=self.session_service,
            resources_service=self.resources_service
        )

        # Template service
        self.template_repo = MongoTemplateRepository(
            db_name=cfg.mongo_db,
            coll_name=cfg.templates_coll
        )
        self.template_service = TemplateService(
            repository=self.template_repo,
            element_registry=self.element_registry,
            blueprint_service=self.blueprint_service,
            resources_service=self.resources_service,
        )

        self._initialized = True

    @staticmethod
    def _create_channel_factory(cfg: AppConfig):
        """
        Resolve the ChannelFactory based on deployment config.

        Used by BOTH the API process (foreground runner) and the
        Temporal worker (background node activities).  One resolution,
        one truth.

        When you add Redis support:
            if cfg.redis_url:
                from outbound.channels.redis_channel_factory import RedisChannelFactory
                return RedisChannelFactory(cfg.redis_url)
        """
        from outbound.channels import LocalChannelFactory
        return LocalChannelFactory()

    @staticmethod
    def _create_background_submitter(engine_name: str):
        """Lazily create a BackgroundSessionSubmitter for engines that support it."""
        if engine_name == "temporal":
            from outbound.temporal.submitter import TemporalSessionSubmitter
            return TemporalSessionSubmitter()
        return None
