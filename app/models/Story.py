from pydantic import BaseModel
from Genre import Genre

class Story(BaseModel):
    title: str
    created_at: str
    genre: Genre
    content_en_id: str = None
    content_chr_id: str = None
    image_id: str = None
