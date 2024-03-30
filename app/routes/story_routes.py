import aiofiles
from anyio import Path
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from models.Story import Story
from db.database import collection, grid_fs_bucket
import datetime
import models.Genre as Genre
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from json import JSONEncoder
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

router = APIRouter()

RESOURCE_DIRECTORY = Path(__file__).parent.parent / "resources"
RESOURCE_DIRECTORY.mkdir(parents=True, exist_ok=True)

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return JSONEncoder.default(self, obj)

@router.get("/")
async def root():
    return {"Welcome to Polyglot API"}

@router.get("/image/{story_id}")
async def get_image(story_id: str):
    file_path = RESOURCE_DIRECTORY / story_id
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, media_type='image/png')

@router.get("/file/{file_id}")
async def get_file(file_id: str):
    try:
        grid_out = await grid_fs_bucket.open_download_stream(ObjectId(file_id))
        
        async def file_generator(file_stream):
            while True:
                chunk = await file_stream.read(8192)
                if not chunk:
                    break
                yield chunk
        
        # Create a streaming response
        return StreamingResponse(file_generator(grid_out), media_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")

@router.get("/stories/")
async def read_items():
    items = []
    async for item in collection.find():
        item = jsonable_encoder(item, custom_encoder={ObjectId: lambda oid: str(oid)})
        items.append(item)
    return JSONResponse(content=items)

@router.post("/story/")
async def create_story(title: str = Form(...), 
                       genre: str = Form(...), 
                       content_en: UploadFile = File(...), 
                       content_cherokee: UploadFile = File(...), 
                       image: UploadFile = File(...)):
    story_data = Story(title=title, genre=genre, created_at=datetime.datetime.now()).dict()
    story_data['genre'] = Genre.Genre[genre.upper()].value
    story_id = await collection.insert_one(story_data)
    inserted_id = str(story_id.inserted_id)
    
    content_en_id = await grid_fs_bucket.upload_from_stream(
        content_en.filename, 
        content_en.file.read(), 
        metadata={"story_id": inserted_id, "language": "en"}
    )
    
    content_cherokee_id = await grid_fs_bucket.upload_from_stream(
        content_cherokee.filename, 
        content_cherokee.file.read(), 
        metadata={"story_id": inserted_id, "language": "cherokee"}
    )
    
    image_file_path = RESOURCE_DIRECTORY / inserted_id
    async with aiofiles.open(image_file_path, 'wb') as out_file:
        content = await image.read()
        await out_file.write(content)
    
    # Update the story with the content and image IDs
    story_data['content_en'] = str(content_en_id)
    story_data['content_cherokee'] = str(content_cherokee_id)
    
    await collection.update_one(
        {"_id": ObjectId(inserted_id)},
        {"$set": {
            "content_en_id": str(content_en_id), 
            "content_chr_id": str(content_cherokee_id)
        }}
    )
    
    return {
        "story_id": str(story_id),
        "title": title,
        "genre": genre,
        "content_en_id": str(content_en_id),
        "content_chr_id": str(content_cherokee_id)
    }

@router.get("/story/{story_id}")
async def get_story_with_metadata_and_multilingual_content(story_id: str):
    try:
        story_id = ObjectId(story_id)
    except:
        raise HTTPException(status_code=404, detail="Invalid ID")
    story_data = await collection.find_one({"_id": story_id})
    if not story_data:
        raise HTTPException(status_code=404, detail="Story not found")
    story_data = jsonable_encoder(story_data, custom_encoder={ObjectId: lambda oid: str(oid)})
    
    return JSONResponse(content=story_data)


@router.put("/story/{story_id}", response_model=Story)
async def update_item(story_id: str, story: Story):
    try:
        story_id = ObjectId(story_id)
    except:
        raise HTTPException(status_code=404, detail="Invalid ID")
    updated_item = await collection.find_one_and_update(
        {"_id": story_id}, {"$set": story.dict()}
    )
    if updated_item:
        return story
    raise HTTPException(status_code=404, detail="Story not found")

@router.delete("/story/{story_id}", response_model=Story)
async def delete_item(story_id: str):
    try:
        story_id = ObjectId(story_id)
    except:
        raise HTTPException(status_code=404, detail="Invalid ID")
    deleted_item = await collection.find_one_and_delete({"_id": story_id})
    
    # Delete the content and image files
    content_en_id = deleted_item.get('content_en_id')
    content_chr_id = deleted_item.get('content_chr_id')
    if content_en_id:
        await grid_fs_bucket.delete(ObjectId(content_en_id))
    if content_chr_id:
        await grid_fs_bucket.delete(ObjectId(content_chr_id))
    image_file_path = RESOURCE_DIRECTORY / str(story_id)
    if image_file_path.exists() and image_file_path.is_file():
        await image_file_path.unlink()
    
    if deleted_item:
        return deleted_item
    raise HTTPException(status_code=404, detail="Item not found")
