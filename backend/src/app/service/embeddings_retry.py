# app/service/embeddings_retry.py
from __future__ import annotations

import random
import time
from typing import List, Sequence, Any, Callable


def _is_transient_embedding_error(e: Exception) -> bool:
    """
    Best-effort transient error detection for network/SSL/provider hiccups.
    """
    msg = repr(e)
    transient_signals = [
        "SSLError",
        "SSL",
        "UNEXPECTED_EOF_WHILE_READING",
        "HTTPSConnectionPool",
        "Max retries exceeded",
        "Read timed out",
        "ConnectTimeout",
        "ConnectionError",
        "RemoteDisconnected",
        "503",
        "502",
        "504",
        "rate limit",
        "Too Many Requests",
    ]
    return any(s in msg for s in transient_signals)


def embed_documents_resilient(
    embedder: Any,
    texts: Sequence[str],
    *,
    batch_size: int = 32,
    max_retries: int = 5,
    base_delay_s: float = 1.0,
    max_delay_s: float = 20.0,
    jitter_s: float = 0.3,
    on_batch_error: Callable[[int, int, Exception], None] | None = None,
) -> List[List[float]]:
    """
    Robust wrapper:
      - splits into batches
      - retries transient failures with exponential backoff + jitter
      - raises non-transient errors immediately

    Returns: vectors aligned with `texts`.
    """
    texts = list(texts)
    vectors: List[List[float]] = []

    for start in range(0, len(texts), batch_size):
        end = min(start + batch_size, len(texts))
        batch = texts[start:end]

        attempt = 0
        while True:
            try:
                batch_vecs = embedder.embed_documents(batch)
                if not isinstance(batch_vecs, list) or len(batch_vecs) != len(batch):
                    raise RuntimeError(
                        f"Embedding provider returned invalid shape: "
                        f"got {type(batch_vecs)} len={getattr(batch_vecs, '__len__', None)} "
                        f"expected len={len(batch)}"
                    )
                vectors.extend(batch_vecs)
                break

            except Exception as e:
                attempt += 1
                transient = _is_transient_embedding_error(e)

                if on_batch_error:
                    on_batch_error(start, end, e)

                if (not transient) or attempt > max_retries:
                    raise

                # exponential backoff + jitter
                delay = min(max_delay_s, base_delay_s * (2 ** (attempt - 1)))
                delay = delay + random.uniform(0, jitter_s)
                time.sleep(delay)

    return vectors