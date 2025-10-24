import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool  # For connection pooling (optional)
from server.app.db.dbmodels import metadata

# Load .env variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "db_user": os.getenv("POSTGRES_USER"),
    "db_password": os.getenv("POSTGRES_PASSWORD"),
    "db": os.getenv("POSTGRES_DB"),
    "db_host": os.getenv("POSTGRES_HOST"),
    "db_port": os.getenv("POSTGRES_PORT"),
}

#print(DB_CONFIG)


DATABASE_URL = "postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}".format(
        DB_CONFIG["db_user"], DB_CONFIG["db_password"], DB_CONFIG["db_host"],
        DB_CONFIG["db_port"], DB_CONFIG["db"]
        )

#print("DATABASE_URL = ", DATABASE_URL)

# Create an asynchronous engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # For debugging, log SQL statements
)

# Create a session maker
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with async_session() as session:
        yield session


# Initialize DB schema (if not exists)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
