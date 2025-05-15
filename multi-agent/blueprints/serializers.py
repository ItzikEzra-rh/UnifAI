import logging
from typing import Any, Dict, List, get_origin
from pydantic import BaseModel

# def meta_to_dict(config_cls: type) -> Dict[str, Any]:
#     """
#     Collect all annotated fields from all Meta classes in the MRO,
#     so that subclass overrides win.
#     """
#     meta = getattr(config_cls, "Meta", None)
#     if not meta:
#         return {}
#     result: Dict[str, Any] = {}
#     # Walk base→subclass so overrides replace defaults
#     for base in reversed(meta.__mro__):
#         for key in getattr(base, "__annotations__", {}):
#             result[key] = getattr(meta, key)
#     return result


from typing import Any, Dict, List
from pydantic import BaseModel


def meta_to_dict(config_cls: type) -> Dict[str, Any]:
    meta = getattr(config_cls, "Meta", None)
    if not meta:
        return {}
    result: Dict[str, Any] = {}
    for base in reversed(meta.__mro__):
        for key in getattr(base, "__annotations__", {}):
            result[key] = getattr(meta, key)
    return result


def blueprint_to_dict_with_meta(spec: BaseModel) -> Dict[str, Any]:
    """
    1) Use model_dump(mode="json") to get a pure-primitive structure.
    2) Walk spec & that primitive tree in parallel to inject any Meta.
    """
    plain = spec.model_dump(mode="json")

    def recurse(inst: Any, data: Any) -> Any:
        # 1) If this is a BaseModel, data is a dict of primitives
        if isinstance(inst, BaseModel):
            out: Dict[str, Any] = {}
            for field in inst.model_fields:
                inst_val = getattr(inst, field)
                data_val = data.get(field)
                out[field] = recurse(inst_val, data_val)

            # attach this model class’s Meta if it exists
            meta = getattr(type(inst), "Meta", None)
            if meta is not None:
                out["_meta"] = meta_to_dict(type(inst))

            return out

        # 2) If this is a list, data is a list of primitives
        if isinstance(inst, list) and isinstance(data, list):
            return [recurse(i, d) for i, d in zip(inst, data)]

        # 3) Otherwise (primitives), just return the JSON-safe value
        return data

    return recurse(spec, plain)
