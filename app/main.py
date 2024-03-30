from fastapi import FastAPI
from routes.story_routes import router as story_router
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()
app.include_router(story_router)
