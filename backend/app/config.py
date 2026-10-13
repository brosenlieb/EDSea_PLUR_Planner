"""
Module for database configuration and environment setup.

This module loads environment variables from a .env file and initializes
the SQLAlchemy database engine and session factory based on the DATABASE_URL
provided in the environment.
"""
import os
from pathlib import Path
from typing import TYPE_CHECKING
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

# Log the active paths for debugging environment setup
print(f"--> ACTIVE ROOT_DIR: {ROOT_DIR}")
print(f"--> ACTIVE ENV_PATH: {ENV_PATH}")

load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL: str = os.getenv("DB_URL")
print(f"--> ACTIVE DATABASE_URL: {DATABASE_URL}")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables!")

engine: "Engine" = create_engine(DATABASE_URL)
SessionLocal: type["Session"] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
