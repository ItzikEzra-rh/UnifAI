from typing import ClassVar
from pydantic import RootModel, model_serializer, SerializerFunctionWrapHandler, SerializationInfo


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
