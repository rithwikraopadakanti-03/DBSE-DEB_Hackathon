import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

def _require_env(key):
    """Raise an error if a required environment variable is missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy backend/.env.example to backend/.env and fill in your values."
        )
    return value

class Config:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/campus_complaints')
    JWT_SECRET_KEY = _require_env('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400)))
