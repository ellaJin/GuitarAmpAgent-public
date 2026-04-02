# app/schemas/tone_recipe.py
from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

State = Literal["ON", "OFF"]


class ChainStep(BaseModel):
    module: str = Field(..., description="Module name, e.g., Noise Gate, Delay, Reverb")
    state: State = Field(..., description="ON or OFF")
    type_or_model: Optional[str] = Field(
        None, description="Optional type/model label, e.g., Digital, Room"
    )


class ToneSection(BaseModel):
    chain: List[ChainStep] = Field(default_factory=list)
    ranges: Dict[str, str] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class ToneRecipe(BaseModel):
    song: str
    device: str
    rhythm: ToneSection
    solo: ToneSection

    def to_text(self) -> str:
        def render_section(title: str, sec: ToneSection) -> str:
            chain_lines: List[str] = []
            for i, step in enumerate(sec.chain, start=1):
                extra = f" ({step.type_or_model})" if step.type_or_model else ""
                chain_lines.append(f"{i}) {step.module}: {step.state}{extra}")

            r = sec.ranges or {}
            notes_lines = "\n".join(f"- {x}" for x in (sec.notes or [])) or "- (none)"

            return (
                f"{title}:\n"
                f"Chain:\n"
                f"{('      '.join(chain_lines) if chain_lines else '- (none)')}\n"
                f"Key settings (suggested ranges):\n"
                f"- Gain/Drive: {r.get('gain_drive', '')}\n"
                f"- EQ: {r.get('eq', '')}\n"
                f"- Delay: {r.get('delay', '')}\n"
                f"- Reverb: {r.get('reverb', '')}\n"
                f"- Gate/NR (if used): {r.get('gate_nr', '')}\n"
                f"Notes:\n{notes_lines}\n"
            )

        return (
            f"Song: {self.song}\n"
            f"Device: {self.device}\n\n"
            + render_section("Rhythm (clean-ish)", self.rhythm)
            + "\n"
            + render_section("Solo (driven)", self.solo)
        )
