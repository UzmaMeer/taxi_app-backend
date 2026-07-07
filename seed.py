"""
Seed script — generates audio files from text using gTTS and populates MongoDB
with all 40 sample MCQs (10 text, 10 audio, 10 image, 10 video).

Run once:  python seed.py
"""
import os
import asyncio
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from gtts import gTTS

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "quizDB")
BACKEND_URL = "http://localhost:8000"

import urllib.request
import urllib.parse
import uuid

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

def download_seed_media(url: str) -> str:
    """
    Downloads media from an external URL, saves it to UPLOADS_DIR, and returns local relative path.
    If it's already a local path, returns it as is.
    """
    if not url:
        return ""
    if not url.startswith("http://") and not url.startswith("https://"):
        return url
    if "localhost" in url or "127.0.0.1" in url:
        return url
        
    try:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        print(f"  [DOWNLOAD] Fetching external media: {url} ...")
        # Set User-Agent to prevent HTTP 403 Forbidden blocks
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read()
            content_type = response.headers.get('Content-Type', '').lower()
            
            ext = None
            if "image/gif" in content_type:
                ext = ".gif"
            elif "image/png" in content_type:
                ext = ".png"
            elif "image/jpeg" in content_type or "image/jpg" in content_type:
                ext = ".jpg"
            elif "video/mp4" in content_type:
                ext = ".mp4"
            else:
                parsed_url = urllib.parse.urlparse(url)
                path = parsed_url.path
                _, ext = os.path.splitext(path)
                ext = ext.lower()
                
            if not ext or ext not in [".gif", ".png", ".jpg", ".jpeg", ".mp4"]:
                ext = ".gif" if ".gif" in url.lower() else ".png"
                
            filename = f"seed_{uuid.uuid4().hex}{ext}"
            filepath = os.path.join(UPLOADS_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(content)
            print(f"  [OK] Saved to: static/uploads/{filename}")
            return f"{BACKEND_URL}/static/uploads/{filename}"
    except Exception as e:
        print(f"  [ERROR] Failed to download {url}: {e}")
        return url

# ─────────────────────── AUDIO GENERATION ────────────────────────
def generate_audio_files():
    """Generate MP3 audio files for all audio-based MCQs using gTTS."""
    audio_questions = {
        "audio_q1": "You are driving and the fog is very heavy ahead. What should you do?",
        "audio_q2": "There is an emergency vehicle coming behind you with sirens on. What should you do?",
        "audio_q3": "Your passenger suddenly feels sick and looks very unwell. What should you do?",
        "audio_q4": "You have been driving continuously for 10 hours and you feel very tired. What should you do?",
        "audio_q5": "The road ahead is very slippery due to heavy rain. What should you do?",
        "audio_q6": "Alert to all drivers: Heavy ice is accumulating on the northern bypass. Expect slick roads and reduced control.",
        "audio_q7": "Warning: Brake fluid pressure is low. Stopping distance may be severely affected.",
        "audio_q8": "Driver, please speed up and run this orange light! I am very late for my flight!",
        "audio_q9": "High wind warnings are in effect for the harbor bridge. Vehicles are advised to seek alternate routes.",
        "audio_q10": "Excuse me, driver, I feel very nauseous and need to get some fresh air.",
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
        "difficulty": "Easy",
        "behavioral_category": "Emotional Stability"
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
        "difficulty": "Medium",
        "behavioral_category": "Safety Awareness"
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
        "difficulty": "Easy",
        "behavioral_category": "Professional Ethics"
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
        "difficulty": "Hard",
        "behavioral_category": "Hazard Reactivity"
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
        "difficulty": "Medium",
        "behavioral_category": "Conflict Resolution"
    },
    {
        "question": "Scenario: You notice the engine temperature gauge rising close to the red zone while on a busy street. What is the safest course of action?",
        "options": [
            "Speed up to reach your destination faster before the engine overheats",
            "Safely pull over to the side, turn off the engine, and wait for it to cool down",
            "Keep driving with the air conditioning set to maximum to cool the vehicle",
            "Ignore it as temporary gauge fluctuation and report it at the end of your shift"
        ],
        "correct_answer": "Safely pull over to the side, turn off the engine, and wait for it to cool down",
        "difficulty": "Easy",
        "behavioral_category": "Safety Awareness"
    },
    {
        "question": "Scenario: A passenger requests that you take a route that goes through a clearly marked flooded underpass. What is the correct response?",
        "options": [
            "Agree to their request immediately to keep the passenger happy",
            "Drive through slowly and test the depth of the water with your front bumper",
            "Politely decline the route, explaining the safety risk of high water, and suggest a dry detour",
            "Accelerate through the water quickly to minimize exposure time"
        ],
        "correct_answer": "Politely decline the route, explaining the safety risk of high water, and suggest a dry detour",
        "difficulty": "Medium",
        "behavioral_category": "Risk Management"
    },
    {
        "question": "Scenario: You are driving in heavy fog with visibility below 50 meters. Which lights should you use?",
        "options": [
            "High-beam headlights to pierce through the thick fog",
            "Low-beam headlights and fog lights, while reducing your driving speed",
            "Hazard warning lights only while continuing to drive at the speed limit",
            "No lights at all to avoid causing glare for oncoming drivers"
        ],
        "correct_answer": "Low-beam headlights and fog lights, while reducing your driving speed",
        "difficulty": "Medium",
        "behavioral_category": "Hazard Reactivity"
    },
    {
        "question": "Scenario: A passenger realizes they left their smartphone in your taxi after you dropped them off, and calls your phone. What should you do?",
        "options": [
            "Keep the smartphone as a tip for your service",
            "Agree to meet them at a safe public location or return it through your taxi company coordinator",
            "Throw the phone away to avoid tracking or passenger disputes",
            "Demand a high cash ransom before agreeing to return the device"
        ],
        "correct_answer": "Agree to meet them at a safe public location or return it through your taxi company coordinator",
        "difficulty": "Easy",
        "behavioral_category": "Professional Ethics"
    },
    {
        "question": "Scenario: You are on a multi-lane highway and miss your passenger's requested exit. How should you correct this?",
        "options": [
            "Shift to reverse gear and back up along the highway shoulder safely",
            "Make a sudden U-turn across the grassy median to reach the opposite lane",
            "Continue driving to the next exit, safely exit, and navigate back to the destination",
            "Stop in the active lane and wait for GPS to calculate a redirection route"
        ],
        "correct_answer": "Continue driving to the next exit, safely exit, and navigate back to the destination",
        "difficulty": "Easy",
        "behavioral_category": "Cognitive Decisions"
    }
]

