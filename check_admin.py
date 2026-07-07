import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "quizDB")

async def check():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    user = await db.users.find_one({"email": "admin@driveiq.com"})
    print("USER_DOCUMENT_IN_DB:", user)
    client.close()

if __name__ == "__main__":
    asyncio.run(check())
