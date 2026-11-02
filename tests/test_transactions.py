from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import configure_mappers

from database.database import Base
import models


def test_database_connection():
    """Check that the database engine can establish a connection."""
    from database.database import engine

    with engine.connect() as connection:
        assert connection is not None


def test_database_tables_created(tmp_path):
    """Check that all three application tables can be created."""
    test_database = tmp_path / "test_spendwise.db"

    test_engine = create_engine(
        f"sqlite:///{test_database}"
    )

    Base.metadata.create_all(bind=test_engine)

    inspector = inspect(test_engine)
    table_names = set(inspector.get_table_names())

    assert "categories" in table_names
    assert "subcategories" in table_names
    assert "transactions" in table_names

    test_engine.dispose()


def test_model_relationships():
    """Check that SQLAlchemy can configure model relationships."""
    configure_mappers()