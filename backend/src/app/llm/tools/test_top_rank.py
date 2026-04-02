from pathlib import Path
from typing import List

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from customize_class.QWen_embeddings import QWenEmbeddings
from langchain_community.retrievers import BM25Retriever


from pprint import pprint

def build_hybrid_retriever(chunks, vectorstore):
    # BM25 keyword retriever
    bm25 = BM25Retriever.from_documents(chunks)

    # FAISS semantic retriever
    semantic = vectorstore.as_retriever(search_kwargs={"k": 5})

    retriever = EnsembleRetriever(
        retrievers=[bm25, semantic],
        weights=[0.8, 0.2]  # bm25 rank 稍微更重要
    )
    return retriever


# 1. 基于当前文件定位到 src，然后拼 vectorstores/GE150_manual_index
THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parents[1]  # .../pythonProject/src
INDEX_DIR = SRC_DIR / "vectorstores" / "GE150_manual_index"

print("THIS_FILE:", THIS_FILE)
print("SRC_DIR  :", SRC_DIR)
print("INDEX_DIR:", INDEX_DIR)
print("INDEX_DIR exists:", INDEX_DIR.exists())
print("index.faiss exists:", (INDEX_DIR / "index.faiss").exists())
print("index.pkl   exists:", (INDEX_DIR / "index.pkl").exists())

# 2. 尝试加载 FAISS 索引
embeddings = QWenEmbeddings()

vectorstore = FAISS.load_local(
    str(INDEX_DIR),  # 显式转成 str
    embeddings,
    allow_dangerous_deserialization=True,
)

print("Loaded vectorstore:", vectorstore)

# for i, (doc_id, doc) in enumerate(store.items()):
#     print("=" * 60)
#     print(f"CHUNK {i} | ID: {doc_id}")
#     print(doc.page_content[:500])  # 截取前500字
#     print("metadata:", doc.metadata)

# docs = vectorstore.similarity_search("How to use FX LOOP on GE150 Pro?", k=3)
# print("---------answer----------")
# for i, d in enumerate(docs):
#     print("="*40, f"HIT {i}", "="*40)
#     print(d.page_content)
#     print(d.metadata)


store = vectorstore.docstore._dict

def search_keyword(keyword: str, max_hits: int = 10):
    print(f"\n===== 搜索关键词: {keyword} =====")
    count = 0
    for doc_id, doc in store.items():
        text = doc.page_content
        if keyword.lower() in text.lower():
            print("-" * 80)
            print(f"ID: {doc_id}, page: {doc.metadata.get('page')}")
            # 把命中的上下文截出来看一眼：
            idx = text.lower().index(keyword.lower())
            start = max(0, idx - 200)
            end = idx + 200
            print(text[start:end])
            count += 1
            if count >= max_hits:
                break
    if count == 0:
        print("没有找到任何命中。")

search_keyword("FX LOOP")
search_keyword("effects loop")
search_keyword("send")
search_keyword("return")

#----test hybrid retriever----
chunks = []
store = vectorstore.docstore._dict

for doc_id, doc in store.items():
    chunks.append(doc)

print(f"We have {len(chunks)} chunks")

# 2. build hybrid retriever
retriever = build_hybrid_retriever(chunks, vectorstore)

# 3. test
docs = retriever.invoke("How to use FX LOOP on GE150 Pro?")
print("----------------output of hybrid retriever")
for i, d in enumerate(docs):
    print("="*40, f"HIT {i}", "="*40)
    print(d.page_content)
    print(d.metadata)

def compare_search(keyword: str, retriever, topk=5):
    print("\n" + "="*80)
    print(f"🔍 compare：Keyword vs Hybrid for: {keyword}")
    print("="*80)

    # ① 关键词搜索（原始）
    print("\n--- 📘 Keyword Search ---")
    search_keyword(keyword)

    # ② Hybrid 搜索
    print("\n--- 🤖 Hybrid Retrieval ---")
    docs = retriever.invoke(keyword)  # hybrid retriever

    for i, d in enumerate(docs[:topk]):
        print("-"*80)
        print(f"[HYBRID HIT {i}] page={d.metadata.get('page')}")
        print(d.page_content[:300])

print("----------------output of compare_search")
compare_search("FX LOOP", retriever)
compare_search("RETURN jack", retriever)
compare_search("guitar amplifier FX LOOP", retriever)
