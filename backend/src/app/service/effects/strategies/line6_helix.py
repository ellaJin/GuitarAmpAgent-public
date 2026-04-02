# app/service/effects/strategies/line6_helix.py
"""Line 6 Helix family strategy (Helix, Helix LT, Helix Stomp, HX Effects, etc.)"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.service.effects.strategies.base import BrandExtractStrategy, BrandMatchResult
from app.llm.prompts.effect_page_prompt_builder import build_effect_page_prompt
from app.llm.prompts.midi_page_prompt_builder import build_midi_page_prompt as _build_midi_prompt


class Line6HelixStrategy(BrandExtractStrategy):

    def brand_key(self) -> str:
        return "line6_helix"

    # ------------------------------------------------------------------ match
    def match(
        self,
        device_name: str,
        brand_hint: str = "",
        sample_text: str = "",
    ) -> Optional[BrandMatchResult]:
        dn = (device_name or "").lower()
        bh = (brand_hint or "").lower()
        st = (sample_text or "").lower()

        if "line 6" in bh or "line6" in bh or "helix" in bh:
            return BrandMatchResult(
                brand_key=self.brand_key(),
                confidence=0.9,
                device_family=self._extract_family(dn or st),
            )

        if re.search(r"helix\s?(lt|stomp|floor|rack)?", dn) or \
           re.search(r"helix\s?(lt|stomp|floor|rack)?", st):
            return BrandMatchResult(
                brand_key=self.brand_key(),
                confidence=0.9,
                device_family=self._extract_family(dn or st),
            )

        if re.search(r"hx\s?(effects|stomp)", dn) or \
           re.search(r"hx\s?(effects|stomp)", st):
            return BrandMatchResult(
                brand_key=self.brand_key(),
                confidence=0.9,
                device_family="HX Series",
            )

        return None

    @staticmethod
    def _extract_family(text: str) -> str:
        m = re.search(r"helix\s?(lt|stomp|floor|rack)?", text, re.IGNORECASE)
        if m:
            suffix = (m.group(1) or "Floor").capitalize()
            return f"Helix {suffix}"
        return "Helix"

    # ------------------------------------------------------------- page gate
    _PAGE_KEYWORDS = frozenset({
        "effects", "amp and preamp", "amp+cab", "cab model",
        "speaker cabinet", "microphone model", "legacy",
        "based on", "captured from", "subcategor",
        "distortion", "dynamics", "modulation", "delay", "reverb",
        "mono, stereo",
    })

    def should_process_page(self, page_chunks: List[Dict[str, Any]]) -> bool:
        combined = self._combine_chunk_text(page_chunks)
        if any(kw in combined for kw in self._PAGE_KEYWORDS):
            return True
        return self._check_section_metadata(
            page_chunks, ("effect", "amp", "cab", "block"),
        )

    # --------------------------------------------------------------- prompt
    _BRAND_CONTEXT = """## Helix Manual Structure
The manual organizes models into these block types (use as raw_type):
- DISTORTION (overdrive, distortion, fuzz, boost effects)
- AMP (standalone amp models, same models as in Amp+Cab)
- PREAMP (preamp-only versions of amp models)
- AMP_CAB (combined amp+cab blocks - extract the AMP name only)
- CAB (speaker cabinet IR models)
- MIC (microphone models used with cabs - extract separately)
- MODULATION (chorus, flanger, phaser, tremolo, rotary, etc.)
- DELAY (all delay types)
- REVERB (all reverb types)
- DYNAMICS (compressors, gates)
- EQ (equalizers)
- WAH (wah pedals)
- PITCH (pitch shifters, harmonizers)
- FILTER (synth filters, envelope filters)
- SEND_RETURN (FX loop blocks - SKIP these)
- LOOPER (looper blocks - SKIP these)
- INPUT/OUTPUT (I/O blocks - SKIP these)

## Table formats (varies by section)
Effects tables: Model | Subcategories | Based On*
Amp tables:    Model | Subcategory | Based On*
Cab tables:    Model | Subcategories | Captured From*
Mic tables:    Model | Captured From*

## Extraction rules
- raw_name = the "Model" column (e.g. "Kinky Boost", "Stone Age 185", "1x12 Blue Bell")
  NOT the "Based On" / "Captured From" column!
- raw_type = block type from the section header
- raw_category = Subcategory value if present (e.g. "Guitar", "Bass", "Mono, Stereo")
- raw_description = "Based On" or "Captured From" column value
- For Amp+Cab sections: extract the amp name, set raw_type = "AMP_CAB"
- For Mic sections: extract mic model, set raw_type = "MIC"
- confidence: 0.9 for clear table rows, 0.7 for ambiguous
- SKIP: Input/Output/Send/Return/Looper blocks, parameter descriptions, tips/notes"""

    def build_page_prompt(
        self,
        device_name: str,
        page_chunks_json: str,
        page_number=None,
        allowed_indices: list[int] | None = None,
    ) -> str:
        return build_effect_page_prompt(
            device_name=device_name,
            page_chunks_json=page_chunks_json,
            allowed_indices=allowed_indices or [],
            brand_context=self._BRAND_CONTEXT,
            page_number=page_number,
        )

    # ---------------------------------------------------- MIDI extraction

    def supports_midi(self) -> bool:
        return True

    _MIDI_PAGE_KEYWORDS = frozenset({
        "midi cc", "midi pc", "control change", "program change",
        "bank select", "command center", "cc#", "sysex",
        "0-127", "emulates fs", "emulates exp",
        "snapshot select", "reserved for global",
    })

    def should_process_midi_page(self, page_chunks: List[Dict[str, Any]]) -> bool:
        combined = self._combine_chunk_text(page_chunks)
        if any(kw in combined for kw in self._MIDI_PAGE_KEYWORDS):
            return True
        return self._check_section_metadata(
            page_chunks, ("midi", "command center")
        )

    _MIDI_BRAND_CONTEXT = """## Helix MIDI Structure

