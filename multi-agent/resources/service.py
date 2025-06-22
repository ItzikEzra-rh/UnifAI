from .registry import ResourcesRegistry


class ResourcesService:
    def __init__(self, resource_registry: ResourcesRegistry):
        """ Initialize the ResourcesService with a resource registry and an element registry."""
        self.res_reg = resource_registry

    def create(self, user_id: str, category: str, type: str, name: str, cfg_dict):
        return self.res_reg.create(user_id=user_id,
                                   category=category,
                                   type=type,
                                   name=name,
                                   cfg_dict=cfg_dict)

    def delete_resource(self, rid: str):
        self.res_reg.delete(rid)

    def get_resource(self, rid: str) -> dict:
        return self.res_reg.get(rid).json_dump()

    def resolve(self, rid: str) -> dict:
        """Return *current* config dict; caller turns it into Pydantic model."""
        resource = self.res_reg.get(rid)
        return resource.cfg_dict
