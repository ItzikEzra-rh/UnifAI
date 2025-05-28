from typing import List
from llms.chat.message import ChatMessage, Role, ToolCall
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage


class LangChainConverter:
    """
    Translates between ChatMessage and LangChain messages.
    """

    @staticmethod
    def to_lc(history: List[ChatMessage]) -> List:
        out = []
        for m in history:
            if m.role == Role.SYSTEM:
                out.append(SystemMessage(content=m.content))

            elif m.role == Role.USER:
                out.append(HumanMessage(content=m.content))

            elif m.role == Role.ASSISTANT:
                if m.tool_calls:
                    tool_calls = [{
                        "name": tc.name,
                        "args": tc.args,
                        "id": tc.tool_call_id,
                        "type": "tool_call"
                    } for tc in m.tool_calls]
                    out.append(AIMessage(content=m.content, tool_calls=tool_calls))
                else:
                    out.append(AIMessage(content=m.content))

            elif m.role == Role.TOOL:
                out.append(ToolMessage(content=m.content, tool_call_id=m.tool_call_id))

            else:
                raise ValueError(f"Unknown role {m.role}")
        return out

    @staticmethod
    def from_lc_message(m) -> ChatMessage:
        if isinstance(m, SystemMessage):
            return ChatMessage(role=Role.SYSTEM, content=m.content)

        elif isinstance(m, HumanMessage):
            return ChatMessage(role=Role.USER, content=m.content)

        elif isinstance(m, AIMessage):
            tool_calls = None
            if getattr(m, "tool_calls", None):
                tool_calls = [
                    ToolCall(name=tc["name"], args=tc["args"], tool_call_id=tc["id"])
                    for tc in m.tool_calls
                ]
            return ChatMessage(role=Role.ASSISTANT, content=m.content, tool_calls=tool_calls)

        elif isinstance(m, ToolMessage):
            return ChatMessage(role=Role.TOOL, content=m.content, tool_call_id=m.tool_call_id)

        else:
            raise ValueError(f"Unknown message type: {type(m)}")

    @staticmethod
    def from_lc(lc_msgs: List) -> List[ChatMessage]:
        return [LangChainConverter.from_lc_message(m) for m in lc_msgs]
