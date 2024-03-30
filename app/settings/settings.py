from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URL = os.getenv("URI")
DATABASE_NAME = "polyglot"
COLLECTION_NAME = "story"
