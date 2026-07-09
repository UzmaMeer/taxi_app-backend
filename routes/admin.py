"""
Admin routes — handles MCQ CRUD, file uploads, dynamic TTS voiceover generation,
bulk imports, and driver results logs. Protected by role-based auth.
"""
import os
import uuid
import json
import shutil
import hashlib
import urllib.request
import urllib.parse
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query, Request
from gtts import gTTS
from bson import ObjectId

from database import get_database
from models import MCQCreate, MCQUpdate, AdminMCQResponse

class CreateAdminRequest(BaseModel):
    full_name: str
    email: str
    password: str

class UpdateUserRoleRequest(BaseModel):
    role: str

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Directory configuration for media assets
ROUTES_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.dirname(ROUTES_DIR)
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
AUDIO_DIR = os.path.join(STATIC_DIR, "audio")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")

# Collection names map
COLLECTION_MAP = {
    "text": "text_mcqs",
    "audio": "audio_mcqs",
    "image": "image_mcqs",
    "video": "video_mcqs",
}
# Magic bytes for supported image/video formats
MAGIC_BYTES = {
    b'\x47\x49\x46\x38': '.gif',   # GIF87a / GIF89a
    b'\x47\x49\x46\x39': '.gif',
    b'\x89\x50\x4e\x47': '.png',   # PNG
    b'\xff\xd8\xff': '.jpg',        # JPEG
    b'\x00\x00\x00': '.mp4',        # MP4 (ftyp box, partial)
}

def _detect_ext_from_content(content: bytes) -> str:
    """Detect file extension from the first bytes of the content."""
    head = content[:8]
    for magic, ext in MAGIC_BYTES.items():
        if head[:len(magic)] == magic:
            return ext
    # Check specifically for MP4 ftyp box
    if b'ftyp' in content[:16]:
        return '.mp4'
    return ''


def _build_giphy_variants(url: str):
    """
    Given any Giphy URL, produce a list of CDN variants to try.
    Giphy uses media0-media4.giphy.com as sharded CDN hosts.
    """
    import re
    variants = [url]
    match = re.search(r'/media/([a-zA-Z0-9]+)/', url)
    if match:
        gif_id = match.group(1)
        for i in range(5):
            variants.append(f"https://media{i}.giphy.com/media/{gif_id}/giphy.gif")
        variants.append(f"https://i.giphy.com/{gif_id}.gif")
    return list(dict.fromkeys(variants))  # deduplicate, preserve order


def _extract_og_image(page_html: bytes) -> Optional[str]:
    """
    Extract the og:image URL from a webpage's HTML meta tags.
    Works for Pinterest, Twitter cards, Facebook OG, and most modern sites.
    """
    import re
    html = page_html.decode('utf-8', errors='ignore')

    # 1. Look for animated GIF links if Pinterest or pinimg CDN link is present in the HTML.
    # Pinterest stores the actual original animated GIF under originals/*.gif in pinimg.com
    gif_match = re.search(r'https?://(?:[a-z0-9\-]+\.)?pinimg\.com/[^"\']+\.gif', html, re.IGNORECASE)
    if gif_match:
        gif_url = gif_match.group(0).strip()
        print(f"  [EXTRACT] Found animated Pinterest GIF: {gif_url}")
        return gif_url

    # 2. Otherwise try og:image first (Pinterest, Facebook, most sites)
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            img_url = match.group(1).strip()
            if img_url.startswith('http'):
                return img_url
    return None


