from pydantic import BaseModel

class Story(BaseModel):
    title: str
    created_at: str
