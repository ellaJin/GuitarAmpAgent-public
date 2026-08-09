# app/service/quota_service.py
from fastapi import HTTPException
from app.dao import user_dao
from app.db import get_db_con


def enforce_and_consume_query_quota(user_id: str) -> None:
    """
    Call before running an LLM query. Atomically lazy-resets the user's
    daily quota if the stored date has rolled over, then checks both caps
    and reserves one query slot. Raises 429 if already at/over either cap.
    """
    with get_db_con() as conn:
        new_count = user_dao.check_and_increment_query(conn, user_id)
        if new_count is not None:
            return
        status = user_dao.get_quota_status(conn, user_id)

    if not status:
        # User row is gone -- let the normal auth/404 path handle it upstream.
        return

    query_limit, token_limit, query_count, token_count, resets_at = status
    which = (
        f"query limit ({query_count}/{query_limit})"
        if query_count >= query_limit
        else f"token limit ({token_count}/{token_limit})"
    )

    raise HTTPException(
        status_code=429,
        detail=f"Daily {which} reached. Resets at {resets_at.isoformat()}.",
    )


def record_token_usage(user_id: str, tokens_used: int) -> None:
    """Call after a query completes, with the tokens the LLM call(s)
    reported. No-op if nothing was reported (inventory route, or an
    early-exit path that never reached the model)."""
    if tokens_used <= 0:
        return
    with get_db_con() as conn:
        user_dao.add_token_usage(conn, user_id, tokens_used)


def refund_query(user_id: str) -> None:
    """Call when a gated query failed after its slot was already consumed,
    so a backend error doesn't silently burn part of the user's daily cap.
    Floored at 0 in the DAO so a concurrent lazy reset can't go negative."""
    with get_db_con() as conn:
        user_dao.decrement_query_count(conn, user_id)