def _try_download(url: str) -> Optional[bytes]:
    """
    Attempt to download from a URL.
    - If the URL is a direct image/video link: downloads and validates content bytes.
    - If the URL is a webpage (Pinterest, news site, etc.): extracts the og:image
      meta tag URL and downloads that instead.
    Returns raw image bytes on success, or None on failure.
    """
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/gif,image/png,image/jpeg,image/webp,video/mp4,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
    }
    image_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'image/gif, image/png, image/jpeg, image/webp, video/mp4, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://giphy.com/',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'cross-site',
    }
    try:
        req = urllib.request.Request(url, headers=image_headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            content_type = response.headers.get('Content-Type', '').lower()

            # ── Webpage URL (Pinterest, news article, etc.) ──
            # Extract og:image from the HTML and download that instead
            if 'text/html' in content_type:
                print(f"  [HTML] {url} → webpage detected, looking for og:image...")
                html_content = response.read()
                og_image_url = _extract_og_image(html_content)
                if og_image_url:
                    print(f"  [OG] Found og:image: {og_image_url[:80]}")
                    # Recursively download the actual image URL
                    return _try_download(og_image_url)
                print(f"  [SKIP] {url} → no og:image found in HTML")
                return None

            # ── Direct image/video URL ──
            content = response.read()
            if len(content) < 1024:
                print(f"  [SKIP] {url} → too small ({len(content)} bytes, likely error)")
                return None
            # Validate it's actually an image via magic bytes
            detected_ext = _detect_ext_from_content(content)
            if not detected_ext:
                if content[:15].lower().strip().startswith(b'<!doctype') or content[:6].lower() == b'<html>':
                    print(f"  [SKIP] {url} → content is HTML despite non-HTML content-type")
                    return None
            return content
    except Exception as e:
        print(f"  [FAIL] {url} → {e}")
        return None


def download_media_from_url(url: str) -> Optional[str]:
    """
    Downloads media from an external URL, saves it to UPLOADS_DIR, and returns the local relative path.
    - Validates that the downloaded content is a real image/GIF (not an HTML error page)
    - For Giphy URLs: tries multiple CDN shard variants automatically
    - Falls back to the original URL string only if ALL download attempts fail
    """
    if not url:
        return None
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        return url  # Already a local/relative path

    os.makedirs(UPLOADS_DIR, exist_ok=True)

    # Build list of URLs to try (multiple CDN shards for Giphy)
    is_giphy = "giphy.com" in url
    urls_to_try = _build_giphy_variants(url) if is_giphy else [url]

    print(f"[DOWNLOAD] Attempting to download: {url}")
    if is_giphy:
        print(f"  Will try {len(urls_to_try)} Giphy CDN variant(s)")

    content = None
    for attempt_url in urls_to_try:
        content = _try_download(attempt_url)
        if content:
            print(f"  [OK] Downloaded {len(content)} bytes from: {attempt_url}")
            break

    if not content:
        print(f"[WARNING] All download attempts failed for: {url} — storing original URL as fallback")
        return url  # Fallback: store original URL (browser may still be able to load it)

    # Detect extension from content bytes (more reliable than URL)
    ext = _detect_ext_from_content(content)
    if not ext:
        # Guess from URL
        parsed = urllib.parse.urlparse(url)
        _, url_ext = os.path.splitext(parsed.path)
        ext = url_ext.lower() if url_ext.lower() in ['.gif', '.png', '.jpg', '.jpeg', '.mp4'] else '.gif'

    filename = f"media_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOADS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    saved_path = f"/static/uploads/{filename}"
    print(f"  [SAVED] {saved_path} ({ext}, {len(content) // 1024} KB)")
    return saved_path


# Root of the question-authoring data pipeline (local machine) — used to resolve
# archive-relative media paths like "data/approved/media/GIA-000113.png".
ARCHIVE_ROOT = os.getenv("ARCHIVE_ROOT", "D:/bc_language_assessment_archive")


def import_local_media_file(candidate_paths: List[str]) -> Optional[str]:
    """
    Copy a media file that already lives on the local filesystem (as produced by the
    question-authoring pipeline) into UPLOADS_DIR, and return the local static URL.

    Unlike download_media_from_url(), this never touches the network — it only
    handles absolute local paths (e.g. "D:/bc_language_assessment_archive/data/media/images/x.png")
    or archive-relative paths (e.g. "data/approved/media/x.png", resolved against ARCHIVE_ROOT).
    Tries each candidate in order and returns on the first that exists on disk.
    """
    for raw_path in candidate_paths:
        if not raw_path:
            continue
        normalized = os.path.normpath(str(raw_path).replace("\\", "/"))
        candidates = [normalized]
        if not os.path.isabs(normalized):
            candidates.append(os.path.normpath(os.path.join(ARCHIVE_ROOT, normalized)))

        for path in candidates:
            try:
                if not os.path.isfile(path):
                    continue
                os.makedirs(UPLOADS_DIR, exist_ok=True)
                ext = os.path.splitext(path)[1].lower() or ".png"
                filename = f"media_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOADS_DIR, filename)
                shutil.copy(path, filepath)
                saved_path = f"/static/uploads/{filename}"
                print(f"  [COPIED] {path} -> {saved_path}")
                return saved_path
            except (OSError, PermissionError) as e:
                print(f"  [FAIL] Could not copy '{path}': {e}")
                continue

    print(f"[WARNING] Could not locate any local media file among candidates: {candidate_paths}")
    return None


def detect_and_normalize_bulk_item(q_data: dict):
    """
    Detect which question-authoring JSON schema an imported item uses, and normalize it
    into a flat dict with the fields the rest of the import pipeline already expects
    (question, options, correct_answer, difficulty, behavioral_category, audio_transcript,
    plus scenario-only image candidate paths). The original item is never mutated.

    Returns (source_format, detected_category, normalized_dict).
    Returns (None, None, None) if the shape isn't recognized at all.
    """
    # ── Scenario / Image (situational judgement item) ──
    if "scenario" in q_data or "media_prompt_spec" in q_data:
        scenario = q_data.get("scenario") or {}
        media_prompt_spec = q_data.get("media_prompt_spec") or {}
        generated_image_asset = q_data.get("generated_image_asset") or {}
        approved_media_files = q_data.get("approved_media_files") or []

        scenario_text = str(scenario.get("scenario_text") or "").strip()
        candidate_question = str(scenario.get("candidate_question") or "").strip()
        question = " ".join(p for p in [scenario_text, candidate_question] if p)

        response_options = scenario.get("response_options") or []
        # Preserve the options' original A/B/C/D order for display — sorting them by score
        # would always push the correct answer to the same displayed position (always "A"),
        # which would let test-takers game the assessment. Only used to pick the correct
        # answer's text, never to reorder what's shown.
        options_in_order = sorted(response_options, key=lambda o: str(o.get("option_id") or ""))
        options = [str(o.get("option_text") or "").strip() for o in options_in_order]

        top_score = max((o.get("score") or 0) for o in response_options) if response_options else 0
        tied_for_top = [o for o in response_options if (o.get("score") or 0) == top_score]
        best_option = sorted(tied_for_top, key=lambda o: str(o.get("option_id") or ""))[0] if tied_for_top else None
        correct_answer = str(best_option.get("option_text") or "").strip() if best_option else ""

        image_candidates = []
        if generated_image_asset.get("file_path"):
            image_candidates.append(generated_image_asset["file_path"])
        image_candidates.extend(approved_media_files)

        normalized = {
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
            "difficulty": "Medium",
            "behavioral_category": scenario.get("construct_measured") or "General",
            "audio_transcript": str(media_prompt_spec.get("audio_transcript") or "").strip(),
            "image_candidates": image_candidates,
        }
        return "scenario_image", "image", normalized

    # ── Question item (Listening / Reading / etc.) ──
    if "item_id" in q_data and "question_text" in q_data:
        audio_metadata = q_data.get("audio_metadata") or {}
        transcript = str(audio_metadata.get("audio_transcript") or "").strip()
        detected_category = "audio" if transcript else "text"

        # Kept as its own field (not merged into `question`) so the frontend can render the
        # stimulus (sign, message, notice, etc.) as a distinct block above the question rather
        # than a single run-on sentence. Reading items have no audio, so this is the only way
        # the driver sees the context the question refers to.
        normalized = {
            "question": str(q_data.get("question_text") or "").strip(),
            "stimulus_text": str(q_data.get("stimulus_text") or "").strip(),
            "options": [str(o).strip() for o in (q_data.get("options") or [])],
            "correct_answer": str(q_data.get("correct_answer") or "").strip(),
            "difficulty": q_data.get("difficulty") or "Easy",
            "behavioral_category": q_data.get("workplace_domain") or q_data.get("skill") or "General",
            "audio_transcript": transcript,
        }
        return "question_item", detected_category, normalized

    # ── Legacy flat MCQ ──
    if "question" in q_data and "options" in q_data and "correct_answer" in q_data:
        detected_category = str(q_data.get("category") or "").lower().strip()
        normalized = {
            "question": str(q_data.get("question") or "").strip(),
            "options": [str(o).strip() for o in (q_data.get("options") or [])],
            "correct_answer": str(q_data.get("correct_answer") or "").strip(),
            "difficulty": q_data.get("difficulty") or "Easy",
            "behavioral_category": q_data.get("behavioral_category") or "General",
            "audio_transcript": str(q_data.get("audio_transcript") or "").strip(),
            "media_url": q_data.get("media_url") or q_data.get("image_url") or "",
        }
        return "legacy", detected_category, normalized

    return None, None, None


# ─── SECURITY TOKEN EXTRACTORS ────────────────────────────────
def get_token_from_header(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return auth_header

async def get_admin_user(request: Request, token: Optional[str] = Query(None)):
    tok = token or get_token_from_header(request)
    if not tok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )
    
    db = get_database()
    user = await db.users.find_one({"token": tok})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )
    
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin role required"
        )
    
    return user


