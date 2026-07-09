"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ─── MCQ Models ───────────────────────────────────────────────
class MCQBase(BaseModel):
    id: str = Field(..., alias="_id")
    question: str
    options: List[str]
    correct_answer: str
    category: str

    class Config:
        populate_by_name = True


class TextMCQ(MCQBase):
    """Text-based MCQ."""
    pass


class AudioMCQ(MCQBase):
    """Audio-based MCQ with audio URL."""
    audio_url: str


class ImageMCQ(MCQBase):
    """Image-based psychometric MCQ."""
    image_url: str


# ─── MCQ Response (hides correct answer from frontend) ───────
class MCQResponse(BaseModel):
    id: str
    question: str
    options: List[str]
    category: str
    media_url: Optional[str] = None
    audio_url: Optional[str] = None  # narration audio, image category only
    stimulus_text: Optional[str] = None  # reading passage / sign / message the question refers to
    video_description: Optional[str] = None
    difficulty: Optional[str] = None
    behavioral_category: Optional[str] = None


# ─── Admin MCQ Models & Response (includes correct answer) ───
class MCQCreate(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    category: str
    media_url: Optional[str] = None
    audio_transcript: Optional[str] = None
    difficulty: Optional[str] = "Easy"
    behavioral_category: Optional[str] = "General"


class MCQUpdate(BaseModel):
    question: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    category: Optional[str] = None
    media_url: Optional[str] = None
    audio_transcript: Optional[str] = None
    difficulty: Optional[str] = None
    behavioral_category: Optional[str] = None


class AdminMCQResponse(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer: str
    category: str
    media_url: Optional[str] = None
    audio_url: Optional[str] = None  # narration audio, image category only
    stimulus_text: Optional[str] = None  # reading passage / sign / message the question refers to
    video_description: Optional[str] = None
    difficulty: Optional[str] = None
    behavioral_category: Optional[str] = None
    audio_transcript: Optional[str] = None
    created_at: Optional[str] = None
    source_format: Optional[str] = None  # "legacy" | "question_item" | "scenario_image"
    raw_json: Optional[dict] = None  # complete original imported JSON, verbatim



# ─── Test Submission ─────────────────────────────────────────
class AnswerItem(BaseModel):
    question_id: str
    selected_answer: str
    category: str  # "text" | "audio" | "image"


class SubmitAnswersRequest(BaseModel):
    user_name: str = "Anonymous Driver"
    answers: List[AnswerItem]


# ─── Result Models ───────────────────────────────────────────
class CategoryScore(BaseModel):
    correct: int
    total: int
    percentage: float


class ResultResponse(BaseModel):
    user_name: str
    total_score: int
    total_questions: int
    overall_percentage: float
    category_scores: dict  # { "text": CategoryScore, "audio": ..., "image": ... }
    risk_level: str  # "Low" | "Medium" | "High"
    recommendation: str
    is_eligible_12hr: bool