AUDIO_MCQS = [
    {
        "question": "You are driving and the fog is very heavy ahead. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q1.mp3",
        "audio_transcript": "You are driving and the fog is very heavy ahead. What should you do?",
        "options": [
            "Speed up to get through quickly",
            "Drive slowly with lights on",
            "Turn off all lights",
            "Stop in the middle of the road",
        ],
        "correct_answer": "Drive slowly with lights on",
        "category": "audio",
        "difficulty": "Medium",
        "behavioral_category": "Hazard Reactivity"
    },
    {
        "question": "There is an emergency vehicle coming behind you with sirens on. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q2.mp3",
        "audio_transcript": "There is an emergency vehicle coming behind you with sirens on. What should you do?",
        "options": [
            "Speed up to stay ahead",
            "Ignore it",
            "Give way immediately",
            "Honk back at them",
        ],
        "correct_answer": "Give way immediately",
        "category": "audio",
        "difficulty": "Easy",
        "behavioral_category": "Safety Awareness"
    },
    {
        "question": "Your passenger suddenly feels sick and looks very unwell. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q3.mp3",
        "audio_transcript": "Your passenger suddenly feels sick and looks very unwell. What should you do?",
        "options": [
            "Drive faster to the destination",
            "Drive slowly and carefully",
            "Ask the passenger to leave",
            "Ignore the situation",
        ],
        "correct_answer": "Drive slowly and carefully",
        "category": "audio",
        "difficulty": "Medium",
        "behavioral_category": "Conflict Resolution"
    },
    {
        "question": "You have been driving continuously for 10 hours and you feel very tired. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q4.mp3",
        "audio_transcript": "You have been driving continuously for 10 hours and you feel very tired. What should you do?",
        "options": [
            "Continue driving",
            "Drink coffee and keep going",
            "Take rest",
            "Drive faster to finish soon",
        ],
        "correct_answer": "Take rest",
        "category": "audio",
        "difficulty": "Hard",
        "behavioral_category": "Fatigue Control"
    },
    {
        "question": "The road ahead is very slippery due to heavy rain. What should you do?",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q5.mp3",
        "audio_transcript": "The road ahead is very slippery due to heavy rain. What should you do?",
        "options": [
            "Drive at full speed",
            "Drive carefully",
            "Stop on the highway",
            "Turn off wipers",
        ],
        "correct_answer": "Drive carefully",
        "category": "audio",
        "difficulty": "Medium",
        "behavioral_category": "Hazard Reactivity"
    },
    {
        "question": "Listen to the dispatcher notification and choose the safest response.",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q6.mp3",
        "audio_transcript": "Alert to all drivers: Heavy ice is accumulating on the northern bypass. Expect slick roads and reduced control.",
        "options": [
            "Drive on the bypass anyway but accelerate to clear it quickly",
            "Decline northern bypass routes, choose a safer alternative road, and reduce driving speed",
            "Keep your speed constant and rely on the vehicle's traction control system",
            "Slam on your brakes if you feel the vehicle begin to slide on the ice"
        ],
        "correct_answer": "Decline northern bypass routes, choose a safer alternative road, and reduce driving speed",
        "category": "audio",
        "difficulty": "Medium",
        "behavioral_category": "Risk Appraisal"
    },
    {
        "question": "Listen to the engine diagnostic voice system warning and choose the correct safety response.",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q7.mp3",
        "audio_transcript": "Warning: Brake fluid pressure is low. Stopping distance may be severely affected.",
        "options": [
            "Ignore the warning if the brake pedal still feels normal to press",
            "Safely pull over to the side, stop, and call for roadside assistance immediately",
            "Drive slowly to a workshop while pump-pressing the brakes repeatedly",
            "Use only the handbrake for all subsequent stops during your shift"
        ],
        "correct_answer": "Safely pull over to the side, stop, and call for roadside assistance immediately",
        "category": "audio",
        "difficulty": "Hard",
        "behavioral_category": "Safety Awareness"
    },
    {
        "question": "Listen to the passenger's request and choose the most professional response.",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q8.mp3",
        "audio_transcript": "Driver, please speed up and run this orange light! I am very late for my flight!",
        "options": [
            "Accelerate immediately to please the passenger and run the light",
            "Explain politely that you must adhere to traffic laws and safety speed limits for a safe trip",
            "Argue loudly with the passenger about the danger of red light running",
            "Slam on your brakes suddenly to demonstrate the danger of high speed"
        ],
        "correct_answer": "Explain politely that you must adhere to traffic laws and safety speed limits for a safe trip",
        "category": "audio",
        "difficulty": "Easy",
        "behavioral_category": "Conflict Resolution"
    },
    {
        "question": "Listen to the weather forecast radio alert and select the appropriate driving adjustment.",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q9.mp3",
        "audio_transcript": "High wind warnings are in effect for the harbor bridge. Vehicles are advised to seek alternate routes.",
        "options": [
            "Drive across the bridge at high speed to minimize exposure to wind gusts",
            "Avoid the harbor bridge, choose a sheltered inland route, and keep two hands on the wheel",
            "Drive with hazard lights on at normal speeds across the harbor bridge",
            "Tailgate a large semi-truck to let it block the wind gusts for you"
        ],
        "correct_answer": "Avoid the harbor bridge, choose a sheltered inland route, and keep two hands on the wheel",
        "category": "audio",
        "difficulty": "Medium",
        "behavioral_category": "Hazard Reactivity"
    },
    {
        "question": "Listen to the passenger's nervous statement and choose the most reassuring response.",
        "audio_url": f"{BACKEND_URL}/static/audio/audio_q10.mp3",
        "audio_transcript": "Excuse me, driver, I feel very nauseous and need to get some fresh air.",
        "options": [
            "Tell them to hold it in until the trip ends in 20 minutes",
            "Safely pull over at the next safe spot, roll down the windows, and offer them assistance",
            "Increase the speed of the taxi to reach the destination faster",
            "Tell them that stopping is not allowed on your schedule"
        ],
        "correct_answer": "Safely pull over at the next safe spot, roll down the windows, and offer them assistance",
        "category": "audio",
        "difficulty": "Easy",
        "behavioral_category": "Customer Support"
    }
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
        "difficulty": "Easy",
        "behavioral_category": "Emotional Stability"
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
        "difficulty": "Medium",
        "behavioral_category": "Safety Awareness"
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
        "difficulty": "Easy",
        "behavioral_category": "Fatigue Control"
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
        "difficulty": "Easy",
        "behavioral_category": "Emotional Stability"
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
        "difficulty": "Easy",
        "behavioral_category": "Conflict Resolution"
    },
    {
        "question": "Look at the busy crosswalk in the image. What hazard should you watch out for?",
        "image_url": "https://images.unsplash.com/photo-1485738422979-f5c462d49f74?w=600",
        "options": [
            "A pedestrian unexpectedly stepping off the curb into your lane",
            "The traffic light turning yellow behind you",
            "A vehicle overtaking you from the left shoulder lane",
            "Clear roads with zero pedestrians present"
        ],
        "correct_answer": "A pedestrian unexpectedly stepping off the curb into your lane",
        "category": "image",
        "difficulty": "Medium",
        "behavioral_category": "Perceptual Awareness"
    },
    {
        "question": "Look at the passenger in the rear-view mirror. What does their body language suggest?",
        "image_url": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600",
        "options": [
            "They are extremely happy and excited for the trip",
            "They are showing signs of stress, discomfort, or anxiety",
            "They are deeply asleep and should not be disturbed",
            "They are distracted by watching a movie on their tablet"
        ],
        "correct_answer": "They are showing signs of stress, discomfort, or anxiety",
        "category": "image",
        "difficulty": "Medium",
        "behavioral_category": "Emotional Appraisal"
    },
    {
        "question": "Look at the traffic merge sign ahead. What should the driver do?",
        "image_url": "https://images.unsplash.com/photo-1502877338535-766e1452684a?w=600",
        "options": [
            "Maintain speed and force other merging vehicles to yield to you",
            "Adjust your speed and position to create a safe gap for merging traffic",
            "Slam on your brakes immediately to let everyone merge first",
            "Honk repeatedly to warn merging cars to stay away from your lane"
        ],
        "correct_answer": "Adjust your speed and position to create a safe gap for merging traffic",
        "category": "image",
        "difficulty": "Easy",
        "behavioral_category": "Cognitive Decisions"
    },
    {
        "question": "Look at the road surface conditions shown in this photo. What is the main driving hazard?",
        "image_url": "https://images.unsplash.com/photo-1475721027785-f74eccf877e2?w=600",
        "options": [
            "Severe potholes and loose gravel causing loss of steering control",
            "Bright sunlight causing temporary blindness and sun glare",
            "Black ice and wet leaves creating extremely slippery conditions",
            "A block construction fence closing the road ahead"
        ],
        "correct_answer": "Black ice and wet leaves creating extremely slippery conditions",
        "category": "image",
        "difficulty": "Hard",
        "behavioral_category": "Hazard Identification"
    },
    {
        "question": "Look at the vehicle dashboard warning light. What does this icon indicate?",
        "image_url": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=600",
        "options": [
            "Tire pressure is dangerously low and requires inflation check",
            "The engine oil pressure is low and needs immediate oil top-up",
            "The parking brake is currently engaged while driving",
            "The fuel level is extremely low and the vehicle needs refueling"
        ],
        "correct_answer": "Tire pressure is dangerously low and requires inflation check",
        "category": "image",
        "difficulty": "Easy",
        "behavioral_category": "Safety Awareness"
    }
]