# ─── DYNAMIC TTS GENERATION HELPER ───────────────────────────
def generate_tts_mp3(text: str) -> str:
    """Generate audio MP3 from text using gTTS and return relative URL path."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    filename = f"tts_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(filepath)
    
    return f"/static/audio/{filename}"


# ─── FORMAT MCQ FOR ADMIN VIEW (INCLUDES CORRECT ANSWER) ──────
def _normalize_static_url(url):
    """Rewrite an absolute/legacy static path into the current /static/... form."""
    if url and "static/" in url:
        parts = url.split("static/")
        return "/static/" + parts[-1]
    return url


def _format_admin_mcq(doc: dict, category: str) -> dict:
    """Transcribe database document into an Admin-rich representation."""
    cat = doc.get("category") or category
    # For image/video, the primary media is the image; audio_url (if present) is a
    # separate narration track and must never displace the image in `media_url`.
    media_url = doc.get("image_url") if cat in ("image", "video") else doc.get("audio_url")
    narration_audio_url = doc.get("audio_url") if cat == "image" else None

    return {
        "id": str(doc["_id"]),
        "question": doc["question"],
        "options": doc["options"],
        "correct_answer": doc["correct_answer"],
        "category": cat,
        "media_url": _normalize_static_url(media_url),
        "audio_url": _normalize_static_url(narration_audio_url),
        "stimulus_text": doc.get("stimulus_text"),
        "audio_transcript": doc.get("audio_transcript"),
        "difficulty": doc.get("difficulty") or "Easy",
        "behavioral_category": doc.get("behavioral_category") or "General",
        "created_at": doc.get("created_at") or None,
        "source_format": doc.get("source_format"),
        "raw_json": doc.get("raw_json"),
    }


# ─── ADMIN ENDPOINTS ──────────────────────────────────────────

@router.get("/mcqs", response_model=List[AdminMCQResponse])
async def list_admin_mcqs(admin: dict = Depends(get_admin_user)):
    """Fetch all MCQs across all collections WITH correct answers."""
    db = get_database()
    all_mcqs = []
    
    for category, collection_name in COLLECTION_MAP.items():
        cursor = db[collection_name].find()
        docs = await cursor.to_list(length=500)
        all_mcqs.extend([_format_admin_mcq(d, category) for d in docs])
        
    return all_mcqs


@router.post("/mcqs", status_code=201)
async def create_mcq(payload: MCQCreate, admin: dict = Depends(get_admin_user)):
    """Create a new MCQ and insert it in the correct collection."""
    db = get_database()
    category = payload.category.lower().strip()
    collection_name = COLLECTION_MAP.get(category)
    
    if not collection_name:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Must be text, audio, image, or video."
        )
        
    doc = {
        "question": payload.question.strip(),
        "options": [opt.strip() for opt in payload.options],
        "correct_answer": payload.correct_answer.strip(),
        "category": category,
        "difficulty": payload.difficulty or "Easy",
        "behavioral_category": payload.behavioral_category or "General",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Validation: Correct answer must match one of the options
    if doc["correct_answer"] not in doc["options"]:
        raise HTTPException(
            status_code=400,
            detail="Correct answer must match one of the four options exactly."
        )
        
    # Audio-specific TTS handling
    if category == "audio":
        if not payload.audio_transcript:
            raise HTTPException(
                status_code=400,
                detail="Audio transcript is required to generate audio MCQs."
            )
        doc["audio_transcript"] = payload.audio_transcript.strip()
        doc["audio_url"] = generate_tts_mp3(doc["audio_transcript"])
    # Media URL mappings
    elif category in ["image", "video"]:
        if not payload.media_url:
            raise HTTPException(
                status_code=400,
                detail=f"Media URL or uploaded file link is required for category '{category}'."
            )
        local_url = download_media_from_url(payload.media_url.strip())
        doc["image_url"] = local_url

    # Optional narration audio for image MCQs (not required — only generated if the
    # admin actually typed a transcript; bulk-imported scenario items always have one).
    if category == "image" and payload.audio_transcript:
        doc["audio_transcript"] = payload.audio_transcript.strip()
        doc["audio_url"] = generate_tts_mp3(doc["audio_transcript"])

    result = await db[collection_name].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return {"message": "MCQ created successfully", "id": doc["_id"]}


@router.put("/mcqs/{category}/{question_id}")
async def update_mcq(
    category: str, 
    question_id: str, 
    payload: MCQUpdate, 
    admin: dict = Depends(get_admin_user)
):
    """Update details of an existing MCQ in its collection."""
    db = get_database()
    cat = category.lower().strip()
    collection_name = COLLECTION_MAP.get(cat)
    
    if not collection_name:
        raise HTTPException(status_code=400, detail="Invalid MCQ category.")
        
    try:
        obj_id = ObjectId(question_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid MCQ ID format.")
        
    existing = await db[collection_name].find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="MCQ not found.")
        
    update_data = {}
    
    if payload.question is not None:
        update_data["question"] = payload.question.strip()
    if payload.options is not None:
        update_data["options"] = [opt.strip() for opt in payload.options]
    if payload.correct_answer is not None:
        update_data["correct_answer"] = payload.correct_answer.strip()
    if payload.difficulty is not None:
        update_data["difficulty"] = payload.difficulty
    if payload.behavioral_category is not None:
        update_data["behavioral_category"] = payload.behavioral_category
        
    # Validate correct answer in options
    opts = update_data.get("options", existing.get("options"))
    ans = update_data.get("correct_answer", existing.get("correct_answer"))
    if ans not in opts:
        raise HTTPException(
            status_code=400,
            detail="Correct answer must match one of the four options exactly."
        )
        
    # Audio transcript change check
    if cat == "audio":
        if payload.audio_transcript is not None:
            tx = payload.audio_transcript.strip()
            update_data["audio_transcript"] = tx
            # Regenerate TTS if transcript changed
            if tx != existing.get("audio_transcript"):
                update_data["audio_url"] = generate_tts_mp3(tx)
    elif cat in ["image", "video"]:
        if payload.media_url is not None:
            local_url = download_media_from_url(payload.media_url.strip())
            update_data["image_url"] = local_url

    # Optional narration audio for image MCQs
    if cat == "image" and payload.audio_transcript is not None:
        tx = payload.audio_transcript.strip()
        update_data["audio_transcript"] = tx
        if tx and tx != existing.get("audio_transcript"):
            update_data["audio_url"] = generate_tts_mp3(tx)

    if update_data:
        await db[collection_name].update_one({"_id": obj_id}, {"$set": update_data})
        
    return {"message": "MCQ updated successfully"}


@router.delete("/mcqs/{category}/{question_id}")
async def delete_mcq(
    category: str, 
    question_id: str, 
    admin: dict = Depends(get_admin_user)
):
    """Remove an MCQ question from MongoDB."""
    db = get_database()
    cat = category.lower().strip()
    collection_name = COLLECTION_MAP.get(cat)
    
    if not collection_name:
        raise HTTPException(status_code=400, detail="Invalid MCQ category.")
        
    try:
        obj_id = ObjectId(question_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid MCQ ID format.")
        
    result = await db[collection_name].delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="MCQ not found.")
        
    return {"message": "MCQ deleted successfully"}


@router.post("/upload")
async def upload_media_file(
    file: UploadFile = File(...), 
    admin: dict = Depends(get_admin_user)
):
    """Upload media file to the static/uploads/ folder."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in [".png", ".jpg", ".jpeg", ".gif", ".mp3", ".wav"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Supported: PNG, JPG, JPEG, GIF, MP3, WAV."
        )
        
    unique_filename = f"upload_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOADS_DIR, unique_filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    relative_url = f"/static/uploads/{unique_filename}"
    return {"media_url": relative_url}


