from .category_builder import CategoryBuilder
from core.enums import ResourceCategory
from plugins.exceptions import PluginConfigurationError


class ToolBuilder(CategoryBuilder):
    category = ResourceCategory.TOOL
    depends_on = (ResourceCategory.PROVIDER,)

    def _iter_specs(self, bp):
        return bp.tools

    # inject provider if declared
    def _extra_kwargs(self, cfg, reg):
        if getattr(cfg, "provider", None):
            try:
                provider = reg.get(ResourceCategory.PROVIDER, cfg.provider)
            except KeyError as e:
                raise PluginConfigurationError(
                    f"Tool {cfg.name!r} references unknown provider {cfg.provider!r}",
                    cfg.dict()
                ) from e
            return {"provider": provider}
        return {}
