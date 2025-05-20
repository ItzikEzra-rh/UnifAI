from typing import Any, Dict, List, Tuple, Set
from llms.chat.message import ChatMessage, Role


def append_dict_to_list(
        existing: List[Dict[str, Any]], new_item: Any
) -> List[Dict[str, Any]]:
    """
    • Flattens any nested lists/tuples in `new_item`
    • Appends each dict exactly once (by identity/equality)
    """
    out = existing if isinstance(existing, list) else []
    seen = out.__contains__  # local binding

    def _flatten(seq):
        for el in seq:
            if isinstance(el, (list, tuple)):
                yield from _flatten(el)
            else:
                yield el

    if isinstance(new_item, (list, tuple)):
        for candidate in _flatten(new_item):
            if isinstance(candidate, dict) and not seen(candidate):
                out.append(candidate)
    elif isinstance(new_item, dict):
        if not seen(new_item):
            out.append(new_item)

    return out


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
