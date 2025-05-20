from typing import List
from llms.chat.message import ChatMessage, Role
from langchain.schema import SystemMessage, HumanMessage, AIMessage


class LangChainConverter:
    """
    Translates back and forth between our ChatMessage and LangChain messages.
    SRP: only conversion logic lives here.
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
                out.append(AIMessage(content=m.content))
            else:
                raise ValueError(f"Unknown role {m.role}")
        return out

    @staticmethod
    def from_lc(lc_msgs: List) -> List[ChatMessage]:
        out: List[ChatMessage] = []
        for m in lc_msgs:
            if isinstance(m, SystemMessage):
                out.append(ChatMessage(Role.SYSTEM, m.content))
            elif isinstance(m, HumanMessage):
                out.append(ChatMessage(Role.USER, m.content))
            elif isinstance(m, AIMessage):
                out.append(ChatMessage(Role.ASSISTANT, m.content))
        return out
