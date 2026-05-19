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
        "question": "What unsafe behavior do you observe, and what should the driver do to correct it?",
        "options": [
            "The driver is navigating safely; no action needed",
            "The driver is distracted by texting; they must put the phone away immediately and focus entirely on the road",
            "Using a phone in slow traffic is acceptable if the driver glances up frequently",
            "The driver should hold the phone higher so they can see both the screen and road"
        ],
        "correct_answer": "The driver is distracted by texting; they must put the phone away immediately and focus entirely on the road",
        "image_url": f"{BACKEND_URL}/static/videos/video_q1.mp4",
        "video_description": "Driver is texting on a mobile phone while driving in busy traffic, eyes repeatedly leaving the road.",
        "difficulty": "Medium",
        "behavioral_category": "Safety Awareness"
    },
    {
        "category": "video",
        "question": "What critical risk is shown and what is the safest professional response?",
        "options": [
            "The driver is well-rested and alert; continue driving normally",
            "The driver is showing signs of severe fatigue; they must immediately pull over to a safe location and rest before continuing",
            "Yawning is normal; the driver should open a window and keep driving",
            "The driver should drink an energy drink and increase speed to reach the destination faster"
        ],
        "correct_answer": "The driver is showing signs of severe fatigue; they must immediately pull over to a safe location and rest before continuing",
        "image_url": f"{BACKEND_URL}/static/videos/video_q2.mp4",
        "video_description": "Driver yawning repeatedly with heavy eyelids closing while driving at night, struggling to stay awake.",
        "difficulty": "Easy",
        "behavioral_category": "Fatigue Monitoring"
    },
    {
        "category": "video",
        "question": "What is the correct emergency response in this situation?",
        "options": [
            "Sound the horn continuously to warn the child and maintain current speed",
            "Apply emergency brakes firmly and immediately, grip the steering wheel tightly, and check mirrors before swerving",
            "Swerve sharply into the opposite lane without checking for oncoming traffic",
            "Flash headlights and accelerate to pass before the child fully enters the lane"
        ],
        "correct_answer": "Apply emergency brakes firmly and immediately, grip the steering wheel tightly, and check mirrors before swerving",
        "image_url": f"{BACKEND_URL}/static/videos/video_q3.mp4",
        "video_description": "A child suddenly dashes across the road from between parked cars, directly in front of the moving vehicle.",
        "difficulty": "Hard",
        "behavioral_category": "Emergency Handling"
    },
    {
        "category": "video",
        "question": "How should a professional driver handle this passenger situation?",
        "options": [
            "Shout back at the passenger to assert control of the situation",
            "Stay completely calm, speak in a respectful tone, and if the situation escalates pull over safely and request the passenger to exit",
            "Ignore the passenger entirely and drive aggressively to end the trip quickly",
            "Stop the vehicle immediately in the middle of the road and refuse to continue"
        ],
        "correct_answer": "Stay completely calm, speak in a respectful tone, and if the situation escalates pull over safely and request the passenger to exit",
        "image_url": f"{BACKEND_URL}/static/videos/video_q4.mp4",
        "video_description": "An aggressive passenger in the backseat is shouting angrily at the driver, gesturing aggressively about the fare or route.",
        "difficulty": "Medium",
        "behavioral_category": "Emotional Stability"
    },
    {
        "category": "video",
        "question": "What is the safest driving strategy in these dangerous weather conditions?",
        "options": [
            "Increase speed to get through the rain quickly and reduce exposure time",
            "Reduce speed significantly, increase following distance, turn on low-beam headlights and wipers, and avoid sudden braking or lane changes",
            "Drive close behind the vehicle ahead to use their tire tracks for better grip",
            "Turn off all lights to reduce glare and maintain normal cruising speed"
        ],
        "correct_answer": "Reduce speed significantly, increase following distance, turn on low-beam headlights and wipers, and avoid sudden braking or lane changes",
        "image_url": f"{BACKEND_URL}/static/videos/video_q5.mp4",
        "video_description": "Heavy rainstorm with extremely low visibility and slippery road surface, the driver struggles to maintain control.",
        "difficulty": "Medium",
        "behavioral_category": "Hazard Awareness"
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
