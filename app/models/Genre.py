from pydantic import BaseModel
from enum import Enum

class Genre(BaseModel):
    MYTHOLOGY = "mythology"
    FOLKLORE = "folklore"
    HISTORY = "history"
    