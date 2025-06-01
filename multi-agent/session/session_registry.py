from typing import Any, Dict
from core.enums import ResourceCategory


class SessionRegistry:
    """
    IOC container for session-scoped resources (LLMs, Tools, Providers, …).

    *One* dict keyed by ResourceCategory, then by user-chosen name.
    """

    def __init__(self) -> None:
        self._store: Dict[ResourceCategory, Dict[str, Any]] = {
            cat: {} for cat in ResourceCategory
        }
        self._frozen = False  # to optionally lock after build

    # ─────────────── public, generic API ────────────────
    def register(self, category: ResourceCategory, name: str, inst: Any) -> None:
        self._assert_not_frozen()
        self._store[category][name] = inst

    def get(self, category: ResourceCategory, name: str) -> Any:
        return self._store[category][name]

    def all_of(self, category: ResourceCategory) -> Dict[str, Any]:
        """Read-only view of a whole bucket (useful in debugging)."""
        return dict(self._store[category])

    # optional safety: freeze after build
    def freeze(self) -> None:
        self._frozen = True

    # internal helper
    def _assert_not_frozen(self):
        if self._frozen:
            raise RuntimeError("SessionRegistry is frozen—no new registrations allowed.")
