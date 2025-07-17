import os
import json
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FakeEmbeddings
from langchain.schema import Document

# Example best practices and bug patterns (can be expanded)
BEST_PRACTICES = [
    {"language": "Python", "text": "Use list comprehensions for simple loops."},
    {"language": "Python", "text": "Avoid using mutable default arguments in functions."},
    {"language": "JavaScript", "text": "Always use === instead of == for comparison."},
    {"language": "JavaScript", "text": "Declare variables with let/const instead of var."},
    {"language": "Java", "text": "Always close resources in a finally block or use try-with-resources."},
    {"language": "C++", "text": "Prefer smart pointers over raw pointers."},
    {"language": "C", "text": "Check the return value of malloc and free memory properly."},
]

# Use a fake embedding for demo; replace with real embeddings for production
EMBEDDINGS = FakeEmbeddings(size=32)

# ChromaDB settings (use a valid directory)
CHROMA_SETTINGS = Settings(
    persist_directory="./chroma_db",
    anonymized_telemetry=False,
)

def initialize_chromadb():
    client = chromadb.Client(CHROMA_SETTINGS)
    collection = client.create_collection("best_practices")
    for idx, item in enumerate(BEST_PRACTICES):
        collection.add(
            documents=[item["text"]],
            metadatas=[{"language": item["language"]}],
            ids=[str(idx)]
        )
    return client, collection

def retrieve_best_practices(language, code_snippet, top_k=2):
    # For demo, just return best practices for the language
    return [item["text"] for item in BEST_PRACTICES if item["language"] == language][:top_k]

# For real RAG, use LangChain Retriever with Chroma and real embeddings

def run_rag_on_linter_results(directory, lang_map, linter_results):
    rag_context = {}
    for rel_path, issues in linter_results.items():
        language = lang_map.get(rel_path, "Unknown")
        file_path = os.path.join(directory, rel_path)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
        except Exception:
            code = ""
        rag_context[rel_path] = []
        for issue in issues:
            context = retrieve_best_practices(language, code)
            rag_context[rel_path].append({
                "issue": issue,
                "context": context
            })
    return rag_context

def save_rag_context(directory, rag_context):
    out_path = os.path.join(directory, 'rag_context.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(rag_context, f, indent=2) 