The Helix manual describes MIDI in two main areas:

### 1. Command Center (main MIDI assignment section)
Each footswitch (FS1–FS12), expression pedal (EXP1–EXP3), and snapshot can send:
- CC  (Control Change): cc_number 0-127, value range (min/max) 0-127
- PC  (Program Change): pc_number 0-127
- BANK (Bank Select):   bank_msb + bank_lsb 0-127

target_type values to use:
- FOOTSWITCH       – FS1 through FS12 (e.g. "FS3")
- EXP_PEDAL        – EXP1, EXP2, EXP3 (expression pedals)
- SNAPSHOT         – Snapshot 1-8 (e.g. "Snapshot 3")
- EXT_AMP          – External amp switching (e.g. "Ext Amp 1")

### 2. MIDI/CV Output block (per-preset MIDI sends)
Some pages describe CC assignments tied to specific effect blocks or parameters.
- target_type = EFFECT_BLOCK for named effect blocks (e.g. "Kinky Boost")
- target_type = PARAMETER   for specific knob parameters

## Extraction rules
- message_type = "CC"   → fill cc_number; leave pc_number, bank_msb, bank_lsb null
- message_type = "PC"   → fill pc_number; leave cc_number, bank_msb, bank_lsb null
- message_type = "BANK" → fill bank_msb and/or bank_lsb; leave cc_number, pc_number null
- midi_channel: integer 1-16 if specified, else null
- target_name: the exact name of the switch/pedal/snapshot as written in the manual
- confidence: 0.9 for explicit table rows, 0.7 for inline/paragraph descriptions
- SKIP: global device MIDI settings (receive channel, MIDI thru, etc.)"""

    def build_midi_page_prompt(
        self,
        device_name: str,
        page_chunks_json: str,
        page_number=None,
        allowed_indices: list[int] | None = None,
    ) -> str:
        return _build_midi_prompt(
            device_name=device_name,
            page_chunks_json=page_chunks_json,
            allowed_indices=allowed_indices or [],
            brand_context=self._MIDI_BRAND_CONTEXT,
            page_number=page_number,
        )

    def post_process_midi(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize target names and deduplicate by MIDI address."""
        seen: Dict[str, Dict] = {}

        for e in entries:
            msg_type = (e.get("message_type") or "").upper().strip()
            if msg_type not in ("CC", "PC", "BANK"):
                continue

            # Drop entries missing the required address field for their type
            if msg_type == "CC" and e.get("cc_number") is None:
                continue
            if msg_type == "PC" and e.get("pc_number") is None:
                continue
            if msg_type == "BANK" and (
                e.get("bank_msb") is None or e.get("bank_lsb") is None
            ):
                continue

            # Normalise target_type casing
            tt = (e.get("target_type") or "UNKNOWN").upper().strip()
            e["target_type"] = tt

            # Build dedup key on MIDI address (not target name, which may vary in text)
            ch  = e.get("midi_channel")
            cc  = e.get("cc_number")
            pc  = e.get("pc_number")
            msb = e.get("bank_msb")
            lsb = e.get("bank_lsb")
            dedup_key = f"{msg_type}|{ch}|{cc}|{pc}|{msb}|{lsb}|{tt}|{e.get('target_name','')}"

            if dedup_key not in seen:
                seen[dedup_key] = e
            else:
                existing = seen[dedup_key]
                existing["confidence"] = max(
                    float(existing.get("confidence", 0.7) or 0.7),
                    float(e.get("confidence", 0.7) or 0.7),
                )
                if not existing.get("raw_description") and e.get("raw_description"):
                    existing["raw_description"] = e["raw_description"]
                existing_src = set(existing.get("source_chunk_indices") or [])
                new_src = set(e.get("source_chunk_indices") or [])
                existing["source_chunk_indices"] = list(existing_src | new_src)

        return list(seen.values())

    # --------------------------------------------------------- post-process
    def post_process(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: Dict[str, Dict] = {}

        for m in modules:
            name = (m.get("raw_name") or "").strip()
            rt = (m.get("raw_type") or "UNKNOWN").upper()

            cat = (m.get("raw_category") or "").strip()
            if cat.lower() in ("mono, stereo", "mono", "stereo"):
                m.setdefault("meta", {})["stereo_options"] = cat
                m["raw_category"] = ""
            elif cat.lower() in ("guitar", "bass", "preamp > mic"):
                m["raw_category"] = cat.lower()

            dedup_key = f"{name}||{rt}"
            if rt in ("AMP", "AMP_CAB", "PREAMP"):
                dedup_key = f"{name}||AMP_FAMILY"

            if dedup_key in seen:
                existing = seen[dedup_key]
                existing.setdefault("meta", {}).setdefault("block_types", [])
                if rt not in existing["meta"]["block_types"]:
                    existing["meta"]["block_types"].append(rt)
                existing_src = set(existing.get("source_chunk_indices") or [])
                new_src = set(m.get("source_chunk_indices") or [])
                existing["source_chunk_indices"] = list(existing_src | new_src)
            else:
                m.setdefault("meta", {})["block_types"] = [rt]
                seen[dedup_key] = m

        return list(seen.values())