from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from models import Story
from db import collection
from fastapi import Request

router = APIRouter()

@router.get("/")
async def root():
    return {"Welcome to Polyglot API"}

@router.get("/stories/")
async def read_items():
    items = []
    async for item in collection.find():
        items.append(item)
    return items

@router.post("/story/", response_model=Story)
async def create_story(story: Story):
    result = await collection.insert_one(story.dict())
    story.id = str(result.inserted_id)
    return story

@router.get("/story/{story_id}", response_model=Story)
async def read_item(story_id: str):
    item = await collection.find_one({"_id": story_id})
    if item:
        return item
    raise HTTPException(status_code=404, detail="Item not found")

@router.put("/story/{story_id}", response_model=Story)
async def update_item(story_id: str, story: Story):
    updated_item = await collection.find_one_and_update(
        {"_id": story_id}, {"$set": story.dict()}
    )
    if updated_item:
        return story
    raise HTTPException(status_code=404, detail="Story not found")

@router.delete("/story/{story_id}", response_model=Story)
async def delete_item(story_id: str):
    deleted_item = await collection.find_one_and_delete({"_id": story_id})
    if deleted_item:
        return deleted_item
    raise HTTPException(status_code=404, detail="Item not found")

@router.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Path not found"},
    )

@router.get("/{_:path}")
async def catch_all(_):
    return JSONResponse(
        status_code=404,
        content={"message": "Path not found"},
    )
