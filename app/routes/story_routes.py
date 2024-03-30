from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from models import Story
from db import collection, grid_fs_bucket
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

@router.post("/story/")
async def create_story(story: Story, 
                       content_en: UploadFile = File(...), 
                       content_cherokee: UploadFile = File(...), 
                       image: UploadFile = File(...)):
    story_data = story.dict()
    story_id = await collection.insert_one(story_data).inserted_id
    
    content_en_id = await grid_fs_bucket.upload_from_stream(
        content_en.filename, 
        content_en.file.read(), 
        metadata={"story_id": str(story_id), "language": "en"}
    )
    
    content_cherokee_id = await grid_fs_bucket.upload_from_stream(
        content_cherokee.filename, 
        content_cherokee.file.read(), 
        metadata={"story_id": str(story_id), "language": "cherokee"}
    )
    
    image_id = await grid_fs_bucket.upload_from_stream(
        image.filename, 
        image.file.read(), 
        metadata={"story_id": str(story_id), "type": "image"}
    )
    
    await collection.update_one(
        {"_id": story_id},
        {"$set": {
            "content_en_id": str(content_en_id), 
            "content_cherokee_id": str(content_cherokee_id), 
            "image_id": str(image_id)
        }}
    )
    
    return {
        "story_id": str(story_id), 
        "content_en_id": str(content_en_id), 
        "content_cherokee_id": str(content_cherokee_id), 
        "image_id": str(image_id)
    }


@router.get("/story/{story_id}")
async def get_story_with_metadata_and_multilingual_content(story_id: str):
    story_data = await collection.find_one({"_id": story_id})
    if not story_data:
        raise HTTPException(status_code=404, detail="Story not found")
    
    response_data = {
        "title": story_data["title"],
        "created_at": story_data["created_at"],
        "content_en_access": f"/story/content/{story_data['content_en_id']}",
        "content_cherokee_access": f"/story/content/{story_data['content_cherokee_id']}",
        "image_access": f"/story/image/{story_data['image_id']}"
    }
    return response_data


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
