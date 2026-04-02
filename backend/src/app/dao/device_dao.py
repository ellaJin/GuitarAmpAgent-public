# app/dao/device_dao.py
import json


def create_device_model(conn, model_data: dict):
    """
    Insert a device model and return UUID.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO device_models (brand, model, variant, source, is_public, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                model_data["brand"],
                model_data["model"],
                model_data.get("variant"),
                "user",
                False,
                model_data["user_id"],
            ),
        )
        return cur.fetchone()[0]


def bind_user_device(conn, bind_data: dict):
    """
    Bind user to device.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_devices (user_id, device_model_id, nickname, is_active)
            VALUES (%s, %s, %s, %s)
            """,
            (
                bind_data["user_id"],
                bind_data["device_model_id"],
                bind_data["nickname"],
                True,
            ),
        )


def activate_full_setup(conn, user_id: str, device_data: dict, file_data: dict):
    """
    Transactional workflow for regular users:
      1) Device model get-or-create
      2) Private kb_source get-or-create (per user + device + source_type)
      3) Document creation
      4) Set active user device

    Returns:
        (model_id, kb_source_id, document_id, user_device_id)
    """
    with conn.cursor() as cur:
        brand = (device_data.get("brand") or "").strip() or None
        model = (device_data.get("model") or "").strip()
        variant = (device_data.get("variant") or "").strip() or None

        if not model:
            raise ValueError("device_data.model is required")

        # ---- 1) device_models: get-or-create ----
        cur.execute(
            """
            INSERT INTO device_models (brand, model, variant, source, created_by)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (brand, model, variant)
            DO UPDATE SET brand = EXCLUDED.brand
            RETURNING id
            """,
            (brand, model, variant, "user", user_id),
        )
        model_id = cur.fetchone()[0]

        # ---- 2) kb_sources: get-or-create (private, per user + device + source_type) ----
        source_type = file_data.get("source_type") or "mixed"

        cur.execute(
            """
            SELECT id
            FROM kb_sources
            WHERE user_id = %s
              AND device_model_id = %s
              AND source_type = %s
              AND is_public = false
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, model_id, source_type),
        )
        row = cur.fetchone()

        if row:
            kb_source_id = row[0]
        else:
            cur.execute(
                """
                INSERT INTO kb_sources (
                    user_id,
                    device_model_id,
                    name,
                    source_type,
                    is_active,
                    is_public
                )
                VALUES (%s, %s, %s, %s, true, false)
                RETURNING id
                """,
                (
                    user_id,
                    model_id,
                    f"{brand or ''} {model} Manual".strip(),
                    source_type,
                ),
            )
            kb_source_id = cur.fetchone()[0]

        # ---- 3) documents ----
        cur.execute(
            """
            INSERT INTO documents (
                user_id,
                kb_source_id,
                title,
                file_name,
                file_type,
                content_hash
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user_id,
                kb_source_id,
                file_data["title"],
                file_data["file_name"],
                file_data["file_type"],
                file_data["content_hash"],
            ),
        )
        document_id = cur.fetchone()[0]

        # ---- 4) deactivate old active device ----
        cur.execute(
            """
            UPDATE user_devices
            SET is_active = false
            WHERE user_id = %s AND is_active = true
            """,
            (user_id,),
        )

        # ---- 5) insert new active device ----
        cur.execute(
            """
            INSERT INTO user_devices (user_id, device_model_id, kb_source_id, is_active)
            VALUES (%s, %s, %s, true)
            RETURNING id
            """,
            (user_id, model_id, kb_source_id),
        )
        user_device_id = cur.fetchone()[0]

        return model_id, kb_source_id, document_id, user_device_id


def admin_activate_full_setup(
    conn,
    system_user_id: str,
    device_info: dict,
    manual_data: dict,
    image_url: str | None,
    image_mime: str | None,
):
    """
    Admin-only path: create/upsert system-owned device + kb_source + document.

    Key differences from activate_full_setup (user path):
      - is_public = true (shared across all users)
      - Create a new kb_source per upload (multiple sources per device).
      - source_type is passed from manual_data, not hardcoded
      - image_url/image_mime are stored in device_models.meta

    Returns:
        (device_model_id, kb_source_id, document_id)
    """
    brand = (device_info.get("brand") or "").strip()
    model = (device_info.get("model") or "").strip()
    variant = (device_info.get("variant") or "").strip() or None
    source_type = (manual_data.get("source_type") or "mixed").strip()

    cur = conn.cursor()

    # ---- 1) device_models: get-or-create, update image if provided ----
    cur.execute(
        """
        SELECT id, meta FROM device_models
        WHERE brand = %s AND model = %s AND (variant IS NOT DISTINCT FROM %s)
        LIMIT 1
        """,
        (brand, model, variant),
    )
    row = cur.fetchone()

    supports_midi           = bool(device_info.get("supports_midi", False))
    supports_snapshots      = bool(device_info.get("supports_snapshots", False))
    supports_command_center = bool(device_info.get("supports_command_center", False))

    if row:
        device_model_id = row[0]
        meta = row[1] or {}
        if image_url:
            meta = dict(meta)
            meta["image_url"] = image_url
            if image_mime:
                meta["image_mime"] = image_mime
        # Always refresh capability flags on every admin upload
        cur.execute(
            """
            UPDATE device_models
            SET meta                   = %s,
                supports_midi          = %s,
                supports_snapshots     = %s,
                supports_command_center = %s
            WHERE id = %s
            """,
            (
                json.dumps(meta),
                supports_midi,
                supports_snapshots,
                supports_command_center,
                device_model_id,
            ),
        )
    else:
        meta = {}
        if image_url:
            meta["image_url"] = image_url
            if image_mime:
                meta["image_mime"] = image_mime

        cur.execute(
            """
            INSERT INTO device_models (
                brand, model, variant, source, created_by, is_public, meta,
                supports_midi, supports_snapshots, supports_command_center
            )
            VALUES (%s, %s, %s, 'system', %s, true, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                brand, model, variant, system_user_id, json.dumps(meta),
                supports_midi, supports_snapshots, supports_command_center,
            ),
        )
        device_model_id = cur.fetchone()[0]

    # A new kb_source is only created on first upload for this device.
    # ---- 2) kb_sources: reuse existing system kb_source for this device ----
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
            system_user_id,
            device_model_id,
            manual_data["title"],
            source_type,
            json.dumps({
                "content_hash": manual_data.get("content_hash"),
                "file_name": manual_data.get("file_name"),
            }),
        ),
    )
    kb_source_id = cur.fetchone()[0]

    # ---- 3) documents: always insert a new document per PDF ----
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
            system_user_id,
            kb_source_id,
            manual_data["title"],
            manual_data["file_name"],
            manual_data["file_type"],
            manual_data["content_hash"],
            json.dumps({"source_type": source_type}),
        ),
    )
    document_id = cur.fetchone()[0]

    # ---- 4) bind system user to device ----
    cur.execute(
        """
        INSERT INTO user_devices (user_id, device_model_id, kb_source_id, is_active)
        VALUES (%s, %s, %s, true)
        ON CONFLICT DO NOTHING
        """,
        (system_user_id, device_model_id, kb_source_id),
    )

    return device_model_id, kb_source_id, document_id


