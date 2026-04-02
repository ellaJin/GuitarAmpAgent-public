# app/dao/rag_dao.py

def query_chunks_by_vector(conn, kb_source_id: str, vector_str: str, user_query: str = "", limit: int = 6):
    boost_keyword = ""
    if "fx loop" in user_query.lower() or "return" in user_query.lower():
        boost_keyword = "%FX LOOP%" # 或者根据逻辑判断

    with conn.cursor() as cur:
        cur.execute(
            """
            WITH scored_chunks AS (
                SELECT
                    c.content,
                    (c.embedding <=> %s::vector) AS raw_dist,
                    CASE 
                        WHEN %s != '' AND c.content ILIKE %s THEN 0.2 
                        ELSE 0 
                    END AS boost,
                    c.document_id
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.kb_source_id = %s
            )
            SELECT 
                content, 
                raw_dist, 
                document_id
            FROM scored_chunks
            ORDER BY (raw_dist - boost) ASC
            LIMIT %s
            """,
            (
                vector_str,
                boost_keyword, boost_keyword,
                kb_source_id,
                limit,
            ),
        )
        return cur.fetchall()




