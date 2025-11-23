import os
import logging
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from models.address import AddressModel  # noqa
from models.base_model import base
from models.bill import BillModel  # noqa
from models.category import CategoryModel  # noqa
from models.client import ClientModel  # noqa
from models.order import OrderModel  # noqa
from models.order_detail import OrderDetailModel  # noqa
from models.product import ProductModel  # noqa
from models.review import ReviewModel  # noqa

# Get logger (logging is configured in main.py)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

# Database configuration with defaults
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
PGSSLMODE = os.getenv('PGSSLMODE', 'prefer')  # SSL mode for PostgreSQL

# High-performance connection pool configuration
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '50'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '100'))
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '10'))
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

# Build DATABASE_URI
DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

# Add SSL mode to URI if required
if PGSSLMODE and PGSSLMODE != 'disable':
    DATABASE_URI = f'{DATABASE_URI}?sslmode={PGSSLMODE}'

# SSL arguments for psycopg2 connection
connect_args = {}
if PGSSLMODE == 'require':
    connect_args = {"sslmode": "require"}

# Create engine with optimized connection pooling
engine = create_engine(
    DATABASE_URI,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    echo=False,
    future=True,
)

# SessionLocal class for creating new sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions.
    Creates a new session for each request and closes it when done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    try:
        base.metadata.create_all(engine)
        logger.info("✅ Tables created successfully.")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise


def drop_database():
    """Drop all tables in the database."""
    try:
        base.metadata.drop_all(engine)
        logger.info("✅ Tables dropped successfully.")
    except Exception as e:
        logger.error(f"❌ Error dropping tables: {e}")
        raise


def check_connection() -> bool:
    """Check if database connection is working."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("✅ Database connection established.")
        return True
    except Exception as e:
        logger.error(f"❌ Error connecting to database: {e}")
        return False