from pydantic import BaseModel

class Story(BaseModel):
    title: str
    created_at: str
    content_en_id: str = None
    content_chr_id: str = None
    image_id: str = None