VIDEO_MCQS = [
    {
        "category": "video",
        "question": "What unsafe behavior do you observe in this clip?",
        "options": [
            "The driver is navigating safely",
            "The driver is distracted by using a mobile phone",
            "Using a phone in slow traffic is acceptable",
            "The driver is checking the GPS properly"
        ],
        "correct_answer": "The driver is distracted by using a mobile phone",
        "image_url": f"{BACKEND_URL}/static/images/video_q1.gif",
        "difficulty": "Medium",
        "behavioral_category": "Safety Awareness"
    },
    {
        "category": "video",
        "question": "A pedestrian is crossing the road ahead. What should the driver do?",
        "options": [
            "Speed up to pass before the pedestrian crosses",
            "Slow down and let the pedestrian cross safely",
            "Honk loudly to warn the pedestrian",
            "Swerve to the other lane without checking"
        ],
        "correct_answer": "Slow down and let the pedestrian cross safely",
        "image_url": f"{BACKEND_URL}/static/images/video_q2.gif",
        "difficulty": "Easy",
        "behavioral_category": "Hazard Awareness"
    },
    {
        "category": "video",
        "question": "How should the driver handle this aggressive passenger?",
        "options": [
            "Shout back at the passenger",
            "Stay calm and speak respectfully",
            "Stop the car in the middle of the road",
            "Ignore the passenger and drive faster"
        ],
        "correct_answer": "Stay calm and speak respectfully",
        "image_url": f"{BACKEND_URL}/static/images/video_q3.gif",
        "difficulty": "Medium",
        "behavioral_category": "Emotional Stability"
    },
    {
        "category": "video",
        "question": "What is the safest action in this heavy rain?",
        "options": [
            "Speed up to get through the rain quickly",
            "Reduce speed and turn on headlights and wipers",
            "Drive close behind the car ahead",
            "Turn off all lights to avoid glare"
        ],
        "correct_answer": "Reduce speed and turn on headlights and wipers",
        "image_url": f"{BACKEND_URL}/static/images/video_q4.gif",
        "difficulty": "Easy",
        "behavioral_category": "Hazard Awareness"
    },
    {
        "category": "video",
        "question": "What risk does this driver show?",
        "options": [
            "The driver is fully alert and safe",
            "The driver is showing signs of fatigue and should rest",
            "Yawning while driving is normal",
            "The driver should drink coffee and keep going"
        ],
        "correct_answer": "The driver is showing signs of fatigue and should rest",
        "image_url": f"{BACKEND_URL}/static/images/video_q5.gif",
        "difficulty": "Easy",
        "behavioral_category": "Fatigue Monitoring"
    },
    {
        "category": "video",
        "question": "Watch this clip. What hazard appears suddenly from the blind spot?",
        "image_url": "https://i.giphy.com/3o7TKs3X96t0LhJszK.gif",
        "options": [
            "A fast-moving motorcyclist overtaking from the right side",
            "A pedestrian crossing the road at a marked crosswalk",
            "A large truck backing out of a hidden driveway",
            "A traffic light changing to red suddenly at the intersection"
        ],
        "correct_answer": "A fast-moving motorcyclist overtaking from the right side",
        "difficulty": "Medium",
        "behavioral_category": "Hazard Reactivity"
    },
    {
        "category": "video",
        "question": "What safety violation is committed by the vehicle in front in this video?",
        "image_url": "https://i.giphy.com/ryx1G5w1tYMpy.gif",
        "options": [
            "Tailgating the vehicle in front with unsafe following distance",
            "Changing lanes without using any turn signal indicators",
            "Driving below the minimum highway speed limit in the fast lane",
            "Running through a red light at the intersection"
        ],
        "correct_answer": "Changing lanes without using any turn signal indicators",
        "difficulty": "Easy",
        "behavioral_category": "Safety Awareness"
    },
    {
        "category": "video",
        "question": "What hazard does the driver react to in this dashcam clip?",
        "image_url": "https://i.giphy.com/H62QdIPlDtb1m.gif",
        "options": [
            "A child running onto the road chasing a ball",
            "An oncoming vehicle drifting into the driver's lane",
            "A dog crossing the street slowly in the dark",
            "Debris falling off the back of a truck in front"
        ],
        "correct_answer": "An oncoming vehicle drifting into the driver's lane",
        "difficulty": "Hard",
        "behavioral_category": "Hazard Reactivity"
    },
    {
        "category": "video",
        "question": "How should the driver adjust their speed when passing this construction zone?",
        "image_url": "https://i.giphy.com/12wsrv85vpG5kA.gif",
        "options": [
            "Speed up to pass the construction dust and noise quickly",
            "Reduce speed to the posted temporary limit and watch for workers",
            "Maintain normal speed and honk to warn construction workers",
            "Stop completely and wait for a green flag indicator sign"
        ],
        "correct_answer": "Reduce speed to the posted temporary limit and watch for workers",
        "difficulty": "Easy",
        "behavioral_category": "Cognitive Decisions"
    },
    {
        "category": "video",
        "question": "What driving error does the taxi driver show in this intersection clip?",
        "image_url": "https://i.giphy.com/uk4iaQGPDR74A.gif",
        "options": [
            "Failing to yield to oncoming traffic when making a left turn",
            "Stopping past the marked solid stop line at the red light",
            "Overtaking another vehicle on a double solid line",
            "Failing to check rear-view mirrors before changing lanes"
        ],
        "correct_answer": "Failing to yield to oncoming traffic when making a left turn",
        "difficulty": "Medium",
        "behavioral_category": "Safety Awareness"
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

    print("[DB] Seeding admin user...")
    admin_email = "admin@driveiq.com"
    await db.users.delete_many({"email": admin_email})
    await db.users.insert_one({
        "full_name": "DriveIQ Admin",
        "email": admin_email,
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "token": secrets.token_hex(32)
    })
    print("   [OK] Seeded admin user: admin@driveiq.com / admin123")

    # Dynamic sequential date creation to enable sorting testing
    now = datetime.now(timezone.utc)
    for idx, item in enumerate(TEXT_MCQS):
        item["created_at"] = (now - timedelta(hours=idx)).isoformat()
    for idx, item in enumerate(AUDIO_MCQS):
        item["created_at"] = (now - timedelta(hours=idx)).isoformat()
    for idx, item in enumerate(IMAGE_MCQS):
        item["created_at"] = (now - timedelta(hours=idx)).isoformat()
    for idx, item in enumerate(VIDEO_MCQS):
        item["created_at"] = (now - timedelta(hours=idx)).isoformat()

    print("[DB] Downloading and caching external seed media locally...")
    for item in IMAGE_MCQS:
        if "image_url" in item:
            item["image_url"] = download_seed_media(item["image_url"])
    for item in VIDEO_MCQS:
        if "image_url" in item:
            item["image_url"] = download_seed_media(item["image_url"])

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
