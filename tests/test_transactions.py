from database.database import DATABASE_PATH, engine


def test_database_connection():
    assert engine.connect()


def test_database_path():
    assert DATABASE_PATH.name == "spendwise.db"