"""
MCQ routes — serves pre-generated questions from MongoDB.
"""
from fastapi import APIRouter
from database import get_database
from models import MCQResponse

router = APIRouter(prefix="/api/mcqs", tags=["MCQs"])


def _normalize_static_url(url):
    """Rewrite an absolute/legacy static path into the current /static/... form."""
    if url and "static/" in url:
        parts = url.split("static/")
        return "/static/" + parts[-1]
    return url


def _format_mcq(doc: dict, fallback_category: str = "") -> dict:
    """Transform a MongoDB document into a frontend-safe MCQ response.
    Uses .get() with safe fallbacks so legacy documents with missing fields don't crash.
    """
    category = doc.get("category") or fallback_category
    # For image/video, the primary media is the image; audio_url (if present) is a
    # separate narration track and must never displace the image in `media_url`.
    media_url = doc.get("image_url") if category in ("image", "video") else doc.get("audio_url")
    narration_audio_url = doc.get("audio_url") if category == "image" else None
    return {
        "id": str(doc["_id"]),
        "question": doc.get("question", ""),
        "options": doc.get("options", []),
        "category": category,
        "media_url": _normalize_static_url(media_url),
        "audio_url": _normalize_static_url(narration_audio_url),
        "stimulus_text": doc.get("stimulus_text"),
        "video_description": doc.get("video_description"),
        "difficulty": doc.get("difficulty"),
        "behavioral_category": doc.get("behavioral_category"),
    }


@router.get("/text", response_model=list[MCQResponse])
async def get_text_mcqs():
    """Fetch all text-based MCQs (returns empty list if none exist)."""
    db = get_database()
    cursor = db.text_mcqs.find()
    docs = await cursor.to_list(length=500)
    return [_format_mcq(d) for d in docs]


@router.get("/audio", response_model=list[MCQResponse])
async def get_audio_mcqs():
    """Fetch all audio-based MCQs (returns empty list if none exist)."""
    db = get_database()
    cursor = db.audio_mcqs.find()
    docs = await cursor.to_list(length=500)
    return [_format_mcq(d) for d in docs]


@router.get("/image", response_model=list[MCQResponse])
async def get_image_mcqs():
    """Fetch all image-based psychometric MCQs (returns empty list if none exist)."""
    db = get_database()
    cursor = db.image_mcqs.find()
    docs = await cursor.to_list(length=500)
    return [_format_mcq(d) for d in docs]


@router.get("/all", response_model=list[MCQResponse])
async def get_all_mcqs():
    """Fetch ALL MCQs across all categories in a single call.
    Always returns the exact live state from MongoDB — no caching.
    Returns empty list if database has no questions yet.
    """
    db = get_database()
    all_mcqs = []

    COLLECTION_CATEGORIES = {
        "text_mcqs": "text",
        "audio_mcqs": "audio",
        "image_mcqs": "image",
        "video_mcqs": "video",
    }

    for collection_name, cat_name in COLLECTION_CATEGORIES.items():
        cursor = db[collection_name].find()
        docs = await cursor.to_list(length=500)  # Raised from 100 to support larger question banks
        all_mcqs.extend([_format_mcq(d, fallback_category=cat_name) for d in docs])

    # Return empty list instead of 404 so the frontend handles 0 questions gracefully
    return all_mcqs
