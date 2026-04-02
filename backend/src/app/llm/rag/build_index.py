from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS

from guitar_fx_agent.config import DOCS_DIR, INDEX_DIR, get_embeddings


def load_docs(doc_dir: Path):
    docs = []
    doc_dir.mkdir(parents=True, exist_ok=True)
    for p in doc_dir.glob("**/*"):
        if p.is_dir():
            continue
        if p.suffix.lower() == ".pdf":
            docs.extend(PyPDFLoader(str(p)).load())
        elif p.suffix.lower() in {".txt", ".md"}:
            docs.extend(TextLoader(str(p), encoding="utf-8").load())
    return docs


def build_index():
    docs = load_docs(DOCS_DIR)
    if not docs:
        print(f"[RAG] No docs found in {DOCS_DIR}. Add PDFs/txt and rerun.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(docs)

    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(INDEX_DIR))
    print(f"[RAG] Index saved to {INDEX_DIR}")


if __name__ == "__main__":
    build_index()
