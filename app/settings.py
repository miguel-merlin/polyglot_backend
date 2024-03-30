from dotenv import load_dotenv
import os

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(env_path)
MONGO_URL = os.getenv("URI")
DATABASE_NAME = "polyglot"
COLLECTION_NAME = "story"

