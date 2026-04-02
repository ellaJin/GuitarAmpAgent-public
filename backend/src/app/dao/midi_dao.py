# app/dao/midi_dao.py
import re
from typing import Dict, List, Optional, Tuple, Any

import json


# -------------------------
# Normalize
# -------------------------
def normalize_target_name(name: str) -> str:
    """
    Normalize MIDI target name for stable upsert key.
    Example: "Wah Pedal" / "wah-pedal" -> "wahpedal"
    """
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


# -------------------------
# Candidate chunks
# -------------------------
def get_candidate_midi_chunks(conn, document_id: str) -> List[dict]:
    """
    Returns chunks likely to contain MIDI mapping tables or descriptions.
    Filters on MIDI-related keywords so we only pass relevant pages to the LLM.
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
            c.meta->>'section'     AS section
        FROM chunks c
        JOIN documents  d  ON c.document_id   = d.id
        JOIN kb_sources ks ON d.kb_source_id  = ks.id
        WHERE c.document_id = %s
          AND (
                c.content ILIKE '%%midi cc%%'
             OR c.content ILIKE '%%midi pc%%'
             OR c.content ILIKE '%%control change%%'
             OR c.content ILIKE '%%program change%%'
             OR c.content ILIKE '%%bank select%%'
             OR c.content ILIKE '%%command center%%'
             OR c.content ILIKE '%%cc#%%'
             OR c.content ILIKE '%%sysex%%'
             OR c.content ILIKE '%%0-127%%'
             OR c.content ILIKE '%%emulates fs%%'
             OR c.content ILIKE '%%emulates exp%%'
             OR c.content ILIKE '%%snapshot select%%'
             OR c.content ILIKE '%%reserved for global%%'
          )
        """,
        (document_id,),
    )
    rows = cur.fetchall()

    out = []
    for r in rows:
        out.append(
            {
                "id":              r[0],
                "content":         r[1],
                "document_id":     r[2],
                "kb_source_id":    r[3],
                "device_model_id": r[4],
                "page":            r[5],
                "section":         r[6],
            }
        )
    return out


