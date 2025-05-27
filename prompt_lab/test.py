import bs4
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain_core.vectorstores import InMemoryVectorStore
from docling.document_converter import DocumentConverter
import re
from langchain.text_splitter import MarkdownHeaderTextSplitter
import getpass
import os
from langchain.embeddings import HuggingFaceEmbeddings

from langchain.chat_models import ChatOpenAI


# Your VLLM server configuration (update as needed)
VLLM_URL = "http://localhost:8000/v1"  # Replace with your VLLM URL
MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"  # Replace if different

# LangChain requires an API key placeholder
os.environ["OPENAI_API_KEY"] = "fake-key"

# Create the ChatOpenAI client with streaming enabled and use a callback to stream tokens
llm = ChatOpenAI(
    openai_api_base=VLLM_URL,
    openai_api_key="fake-key",   # This key is just a placeholder when using VLLM
    model=MODEL_NAME,
    temperature=0.7,
    max_tokens=500  # This will print tokens as they stream
)
embeddings_model_name = "sentence-transformers/all-mpnet-base-v2"

embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

with open("document.txt", "r") as f:
    document = f.read()
splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3"), ("####", "Header 4")]
)

chunks = splitter.split_text(document)

vector_store = InMemoryVectorStore(embeddings)
# Index chunks
_ = vector_store.add_documents(documents=chunks)

# Define prompt for question-answering
prompt = hub.pull("rlm/rag-prompt")


# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


# Define application steps
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}


# Compile application and test
graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()


response = graph.invoke({"question": "in the sentences that were encoded using byte-pair encoding in training, how much tokens in the target vocabulary?"})
print(response["answer"])