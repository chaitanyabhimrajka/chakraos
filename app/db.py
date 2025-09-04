# app/db.py
import os
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker


DB_URL_ENV = os.getenv("DB_URL")  # allow explicit override
if DB_URL_ENV:
    DB_URL = DB_URL_ENV
else:
    DB_USER = os.getenv("DB_USER", "chakraos_app")
    DB_PASS = os.getenv("DB_PASS", "")
    DB_NAME = os.getenv("DB_NAME", "chakraos_db")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "5432")

    if DB_HOST.startswith("/"):
        # Cloud Run unix socket
        DB_URL = URL.create(
            "postgresql+asyncpg",
            username=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            query={"host": DB_HOST},
        )
    else:
        DB_URL = URL.create(
            "postgresql+asyncpg",
            username=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME,
        )

engine = create_async_engine(DB_URL, pool_pre_ping=True, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession, )

async def get_db():
    async with SessionLocal() as session:
        yield session