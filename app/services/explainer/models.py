"""Data models for the MIXED EXPLAINER production mode."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# Explora Ciencia 360 narrator: the user-approved ElevenLabs voice.
DEFAULT_VOICE_ID = "851ejYcv2BoNPjrkw93G"
DEFAULT_VOICE_NAME = f"elevenlabs:{DEFAULT_VOICE_ID}:Explora Ciencia 360"

VisualKind = Literal["hook", "mechanism", "flow", "cycle", "layers", "stat", "cta"]
SceneRole = Literal["hook", "problem", "step", "discovery", "cta"]
SfxType = Literal["whoosh", "ping", "rumble", "hiss", "thump", "tick"]


class Fact(BaseModel):
    claim: str
    confidence: Literal["high", "medium"] = "high"
    note: str = ""


class SfxCue(BaseModel):
    type: SfxType
    at_word: int = 0            # index of the narration word the cue is attached to
    reason: str = ""            # why the cue carries information (required by the planner)


class Visual(BaseModel):
    kind: VisualKind
    model: str = ""             # piston_engine | turbofan | gear | ""
    stage: str = ""             # model-specific phase (see models3d.*_STAGES)
    title: str = ""             # short on-screen headline
    labels: list[str] = Field(default_factory=list)   # "anchor|Texto" or node/layer names
    icons: list[str] = Field(default_factory=list)    # node shapes: gear/box/cylinder/sphere/cone
    values: list[float] = Field(default_factory=list)  # for stat bars (must come from facts)
    unit: str = ""


class Scene(BaseModel):
    id: str
    role: SceneRole = "step"
    narration: str
    keywords: list[str] = Field(default_factory=list)
    visual: Visual
    sfx: list[SfxCue] = Field(default_factory=list)


class Plan(BaseModel):
    topic: str
    title: str = ""
    facts: list[Fact] = Field(default_factory=list)
    scenes: list[Scene]
    research_note: str = ""
    source: str = "llm"         # llm | reference_pack | user_edited

    def narration_text(self) -> str:
        return " ".join(s.narration.strip() for s in self.scenes)

    def word_count(self) -> int:
        return len(self.narration_text().split())


class ExplainerParams(BaseModel):
    """Everything the user may set. The only mandatory field is ``topic``."""

    topic: str = Field(min_length=3, max_length=300)
    duration: Literal[45, 60] = 45
    style: Literal["mixed_2d_3d"] = "mixed_2d_3d"
    voice_name: str = DEFAULT_VOICE_NAME
    review_script: bool = False            # True: stop after the script for approval
    music: Literal["ambient", "none"] = "ambient"
    fps: int = Field(default=30, ge=24, le=60)
    plan: Optional[Plan] = None            # pre-approved / edited plan (skips research)

    @field_validator("topic")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class Word(BaseModel):
    text: str
    start: float
    end: float


class SceneTiming(BaseModel):
    id: str
    start: float                # global start (s)
    duration: float             # total scene length including lead-in / tail
    lead: float                 # silence before the narration in this scene
    audio_duration: float
    words: list[Word]           # scene-local timestamps (already include ``lead``)
    audio_path: str = ""
