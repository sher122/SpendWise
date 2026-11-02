
from datetime import date

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from database.database import Base, enable_foreign_keys
from models.category import Category, CategoryType
from models.transaction import PaymentMethod, Transaction, TransactionType
from services.transaction_service import (
    create_transaction,
    delete_transaction,
)


def create_test_session(tmp_path):
    """Create an isolated SQLite database for deletion tests."""
    test_database = tmp_path / "test_delete.db"

    test_engine = create_engine(
        f"sqlite:///{test_database}",
        connect_args={"check_same_thread": False},
    )

    event.listen(test_engine, "connect", enable_foreign_keys)

    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(bind=test_engine)

    return test_engine, TestSession()


def create_sample_transaction(session):
    """Create one expense transaction for testing."""
    food = Category(
        name="Food",
        category_type=CategoryType.EXPENSE,
    )

    session.add(food)
    session.flush()

    transaction = create_transaction(
        session=session,
        transaction_type=TransactionType.EXPENSE,
        amount_paise=25000,
        description="Weekly groceries",
        transaction_date=date(2026, 11, 2),
        payment_method=PaymentMethod.UPI,
        category_id=food.id,
    )

    session.commit()

    return transaction


def test_delete_existing_transaction(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        transaction = create_sample_transaction(session)
        transaction_id = transaction.id

        delete_transaction(session, transaction_id)
        session.commit()

        deleted_transaction = session.get(
            Transaction,
            transaction_id,
        )

        assert deleted_transaction is None

    finally:
        session.close()
        engine.dispose()


def test_deleted_transaction_is_removed_from_history(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        transaction = create_sample_transaction(session)

        delete_transaction(session, transaction.id)
        session.commit()

        remaining_transactions = session.scalars(
            select(Transaction)
        ).all()

        assert len(remaining_transactions) == 0

    finally:
        session.close()
        engine.dispose()


def test_delete_nonexistent_transaction(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        with pytest.raises(ValueError, match="Transaction not found"):
            delete_transaction(session, 99999)

    finally:
        session.close()
        engine.dispose()