def get_available_devices(conn) -> list[dict]:
    """
    Return all admin-uploaded (system, public) devices that have at least one
    active public kb_source.  Used by the onboarding Device picker.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                dm.id          AS device_model_id,
                dm.brand,
                dm.model,
                dm.variant,
                dm.meta->>'image_url' AS image_url
            FROM device_models dm
            WHERE dm.source = 'system'
              AND dm.is_public = true
              AND EXISTS (
                  SELECT 1 FROM kb_sources ks
                  WHERE ks.device_model_id = dm.id
                    AND ks.is_active = true
                    AND ks.is_public  = true
              )
            ORDER BY dm.brand, dm.model
            """
        )
        rows = cur.fetchall()
    return [
        {
            "device_model_id": str(r[0]),
            "brand":           r[1],
            "model":           r[2],
            "variant":         r[3],
            "image_url":       r[4],
        }
        for r in rows
    ]


def bind_user_to_system_device(conn, user_id: str, device_model_id: str) -> dict:
    """
    Bind a regular user to an existing admin-created (system/public) device.

    Steps:
      1. Verify the device exists and is public.
      2. Pick the most recent active public kb_source for that device.
      3. Deactivate any currently active user_devices row for this user.
      4. Insert a new active user_devices row.

    Returns dict with user_device_id, device_model_id, kb_source_id.
    Raises ValueError on validation failures.
    """
    with conn.cursor() as cur:
        # 1) Verify device
        cur.execute(
            """
            SELECT id FROM device_models
            WHERE id = %s AND source = 'system' AND is_public = true
            """,
            (device_model_id,),
        )
        if not cur.fetchone():
            raise ValueError(f"Device {device_model_id} not found or not available.")

        # 2) Pick latest active public kb_source
        cur.execute(
            """
            SELECT id FROM kb_sources
            WHERE device_model_id = %s
              AND is_active = true
              AND is_public  = true
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (device_model_id,),
        )
        ks_row = cur.fetchone()
        if not ks_row:
            raise ValueError(f"No active knowledge base found for device {device_model_id}.")
        kb_source_id = ks_row[0]

        # 3) Deactivate any current active device for this user
        cur.execute(
            "UPDATE user_devices SET is_active = false WHERE user_id = %s AND is_active = true",
            (user_id,),
        )

        # 4) Insert new active binding
        cur.execute(
            """
            INSERT INTO user_devices (user_id, device_model_id, kb_source_id, is_active)
            VALUES (%s, %s, %s, true)
            RETURNING id
            """,
            (user_id, device_model_id, kb_source_id),
        )
        user_device_id = cur.fetchone()[0]

    return {
        "user_device_id":  str(user_device_id),
        "device_model_id": str(device_model_id),
        "kb_source_id":    str(kb_source_id),
    }


def get_user_devices(conn, user_id: str) -> list[dict]:
    """Return all devices bound to a user, joined with device_models for display info."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                ud.id             AS user_device_id,
                ud.is_active,
                dm.id             AS device_model_id,
                dm.brand,
                dm.model,
                dm.variant,
                dm.meta->>'image_url' AS image_url
            FROM user_devices ud
            JOIN device_models dm ON ud.device_model_id = dm.id
            WHERE ud.user_id = %s
            ORDER BY ud.is_active DESC, dm.brand, dm.model
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    return [
        {
            "user_device_id":  str(r[0]),
            "is_active":       bool(r[1]),
            "device_model_id": str(r[2]),
            "brand":           r[3],
            "model":           r[4],
            "variant":         r[5],
            "image_url":       r[6],
        }
        for r in rows
    ]


def bind_user_device_inactive(conn, user_id: str, device_model_id: str) -> dict:
    """
    Bind a user to a system device with is_active = false.
    Does not touch the current active device.
    Raises ValueError if device not found, no kb_source, or already bound.
    """
    with conn.cursor() as cur:
        # 1) Verify device exists and is public
        cur.execute(
            """
            SELECT id FROM device_models
            WHERE id = %s AND source = 'system' AND is_public = true
            """,
            (device_model_id,),
        )
        if not cur.fetchone():
            raise ValueError(f"Device {device_model_id} not found or not available.")

        # 2) Pick latest active public kb_source
        cur.execute(
            """
            SELECT id FROM kb_sources
            WHERE device_model_id = %s AND is_active = true AND is_public = true
            ORDER BY created_at DESC LIMIT 1
            """,
            (device_model_id,),
        )
        ks_row = cur.fetchone()
        if not ks_row:
            raise ValueError(f"No active knowledge base found for device {device_model_id}.")
        kb_source_id = ks_row[0]

        # 3) Guard against duplicate binding
        cur.execute(
            "SELECT id FROM user_devices WHERE user_id = %s AND device_model_id = %s",
            (user_id, device_model_id),
        )
        if cur.fetchone():
            raise ValueError("You already have this device in your list.")

        # 4) Insert inactive binding
        cur.execute(
            """
            INSERT INTO user_devices (user_id, device_model_id, kb_source_id, is_active)
            VALUES (%s, %s, %s, false)
            RETURNING id
            """,
            (user_id, device_model_id, kb_source_id),
        )
        user_device_id = cur.fetchone()[0]

    return {
        "user_device_id":  str(user_device_id),
        "device_model_id": str(device_model_id),
        "kb_source_id":    str(kb_source_id),
    }


def activate_user_device(conn, user_id: str, user_device_id: str) -> None:
    """
    Swap active device for a user:
    deactivates all user_devices rows, then activates the requested one.
    Raises ValueError if user_device_id doesn't belong to this user.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM user_devices WHERE id = %s AND user_id = %s",
            (user_device_id, user_id),
        )
        if not cur.fetchone():
            raise ValueError("Device not found.")

        cur.execute(
            "UPDATE user_devices SET is_active = false WHERE user_id = %s",
            (user_id,),
        )
        cur.execute(
            "UPDATE user_devices SET is_active = true WHERE id = %s AND user_id = %s",
            (user_device_id, user_id),
        )


def get_active_device_model_id(conn, user_id: str) -> str | None:
    """Return the device_model_id of the user's currently active device, or None."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT device_model_id FROM user_devices
            WHERE user_id = %s AND is_active = true
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
    return str(row[0]) if row else None


def get_device_supports_midi(conn, device_model_id: str) -> bool:
    """Return True if the device_model has supports_midi = true."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT supports_midi FROM device_models WHERE id = %s",
            (device_model_id,),
        )
        row = cur.fetchone()
    return bool(row[0]) if row else False


def get_document_device_supports_midi(conn, document_id: str) -> bool:
    """
    Resolve the device_model for the given document and return supports_midi.
    Joins: documents -> kb_sources -> device_models.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT dm.supports_midi
            FROM documents   d
            JOIN kb_sources  ks ON d.kb_source_id   = ks.id
            JOIN device_models dm ON ks.device_model_id = dm.id
            WHERE d.id = %s
            LIMIT 1
            """,
            (document_id,),
        )
        row = cur.fetchone()
    return bool(row[0]) if row else False


def get_latest_document_id(conn, user_id, file_hash):
    """
    Get latest document id by hash.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM documents
            WHERE user_id = %s AND content_hash = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, file_hash),
        )
        return cur.fetchone()[0]


def insert_document_chunks(conn, user_id, document_id, chunks_data):
    """
    Batch insert chunk embeddings.
    """
    sql = """
        INSERT INTO chunks (user_id, document_id, chunk_index, content, embedding, meta)
        VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb)
        ON CONFLICT (document_id, chunk_index) DO UPDATE
        SET content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            meta = EXCLUDED.meta
    """
    with conn.cursor() as cur:
        cur.executemany(sql, chunks_data)