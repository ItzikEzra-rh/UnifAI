from typing import Any, Dict, List, Tuple, Set
from llms.chat.message import ChatMessage, Role


def merge_string_dicts(existing: Dict[str, str], new_item: Any) -> Dict[str, str]:
    """
    Merge strategy for Dict[str, str]:
    - Accepts new_item as dict[str, str]
    - Overwrites or adds keys
    - Returns merged result
    """
    if not isinstance(existing, dict):
        existing = {}
    if isinstance(new_item, dict):
        # filter only str->str keys for safety
        merged = existing.copy()
        for k, v in new_item.items():
            if isinstance(k, str) and isinstance(v, str):
                merged[k] = v
        return merged
    return existing


def merge_dynamic_fields(
        existing: Dict[str, Any], new_values: Any
) -> Dict[str, Any]:
    """
    Simply updates `existing` with `new_values` if it’s a dict.
    """
    if not isinstance(existing, dict):
        existing = {}
    if isinstance(new_values, dict):
        existing.update(new_values)
    return existing


def _to_chat(msg: Any):
    """Single-pass conversion to ChatMessage (or None)."""
    if isinstance(msg, ChatMessage):
        return msg
    if isinstance(msg, dict) and "role" in msg and "content" in msg:
        return ChatMessage(**msg)
    if isinstance(msg, str):
        return ChatMessage(role=Role.ASSISTANT, content=msg)
    return None


def append_chat_messages(
        existing: List[ChatMessage], new_item: Any
) -> List[ChatMessage]:
    """
    • Normalizes inputs: ChatMessage | dict | str | list/tuple[...]
    • De-duplicates by (role, content) tuple
    """
    out = existing if isinstance(existing, list) else []
    seen: Set[Tuple[str, str]] = {(m.role, m.content) for m in out}
    to_process = new_item if isinstance(new_item, (list, tuple)) else [new_item]

    for raw in to_process:
        cm = _to_chat(raw)
        if cm:
            key = (cm.role, cm.content)
            if key not in seen:
                out.append(cm)
                seen.add(key)

    return out
