# app/dao/job_dao.py
import uuid
from typing import Optional, Dict, Any


def create_job(conn, user_id: str, kb_source_id: str, document_id: str) -> str:
    """
    Create an ingestion job record and return the new job_id.

    Notes:
    - The caller is responsible for conn.commit().
    - We keep enrichment_* fields initialized so the UI can render progress consistently.
    """
    job_id = str(uuid.uuid4())
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO kb_ingestion_jobs (
            id, user_id, kb_source_id, document_id,
            status, stage, progress,
            enrichment_status, enrichment_total, enrichment_done,
            midi_enrichment_status, midi_enrichment_total
        )
        VALUES (%s, %s, %s, %s, 'PENDING', 'PENDING', 0, 'PENDING', 0, 0, 'PENDING', 0)
        """,
        (job_id, user_id, kb_source_id, document_id),
    )
    return job_id


def update_job(
    conn,
    job_id: str,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    progress: Optional[int] = None,
    error: Optional[str] = None,
    enrichment_status: Optional[str] = None,
):
    """
    Update a job record with partial fields.
    The caller is responsible for conn.commit().
    """
    sets = []
    vals = []

    if status is not None:
        sets.append("status=%s")
        vals.append(status)

    if stage is not None:
        sets.append("stage=%s")
        vals.append(stage)

    if progress is not None:
        sets.append("progress=%s")
        vals.append(int(progress))

    if error is not None:
        sets.append("error=%s")
        vals.append(error)

    if enrichment_status is not None:
        sets.append("enrichment_status=%s")
        vals.append(enrichment_status)

    if not sets:
        return

    sets.append("updated_at=now()")
    sql = f"UPDATE kb_ingestion_jobs SET {', '.join(sets)} WHERE id=%s"
    vals.append(job_id)

    cur = conn.cursor()
    cur.execute(sql, tuple(vals))


def get_job(conn, job_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a job record by id.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id, user_id, kb_source_id, document_id,
            enrichment_status, enrichment_total, enrichment_done,
            midi_enrichment_status, midi_enrichment_total,
            status, stage, progress, error,
            created_at, updated_at
        FROM kb_ingestion_jobs
        WHERE id=%s
        """,
        (job_id,),
    )
    row = cur.fetchone()
    if not row:
        return None

    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def get_job_context(conn, job_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the minimal ingestion context needed by the background worker.

    The worker should only accept `job_id` and load everything else from DB.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            j.user_id,
            j.document_id,
            j.kb_source_id,

            -- File info comes from documents table, not kb_sources
            d.file_name,
            d.file_type,

            -- source_type determines chunking profile and pipeline routing
            s.source_type,

            -- Device identity
            m.brand,
            m.model,
            m.variant

        FROM kb_ingestion_jobs j
        JOIN kb_sources s ON s.id = j.kb_source_id
        LEFT JOIN device_models m ON m.id = s.device_model_id
        LEFT JOIN documents d ON d.id = j.document_id
        WHERE j.id = %s
        """,
        (job_id,),
    )
    row = cur.fetchone()
    if not row:
        return None

    cols = [d[0] for d in cur.description]
    ctx = dict(zip(cols, row))

    return {
        "user_id":      ctx.get("user_id"),
        "document_id":  ctx.get("document_id"),
        "kb_source_id": ctx.get("kb_source_id"),
        "file_name":    ctx.get("file_name"),    # from documents
        "file_type":    ctx.get("file_type"),    # from documents
        "source_type":  ctx.get("source_type"),  # from kb_sources, drives profile + pipeline
        "brand":        ctx.get("brand"),
        "model":        ctx.get("model"),
        "variant":      ctx.get("variant"),
    }


def set_enrichment_progress(conn, job_id: str, enrichment_status: str, total: int, done: int):
    """
    Set enrichment progress fields for a job.
    The caller is responsible for conn.commit().
    """
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE kb_ingestion_jobs
        SET enrichment_status=%s,
            enrichment_total=%s,
            enrichment_done=%s,
            updated_at=now()
        WHERE id=%s
        """,
        (enrichment_status, int(total), int(done), job_id),
    )


def set_midi_enrichment(conn, job_id: str, status: str, total: int = 0):
    """
    Set MIDI enrichment tracking fields. Completely independent of effect enrichment.
    The caller is responsible for conn.commit().
    """
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE kb_ingestion_jobs
        SET midi_enrichment_status=%s,
            midi_enrichment_total=%s,
            updated_at=now()
        WHERE id=%s
        """,
        (status, int(total), job_id),
    )


def inc_enrichment_done(conn, job_id: str, delta: int = 1):
    """
    Increment enrichment_done by delta.
    The caller is responsible for conn.commit().
    """
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE kb_ingestion_jobs
        SET enrichment_done = enrichment_done + %s,
            updated_at=now()
        WHERE id=%s
        """,
        (int(delta), job_id),
    )