# app/llm/tools/rag_tool.py
from app.dao import rag_dao
from app.db import get_db_con
from app.llm.customize_class.QWen_embeddings import QWenEmbeddings

embeddings = QWenEmbeddings()

def search_local_docs_logic(query: str, user_id: str, kb_source_id: str) -> str:
    """
    工具逻辑层：将文本转向量，并在指定 kb_source 内检索 chunks
    """
    # （可选但强烈建议）简单日志，方便你确认确实定向到某个设备
    print("[rag] query =", query)
    print("[rag] user_id =", user_id, "kb_source_id =", kb_source_id)

    # 1) 文本 -> 向量
    query_vec = embeddings.embed_query(query)
    vec_str = "[" + ",".join(map(str, query_vec)) + "]"

    # 2) 调 DAO：按 kb_source_id 过滤
    try:
        with get_db_con() as conn:
            rows = rag_dao.query_chunks_by_vector(conn, kb_source_id, vec_str,user_query=query)
            print("[rag] hits =", len(rows))
            for i, r in enumerate(rows[:6]):
                # r = (content, dist, document_id)
                print(f"[rag] #{i} dist={r[1]:.4f} doc={r[2]}")

            if not rows:
                return "在当前设备的知识库中未找到相关信息。"

            context = "\n---\n".join([r[0] for r in rows])
            return context

    except Exception as e:
        print("[rag] ERROR:", repr(e))
        return f"知识库检索异常: {str(e)}"
