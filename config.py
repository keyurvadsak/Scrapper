import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Parse DEFAULT_TAGS from environment variable or use fallback
_tags_env = os.getenv("DEFAULT_TAGS")
if _tags_env:
    DEFAULT_TAGS = [tag.strip() for tag in _tags_env.split(",")]
else:
    DEFAULT_TAGS = ["h1", "h2", "p", "a", "img", "span", "div"]