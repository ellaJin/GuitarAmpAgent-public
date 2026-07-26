# app/utils/quality.py
from typing import Dict

UNCERTAINTY_PHRASES = (
    "I think",
    "I believe",
    "I'm not sure",
    "probably",
    "might be",
    "I guess",
)


def compute_quality_flags(response_text: str, source_count: int) -> Dict[str, object]:
    grounded = source_count > 0
    hallucination_flag = any(phrase in response_text for phrase in UNCERTAINTY_PHRASES)

    if grounded and not hallucination_flag:
        quality_level = "high"
    elif grounded and hallucination_flag:
        quality_level = "medium"
    else:
        quality_level = "low"

    return {
        "grounded": grounded,
        "hallucination_flag": hallucination_flag,
        "quality_level": quality_level,
    }
