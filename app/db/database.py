from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from settings import MONGO_URL, DATABASE_NAME

client = AsyncIOMotorClient(MONGO_URL)
database = client[DATABASE_NAME]
collection = database["story"]
grid_fs_bucket = AsyncIOMotorGridFSBucket(database)
