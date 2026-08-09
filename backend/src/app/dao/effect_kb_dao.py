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


def query_allow_list_entries(
    conn,
    *,
    device_model_id: str,
    raw_types: Sequence[str],
) -> List[Row]:
    """
    Fetch this device's module rows for the given raw_type(s) straight from
    raw_effect_entries — the ground truth for module naming in tone-recipe
    generation (AMP/CAB names, delay/reverb/gate types, etc.).

    Scoped by device_model_id only, not kb_source_id: a device's module list
    is a property of the device, not of any single ingested PDF. A device can
    have several kb_sources (owner's manual, parameter guide, editor manual,
    ...) and the extracted rows may live under any of them, while
    ctx.active_device.kb_source_id points at whichever one this user last
    activated.

    Unlike query_raw_effect_entries, this is not a keyword search: it returns
    the device's full row set for the given raw_type(s) so the caller can
    build an allow-list, not a relevance-ranked subset. A device with no
    rows for a given raw_type simply gets an empty list back.

    raw_type is not a fixed enum across brand extraction strategies (e.g.
    delay is "DLY" on Boss GT devices, "DELAY" on Mooer/Line 6) — pass every
    known spelling for the category being queried.

    Assumes admin-seeded public sources only; enabling private user uploads
    means extending this to (is_public = true OR user_id = <caller>).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                re.id::text,
                re.raw_name,
                coalesce(re.raw_name_norm,'') as raw_name_norm,
                re.raw_type,
                coalesce(re.raw_category,'') as raw_category,
                coalesce(re.raw_description,'') as raw_description,
                coalesce(re.source_section,'') as source_section,
                re.source_page,
                re.confidence
            FROM raw_effect_entries re
            JOIN kb_sources ks ON ks.id = re.kb_source_id
            WHERE re.device_model_id = %s
              AND ks.is_public = true
              AND re.raw_type = ANY(%s)
            ORDER BY re.raw_type ASC, re.raw_name ASC
            """,
            (device_model_id, list(raw_types)),
        )
        return cur.fetchall()
