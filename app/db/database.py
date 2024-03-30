from motor.motor_asyncio import AsyncIOMotorClient
from settings import MONGO_URL, DATABASE_NAME

client = AsyncIOMotorClient(MONGO_URL)
database = client[DATABASE_NAME]
collection = database["story"]
