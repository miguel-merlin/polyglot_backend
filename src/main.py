from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Initialize app
app = FastAPI()

load_dotenv()

# MongoDB connection
URI = os.getenv("URI")
client = MongoClient(URI, server_api=ServerApi("1"))

# Check if MongoDB is connected
try:
    print("Connecting to MongoDB")
    client.admin.command("ping")
    print("Connected to MongoDB")
except Exception as e:
    print(e)
    exit()


# Check if MongoDB is connected
@app.on_event("startup")
async def startup():
    try:
        print("INFO: Connecting to MongoDB")
        await client.server_info()
        print("Connected to MongoDB")
    except Exception as e:
        print(f"An error occurred: {e}")

collection = client["polyglot"]["stories"]

# Model
class Story(BaseModel):
    title: str
    created_at: str
    s3_url: str


# Routes
@app.get("/")
async def root():
    return {"Welcome to Polyglot API"}

# Get all
@app.get("/stories/")
async def read_items():
    items = []
    async for item in collection.find():
        items.append(item)
    return items

@app.post("/story/", response_model=Story)
async def create_story(story: Story):
    result = await collection.insert_one(story.dict())
    story.id = str(result.inserted_id)
    return story

@app.get("/story/{story_id}", response_model=Story)
async def read_item(story_id: str):
    item = await collection.find_one({"_id": story_id})
    if item:
        return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/story/{story_id}", response_model=Story)
async def update_item(story_id: str, story: Story):
    updated_item = await collection.find_one_and_update(
        {"_id": story_id}, {"$set": story.dict()}
    )
    if updated_item:
        return story
    raise HTTPException(status_code=404, detail="Story not found")

@app.delete("/story/{story_id}", response_model=Story)
async def delete_item(story_id: str):
    deleted_item = await collection.find_one_and_delete({"_id": story_id})
    if deleted_item:
        return deleted_item
    raise HTTPException(status_code=404, detail="Item not found")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Path not found"},
    )

# Custom 404
@app.get("/{_:path}")
async def catch_all(_):
    return JSONResponse(
        status_code=404,
        content={"message": "Path not found"},
    )
