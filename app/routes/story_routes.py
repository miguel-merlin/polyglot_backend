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
async def create_story(story: Story, file: UploadFile = File(...), image: UploadFile = File(...)):
    story_data = story.dict()
    story_id = await collection.insert_one(story_data).inserted_id
    
    content_file_id = await grid_fs_bucket.upload_from_stream(
        file.filename, 
        file.file.read(), 
        metadata={"story_id": str(story_id), "type": "content"}
    )
    
    image_file_id = await grid_fs_bucket.upload_from_stream(
        image.filename, 
        image.file.read(), 
        metadata={"story_id": str(story_id), "type": "image"}
    )

    await collection.update_one(
        {"_id": story_id},
        {"$set": {"content_file_id": str(content_file_id), "image_file_id": str(image_file_id)}}
    )
    
    return {
        "story_id": str(story_id), 
        "content_file_id": str(content_file_id), 
        "image_file_id": str(image_file_id),
        "content_access": f"/story/content/{story_id}",
        "image_access": f"/story/image/{story_id}"
    }

@router.get("/story/{story_id}")
async def get_story_with_metadata_and_image(story_id: str):
    story_data = await collection.find_one({"_id": story_id})
    if not story_data:
        raise HTTPException(status_code=404, detail="Story not found")
    
    image_file_id = story_data.get("image_file_id")
    if image_file_id:
        image_access_url = f"/story/image/{image_file_id}" 
    else:
        image_access_url = None
    
    response_data = {
        "title": story_data["title"],
        "created_at": story_data["created_at"],
        "image_access": image_access_url
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
