
from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database.database import Base, enable_foreign_keys
from models.category import Category, CategoryType
from models.transaction import PaymentMethod, Transaction, TransactionType
from services.transaction_service import (
    create_transaction,
    update_transaction,
)


def create_test_session(tmp_path):
    """Create an isolated SQLite database for update tests."""
    test_database = tmp_path / "test_update.db"

    test_engine = create_engine(
        f"sqlite:///{test_database}",
        connect_args={"check_same_thread": False},
    )

    event.listen(test_engine, "connect", enable_foreign_keys)
    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(bind=test_engine)

    return test_engine, TestSession()


def create_sample_transaction(session):
    """Create a transaction and its categories."""
    food = Category(
        name="Food",
        category_type=CategoryType.EXPENSE,
    )

    transport = Category(
        name="Transport",
        category_type=CategoryType.EXPENSE,
    )

    salary = Category(
        name="Salary",
        category_type=CategoryType.INCOME,
    )

    session.add_all([food, transport, salary])
    session.flush()

    transaction = create_transaction(
        session=session,
        transaction_type=TransactionType.EXPENSE,
        amount_paise=25000,
        description="Weekly groceries",
        transaction_date=date(2026, 11, 1),
        payment_method=PaymentMethod.UPI,
        category_id=food.id,
    )

    session.commit()

    return transaction, food, transport, salary


def test_update_transaction_successfully(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        transaction, food, _, _ = create_sample_transaction(session)

        updated = update_transaction(
            session=session,
            transaction_id=transaction.id,
            transaction_type=TransactionType.EXPENSE,
            amount_paise=50000,
            description="Monthly groceries",
            transaction_date=date(2026, 11, 2),
            payment_method=PaymentMethod.CARD,
            category_id=food.id,
        )

        session.commit()

        assert updated.amount_paise == 50000
        assert updated.description == "Monthly groceries"
        assert updated.transaction_date == date(2026, 11, 2)
        assert updated.payment_method == PaymentMethod.CARD

    finally:
        session.close()
        engine.dispose()


def test_update_transaction_category(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        transaction, _, transport, _ = create_sample_transaction(session)

        updated = update_transaction(
            session=session,
            transaction_id=transaction.id,
            transaction_type=TransactionType.EXPENSE,
            amount_paise=25000,
            description="Bus travel",
            transaction_date=date(2026, 11, 1),
            payment_method=PaymentMethod.UPI,
            category_id=transport.id,
        )

        session.commit()

        assert updated.category_id == transport.id

    finally:
        session.close()
        engine.dispose()


def test_reject_update_for_nonexistent_transaction(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        with pytest.raises(ValueError, match="Transaction not found"):
            update_transaction(
                session=session,
                transaction_id=99999,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=10000,
                description="Missing transaction",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=1,
            )

    finally:
        session.close()
        engine.dispose()


def test_reject_invalid_amount_during_update(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        transaction, food, _, _ = create_sample_transaction(session)

        with pytest.raises(ValueError, match="greater than zero"):
            update_transaction(
                session=session,
                transaction_id=transaction.id,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=0,
                description="Invalid update",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=food.id,
            )

    finally:
        session.close()
        engine.dispose()


def test_reject_wrong_category_type_during_update(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        transaction, _, _, salary = create_sample_transaction(session)

        with pytest.raises(ValueError, match="does not match"):
            update_transaction(
                session=session,
                transaction_id=transaction.id,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=25000,
                description="Incorrect category",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=salary.id,
            )

    finally:
        session.close()
        engine.dispose()


def test_reject_empty_description_during_update(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        transaction, food, _, _ = create_sample_transaction(session)

        with pytest.raises(ValueError, match="Description cannot be empty"):
            update_transaction(
                session=session,
                transaction_id=transaction.id,
                transaction_type=TransactionType.EXPENSE,
                amount_paise=25000,
                description="   ",
                transaction_date=date(2026, 11, 2),
                payment_method=PaymentMethod.CASH,
                category_id=food.id,
            )

    finally:
        session.close()
        engine.dispose()
