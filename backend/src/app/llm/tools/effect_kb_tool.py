# app/llm/tools/effect_kb_tool.py
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.db import get_db_con
from app.dao.effect_kb_dao import query_raw_effect_entries


def _tokenize(query: str) -> List[str]:
    """
    Lightweight tokenizer:
    - lower-case
    - split by non-alphanum
    - keep len>=3
    - dedupe preserve order
    """
    raw = re.split(r"[^a-zA-Z0-9]+", (query or "").lower())
    out: List[str] = []
    seen = set()
    for t in raw:
        if len(t) < 3:
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def search_effect_kb_logic(
    *,
    query: str,
    user_id: str,  # reserved (audit/ACL later)
    device_model_id: str,
    kb_source_id: str,
    top_k: int = 8,
) -> str:
    """
    Search structured effects KB (raw_effect_entries).
    Returns JSON string: {"items":[...], "meta": {...}}
    """
    tokens = _tokenize(query)

    if not device_model_id or not kb_source_id:
        return json.dumps(
            {
                "items": [],
                "meta": {
                    "error": "missing_device_context",
                    "device_model_id": device_model_id,
                    "kb_source_id": kb_source_id,
                },
            },
            ensure_ascii=False,
        )

    if not tokens:
        return json.dumps(
            {
                "items": [],
                "meta": {
                    "reason": "no_valid_tokens",
                    "device_model_id": device_model_id,
                    "kb_source_id": kb_source_id,
                },
            },
            ensure_ascii=False,
        )

    try:
        with get_db_con() as conn:
            rows = query_raw_effect_entries(
                conn,
                device_model_id=device_model_id,
                kb_source_id=kb_source_id,
                tokens=tokens,
                limit=top_k,
            )
    except Exception as e:
        return json.dumps(
            {
                "items": [],
                "meta": {
                    "error": f"{type(e).__name__}: {str(e)}",
                    "device_model_id": device_model_id,
                    "kb_source_id": kb_source_id,
                    "tokens": tokens,
                },
            },
            ensure_ascii=False,
        )

    items: List[Dict[str, Any]] = []
    for (
        _id,
        raw_name,
        raw_name_norm,
        raw_type,
        raw_category,
        raw_description,
        source_section,
        source_page,
        confidence,
    ) in rows:
        items.append(
            {
                "id": _id,
                "raw_name": raw_name,
                "raw_name_norm": raw_name_norm or None,
                "raw_type": raw_type or None,
                "raw_category": raw_category or None,
                "raw_description": raw_description or None,
                "source_section": source_section or None,
                "source_page": source_page,
                "confidence": float(confidence) if confidence is not None else None,
            }
        )

    return json.dumps(
        {
            "items": items,
            "meta": {
                "hits": len(items),
                "tokens": tokens,
                "device_model_id": device_model_id,
                "kb_source_id": kb_source_id,
            },
        },
        ensure_ascii=False,
    )
