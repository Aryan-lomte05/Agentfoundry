from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables"""
    logger.info("🗄️ Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized")

def drop_db():
    """Drop all tables (for development only)"""
    logger.warning("⚠️ Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("✅ Database dropped")
