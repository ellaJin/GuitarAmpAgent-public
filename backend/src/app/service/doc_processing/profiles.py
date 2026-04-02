# app/service/doc_processing/profiles.py
from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkProfile:
    """
    Chunking profile (pure configuration).

    Use this to tune chunk size/overlap per brand/source/doc_type without changing business logic.
    All values are in approximate "tokens" (or any consistent unit your splitter uses).
    """
    name: str
    chunk_tokens: int
    overlap_tokens: int
    min_tokens: int = 200
    max_tokens: int = 1400

    # Heuristic flags (optional, for future splitters)
    header_aware: bool = True          # try to split on headings first
    protect_lists: bool = True         # avoid splitting inside bullet/numbered lists
    protect_param_blocks: bool = True  # avoid splitting inside "PARAM: value/desc" blocks


# ---- Default profiles (tune later based on retrieval quality) ----

# BOSS manuals/parameter guides are usually granular (lots of per-parameter entries).
BOSS_FINE = ChunkProfile(
    name="boss_fine",
    chunk_tokens=450,
    overlap_tokens=80,
    min_tokens=180,
    max_tokens=800,
)

# Line 6 Helix manuals are more workflow/tutorial oriented; keep larger context.
HELIX_COARSE = ChunkProfile(
    name="helix_coarse",
    chunk_tokens=1050,
    overlap_tokens=160,
    min_tokens=250,
    max_tokens=1600,
)

# A safe middle ground for other brands or unknown sources.
DEFAULT_MED = ChunkProfile(
    name="default_med",
    chunk_tokens=800,
    overlap_tokens=120,
    min_tokens=220,
    max_tokens=1400,
)