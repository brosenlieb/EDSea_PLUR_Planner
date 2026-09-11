import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
print(f"--> ACTIVE ROOT_DIR: {ROOT_DIR}")
print(f"--> ACTIVE ENV_PATH: {ENV_PATH}")
load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DB_URL")
print(f"--> ACTIVE DATABASE_URL: {DATABASE_URL}")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)