async def _process_question_batch(db, questions: list, category: Optional[str]) -> dict:
    """
    Validate then insert one batch of question JSON items (i.e. the contents of a single
    uploaded file). All-or-nothing WITHIN this batch — if any row fails validation, nothing
    in this batch is inserted — but the caller may run multiple independent batches (one per
    uploaded file) so a bad file never blocks the others.

    Returns {"inserted": int, "errors": list[str] | None}.
    """
    # Pass 1: Strict validation of all rows.
    # Each item's JSON shape is auto-detected (legacy flat MCQ, question_item, or
    # scenario_image) and normalized before the same validation rules apply to all three.
    validated_docs = []
    errors = []

    for idx, q_data in enumerate(questions):
        source_format, detected_category, normalized = detect_and_normalize_bulk_item(q_data)

        if source_format is None:
            errors.append(
                f"Row {idx+1}: Unrecognized question format "
                f"(expected a flat MCQ, question_item, or scenario_image JSON shape)"
            )
            continue

        # Verify category query (the admin's active tab) matches the item's detected category
        if category and detected_category != category.lower().strip():
            errors.append(f"Row {idx+1}: Expected category '{category}' but detected '{detected_category}' from this item's JSON shape")
            continue

        collection_name = COLLECTION_MAP.get(detected_category)
        if not collection_name:
            errors.append(f"Row {idx+1}: Invalid category '{detected_category}'")
            continue

        question = normalized["question"]
        options = normalized["options"]
        correct_answer = normalized["correct_answer"]

        if not question or len(options) != 4 or not correct_answer:
            errors.append(f"Row {idx+1}: Missing question, options (must be 4), or correct_answer")
            continue

        if correct_answer not in options:
            errors.append(f"Row {idx+1}: Correct answer must match one of the options exactly.")
            continue

        doc = {
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
            "category": detected_category,
            "difficulty": normalized.get("difficulty") or "Easy",
            "behavioral_category": normalized.get("behavioral_category") or "General",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_format": source_format,
            "raw_json": q_data,
        }
        if normalized.get("stimulus_text"):
            doc["stimulus_text"] = normalized["stimulus_text"]

        transcript = normalized.get("audio_transcript") or ""

        if detected_category == "audio":
            if not transcript:
                errors.append(f"Row {idx+1}: Audio transcript is required for audio category.")
                continue
            doc["audio_transcript"] = transcript
        elif detected_category in ["image", "video"]:
            if source_format == "scenario_image":
                local_url = import_local_media_file(normalized.get("image_candidates") or [])
                if not local_url:
                    errors.append(
                        f"Row {idx+1}: Could not locate or copy the scenario's image file from disk "
                        f"(checked generated_image_asset.file_path and approved_media_files)."
                    )
                    continue
            else:
                media_url = str(normalized.get("media_url") or "").strip()
                if not media_url:
                    errors.append(f"Row {idx+1}: media_url is required for image/video categories.")
                    continue
                local_url = download_media_from_url(media_url)
                if not local_url or local_url.startswith("http://") or local_url.startswith("https://"):
                    errors.append(f"Row {idx+1}: Failed to download media content from '{media_url}' (URL may be broken, offline, or invalid)")
                    continue
            doc["image_url"] = local_url
            # Optional narration audio (only scenario_image items carry a transcript here)
            if transcript:
                doc["audio_transcript"] = transcript

        validated_docs.append((collection_name, doc))

    if errors:
        return {"inserted": 0, "errors": errors}

    # Pass 2: Insert in sequence since validation passed.
    # Any doc carrying a transcript gets narration TTS generated — covers legacy audio,
    # question_item Listening items, and scenario_image narration alike.
    inserted_count = 0
    for collection_name, doc in validated_docs:
        if doc.get("audio_transcript"):
            doc["audio_url"] = generate_tts_mp3(doc["audio_transcript"])
        await db[collection_name].insert_one(doc)
        inserted_count += 1

    return {"inserted": inserted_count, "errors": None}


@router.post("/mcqs/import")
async def import_bulk_mcqs(
    files: List[UploadFile] = File(...),
    category: Optional[str] = Query(None),
    admin: dict = Depends(get_admin_user)
):
    """
    Import MCQs from one or more JSON files. Each file is parsed, validated, and inserted
    completely independently of the others — one malformed or mismatched file never blocks
    the rest of the batch. Every file's outcome is reported separately in `results`.
    """
    db = get_database()
    results = []
    total_inserted = 0

    for f in files:
        try:
            contents = await f.read()
            parsed = json.loads(contents.decode("utf-8"))
        except Exception as e:
            results.append({"filename": f.filename, "imported": 0, "errors": [f"Failed to parse JSON file: {str(e)}"]})
            continue

        if not isinstance(parsed, list):
            if isinstance(parsed, dict):
                parsed = [parsed]
            else:
                results.append({"filename": f.filename, "imported": 0, "errors": ["JSON must be an object or an array of questions."]})
                continue

        outcome = await _process_question_batch(db, parsed, category)
        total_inserted += outcome["inserted"]
        results.append({"filename": f.filename, "imported": outcome["inserted"], "errors": outcome["errors"]})

    files_ok = sum(1 for r in results if r["imported"] > 0 and not r["errors"])
    return {
        "message": f"Processed {len(files)} file(s): {total_inserted} MCQ(s) imported ({files_ok}/{len(files)} file(s) fully succeeded).",
        "results": results,
    }


# ─── MEDIA REPAIR ENDPOINT ────────────────────────────────────

@router.post("/media/repair")
async def repair_broken_media(admin: dict = Depends(get_admin_user)):
    """
    Scans ALL MCQ collections for entries whose media URL is still an
    external HTTP link (meaning the original download failed or was skipped).
    Re-attempts the download using the improved robust downloader and updates
    the database with the locally-saved path.

    Returns a summary of how many entries were fixed vs still failing.
    """
    db = get_database()
    fixed = []
    still_failing = []
    skipped = 0

    # Only scan image and video collections.
    # Audio files are TTS-generated locally by the backend — they are NEVER
    # external URLs and must NEVER be re-downloaded.
    MEDIA_COLLECTIONS = {
        "image_mcqs": "image_url",
        "video_mcqs": "image_url",
    }

    for collection_name, field in MEDIA_COLLECTIONS.items():
        cursor = db[collection_name].find()
        docs = await cursor.to_list(length=500)

        for doc in docs:
            doc_id = doc["_id"]
            url = doc.get(field, "")

            if not url:
                skipped += 1
                continue

            # Skip if already a local path (download already succeeded before)
            if not url.startswith("http://") and not url.startswith("https://"):
                skipped += 1
                continue

            # Skip localhost URLs — they are server-generated paths, not external media
            if "localhost" in url or "127.0.0.1" in url:
                skipped += 1
                continue

            print(f"[REPAIR] {collection_name}/{doc_id} → {url[:80]}")
            new_path = download_media_from_url(url)
            if new_path and not new_path.startswith("http"):
                await db[collection_name].update_one(
                    {"_id": doc_id},
                    {"$set": {field: new_path}}
                )
                fixed.append({
                    "collection": collection_name,
                    "id": str(doc_id),
                    "field": field,
                    "original_url": url[:100],
                    "saved_as": new_path,
                })
            else:
                # Delete the MCQ since its content cannot be fetched (broken link)
                await db[collection_name].delete_one({"_id": doc_id})
                still_failing.append({
                    "collection": collection_name,
                    "id": str(doc_id),
                    "field": field,
                    "url": url[:100],
                    "status": "Deleted (broken/dead link)"
                })

    return {
        "message": f"Repair complete. Fixed: {len(fixed)}, Still failing: {len(still_failing)}, Skipped (already local or audio): {skipped}",
        "fixed": fixed,
        "still_failing": still_failing,
    }


