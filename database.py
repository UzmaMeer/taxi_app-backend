"""
MongoDB connection management using Motor (async driver).
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "quizDB")

client: AsyncIOMotorClient = None
db = None


async def connect_to_mongo():
    """Initialize the MongoDB connection."""
    global client, db
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    # Verify connection
    await client.admin.command("ping")
    print(f"[OK] Connected to MongoDB: {DB_NAME}")


async def close_mongo_connection():
    """Close the MongoDB connection."""
    global client
    if client:
        client.close()
        print("[OK] MongoDB connection closed.")


def get_database():
    """Return the database instance."""
    return db
