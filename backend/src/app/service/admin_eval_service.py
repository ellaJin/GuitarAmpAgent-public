# app/service/admin_eval_service.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.db import get_db_con

SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"

RETRIEVAL_LIMIT = 6




def _lookup_device(device_model_id: str) -> Dict:
    """
    Look up brand, model, and one associated kb_source_id from a device_model_id.
    Needed to build ActiveDeviceContext for the chat pipeline.
    """
    with get_db_con() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT dm.brand, dm.model, ks.id
                FROM device_models dm
                LEFT JOIN kb_sources ks ON ks.device_model_id = dm.id
                WHERE dm.id = %s
                LIMIT 1
                """,
                (device_model_id,),
            )
            row = cur.fetchone()
    if not row:
        raise ValueError(f"No device found for device_model_id: {device_model_id}")
    return {
        "device_model_id": device_model_id,
        "brand":           row[0] or "",
        "model":           row[1] or "",
        "kb_source_id":    str(row[2]) if row[2] else None,
    }


async def _run_pipeline_for_eval(
    question: str,
    active_device,
) -> Tuple[str, List[str]]:
    """
    Run the full chat pipeline for a single eval question.

    Returns:
        (answer, contexts)
        - answer:   final response from get_chat_response() (full routing + agent)
        - contexts: list of chunk strings retrieved by search_manual_chunks tool

    get_chat_response() returns only the answer string; contexts are captured
    by a second agent pass that inspects the search_manual_chunks ToolMessages.
    """
    from langchain_core.messages import ToolMessage
    from app.schemas.chat import ChatQueryRequest, ChatQueryContext
    from app.service.chat_service import get_chat_response
    from app.llm.tool_factory import ToolFactory
    from app.llm.agents.deep_agent import build_deep_agent

    # 1. Answer via the full chat pipeline (routing + ReAct agent)
    req = ChatQueryRequest(user_input=question, chat_history=[])
    ctx = ChatQueryContext(
        user_id=SYSTEM_USER_ID,
        user_name="eval",
        active_device=active_device,
    )
    answer, _tokens_used, _ok = await get_chat_response(req, ctx)

    # 2. Collect retrieved contexts for RAGAS by inspecting ToolMessages.
    #    get_chat_response() does not expose internal messages, so we run a
    #    second agent pass solely to capture what search_manual_chunks returns.
    accumulator = {"source_count": 0}
    tools = ToolFactory.get_tools(SYSTEM_USER_ID, active_device, accumulator)
    graph = build_deep_agent(tools)
    result_state = await graph.ainvoke({"messages": [("human", question)]})
    msgs = result_state.get("messages", [])

    contexts: List[str] = []
    for m in msgs:
        if isinstance(m, ToolMessage) and getattr(m, "name", "") == "search_manual_chunks":
            content = getattr(m, "content", "") or ""
            chunks = [c.strip() for c in content.split("\n---\n") if c.strip()]
            contexts.extend(chunks)

    return answer, contexts


def _safe_float(val: Any) -> Optional[float]:
    try:
        f = float(val)
        return round(f, 4)
    except (TypeError, ValueError):
        return None


async def run_eval(device_model_id: str, questions: List[Dict]) -> Dict:
    """
    Run a full-pipeline RAGAS evaluation for a given device_model_id and question set.

    For each question:
      - Runs the real ReAct agent (ToolFactory + build_deep_agent + ainvoke)
      - Extracts answer from the last message
      - Extracts retrieved contexts from search_manual_chunks ToolMessages
    Then evaluates with RAGAS metrics and returns per-question scores + summary.

    Each question dict: {"question": str, "ground_truth": str (optional)}
    """
    from app.schemas.device import ActiveDeviceContext

    # Look up device info to build ActiveDeviceContext
    device_info = _lookup_device(device_model_id)
    active_device = ActiveDeviceContext(
        device_model_id=device_info["device_model_id"],
        brand=device_info["brand"],
        model=device_info["model"],
        kb_source_id=device_info["kb_source_id"],
    )

    # --- 1) Run full pipeline for each question ---
    samples: List[Dict] = []
    for item in questions:
        q = (item.get("question") or "").strip()
        if not q:
            continue
        ground_truth = (item.get("ground_truth") or "").strip() or None

        answer, contexts = await _run_pipeline_for_eval(q, active_device)

        samples.append({
            "question":     q,
            "answer":       answer,
            "contexts":     contexts,
            "ground_truth": ground_truth,
        })

    if not samples:
        return {
            "summary": {
                "faithfulness":      None,
                "answer_relevancy":  None,
                "context_precision": None,
                "composite_score":   None,
            },
            "rows": [],
        }

    # --- 2) RAGAS 0.4.x evaluation ---
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory
    from ragas.embeddings.base import embedding_factory
    from ragas.metrics.collections import Faithfulness, AnswerRelevancy, ContextPrecision
    from app.core.config import settings

    has_ground_truths = all(s["ground_truth"] for s in samples)

    client = AsyncOpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )
    judge_llm = llm_factory("deepseek-v3", client=client)

    embed_client = AsyncOpenAI(
        api_key=settings.QWEN_EMB_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )
    judge_embeddings = embedding_factory("openai", model="text-embedding-v3", client=embed_client, interface="modern")

    faithfulness_metric = Faithfulness(llm=judge_llm)
    answer_relevancy_metric = AnswerRelevancy(llm=judge_llm, embeddings=judge_embeddings)
    context_precision_metric = ContextPrecision(llm=judge_llm)

    per_sample_scores: List[Dict[str, Optional[float]]] = []
    for sample in samples:
        if sample["contexts"]:
            faith_result = await faithfulness_metric.ascore(
                user_input=sample["question"],
                response=sample["answer"],
                retrieved_contexts=sample["contexts"]
            )
            faith_value = faith_result.value
        else:
            faith_value = None
        ar_result = await answer_relevancy_metric.ascore(
            user_input=sample["question"],
            response=sample["answer"],
        )
        row: Dict[str, Optional[float]] = {
            "faithfulness":      faith_value,
            "answer_relevancy":  ar_result.value,
            "context_precision": None,
        }
        if sample.get("ground_truth"):
            cp_result = await context_precision_metric.ascore(
                user_input=sample["question"],
                response=sample["answer"],
                retrieved_contexts=sample["contexts"],
                reference=sample["ground_truth"]
            )
            row["context_precision"] = cp_result.value
        per_sample_scores.append(row)

    # --- 3) Build per-row output ---
    rows = []
    for i, s in enumerate(samples):
        sc = per_sample_scores[i]
        row_faith = _safe_float(sc.get("faithfulness"))
        row_ar    = _safe_float(sc.get("answer_relevancy"))
        row_cp    = _safe_float(sc.get("context_precision")) if has_ground_truths else None
        rows.append({
            "question":          s["question"],
            "answer":            s["answer"],
            "faithfulness":      row_faith,
            "answer_relevancy":  row_ar,
            "context_precision": row_cp,
            "has_ground_truth":  s["ground_truth"] is not None,
        })

    # --- 4) Summary — simple average per metric ---
    def _avg(vals: List[Optional[float]]) -> Optional[float]:
        valid = [v for v in vals if v is not None]
        if not valid:
            return None
        return round(sum(valid) / len(valid), 4)

    faith_avg = _avg([r["faithfulness"]      for r in rows])
    ar_avg    = _avg([r["answer_relevancy"]  for r in rows])
    cp_avg    = _avg([r["context_precision"] for r in rows])

    # Composite: simple average of the three metrics
    composite_inputs = [v for v in [faith_avg, ar_avg, cp_avg] if v is not None]
    composite = round(sum(composite_inputs) / len(composite_inputs), 4) if composite_inputs else None

    return {
        "summary": {
            "faithfulness":      faith_avg,
            "answer_relevancy":  ar_avg,
            "context_precision": cp_avg,
            "composite_score":   composite,
        },
        "rows": rows,
    }
