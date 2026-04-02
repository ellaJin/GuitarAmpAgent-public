# app/dao/effect_dao.py
import re
from typing import Dict, List, Optional, Tuple, Any

import json


# -------------------------
# Normalize
# -------------------------
def normalize_raw_name(name: str) -> str:
    """
    Normalize raw effect name for stable upsert key.
    Example: "NS-2" / "NS 2" -> "ns2"
    """
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


# -------------------------
# Candidate chunks
# -------------------------
def get_candidate_chunks(conn, document_id: str) -> List[dict]:
    """
    Returns chunks + kb_source_id + device_model_id + meta(page/section)
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
        c.id,
        c.content,
        c.document_id,
        d.kb_source_id,
        ks.device_model_id,
        (c.meta->>'page')::int AS page,
        c.meta->>'section' AS section
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    JOIN kb_sources ks ON d.kb_source_id = ks.id
    WHERE c.document_id = %s
      AND (
        c.content ILIKE '%%effect%%'
        OR c.content ILIKE '%%module%%'
        OR c.content ILIKE '%%annex%%'
        OR c.content ILIKE '%%model%%'
      )
        """,
        (document_id,),
    )
    rows = cur.fetchall()

    out = []
    for r in rows:
        out.append(
            {
                "id": r[0],
                "content": r[1],
                "document_id": r[2],
                "kb_source_id": r[3],
                "device_model_id": r[4],
                "page": r[5],
                "section": r[6],
            }
        )
    return out


# -------------------------
# Bulk upsert raw_effect_entries
# -------------------------
def upsert_raw_effects_bulk(
    conn,
    kb_source_id: str,
    device_model_id: str,
    effects: List[dict],
    source_page: Optional[int] = None,
    source_section: Optional[str] = None,
) -> Dict[Tuple[str, str], str]:
    """
    Upsert raw_effect_entries.
    Unique key: (device_model_id, raw_name_norm, raw_type)

    effects item dict expected keys:
      raw_name (required)
      raw_type (optional)
      raw_category (optional)
      raw_description (optional)
      confidence (optional)
      meta (optional dict)
    Return: {(raw_name_norm, raw_type): id}
    """
    if not effects:
        return {}

    # 1) dedup in-memory per (norm, type)
    uniq: Dict[Tuple[str, str], dict] = {}
    for e in effects:
        raw_name = (e.get("raw_name") or "").strip()
        if not raw_name:
            continue
        raw_type = (e.get("raw_type") or "UNKNOWN")
        raw_type = (raw_type or "UNKNOWN").strip() or "UNKNOWN"

        raw_name_norm = normalize_raw_name(raw_name)
        key = (raw_name_norm, raw_type)

        conf = float(e.get("confidence", 0.5) or 0.5)

        if key not in uniq:
            uniq[key] = {
                "raw_name": raw_name,
                "raw_name_norm": raw_name_norm,
                "raw_type": raw_type,
                "raw_category": e.get("raw_category"),
                "raw_description": e.get("raw_description"),
                "confidence": conf,
                "meta": e.get("meta") or {},
            }
        else:
            old = uniq[key]
            old["confidence"] = max(old["confidence"], conf)
            if not old.get("raw_description") and e.get("raw_description"):
                old["raw_description"] = e.get("raw_description")
            if (old.get("raw_category") in (None, "", "unknown")) and e.get("raw_category"):
                old["raw_category"] = e.get("raw_category")
            if e.get("meta"):
                old["meta"] = {**(old.get("meta") or {}), **e["meta"]}

    rows = []
    for (_, _), v in uniq.items():
        rows.append(
            (
                kb_source_id,
                device_model_id,
                v["raw_name"],
                v["raw_name_norm"],
                v["raw_type"],
                v.get("raw_category"),
                v.get("raw_description"),
                source_section,
                source_page,
                v.get("confidence", 0.5),
                json.dumps(v.get("meta") or {}),
            )
        )

    sql = """
    INSERT INTO raw_effect_entries (
      kb_source_id,
      device_model_id,
      raw_name,
      raw_name_norm,
      raw_type,
      raw_category,
      raw_description,
      source_section,
      source_page,
      confidence,
      meta
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (device_model_id, raw_name_norm, raw_type)
    DO UPDATE SET
      confidence      = GREATEST(raw_effect_entries.confidence, EXCLUDED.confidence),
      raw_name        = EXCLUDED.raw_name,
      raw_category    = COALESCE(EXCLUDED.raw_category, raw_effect_entries.raw_category),
      raw_description = COALESCE(EXCLUDED.raw_description, raw_effect_entries.raw_description),
      source_section  = COALESCE(raw_effect_entries.source_section, EXCLUDED.source_section),
      source_page     = COALESCE(raw_effect_entries.source_page, EXCLUDED.source_page),
      kb_source_id    = raw_effect_entries.kb_source_id,
      meta            = raw_effect_entries.meta || EXCLUDED.meta
    RETURNING id, raw_name_norm, raw_type
    """

    cur = conn.cursor()
    id_map: Dict[Tuple[str, str], str] = {}
    for row in rows:
        cur.execute(sql, row)
        result = cur.fetchone()
        if result:
            rid, rn, rt = result
            id_map[(rn, rt)] = rid
    return id_map


