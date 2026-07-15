from motor.motor_asyncio import AsyncIOMotorClient
import os

# Fallback string for local dev if environment variable isn't configured
MONGO_DETAILS = os.getenv("MONGO_URL", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.bank_database
account_collection = database.get_collection("accounts")