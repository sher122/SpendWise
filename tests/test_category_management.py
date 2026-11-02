
import pytest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database.database import Base, enable_foreign_keys
from models.category import Category, CategoryType
from models.subcategory import Subcategory
from services.category_service import (
    create_category,
    create_subcategory,
    update_category,
    update_subcategory,
    )


@pytest.fixture
def session():
    """Provide a fresh isolated SQLite database for each test."""

    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect", enable_foreign_keys)
    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(bind=engine)

    with TestingSession() as test_session:
        yield test_session

    engine.dispose()


def test_create_custom_category(session):
    category = create_category(
        session, "Travel", CategoryType.EXPENSE
    )

    assert category.name == "Travel"
    assert category.category_type == CategoryType.EXPENSE
    assert category.is_active is True


def test_create_income_category(session):
    category = create_category(
        session, "Rental Income", CategoryType.INCOME
    )

    assert category.category_type == CategoryType.INCOME


def test_reject_duplicate_category(session):
    create_category(session, "Travel", CategoryType.EXPENSE)

    with pytest.raises(ValueError, match="already exists"):
        create_category(session, "Travel", CategoryType.EXPENSE)


def test_same_name_allowed_for_different_types(session):
    expense = create_category(
        session, "Other", CategoryType.EXPENSE
    )
    income = create_category(
        session, "Other", CategoryType.INCOME
    )

    assert expense.id != income.id


def test_reject_invalid_category_type(session):
    with pytest.raises(ValueError, match="Invalid category type"):
        create_category(session, "Travel", "expense")


@pytest.mark.parametrize("name", ["", "   ", None])
def test_reject_invalid_category_name(session, name):
    with pytest.raises(ValueError):
        create_category(session, name, CategoryType.EXPENSE)


def test_create_custom_subcategory(session):
    category = create_category(
        session, "Travel", CategoryType.EXPENSE
    )

    subcategory = create_subcategory(
        session, "Flight Tickets", category.id
    )

    assert subcategory.name == "Flight Tickets"
    assert subcategory.category_id == category.id
    assert subcategory.is_active is True


def test_reject_duplicate_subcategory(session):
    category = create_category(
        session, "Travel", CategoryType.EXPENSE
    )

    create_subcategory(session, "Flights", category.id)

    with pytest.raises(ValueError, match="already exists"):
        create_subcategory(session, "Flights", category.id)


def test_reject_subcategory_for_missing_category(session):
    with pytest.raises(ValueError, match="Active category not found"):
        create_subcategory(session, "Flights", 999)


def test_rename_category(session):
    category = create_category(
        session, "Travel", CategoryType.EXPENSE
    )

    updated = update_category(
        session, category.id, "Holidays"
    )

    assert updated.name == "Holidays"


def test_reject_duplicate_category_name_during_update(session):
    create_category(session, "Travel", CategoryType.EXPENSE)
    second = create_category(
        session, "Holidays", CategoryType.EXPENSE
    )

    with pytest.raises(ValueError, match="already exists"):
        update_category(session, second.id, "Travel")


def test_rename_subcategory(session):
    category = create_category(
        session, "Travel", CategoryType.EXPENSE
    )
    subcategory = create_subcategory(
        session, "Flights", category.id
    )

    updated = update_subcategory(
        session, subcategory.id, "Air Travel"
    )

    assert updated.name == "Air Travel"


def test_reject_duplicate_subcategory_name_during_update(session):
    category = create_category(
        session, "Travel", CategoryType.EXPENSE
    )
    first = create_subcategory(session, "Flights", category.id)
    second = create_subcategory(session, "Hotels", category.id)

    with pytest.raises(ValueError, match="already exists"):
        update_subcategory(session, second.id, first.name)









