import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool  # For connection pooling (optional)

# Load .env variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "db_user": os.getenv("POSTGRES_USER"),
    "db_password": os.getenv("POSTGRES_PASSWORD"),
    "db": os.getenv("POSTGRES_DB"),
    "db_host_ip": os.getenv("MYIP"),
    "db_host_name": os.getenv("HOSTNAME"),
    "db_port": 5432, # Default PostgreSQL port
}

if DB_CONFIG['db_host_ip'] and DB_CONFIG['db_host_ip'] != "127.0.0.1":
    DB_CONFIG["db_host"] = DB_CONFIG['db_host_ip']
else:
    DB_CONFIG["db_host"] = DB_CONFIG['db_host_name']


DATABASE_URL = "postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}".format(
        DB_CONFIG["db_user"], DB_CONFIG["db_password"], DB_CONFIG["db_host"],
        DB_CONFIG["db_port"], DB_CONFIG["db"]
        )


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

