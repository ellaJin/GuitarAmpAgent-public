# app/dao/rag_dao.py

def query_chunks_by_vector(conn, device_model_id: str, vector_str: str, user_query: str = "", limit: int = 6):
    boost_keyword = ""
    if "fx loop" in user_query.lower() or "return" in user_query.lower():
        boost_keyword = "%FX LOOP%" # 或者根据逻辑判断

    # Scoped to all of this device's public kb_sources, not a single manual.
    # Assumes admin-seeded public sources only; enabling private user uploads
    # means extending this to (is_public = true OR user_id = <caller>).
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
                JOIN kb_sources ks ON ks.id = d.kb_source_id
                WHERE ks.device_model_id = %s
                  AND ks.is_public = true
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
                device_model_id,
                limit,
            ),
        )
        return cur.fetchall()




