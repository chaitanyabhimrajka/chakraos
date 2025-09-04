# migrations/env.py
from __future__ import annotations
import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Base  # <-- we use your app's models metadata

# Alembic Config object
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use your SQLAlchemy models' metadata for autogenerate (if ever needed)
target_metadata = Base.metadata

def build_db_url() -> str:
    url = os.getenv("DB_URL")
    if url:
        return url
    user = os.getenv("DB_USER", "chakraos_app")
    pw   = os.getenv("DB_PASS", "")
    name = os.getenv("DB_NAME", "chakraos_db")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "5432")
    if host.startswith("/"):
        # Cloud SQL unix socket
        return f"postgresql+asyncpg://{user}:{pw}@/{name}?host={host}"
    return f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{name}"

def run_migrations_offline() -> None:
    url = build_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_async_engine(build_db_url(), poolclass=pool.NullPool)

    def do_run(connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    import asyncio
    async def run():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run)
        await connectable.dispose()

    asyncio.run(run())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()