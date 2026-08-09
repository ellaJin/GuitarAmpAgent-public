# app/llm/tools/rag_tool.py
import json
import logging
import time

from app.dao import rag_dao
from app.db import get_db_con
from app.llm.customize_class.QWen_embeddings import QWenEmbeddings

logger = logging.getLogger("retrieval")

embeddings = QWenEmbeddings()

def search_local_docs_logic(query: str, user_id: str, device_model_id: str) -> str:
    """
    工具逻辑层：将文本转向量，并在该设备的全部公开 kb_source 内检索 chunks
    """
    # （可选但强烈建议）简单日志，方便你确认确实定向到某个设备
    print("[rag] query =", query)
    print("[rag] user_id =", user_id, "device_model_id =", device_model_id)

    # 1) 文本 -> 向量
    query_vec = embeddings.embed_query(query)
    vec_str = "[" + ",".join(map(str, query_vec)) + "]"

    # 2) 调 DAO：按 device_model_id 过滤（覆盖该设备全部 manual）
    try:
        with get_db_con() as conn:
            _t0 = time.perf_counter()
            rows = rag_dao.query_chunks_by_vector(conn, device_model_id, vec_str, user_query=query)
            _latency_ms = round((time.perf_counter() - _t0) * 1000, 2)
            logger.info(json.dumps({
                "event": "retrieval",
                "tool": "rag",
                "query": query[:80],
                "num_results": len(rows),
                "latency_ms": _latency_ms,
            }))
            print("[rag] hits =", len(rows))
            for i, r in enumerate(rows[:6]):
                # r = (content, dist, document_id)
                print(f"[rag] #{i} dist={r[1]:.4f} doc={r[2]}")

            if not rows:
                return json.dumps({"content": "No relevant information found in the current device knowledge base.", "source_count": 0})

            context = "\n---\n".join([r[0] for r in rows])
            return json.dumps({"content": context, "source_count": len(rows)})

    except Exception as e:
        print("[rag] ERROR:", repr(e))
        return json.dumps({"content": f"Knowledge base retrieval error: {str(e)}", "source_count": 0})
