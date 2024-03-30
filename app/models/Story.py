from pydantic import BaseModel
from models.Genre import Genre
from datetime import datetime
class Story(BaseModel):
    title: str
    created_at: datetime
    genre: Genre
    content_en_id: str = None
    content_chr_id: str = None
    image_id: str = None
