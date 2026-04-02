# app/dao/admin_device_dao.py
import json
from typing import List, Dict, Any, Tuple

SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"


def list_system_devices(conn) -> List[Dict[str, Any]]:
    """
    Return all system devices (device_models) with their bound kb_sources and the latest
    ingestion job status per kb_source.

    Notes:
    - Device is the primary entity (device_models row).
    - Each device can have 0..N kb_sources (documents) bound.
    - For each kb_source, we attach the most recent kb_ingestion_jobs row (if any),
      and also join the corresponding documents row (via latest job.document_id) to expose file_name.
    - Only system-user kb_sources are included (SYSTEM_USER_ID), and only active sources are listed.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            -- -------------------------
            -- device_models (device-level fields)
            -- -------------------------
            m.id            AS device_model_id,
            m.brand,
            m.model,
            m.variant,
            m.source        AS source,
            m.is_public     AS is_public,
            m.created_at    AS created_at,
            m.supports_midi,
            m.supports_snapshots,
            m.supports_command_center,

            -- -------------------------
            -- kb_sources (document binding)
            -- -------------------------
            s.id            AS kb_source_id,
            s.source_type,
            s.name          AS title,
            s.is_active     AS kb_is_active,
            s.is_public     AS kb_is_public,
            s.created_at    AS kb_created_at,

            -- -------------------------
            -- latest job for this kb_source (nullable)
            -- -------------------------
            j.id                 AS job_id,
            j.status             AS job_status,
            j.stage              AS job_stage,
            j.progress           AS job_progress,
            j.error              AS job_error,
            j.document_id        AS document_id,
            j.enrichment_status       AS enrichment_status,
            j.enrichment_total        AS enrichment_total,
            j.enrichment_done         AS enrichment_done,
            j.midi_enrichment_status  AS midi_enrichment_status,
            j.midi_enrichment_total   AS midi_enrichment_total,

            -- -------------------------
            -- documents (nullable; joined via latest job.document_id)
            -- -------------------------
            d.file_name     AS file_name

        FROM device_models m
        LEFT JOIN kb_sources s
               ON s.device_model_id = m.id
              AND s.user_id = %s
              AND s.is_active = true

        LEFT JOIN LATERAL (
            SELECT
                id,
                status,
                stage,
                progress,
                error,
                document_id,
                enrichment_status,
                enrichment_total,
                enrichment_done,
                midi_enrichment_status,
                midi_enrichment_total
            FROM kb_ingestion_jobs
            WHERE kb_source_id = s.id
            ORDER BY created_at DESC
            LIMIT 1
        ) j ON true

        LEFT JOIN documents d
               ON d.id = j.document_id

        WHERE m.source = 'system'
        ORDER BY m.brand, m.model, kb_created_at DESC
        """,
        (SYSTEM_USER_ID,),
    )
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    # Group sources under their device
    devices: dict[str, Dict[str, Any]] = {}

    for row in rows:
        r = dict(zip(cols, row))
        did = r["device_model_id"]

        if did not in devices:
            devices[did] = {
                "device_model_id": did,
                "brand": r["brand"] or "",
                "model": r["model"] or "",
                "variant": r["variant"],  # keep null if null
                # device_models fields
                "source": r["source"] or "",
                "is_public": bool(r["is_public"]) if r["is_public"] is not None else False,
                "created_at": str(r["created_at"]) if r["created_at"] is not None else "",
                # capability flags
                "supports_midi": bool(r["supports_midi"]) if r["supports_midi"] is not None else False,
                "supports_snapshots": bool(r["supports_snapshots"]) if r["supports_snapshots"] is not None else False,
                "supports_command_center": bool(r["supports_command_center"]) if r["supports_command_center"] is not None else False,
                # bound kb_sources
                "sources": [],
            }

        # Append kb_source if present (LEFT JOIN can produce null kb_source rows)
        if r.get("kb_source_id"):
            devices[did]["sources"].append(
                {
                    "kb_source_id": r["kb_source_id"],
                    "source_type": (r.get("source_type") or "mixed"),
                    "title": r.get("title") or "",
                    "file_name": r.get("file_name") or "",

                    # Optional: useful for admin "unlink" UI and diagnostics
                    "is_active": bool(r["kb_is_active"]) if r.get("kb_is_active") is not None else False,
                    "is_public": bool(r["kb_is_public"]) if r.get("kb_is_public") is not None else False,
                    "created_at": str(r["kb_created_at"]) if r.get("kb_created_at") is not None else "",

                    # Latest job info (may be null if not ingested yet)
                    "job_id": r.get("job_id") or "",
                    "job_status": r.get("job_status") or "PENDING",
                    "job_stage": r.get("job_stage") or "",
                    "job_progress": float(r["job_progress"]) if r.get("job_progress") is not None else 0.0,
                    "job_error": r.get("job_error") or "",

                    "enrichment_status": r.get("enrichment_status") or "PENDING",
                    "enrichment_total": int(r["enrichment_total"]) if r.get("enrichment_total") is not None else 0,
                    "enrichment_done": int(r["enrichment_done"]) if r.get("enrichment_done") is not None else 0,

                    # MIDI enrichment — independent of effect enrichment
                    "midi_enrichment_status": r.get("midi_enrichment_status") or "PENDING",
                    "midi_enrichment_total": int(r["midi_enrichment_total"]) if r.get("midi_enrichment_total") is not None else 0,
                }
            )

    return list(devices.values())


