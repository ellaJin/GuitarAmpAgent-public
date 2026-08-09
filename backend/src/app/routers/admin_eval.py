# app/routers/admin_eval.py
import os
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.service import admin_eval_service

router = APIRouter(prefix="/admin/eval", tags=["AdminEval"])


def _require_admin(x_admin_token: Optional[str]) -> None:
    token = os.getenv("ADMIN_TOKEN")
    if not token or x_admin_token != token:
        raise HTTPException(status_code=401, detail="Unauthorized")


class EvalQuestion(BaseModel):
    question: str
    ground_truth: Optional[str] = None


class EvalRunRequest(BaseModel):
    device_model_id: str
    questions: List[EvalQuestion]


@router.post("/run")
async def run_eval(
    body: EvalRunRequest,
    x_admin_token: Optional[str] = Header(None),
):
    """
    Run a RAGAS evaluation for a given device_model_id and question set.
    Returns per-question scores and aggregated summary.
    """
    _require_admin(x_admin_token)

    if not body.device_model_id.strip():
        raise HTTPException(status_code=422, detail="device_model_id is required.")
    if not body.questions:
        raise HTTPException(status_code=422, detail="questions list is empty.")

    questions = [q.model_dump() for q in body.questions]

    try:
        result = await admin_eval_service.run_eval(
            device_model_id=body.device_model_id.strip(),
            questions=questions,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eval failed: {type(e).__name__}: {e}")

    return result