# -------------------------
# Bulk upsert raw_midi_entries
# -------------------------
def upsert_raw_midi_bulk(
    conn,
    kb_source_id: str,
    device_model_id: str,
    entries: List[dict],
    source_page: Optional[int] = None,
    source_section: Optional[str] = None,
) -> Dict[Tuple, str]:
    """
    Upsert raw_midi_entries.

    Unique key (mirrors uniq_raw_midi_entries index):
      (device_model_id, message_type,
       coalesce(midi_channel, -1), coalesce(cc_number, -1),
       coalesce(pc_number, -1),   coalesce(bank_msb, -1),
       coalesce(bank_lsb, -1),    target_type, target_name_norm)

    entries item dict expected keys:
      message_type    (required): 'CC' | 'PC' | 'BANK'
      target_type     (required): e.g. 'EFFECT_BLOCK', 'FOOTSWITCH', 'SNAPSHOT'
      target_name     (required): human-readable name
      midi_channel    (optional int 1-16)
      cc_number       (optional int 0-127)
      pc_number       (optional int 0-127)
      bank_msb        (optional int 0-127)
      bank_lsb        (optional int 0-127)
      value_min       (optional int 0-127)
      value_max       (optional int 0-127)
      target_path     (optional str)
      raw_description (optional str)
      confidence      (optional float, default 0.7)
      meta            (optional dict)

    Returns:
      {(message_type, midi_channel, cc_number, pc_number,
        bank_msb, bank_lsb, target_type, target_name_norm): id}
    """
    if not entries:
        return {}

    # 1) In-memory dedup: keep highest confidence per unique MIDI address
    uniq: Dict[Tuple, dict] = {}

    for e in entries:
        msg_type = (e.get("message_type") or "").upper().strip()
        if msg_type not in ("CC", "PC", "BANK"):
            continue

        target_name = (e.get("target_name") or "").strip()
        if not target_name:
            continue

        target_type      = (e.get("target_type") or "UNKNOWN").strip()
        target_name_norm = normalize_target_name(target_name)

        midi_channel = _to_int_or_none(e.get("midi_channel"))
        cc_number    = _to_int_or_none(e.get("cc_number"))
        pc_number    = _to_int_or_none(e.get("pc_number"))
        bank_msb     = _to_int_or_none(e.get("bank_msb"))
        bank_lsb     = _to_int_or_none(e.get("bank_lsb"))

        key = (
            msg_type, midi_channel, cc_number, pc_number,
            bank_msb, bank_lsb, target_type, target_name_norm,
        )

        conf = float(e.get("confidence", 0.7) or 0.7)

        if key not in uniq:
            uniq[key] = {
                "message_type":    msg_type,
                "midi_channel":    midi_channel,
                "cc_number":       cc_number,
                "pc_number":       pc_number,
                "bank_msb":        bank_msb,
                "bank_lsb":        bank_lsb,
                "value_min":       _to_int_or_none(e.get("value_min")),
                "value_max":       _to_int_or_none(e.get("value_max")),
                "target_type":     target_type,
                "target_name":     target_name,
                "target_name_norm": target_name_norm,
                "target_path":     e.get("target_path"),
                "raw_description": e.get("raw_description"),
                "confidence":      conf,
                "meta":            e.get("meta") or {},
            }
        else:
            old = uniq[key]
            old["confidence"] = max(old["confidence"], conf)
            if not old.get("raw_description") and e.get("raw_description"):
                old["raw_description"] = e["raw_description"]
            if not old.get("target_path") and e.get("target_path"):
                old["target_path"] = e["target_path"]
            if e.get("meta"):
                old["meta"] = {**(old.get("meta") or {}), **e["meta"]}

    if not uniq:
        return {}

    sql = """
    INSERT INTO raw_midi_entries (
      kb_source_id,
      device_model_id,
      message_type,
      midi_channel,
      cc_number,
      pc_number,
      bank_msb,
      bank_lsb,
      value_min,
      value_max,
      target_type,
      target_name,
      target_name_norm,
      target_path,
      raw_description,
      source_section,
      source_page,
      confidence,
      meta
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (
      device_model_id,
      message_type,
      coalesce(midi_channel, -1),
      coalesce(cc_number,    -1),
      coalesce(pc_number,    -1),
      coalesce(bank_msb,     -1),
      coalesce(bank_lsb,     -1),
      target_type,
      target_name_norm
    )
    DO UPDATE SET
      confidence      = GREATEST(raw_midi_entries.confidence, EXCLUDED.confidence),
      target_name     = EXCLUDED.target_name,
      raw_description = COALESCE(EXCLUDED.raw_description, raw_midi_entries.raw_description),
      target_path     = COALESCE(EXCLUDED.target_path, raw_midi_entries.target_path),
      value_min       = COALESCE(EXCLUDED.value_min,   raw_midi_entries.value_min),
      value_max       = COALESCE(EXCLUDED.value_max,   raw_midi_entries.value_max),
      source_section  = COALESCE(raw_midi_entries.source_section, EXCLUDED.source_section),
      source_page     = COALESCE(raw_midi_entries.source_page,    EXCLUDED.source_page),
      meta            = raw_midi_entries.meta || EXCLUDED.meta
    RETURNING
      id, message_type, midi_channel, cc_number, pc_number,
      bank_msb, bank_lsb, target_type, target_name_norm
    """

    cur = conn.cursor()
    id_map: Dict[Tuple, str] = {}

    for v in uniq.values():
        row = (
            kb_source_id,
            device_model_id,
            v["message_type"],
            v["midi_channel"],
            v["cc_number"],
            v["pc_number"],
            v["bank_msb"],
            v["bank_lsb"],
            v["value_min"],
            v["value_max"],
            v["target_type"],
            v["target_name"],
            v["target_name_norm"],
            v.get("target_path"),
            v.get("raw_description"),
            source_section,
            source_page,
            v["confidence"],
            json.dumps(v.get("meta") or {}),
        )
        cur.execute(sql, row)
        result = cur.fetchone()
        if result:
            rid, msg_t, ch, cc, pc, msb, lsb, tt, tnn = result
            id_map[(msg_t, ch, cc, pc, msb, lsb, tt, tnn)] = str(rid)

    return id_map


# -------------------------
# Helpers
# -------------------------
def _to_int_or_none(val: Any) -> Optional[int]:
    """Convert a value to int or return None."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
