# app/dao/effect_kb_dao.py
from typing import List, Sequence, Tuple


Row = Tuple[
    str,   # id (uuid)
    str,   # raw_name
    str,   # raw_name_norm
    str,   # raw_type
    str,   # raw_category
    str,   # raw_description
    str,   # source_section
    int,   # source_page
    float, # confidence
]


def query_raw_effect_entries(
    conn,
    *,
    device_model_id: str,
    kb_source_id: str,
    tokens: Sequence[str],
    limit: int = 8,
) -> List[Row]:
    """
    Query raw_effect_entries using:
    - strict device filter: device_model_id
    - strict KB filter: kb_source_id
    - keyword matching across name/norm/category/description
    - order by confidence DESC, then source_page ASC

    NOTE: This is ILIKE/LIKE-based (no embedding). Stable + easy to debug.
    """

    toks = [t.strip().lower() for t in (tokens or []) if t and t.strip()]
    if not toks:
        return []

    # Build OR clauses across tokens.
    # Each token maps to 4 LIKE checks.
    like_clauses = []
    params: List[str] = []

    for t in toks:
        p = f"%{t}%"
        like_clauses.append(
            "("
            "lower(raw_name) LIKE %s "
            "OR lower(coalesce(raw_name_norm,'')) LIKE %s "
            "OR lower(coalesce(raw_category,'')) LIKE %s "
            "OR lower(coalesce(raw_description,'')) LIKE %s"
            ")"
        )
        params.extend([p, p, p, p])

    where_like = " OR ".join(like_clauses)

    sql = f"""
        SELECT
            id::text,
            raw_name,
            coalesce(raw_name_norm,'') as raw_name_norm,
            coalesce(raw_type,'') as raw_type,
            coalesce(raw_category,'') as raw_category,
            coalesce(raw_description,'') as raw_description,
            coalesce(source_section,'') as source_section,
            source_page,
            confidence
        FROM raw_effect_entries
        WHERE device_model_id = %s
          AND kb_source_id = %s
          AND ({where_like})
        ORDER BY
          confidence DESC NULLS LAST,
          source_page ASC NULLS LAST,
          raw_name ASC
        LIMIT %s
    """

    with conn.cursor() as cur:
        cur.execute(sql, [device_model_id, kb_source_id, *params, limit])
        return cur.fetchall()
