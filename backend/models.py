from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class Slide(BaseModel):
    title: str = Field(..., max_length=120)
    bullets: List[str] = Field(default_factory=list)
    layout_hint: Optional[str] = Field(default="Title and Content")
    notes: Optional[str] = Field(default=None, description="Speaker notes")

    @field_validator("bullets")
    @classmethod
    def clamp_bullets(cls, v):
        # Keep slides readable
        return v[:8]

class SlideDeck(BaseModel):
    slides: List[Slide]
    tone: Optional[str] = None
    use_case: Optional[str] = None
    fill_missing_notes: bool = False
    llm: Optional[dict] = None

class AnalyzeResponse(BaseModel):
    deck: SlideDeck
    theme_summary: dict

class GenerateRequest(BaseModel):
    deck: SlideDeck