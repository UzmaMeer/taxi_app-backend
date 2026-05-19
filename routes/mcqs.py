"""
MCQ routes — serves pre-generated questions from MongoDB.
"""
from fastapi import APIRouter, HTTPException
from database import get_database
from models import MCQResponse

router = APIRouter(prefix="/api/mcqs", tags=["MCQs"])


def _format_mcq(doc: dict) -> dict:
    """Transform a MongoDB document into a frontend-safe MCQ response."""
    media_url = doc.get("audio_url") or doc.get("image_url") or None
    if media_url and "static/" in media_url:
        parts = media_url.split("static/")
        media_url = "/static/" + parts[-1]
    return {
        "id": str(doc["_id"]),
        "question": doc["question"],
        "options": doc["options"],
        "category": doc["category"],
        "media_url": media_url,
        "video_description": doc.get("video_description"),
        "difficulty": doc.get("difficulty"),
        "behavioral_category": doc.get("behavioral_category"),
    }


@router.get("/text", response_model=list[MCQResponse])
async def get_text_mcqs():
    """Fetch all text-based MCQs."""
    db = get_database()
    cursor = db.text_mcqs.find()
    docs = await cursor.to_list(length=100)
    if not docs:
        raise HTTPException(status_code=404, detail="No text MCQs found")
    return [_format_mcq(d) for d in docs]


@router.get("/audio", response_model=list[MCQResponse])
async def get_audio_mcqs():
    """Fetch all audio-based MCQs."""
    db = get_database()
    cursor = db.audio_mcqs.find()
    docs = await cursor.to_list(length=100)
    if not docs:
        raise HTTPException(status_code=404, detail="No audio MCQs found")
    return [_format_mcq(d) for d in docs]


@router.get("/image", response_model=list[MCQResponse])
async def get_image_mcqs():
    """Fetch all image-based psychometric MCQs."""
    db = get_database()
    cursor = db.image_mcqs.find()
    docs = await cursor.to_list(length=100)
    if not docs:
        raise HTTPException(status_code=404, detail="No image MCQs found")
    return [_format_mcq(d) for d in docs]


@router.get("/all", response_model=list[MCQResponse])
async def get_all_mcqs():
    """Fetch ALL MCQs across all categories in a single call."""
    db = get_database()
    all_mcqs = []

    for collection_name in ["text_mcqs", "audio_mcqs", "image_mcqs", "video_mcqs"]:
        cursor = db[collection_name].find()
        docs = await cursor.to_list(length=100)
        all_mcqs.extend([_format_mcq(d) for d in docs])

    if not all_mcqs:
        raise HTTPException(status_code=404, detail="No MCQs found in database")
    return all_mcqs