# -------------------------
# Bulk bind effect_chunk_refs
# -------------------------
def bind_effect_chunks_bulk(conn, pairs: List[Tuple[str, str]]) -> None:
    """
    pairs: [(raw_effect_entry_id, chunk_id), ...]
    """
    if not pairs:
        return
    cur = conn.cursor()
    sql = """
    INSERT INTO effect_chunk_refs (raw_effect_entry_id, chunk_id)
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING
    """
    cur.executemany(sql, pairs)


# -------------------------
# system user uploads devices
# -------------------------
def admin_activate_full_setup(conn, system_user_id: str, device_info: dict, manual_data: dict, image_url: str | None, image_mime: str | None):
    """
    Create/Upsert device_models (system), create kb_sources+documents (system).
    returns: (device_model_id, kb_source_id, document_id)
    """
    brand = (device_info.get("brand") or "").strip()
    model = (device_info.get("model") or "").strip()
    variant = (device_info.get("variant") or "").strip() or None

    cur = conn.cursor()

    # 1) find existing device_model
    cur.execute(
        """
        SELECT id, meta FROM device_models
        WHERE brand=%s AND model=%s AND (variant IS NOT DISTINCT FROM %s)
        LIMIT 1
        """,
        (brand, model, variant),
    )
    row = cur.fetchone()

    if row:
        device_model_id = row[0]
        meta = row[1] or {}
        if image_url:
            meta = dict(meta)
            meta["image_url"] = image_url
            if image_mime:
                meta["image_mime"] = image_mime
            cur.execute(
                "UPDATE device_models SET meta=%s WHERE id=%s",
                (json.dumps(meta), device_model_id),
            )
    else:
        meta = {}
        if image_url:
            meta["image_url"] = image_url
            if image_mime:
                meta["image_mime"] = image_mime

        cur.execute(
            """
            INSERT INTO device_models (brand, model, variant, source, created_by, is_public, meta)
            VALUES (%s,%s,%s,%s,%s,true,%s)
            RETURNING id
            """,
            (brand, model, variant, "system", system_user_id, json.dumps(meta)),
        )
        device_model_id = cur.fetchone()[0]

    # 2) kb_source
    cur.execute(
        """
        INSERT INTO kb_sources (user_id, device_model_id, name, source_type, is_active, is_public, meta)
        VALUES (%s,%s,%s,%s,true,true,%s)
        RETURNING id
        """,
        (
            system_user_id,
            device_model_id,
            manual_data["title"],
            "manual_pdf",
            json.dumps({"content_hash": manual_data["content_hash"], "file_name": manual_data["file_name"]}),
        ),
    )
    kb_source_id = cur.fetchone()[0]

    # 3) document
    cur.execute(
        """
        INSERT INTO documents (user_id, kb_source_id, title, file_name, file_type, content_hash, meta)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
        """,
        (
            system_user_id,
            kb_source_id,
            manual_data["title"],
            manual_data["file_name"],
            manual_data["file_type"],
            manual_data["content_hash"],
            json.dumps({}),
        ),
    )
    document_id = cur.fetchone()[0]

    return device_model_id, kb_source_id, document_id