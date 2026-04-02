# app/service/chat_handlers/inventory_handler.py
from typing import Optional, List, Dict
from app.dao import user_device_dao
from app.schemas.chat import ChatQueryContext


def _format_device_name(d: Dict) -> str:
    name = f"{d.get('brand','')} {d.get('model','')}".strip()
    if d.get("variant"):
        name += f" ({d['variant']})"
    if d.get("nickname"):
        name += f' — "{d["nickname"]}"'
    if d.get("is_active"):
        name += " [active]"
    return name

def handle_inventory(conn, ctx: ChatQueryContext) -> str:
    """
    Inventory handler: DB only. No tools. No RAG.
    Returns a user-facing string.
    """
    devices = user_device_dao.list_user_devices(conn, ctx.user_id)
    active = user_device_dao.get_active_user_device(conn, ctx.user_id)

    n = len(devices)
    if n == 0:
        return "You don't have any linked devices yet. Please add a device first."

    active_name = "None"
    if active:
        active_name = _format_device_name(active).replace(" [active]", "")

    lines = [_format_device_name(d) for d in devices[:10]]
    more = ""
    if n > 10:
        more = f"\n...and {n - 10} more."

    return (
        f"You have {n} linked device(s).\n\n"
        f"Active device: {active_name}\n\n"
        f"Devices:\n\n"
        f"{lines}"
        f"{more}"
    )
