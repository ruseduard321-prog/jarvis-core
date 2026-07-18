from contextlib import asynccontextmanager

from backend.core.dependencies import get_database


@asynccontextmanager
async def lifespan(app):
    database = get_database()
    await database.connect()
    try:
        yield
    finally:
        await database.disconnect()
