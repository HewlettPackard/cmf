import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool  # For connection pooling (optional)

# Load .env variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
}

user='myuser'
password='mypassword'
host='192.168.20.67'
port=5432
database='mlmd'


DATABASE_URL = "postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}".format(
            user, password, host, port, database
        )

#engine = create_async_engine(DATABASE_URL, echo=True)
#async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Create an asynchronous engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # For debugging, log SQL statements
)
#     poolclass=NullPool,  # You can also use other pool classes like QueuePool
#     pool_size=10,         # Number of connections to maintain in the pool
#     max_overflow=20,      # Number of connections to allow above pool_size
# )

# Create a session maker
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with async_session() as session:
        yield session

