from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from server.app.db.dbconfig import get_db
from sqlalchemy import text


async def register_server_details(
    server_name: str,
    ip_or_host: str,
    db: AsyncSession = Depends(get_db())):
    """
    Register server details in the database.
    """
    # Use a raw SQL query to insert into the registered_servers table
    query = text("""
        INSERT INTO registred_servers (server_name, ip_or_host)
        VALUES (:server_name, :ip_or_host)
    """)
    await db.execute(query, {"server_name": server_name, "ip_or_host": ip_or_host})
    await db.commit()  # Commit the transaction
    return {"message": "Added records inside table"}


async def get_registred_server_details(db: AsyncSession = Depends(get_db())):
    """
    Get all registered server details from the database.
    """
    query = text("""SELECT * FROM registred_servers""")  # Correct table name
    result = await db.execute(query)
    return result.fetchall()