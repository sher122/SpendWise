
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Find the main SpendWise project directory.
BASE_DIR = Path(__file__).resolve().parent.parent

# Store the database inside the data directory.
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "spendwise.db"

# Create the SQLite database connection URL.
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


# Create the SQLAlchemy engine.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)


# Base class for all database models.
class Base(DeclarativeBase):
    pass


# Create a factory for database sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# Initialize the database tables.
def init_db():
    Base.metadata.create_all(bind=engine)
