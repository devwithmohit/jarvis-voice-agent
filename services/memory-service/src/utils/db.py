"""
Database connection pool using SQLAlchemy
Provides connection management for PostgreSQL
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
from contextlib import contextmanager
from typing import Generator
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_settings

settings = get_settings()

# Construct PostgreSQL connection URL
DATABASE_URL = (
    f"postgresql://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=settings.db_pool_pre_ping,
    echo=settings.debug,
    pool_recycle=3600,  # Recycle connections after 1 hour
)


# Add connection pool event listeners for monitoring
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new database connections"""
    if settings.debug:
        print(f"New database connection established: {id(dbapi_conn)}")


@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkouts from pool"""
    if settings.debug:
        print(f"Connection checked out: {id(dbapi_conn)}")


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions

    Usage:
        with get_db() as db:
            db.execute(query)
            # Automatically commits on success, rolls back on error
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        db.close()


def test_connection() -> bool:
    """Test database connection"""
    try:
        with get_db() as db:
            db.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection when run directly
    if test_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
