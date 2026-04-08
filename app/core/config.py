import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parents[2]
ROOT_DOTENV_PATH = BASE_DIR / ".env"

if load_dotenv is not None and ROOT_DOTENV_PATH.exists():
    load_dotenv(ROOT_DOTENV_PATH, override=False)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    # Use an in-memory database by default; set DATABASE_URL for persistence.
    # SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
