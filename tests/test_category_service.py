from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.category import Category, CategoryType
from models.subcategory import Subcategory
from services.category_service import seed_default_categories


def create_test_session(tmp_path):
    """Create an isolated SQLite database for testing."""
    test_database = tmp_path / "test_categories.db"

    test_engine = create_engine(
        f"sqlite:///{test_database}"
    )

    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(bind=test_engine)
    return test_engine, TestSession()


def test_default_categories_are_created(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        seed_default_categories(session)
        session.commit()

        expense_count = session.scalar(
            select(func.count())
            .select_from(Category)
            .where(Category.category_type == CategoryType.EXPENSE)
        )

        income_count = session.scalar(
            select(func.count())
            .select_from(Category)
            .where(Category.category_type == CategoryType.INCOME)
        )

        assert expense_count == 10
        assert income_count == 5

    finally:
        session.close()
        engine.dispose()


def test_default_subcategories_are_created(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        seed_default_categories(session)
        session.commit()

        food = session.scalar(
            select(Category).where(
                Category.name == "Food",
                Category.category_type == CategoryType.EXPENSE,
            )
        )

        subcategory_names = {
            subcategory.name for subcategory in food.subcategories
        }

        assert subcategory_names == {"Groceries", "Eating Out"}

    finally:
        session.close()
        engine.dispose()


def test_seeding_does_not_create_duplicates(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        seed_default_categories(session)
        session.commit()

        seed_default_categories(session)
        session.commit()

        category_count = session.scalar(
            select(func.count()).select_from(Category)
        )

        subcategory_count = session.scalar(
            select(func.count()).select_from(Subcategory)
        )

        assert category_count == 15
        assert subcategory_count == 33

    finally:
        session.close()
        engine.dispose()


def test_custom_category_is_preserved(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        custom_category = Category(
            name="Pets",
            category_type=CategoryType.EXPENSE,
        )

        session.add(custom_category)
        session.commit()

        seed_default_categories(session)
        session.commit()

        pets = session.scalar(
            select(Category).where(
                Category.name == "Pets",
                Category.category_type == CategoryType.EXPENSE,
            )
        )

        assert pets is not None

    finally:
        session.close()
        engine.dispose()