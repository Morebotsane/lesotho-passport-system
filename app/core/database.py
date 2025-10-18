# app/core/database.py
import logging
import time
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from app.core.config import settings

# Database setup
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============ Query Performance Monitoring ============

# Configure logging
logging.basicConfig()
query_logger = logging.getLogger('sqlalchemy.engine')
query_logger.setLevel(logging.INFO)

# Track query execution time (ONE set of listeners only!)
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time"""
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries (>100ms)"""
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    
    if total_time > 0.1:  # Queries taking more than 100ms
        query_logger.warning(
            f"🐌 SLOW QUERY ({total_time:.3f}s):\n{statement}\n"
            f"Parameters: {parameters}\n"
        )
    else:
        query_logger.debug(f"✓ Query completed in {total_time:.3f}s")

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()