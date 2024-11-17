from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import config

DB_URL = config.DB_URL
DB_USERNAME = config.DB_USERNAME
DB_PASSWORD = config.DB_PASSWORD
DB_NAME = config.DB_NAME

DATABASE_URL = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}/{DB_NAME}'

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # Remove 'connect_args' for PostgreSQL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
