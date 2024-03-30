from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Initialize app
app = FastAPI()

load_dotenv()
# MongoDB connection
MONGO_URL = os.getenv("DB_URL")
client = AsyncIOMotorClient(MONGO_URL)
database = client["polyglot"]
collection = database["story"]

# Model
class Story(BaseModel):
    title: str
    created_at: str
    s3_url: str


# Routes
@app.get("/")
async def root():
    return {"Welcome to Polyglot API"}

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
