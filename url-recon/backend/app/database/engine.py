"""
engine.py — The single point of contact between our app and PostgreSQL.

Think of this file like the ignition key for a car:
  - create_async_engine()   → turns the key, opens the connection to Postgres
  - AsyncSessionLocal()     → rents you a desk at the library to do your work
  - get_db()                → FastAPI dependency that hands a desk to each route,
                              then tidies up automatically when the route finishes

Nothing else in the app talks to Postgres directly — everything goes through here.
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# load_dotenv() reads the .env file and puts those key=value pairs into
# the environment so os.getenv() can find them.
# RULE: credentials never live in code — always in .env (which is gitignored).
load_dotenv()

# The connection URL tells SQLAlchemy three things:
#   1. Which database dialect: postgresql
#   2. Which async driver:     asyncpg
#   3. Where + credentials:    user:pass@host:port/dbname
#
# os.getenv() reads from the .env file. The second argument is a safe
# fallback for local development — NEVER use the fallback on a real server.
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://recon_user:recon_pass@localhost:5432/recon_db",
)

# create_async_engine() — opens the door to Postgres.
#
#   echo=False      → don't print every SQL statement to the terminal.
#                     Set to True temporarily if you need to debug a query.
#
#   pool_size=10    → keep 10 connections open and ready at all times.
#                     Like having 10 staff members always at their desks.
#
#   max_overflow=20 → allow up to 20 EXTRA temporary connections under
#                     heavy load (burst traffic). They close when traffic drops.
#
#   pool_pre_ping=True → before reusing a connection, send a quick "are you
#                        alive?" ping to Postgres. Prevents "connection dropped"
#                        errors after the server has been idle for a while.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# async_sessionmaker() — builds a factory that stamps out fresh sessions.
# A session is your temporary workspace with the database:
#   - you open it
#   - read/write inside it
#   - commit (save) or rollback (undo)
#   - close it
#
#   expire_on_commit=False → after you commit, keep the Python objects alive
#                            so you can still read their data. Without this,
#                            accessing result.meta after commit would crash.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """
    FastAPI dependency — use with Depends(get_db) in route parameters.

    'async with' ensures the session is ALWAYS closed after the route
    finishes — even if an exception is thrown halfway through.
    'yield' is the pause button: give the session to the route, wait for
    it to finish its work, then close the session.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):
            result = await db_store.load_scan(scan_id, db)
    """
    async with AsyncSessionLocal() as session:
        yield session
