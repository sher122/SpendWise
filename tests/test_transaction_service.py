
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base, enable_foreign_keys
from models.category import Category, CategoryType
from models.subcategory import Subcategory
from models.transaction import PaymentMethod, Transaction, TransactionType
from services.transaction_service import create_transaction


def create_test_session(tmp_path):
    """Create an isolated SQLite database with foreign keys enabled."""
    test_database = tmp_path / "test_transactions.db"

    test_engine = create_engine(
        f"sqlite:///{test_database}",
        connect_args={"check_same_thread": False},
    )

    from sqlalchemy import event
    event.listen(test_engine, "connect", enable_foreign_keys)

    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(bind=test_engine)
    return test_engine, TestSession()


def create_test_categories(session):
    """Create categories and subcategories for transaction tests."""
    food = Category(
        name="Food",
        category_type=CategoryType.EXPENSE,
    )

    salary = Category(
        name="Salary",
        category_type=CategoryType.INCOME,
    )

    transport = Category(
        name="Transport",
        category_type=CategoryType.EXPENSE,
    )

    session.add_all([food, salary, transport])
    session.flush()

    groceries = Subcategory(
        name="Groceries",
        category_id=food.id,
    )

    session.add(groceries)
    session.flush()

    return food, salary, transport, groceries


def test_create_valid_expense_transaction(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        food, _, _, groceries = create_test_categories(session)

        transaction = create_transaction(
            session=session,
            transaction_type=TransactionType.EXPENSE,
            amount_paise=25000,
            description="Weekly groceries",
            transaction_date=date(2026, 11, 2),
            payment_method=PaymentMethod.UPI,
            category_id=food.id,
            subcategory_id=groceries.id,
        )

        assert transaction.id is not None
        assert transaction.amount_paise == 25000
        assert transaction.description == "Weekly groceries"
        assert transaction.category_id == food.id
        assert transaction.subcategory_id == groceries.id

    finally:
        session.close()
        engine.dispose()


def test_create_valid_income_transaction(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        _, salary, _, _ = create_test_categories(session)

        transaction = create_transaction(
            session=session,
            transaction_type=TransactionType.INCOME,
            amount_paise=5000000,
            description="Monthly salary",
            transaction_date=date(2026, 11, 1),
            payment_method=PaymentMethod.BANK_TRANSFER,
            category_id=salary.id,
        )

        assert transaction.id is not None
        assert transaction.transaction_type == TransactionType.INCOME
        assert transaction.amount_paise == 5000000
        assert transaction.subcategory_id is None

    finally:
        session.close()
        engine.dispose()


@pytest.mark.parametrize("amount", [0, -100, -1])
def test_reject_non_positive_amount(tmp_path, amount):
    engine, session = create_test_session(tmp_path)

    try:
        food, _, _, _ = create_test_categories(session)

        with pytest.raises(ValueError, match="greater than zero"):
            create_transaction(
                session=session,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=amount,
                description="Invalid amount",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=food.id,
            )

    finally:
        session.close()
        engine.dispose()


def test_reject_category_with_wrong_transaction_type(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        _, salary, _, _ = create_test_categories(session)

        with pytest.raises(ValueError, match="does not match"):
            create_transaction(
                session=session,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=10000,
                description="Incorrect category",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=salary.id,
            )

    finally:
        session.close()
        engine.dispose()


def test_reject_subcategory_from_another_category(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        food, _, transport, groceries = create_test_categories(session)

        with pytest.raises(ValueError, match="does not belong"):
            create_transaction(
                session=session,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=10000,
                description="Incorrect subcategory",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=transport.id,
                subcategory_id=groceries.id,
            )

    finally:
        session.close()
        engine.dispose()


def test_reject_inactive_category(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        food, _, _, _ = create_test_categories(session)
        food.is_active = False
        session.flush()

        with pytest.raises(ValueError, match="category is inactive"):
            create_transaction(
                session=session,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=10000,
                description="Inactive category",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=food.id,
            )

    finally:
        session.close()
        engine.dispose()


def test_reject_empty_description(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        food, _, _, _ = create_test_categories(session)

        with pytest.raises(ValueError, match="Description cannot be empty"):
            create_transaction(
                session=session,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=10000,
                description="   ",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=food.id,
            )

    finally:
        session.close()
        engine.dispose()

@pytest.mark.parametrize("amount", [100.5, True, False])
def test_reject_non_integer_amount(tmp_path, amount):
    engine, session = create_test_session(tmp_path)

    try:
        food, _, _, _ = create_test_categories(session)

        with pytest.raises(ValueError, match="whole number of paise"):
            create_transaction(
                session=session,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=amount,
                description="Invalid amount type",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=food.id,
            )

    finally:
        session.close()
        engine.dispose()


def test_reject_description_longer_than_200_characters(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        food, _, _, _ = create_test_categories(session)

        with pytest.raises(ValueError, match="200 characters"):
            create_transaction(
                session=session,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=10000,
                description="A" * 201,
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=food.id,
            )

    finally:
        session.close()
        engine.dispose()


def test_reject_inactive_subcategory(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        food, _, _, groceries = create_test_categories(session)
        groceries.is_active = False
        session.flush()

        with pytest.raises(ValueError, match="subcategory is inactive"):
            create_transaction(
                session=session,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=10000,
                description="Inactive subcategory",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=food.id,
                subcategory_id=groceries.id,
            )

    finally:
        session.close()
        engine.dispose()
