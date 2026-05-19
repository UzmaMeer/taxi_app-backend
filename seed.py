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
            "Sending a fast text since traffic is moving slowly",
            "Distracted driving due to mobile usage; pull over to a safe spot if checking navigation is urgent",
            "Proper seatbelt usage and driving technique",
            "Keep phone held in hand for immediate warning signals"
        ],
        "correct_answer": "Distracted driving due to mobile usage; pull over to a safe spot if checking navigation is urgent",
        "image_url": f"{BACKEND_URL}/static/videos/video_q1.mp4",
        "video_description": "The taxi driver is checking navigation and sending a quick message on a mobile phone while cruising down a busy urban street.",
        "difficulty": "Medium",
        "behavioral_category": "Safety Awareness"
    },
    {
        "category": "video",
        "question": "What is the correct emergency response when a passenger experiences a sudden serious illness or medical emergency?",
        "options": [
            "Continue driving to original destination to avoid losing fare progress",
            "Safely pull over immediately, turn on hazard lights, check on the passenger, and call emergency services (911/ambulance)",
            "Hand the passenger a water bottle and tell them to wait until the trip ends",
            "Drive as fast as possible through traffic signals directly to the nearest hospital"
        ],
        "correct_answer": "Safely pull over immediately, turn on hazard lights, check on the passenger, and call emergency services (911/ambulance)",
        "image_url": f"{BACKEND_URL}/static/videos/video_q3.mp4",
        "video_description": "An elderly passenger suddenly clutches their chest, breathing heavily, and exhibits signs of a sudden medical emergency in the backseat of the vehicle.",
        "difficulty": "Hard",
        "behavioral_category": "Emergency Handling"
    },
    {
        "category": "video",
        "question": "How should a professional driver respond when an emergency vehicle (ambulance/fire truck) with active sirens is approaching behind them?",
        "options": [
            "Speed up and try to stay ahead of the emergency vehicle to clear the lane",
            "Safely yield, move to the left or right edge of the road, and come to a complete stop to let it pass safely",
            "Maintain your current speed and lane to avoid causing traffic congestion",
            "Stop immediately in the middle of your active lane"
        ],
        "correct_answer": "Safely yield, move to the left or right edge of the road, and come to a complete stop to let it pass safely",
        "image_url": f"{BACKEND_URL}/static/videos/video_q2.mp4",
        "video_description": "An emergency ambulance with flashing lights and sirens is approaching rapidly from behind in heavy traffic.",
        "difficulty": "Medium",
        "behavioral_category": "Traffic Compliance"
    },
    {
        "category": "video",
        "question": "What is the safest tactical driving action during heavy rain or slippery road conditions?",
        "options": [
            "Speed up to reach the destination quickly before road flooding worsens",
            "Reduce speed, double the following distance, and keep low-beam headlights on",
            "Maintain speed and tail the car in front closely to follow its track",
            "Turn off lights to avoid glare and keep standard speed"
        ],
        "correct_answer": "Reduce speed, double the following distance, and keep low-beam headlights on",
        "image_url": f"{BACKEND_URL}/static/videos/video_q4.mp4",
        "video_description": "Heavy torrential rain is pouring down on the road, severely reducing visibility and road traction.",
        "difficulty": "Easy",
        "behavioral_category": "Traffic Compliance"
    },
    {
        "category": "video",
        "question": "What is the best professional response when faced with aggressive road rage or close tailgating from another driver?",
        "options": [
            "Tap your brakes suddenly to warn them to back off",
            "Stay calm, avoid eye contact, maintain a safe speed, and allow them to pass safely at the earliest opportunity",
            "Gesture back angrily and block them from overtaking you",
            "Accelerate rapidly to match their speed and keep distance"
        ],
        "correct_answer": "Stay calm, avoid eye contact, maintain a safe speed, and allow them to pass safely at the earliest opportunity",
        "image_url": f"{BACKEND_URL}/static/videos/video_q5.mp4",
        "video_description": "Another aggressive driver behind you is tailgating closely, flashing headlights, and expressing intense road rage.",
        "difficulty": "Medium",
        "behavioral_category": "Aggression Control"
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
