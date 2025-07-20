from typing import ClassVar, Literal, Annotated
from pydantic import RootModel, model_serializer, SerializerFunctionWrapHandler, SerializationInfo, Field
from core.enums import ResourceCategory


class Ref(RootModel[str]):
    """
    A wrapper around a single string that may be:
      - a bare ID, e.g. "abcd-1234"
      - an external ref, e.g. "$ref:abcd-1234"

    Exposes:
      - .root         the original string
      - .ref          the ID without prefix
      - .is_external_ref()
      - .is_inline()
    """
    REF_PREFIX: ClassVar[str] = "$ref:"

    @property
    def ref(self) -> str:
        raw = self.root
        if raw.startswith(self.REF_PREFIX):
            return raw[len(self.REF_PREFIX):]
        return raw

    def is_external_ref(self) -> bool:
        return self.root.startswith(self.REF_PREFIX)

    def is_inline(self) -> bool:
        return not self.is_external_ref()

    @model_serializer(mode="wrap")
    def _serialize(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo) -> str:
        """
        For 'json' output: return raw self.root (preserve $ref:)
        For 'python' output: return self.ref (strip $ref:)
        """
        if info.mode == "json":
            return self.root
        return self.ref


def _create_ref_type(category: ResourceCategory) -> type[Annotated[Ref, Field]]:
    """
    Factory function to create a typed reference for a specific resource category.

    Args:
        category: The resource category this reference points to

    Returns:
        An Annotated Ref type with category metadata
    """
    return Annotated[Ref, Field(
        description=f"Reference to a {category.value} resource",
        json_schema_extra={
            "category": category.value,
            "examples": [f"$ref:<rid> - resource reference from DB", f"<rid> - inline reference"]
        }
    )]


LLMRef = _create_ref_type(ResourceCategory.LLM)
NodeRef = _create_ref_type(ResourceCategory.NODE)
RetrieverRef = _create_ref_type(ResourceCategory.RETRIEVER)
ToolRef = _create_ref_type(ResourceCategory.TOOL)
ProviderRef = _create_ref_type(ResourceCategory.PROVIDER)
ConditionRef = _create_ref_type(ResourceCategory.CONDITION)
