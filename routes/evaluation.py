"""
Evaluation routes — scores answers and generates result cards.
"""
from fastapi import APIRouter, HTTPException
from database import get_database
from models import SubmitAnswersRequest, ResultResponse, CategoryScore
from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter(prefix="/api", tags=["Evaluation"])

# Collection map for looking up correct answers
COLLECTION_MAP = {
    "text": "text_mcqs",
    "audio": "audio_mcqs",
    "image": "image_mcqs",
    "video": "video_mcqs",
}


def _assess_risk(percentage: float) -> tuple[str, str, bool]:
    """
    Determine risk level, recommendation, and 12-hour eligibility
    based on overall score percentage.
    """
    if percentage >= 80:
        return (
            "Low",
            "✅ Driver is safe and mentally stable. Approved for 12-hour driving shifts.",
            True,
        )
    elif percentage >= 60:
        return (
            "Medium",
            "⚠️ Driver shows moderate risk. Recommended for short-distance trips only. Additional training suggested.",
            False,
        )
    else:
        return (
            "High",
            "🚫 Driver is NOT recommended for active duty. Psychological evaluation and mandatory retraining required.",
            False,
        )


@router.post("/submit-answers", response_model=ResultResponse)
async def submit_answers(payload: SubmitAnswersRequest):
    """Score a completed test and return a detailed result card."""
    db = get_database()

    # Tally scores per category
    category_tallies = {
        "text": {"correct": 0, "total": 0},
        "audio": {"correct": 0, "total": 0},
        "image": {"correct": 0, "total": 0},
        "video": {"correct": 0, "total": 0},
    }

    for answer in payload.answers:
        cat = answer.category
        collection_name = COLLECTION_MAP.get(cat)
        if not collection_name:
            continue

        category_tallies[cat]["total"] += 1

        # Look up correct answer from DB
        try:
            doc = await db[collection_name].find_one(
                {"_id": ObjectId(answer.question_id)}
            )
        except Exception:
            continue

        if doc and doc.get("correct_answer") == answer.selected_answer:
            category_tallies[cat]["correct"] += 1

    # Calculate scores
    total_correct = sum(t["correct"] for t in category_tallies.values())
    total_questions = sum(t["total"] for t in category_tallies.values())
    overall_pct = (total_correct / total_questions * 100) if total_questions > 0 else 0

    category_scores = {}
    for cat, tally in category_tallies.items():
        pct = (tally["correct"] / tally["total"] * 100) if tally["total"] > 0 else 0
        category_scores[cat] = CategoryScore(
            correct=tally["correct"],
            total=tally["total"],
            percentage=round(pct, 1),
        )

    risk_level, recommendation, is_eligible = _assess_risk(overall_pct)

    # Persist result to MongoDB
    result_doc = {
        "user_name": payload.user_name,
        "total_score": total_correct,
        "total_questions": total_questions,
        "overall_percentage": round(overall_pct, 1),
        "category_scores": {k: v.model_dump() for k, v in category_scores.items()},
        "risk_level": risk_level,
        "recommendation": recommendation,
        "is_eligible_12hr": is_eligible,
        "submitted_at": datetime.now(timezone.utc),
    }
    await db.results.insert_one(result_doc)

    return ResultResponse(
        user_name=payload.user_name,
        total_score=total_correct,
        total_questions=total_questions,
        overall_percentage=round(overall_pct, 1),
        category_scores={k: v.model_dump() for k, v in category_scores.items()},
        risk_level=risk_level,
        recommendation=recommendation,
        is_eligible_12hr=is_eligible,
    )


@router.get("/result/{user_name}")
async def get_latest_result(user_name: str):
    """Retrieve the most recent result for a given user."""
    db = get_database()
    doc = await db.results.find_one(
        {"user_name": user_name},
        sort=[("submitted_at", -1)],
    )
    if not doc:
        raise HTTPException(status_code=404, detail="No results found for this user")
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/results/history/{user_name}")
async def get_test_history(user_name: str):
    """Retrieve all past results for a given user."""
    db = get_database()
    cursor = db.results.find({"user_name": user_name}).sort("submitted_at", -1)
    docs = await cursor.to_list(length=100)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs

