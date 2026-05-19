"""
Seed script — generates audio files from text using gTTS and populates MongoDB
with all 15 sample MCQs (5 text, 5 audio, 5 image).

Run once:  python seed.py
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from gtts import gTTS

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "quizDB")
BACKEND_URL = "http://localhost:8000"

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


# ─────────────────────── AUDIO GENERATION ────────────────────────
def generate_audio_files():
    """Generate MP3 audio files for all audio-based MCQs using gTTS."""
    audio_questions = {
        "audio_q1": "You are driving and the fog is very heavy ahead. What should you do?",
        "audio_q2": "There is an emergency vehicle coming behind you with sirens on. What should you do?",
        "audio_q3": "Your passenger suddenly feels sick and looks very unwell. What should you do?",
        "audio_q4": "You have been driving continuously for 10 hours and you feel very tired. What should you do?",
        "audio_q5": "The road ahead is very slippery due to heavy rain. What should you do?",
    }

    for filename, text in audio_questions.items():
        filepath = os.path.join(AUDIO_DIR, f"{filename}.mp3")
        if os.path.exists(filepath):
            print(f"  [SKIP] Audio already exists: {filename}.mp3")
            continue
        print(f"  [GEN] Generating audio: {filename}.mp3 ...")
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(filepath)
        print(f"  [OK] Saved: {filepath}")

    print("\n[AUDIO] All audio files generated!\n")


# ─────────────────────── MCQ DATA ────────────────────────────────
TEXT_MCQS = [
    {
        "question": "A passenger is angry and shouting at you. What should the driver do?",
        "options": [
            "Shout back at the passenger",
            "Stay calm and professional",
            "Stop the car and leave",
            "Ignore the passenger completely",
        ],
        "correct_answer": "Stay calm and professional",
        "category": "text",
    },
    {
        "question": "The road ahead is blocked due to a serious accident. What is the best action?",
        "options": [
            "Wait indefinitely at the scene",
            "Drive through the accident area",
            "Take an alternative safe route",
            "Honk continuously",
        ],
        "correct_answer": "Take an alternative safe route",
        "category": "text",
    },
    {
        "question": "A passenger forgets their phone in your taxi. What should the driver do?",
        "options": [
            "Keep the phone for yourself",
            "Throw it away",
            "Return the item safely",
            "Sell the phone",
        ],
        "correct_answer": "Return the item safely",
        "category": "text",
    },
    {
        "question": "A child suddenly crosses the road while you are driving. What should the driver do?",
        "options": [
            "Speed up to pass quickly",
            "Honk loudly and keep driving",
            "Stop immediately",
            "Swerve into oncoming traffic",
        ],
        "correct_answer": "Stop immediately",
        "category": "text",
    },
    {
        "question": "A passenger asks you to break traffic rules to reach faster. The driver should:",
        "options": [
            "Follow the passenger's instructions",
            "Politely refuse",
            "Drive faster without telling them",
            "Argue with the passenger",
        ],
        "correct_answer": "Politely refuse",
        "category": "text",
    },
]

AUDIO_MCQS = [
    {
        "question": "You are driving and the fog is very heavy ahead. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q1.mp3",
        "options": [
            "Speed up to get through quickly",
            "Drive slowly with lights on",
            "Turn off all lights",
            "Stop in the middle of the road",
        ],
        "correct_answer": "Drive slowly with lights on",
        "category": "audio",
    },
    {
        "question": "There is an emergency vehicle coming behind you with sirens on. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q2.mp3",
        "options": [
            "Speed up to stay ahead",
            "Ignore it",
            "Give way immediately",
            "Honk back at them",
        ],
        "correct_answer": "Give way immediately",
        "category": "audio",
    },
    {
        "question": "Your passenger suddenly feels sick and looks very unwell. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q3.mp3",
        "options": [
            "Drive faster to the destination",
            "Drive slowly and carefully",
            "Ask the passenger to leave",
            "Ignore the situation",
        ],
        "correct_answer": "Drive slowly and carefully",
        "category": "audio",
    },
    {
        "question": "You have been driving continuously for 10 hours and you feel very tired. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q4.mp3",
        "options": [
            "Continue driving",
            "Drink coffee and keep going",
            "Take rest",
            "Drive faster to finish soon",
        ],
        "correct_answer": "Take rest",
        "category": "audio",
    },
    {
        "question": "The road ahead is very slippery due to heavy rain. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q5.mp3",
        "options": [
            "Drive at full speed",
            "Drive carefully",
            "Stop on the highway",
            "Turn off wipers",
        ],
        "correct_answer": "Drive carefully",
        "category": "audio",
    },
]

IMAGE_MCQS = [
    {
        "question": "Look at the image. An angry passenger is in your taxi. What is the best response?",
        "image_url": f"{BACKEND_URL}/static/images/angry_passenger.png",
        "options": [
            "Shout back",
            "Stay calm",
            "Leave the vehicle",
            "Call the police immediately",
        ],
        "correct_answer": "Stay calm",
        "category": "image",
    },
    {
        "question": "You see this accident scene ahead. What should you do?",
        "image_url": f"{BACKEND_URL}/static/images/accident_scene.png",
        "options": [
            "Drive past quickly",
            "Take photos for social media",
            "Call emergency help",
            "Ignore the scene",
        ],
        "correct_answer": "Call emergency help",
        "category": "image",
    },
    {
        "question": "Look at this driver. He appears very tired. What should he do?",
        "image_url": f"{BACKEND_URL}/static/images/tired_driver.png",
        "options": [
            "Continue driving",
            "Drink energy drinks",
            "Stop and rest",
            "Drive faster to finish",
        ],
        "correct_answer": "Stop and rest",
        "category": "image",
    },
    {
        "question": "You are stuck in this heavy traffic. What is the best response?",
        "image_url": f"{BACKEND_URL}/static/images/traffic_jam_stress.png",
        "options": [
            "Honk aggressively",
            "Drive on sidewalk",
            "Stay patient",
            "Yell at other drivers",
        ],
        "correct_answer": "Stay patient",
        "category": "image",
    },
    {
        "question": "Your passenger is crying and upset. How should you respond?",
        "image_url": f"{BACKEND_URL}/static/images/crying_passenger.png",
        "options": [
            "Ignore completely",
            "Offer help politely",
            "Ask them to leave",
            "Play loud music",
        ],
        "correct_answer": "Offer help politely",
        "category": "image",
    },
]

VIDEO_MCQS = [
    {
        "category": "video",
        "question": "What dangerous behavior is shown in this video scenario, and how should a professional driver manage it?",
        "options": [
            "A. Sending a fast text since traffic is moving slowly",
            "B. Distracted driving due to mobile usage; pull over to a safe spot if checking navigation is urgent",
            "C. Proper seatbelt usage and driving technique",
            "D. Keep phone held in hand for immediate warning signals"
        ],
        "correct_answer": "B. Distracted driving due to mobile usage; pull over to a safe spot if checking navigation is urgent",
        "image_url": f"{BACKEND_URL}/static/videos/video_q1.mp4",
        "video_description": "The taxi driver is checking navigation and sending a quick message on a mobile phone while cruising down a busy urban street.",
        "difficulty": "Medium",
        "behavioral_category": "Safety Awareness"
    },
    {
        "category": "video",
        "question": "What should the driver do immediately when a pedestrian unexpectedly enters the active driving lane?",
        "options": [
            "A. Speed up to quickly clear the crossing space",
            "B. Apply brakes immediately and safely while keeping a firm grip on the steering wheel",
            "C. Sound the horn loudly and continue driving at normal speed",
            "D. Swerve immediately into the opposite lane to bypass the child"
        ],
        "correct_answer": "B. Apply brakes immediately and safely while keeping a firm grip on the steering wheel",
        "image_url": f"{BACKEND_URL}/static/videos/video_q2.mp4",
        "video_description": "A child suddenly runs out from between parked vehicles to cross the street without checking traffic.",
        "difficulty": "Hard",
        "behavioral_category": "Emergency Handling"
    },
    {
        "category": "video",
        "question": "What is the most professional behavioral response when dealing with an aggressive or shouting passenger?",
        "options": [
            "A. Shout back at the passenger to establish authority",
            "B. Stay calm, speak in a polite tone, and pull over safely if safety is compromised",
            "C. Stop the vehicle in the middle of traffic and refuse to move",
            "D. Ignore the passenger completely and drive at high speed"
        ],
        "correct_answer": "B. Stay calm, speak in a polite tone, and pull over safely if safety is compromised",
        "image_url": f"{BACKEND_URL}/static/videos/video_q3.mp4",
        "video_description": "An upset passenger in the backseat starts speaking loudly and shouting aggressively at the driver about the route choice.",
        "difficulty": "Medium",
        "behavioral_category": "Passenger Management"
    },
    {
        "category": "video",
        "question": "What is the safest tactical driving action during heavy rain or slippery road conditions?",
        "options": [
            "A. Speed up to reach the destination quickly before road flooding worsens",
            "B. Reduce speed, double the following distance, and keep low-beam headlights on",
            "C. Maintain speed and tail the car in front closely to follow its track",
            "D. Turn off lights to avoid glare and keep standard speed"
        ],
        "correct_answer": "B. Reduce speed, double the following distance, and keep low-beam headlights on",
        "image_url": f"{BACKEND_URL}/static/videos/video_q4.mp4",
        "video_description": "Heavy torrential rain is pouring down on the road, severely reducing visibility and road traction.",
        "difficulty": "Easy",
        "behavioral_category": "Traffic Compliance"
    },
    {
        "category": "video",
        "question": "What primary risk is demonstrated in this scene, and what is the best professional response?",
        "options": [
            "A. Driver fatigue risk; stop at the nearest safe rest area to rest and recover",
            "B. Standard boredom; drink coffee while maintaining driving speed",
            "C. Normal night driving alertness",
            "D. Turn on loud music to prevent yawning"
        ],
        "correct_answer": "A. Driver fatigue risk; stop at the nearest safe rest area to rest and recover",
        "image_url": f"{BACKEND_URL}/static/videos/video_q5.mp4",
        "video_description": "The driver looks highly fatigued, rubbing eyes and yawning heavily while driving in the late evening.",
        "difficulty": "Easy",
        "behavioral_category": "Fatigue Monitoring"
    }
]


# ─────────────────────── DATABASE SEEDING ────────────────────────
async def seed_database():
    """Clear existing MCQs and insert fresh sample data."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]

    print("[DB] Clearing existing MCQ collections...")
    await db.text_mcqs.delete_many({})
    await db.audio_mcqs.delete_many({})
    await db.image_mcqs.delete_many({})
    await db.video_mcqs.delete_many({})

    print("[DB] Inserting text MCQs...")
    result = await db.text_mcqs.insert_many(TEXT_MCQS)
    print(f"   [OK] Inserted {len(result.inserted_ids)} text MCQs")

    print("[DB] Inserting audio MCQs...")
    result = await db.audio_mcqs.insert_many(AUDIO_MCQS)
    print(f"   [OK] Inserted {len(result.inserted_ids)} audio MCQs")

    print("[DB] Inserting image MCQs...")
    result = await db.image_mcqs.insert_many(IMAGE_MCQS)
    print(f"   [OK] Inserted {len(result.inserted_ids)} image MCQs")

    print("[DB] Inserting video MCQs...")
    result = await db.video_mcqs.insert_many(VIDEO_MCQS)
    print(f"   [OK] Inserted {len(result.inserted_ids)} video MCQs")

    print("\n[DB] Database seeded successfully!")
    print(f"   Total MCQs: {len(TEXT_MCQS) + len(AUDIO_MCQS) + len(IMAGE_MCQS) + len(VIDEO_MCQS)}")

    client.close()


# ─────────────────────── MAIN ────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  [DRIVEIQ] AntiGravity -- Database Seed Script")
    print("=" * 55)
    print()

    print("Step 1: Generating audio files...")
    generate_audio_files()

    print("Step 2: Seeding MongoDB...")
    asyncio.run(seed_database())

    print()
    print("=" * 55)
    print("  [OK] Seeding complete! Start the server with:")
    print("     uvicorn main:app --reload --port 8000")
    print("=" * 55)