def add_document_to_device(
    conn,
    device_model_id: str,
    manual_data: dict,
) -> Tuple[str, str]:
    """
    Add a new document (kb_source + document) to an already-existing system device.

    Does NOT touch device_models (caller is responsible for verifying the device exists
    and belongs to the system user before calling this function).

    manual_data expected keys:
        title        (str) — original filename, used as kb_sources.name
        file_name    (str) — relative path stored for the worker (e.g. "manuals/<hash>.pdf")
        file_type    (str) — MIME type
        content_hash (str) — MD5 hex digest
        source_type  (str) — "mixed" | "effects_settings" | "user_manual"

    Returns:
        (kb_source_id, document_id)
    """
    cur = conn.cursor()
    source_type = (manual_data.get("source_type") or "mixed").strip()

    # 1) Guard: verify device exists and is a system device
    cur.execute(
        "SELECT id FROM device_models WHERE id = %s AND source = 'system' LIMIT 1",
        (device_model_id,),
    )
    if not cur.fetchone():
        raise ValueError(f"System device not found: {device_model_id}")

    # 2) Insert new kb_source (always a fresh row per upload, same as admin_activate_full_setup)
    cur.execute(
        """
        INSERT INTO kb_sources (
            user_id,
            device_model_id,
            name,
            source_type,
            is_active,
            is_public,
            meta
        )
        VALUES (%s, %s, %s, %s, true, true, %s)
        RETURNING id
        """,
        (
            SYSTEM_USER_ID,
            device_model_id,
            manual_data["title"],
            source_type,
            json.dumps({
                "content_hash": manual_data.get("content_hash"),
                "file_name":    manual_data.get("file_name"),
            }),
        ),
    )
    kb_source_id = str(cur.fetchone()[0])

    # 3) Insert document linked to the new kb_source
    cur.execute(
        """
        INSERT INTO documents (
            user_id,
            kb_source_id,
            title,
            file_name,
            file_type,
            content_hash,
            meta
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            SYSTEM_USER_ID,
            kb_source_id,
            manual_data["title"],
            manual_data["file_name"],
            manual_data["file_type"],
            manual_data["content_hash"],
            json.dumps({"source_type": source_type}),
        ),
    )
    document_id = str(cur.fetchone()[0])

    # 4) Bind system user to device (DO NOTHING if already bound)
    cur.execute(
        """
        INSERT INTO user_devices (user_id, device_model_id, kb_source_id, is_active)
        VALUES (%s, %s, %s, true)
        ON CONFLICT DO NOTHING
        """,
        (SYSTEM_USER_ID, device_model_id, kb_source_id),
    )

    return kb_source_id, document_id


def unlink_source(conn, device_model_id: str, kb_source_id: str) -> bool:
    """
    Cascade-delete all data associated with a kb_source from a system device.

    Deletion order (respects FK constraints):
        1. effect_chunk_refs  — junction table referencing chunks
        2. chunks             — embeddings for the document
        3. raw_effect_entries — extracted effects for this source
        4. raw_midi_entries   — extracted MIDI for this source
        5. kb_ingestion_jobs  — job records for this source
        6. documents          — the document row itself
        7. user_devices       — system user binding for this source
        8. kb_sources         — the source row itself

    Raises:
        ValueError if kb_source_id does not belong to device_model_id.

    Returns:
        True on success.
    """
    cur = conn.cursor()

    # 0) Guard: verify the kb_source belongs to this device
    cur.execute(
        """
        SELECT id FROM kb_sources
        WHERE id = %s AND device_model_id = %s
        LIMIT 1
        """,
        (kb_source_id, device_model_id),
    )
    if not cur.fetchone():
        raise ValueError(
            f"kb_source {kb_source_id} does not belong to device {device_model_id}"
        )

    # Resolve document_id (may be null if ingestion never started)
    cur.execute(
        "SELECT id FROM documents WHERE kb_source_id = %s",
        (kb_source_id,),
    )
    doc_rows = cur.fetchall()
    document_ids = [str(r[0]) for r in doc_rows]

    # 1) effect_chunk_refs — must go before chunks
    if document_ids:
        cur.execute(
            """
            DELETE FROM effect_chunk_refs
            WHERE chunk_id IN (
                SELECT id FROM chunks WHERE document_id = ANY(%s)
            )
            """,
            (document_ids,),
        )

    # 2) chunks
    if document_ids:
        cur.execute(
            "DELETE FROM chunks WHERE document_id = ANY(%s)",
            (document_ids,),
        )

    # 3) raw_effect_entries
    cur.execute(
        "DELETE FROM raw_effect_entries WHERE kb_source_id = %s",
        (kb_source_id,),
    )

    # 4) raw_midi_entries
    cur.execute(
        "DELETE FROM raw_midi_entries WHERE kb_source_id = %s",
        (kb_source_id,),
    )

    # 5) kb_ingestion_jobs
    cur.execute(
        "DELETE FROM kb_ingestion_jobs WHERE kb_source_id = %s",
        (kb_source_id,),
    )

    # 6) documents
    cur.execute(
        "DELETE FROM documents WHERE kb_source_id = %s",
        (kb_source_id,),
    )

    # 7) user_devices (system user binding only)
    cur.execute(
        "DELETE FROM user_devices WHERE kb_source_id = %s AND user_id = %s",
        (kb_source_id, SYSTEM_USER_ID),
    )

    # 8) kb_sources — last, after all dependents are gone
    cur.execute(
        "DELETE FROM kb_sources WHERE id = %s",
        (kb_source_id,),
    )

    return True