# ─── DRIVER ASSESSMENT RESULTS LOG ENDPOINTS ─────────────────

@router.get("/results")
async def get_all_driver_results(admin: dict = Depends(get_admin_user)):
    """Fetch all submitted driver test results, sorted by date."""
    db = get_database()
    cursor = db.results.find().sort("submitted_at", -1)
    docs = await cursor.to_list(length=500)
    
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        
    return docs


@router.delete("/results/{result_id}")
async def delete_driver_result(result_id: str, admin: dict = Depends(get_admin_user)):
    """Delete a driver assessment result from history."""
    db = get_database()
    try:
        obj_id = ObjectId(result_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid result ID format.")
        
    result = await db.results.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Result log not found.")
        
    return {"message": "Driver result log deleted successfully"}


# ─── USER PRIVILEGES MANAGEMENT ENDPOINTS ─────────────────────

@router.get("/users")
async def list_users(admin: dict = Depends(get_admin_user)):
    """Fetch all users to manage privileges."""
    db = get_database()
    cursor = db.users.find()
    users = await cursor.to_list(length=1000)
    
    formatted_users = []
    for u in users:
        formatted_users.append({
            "id": str(u["_id"]),
            "full_name": u.get("full_name", ""),
            "email": u.get("email", ""),
            "role": u.get("role", "driver")
        })
    return formatted_users


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    payload: UpdateUserRoleRequest,
    admin: dict = Depends(get_admin_user)
):
    """Change a user's role (promote/demote)."""
    db = get_database()
    
    # Do not allow demoting oneself
    if str(admin["_id"]) == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot change your own admin role."
        )
        
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid User ID format.")
        
    target_role = payload.role.lower().strip()
    if target_role not in ["admin", "driver"]:
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'driver'.")
        
    result = await db.users.update_one(
        {"_id": obj_id},
        {"$set": {"role": target_role}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
        
    return {"message": f"User role updated to '{target_role}' successfully."}


@router.post("/users/create-admin")
async def create_new_admin(
    payload: CreateAdminRequest,
    admin: dict = Depends(get_admin_user)
):
    """Directly register a new administrator account."""
    db = get_database()
    email_clean = payload.email.lower().strip()
    
    existing = await db.users.find_one({"email": email_clean})
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="A user with this email already exists. You can promote them in the user list."
        )
        
    import secrets
    password_hash = hashlib.sha256(payload.password.encode()).hexdigest()
    
    user_doc = {
        "full_name": payload.full_name.strip(),
        "email": email_clean,
        "password_hash": password_hash,
        "role": "admin",
        "token": secrets.token_hex(32)
    }
    
    await db.users.insert_one(user_doc)
    return {"message": f"Admin account for '{payload.full_name}' created successfully."}


class DriverResultUpdateRequest(BaseModel):
    total_score: int
    total_questions: int
    overall_percentage: float
    risk_level: str
    is_eligible_12hr: bool
    recommendation: Optional[str] = None


@router.put("/results/{result_id}")
async def update_driver_result(
    result_id: str,
    payload: DriverResultUpdateRequest,
    admin: dict = Depends(get_admin_user)
):
    """Update a driver assessment result (manually edit marks)."""
    db = get_database()
    try:
        obj_id = ObjectId(result_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid result ID format.")
        
    update_data = {
        "total_score": payload.total_score,
        "total_questions": payload.total_questions,
        "overall_percentage": payload.overall_percentage,
        "risk_level": payload.risk_level.strip(),
        "is_eligible_12hr": payload.is_eligible_12hr,
    }
    if payload.recommendation is not None:
        update_data["recommendation"] = payload.recommendation.strip()
        
    result = await db.results.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Result log not found.")
        
    return {"message": "Driver assessment marks updated successfully."}
