
from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database.database import Base, enable_foreign_keys
from models.category import Category, CategoryType
from models.transaction import PaymentMethod, TransactionType
from services.transaction_service import (
    create_transaction,
    get_transactions,
)


def create_test_session(tmp_path):
    """Create an isolated SQLite database for testing."""
    test_database = tmp_path / "test_history.db"

    test_engine = create_engine(
        f"sqlite:///{test_database}",
        connect_args={"check_same_thread": False},
    )

    event.listen(test_engine, "connect", enable_foreign_keys)

    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(bind=test_engine)

    return test_engine, TestSession()


def create_sample_transactions(session):
    """Create sample income and expense transactions."""

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

    create_transaction(
        session=session,
        transaction_type=TransactionType.EXPENSE,
        amount_paise=25000,
        description="Weekly groceries",
        transaction_date=date(2026, 11, 1),
        payment_method=PaymentMethod.UPI,
        category_id=food.id,
    )

    create_transaction(
        session=session,
        transaction_type=TransactionType.EXPENSE,
        amount_paise=15000,
        description="Bus ticket",
        transaction_date=date(2026, 11, 2),
        payment_method=PaymentMethod.CASH,
        category_id=transport.id,
    )

    create_transaction(
        session=session,
        transaction_type=TransactionType.INCOME,
        amount_paise=5000000,
        description="Monthly salary",
        transaction_date=date(2026, 11, 1),
        payment_method=PaymentMethod.BANK_TRANSFER,
        category_id=salary.id,
    )

    session.commit()

    return food, transport, salary


def test_get_all_transactions(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        create_sample_transactions(session)

        transactions = get_transactions(session)

        assert len(transactions) == 3

    finally:
        session.close()
        engine.dispose()


def test_filter_transactions_by_type(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        create_sample_transactions(session)

        expenses = get_transactions(
            session,
            transaction_type=TransactionType.EXPENSE,
        )

        income = get_transactions(
            session,
            transaction_type=TransactionType.INCOME,
        )

        assert len(expenses) == 2
        assert len(income) == 1

    finally:
        session.close()
        engine.dispose()


def test_filter_transactions_by_category(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        food, _, _ = create_sample_transactions(session)

        transactions = get_transactions(
            session,
            category_id=food.id,
        )

        assert len(transactions) == 1
        assert transactions[0].description == "Weekly groceries"

    finally:
        session.close()
        engine.dispose()


def test_filter_transactions_by_payment_method(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        create_sample_transactions(session)

        transactions = get_transactions(
            session,
            payment_method=PaymentMethod.UPI,
        )

        assert len(transactions) == 1
        assert transactions[0].description == "Weekly groceries"

    finally:
        session.close()
        engine.dispose()


def test_filter_transactions_by_date_range(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        create_sample_transactions(session)

        transactions = get_transactions(
            session,
            start_date=date(2026, 11, 2),
            end_date=date(2026, 11, 2),
        )

        assert len(transactions) == 1
        assert transactions[0].description == "Bus ticket"

    finally:
        session.close()
        engine.dispose()


def test_search_transactions_by_description(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        create_sample_transactions(session)

        transactions = get_transactions(
            session,
            search_text="GROCERIES",
        )

        assert len(transactions) == 1
        assert transactions[0].description == "Weekly groceries"

    finally:
        session.close()
        engine.dispose()


def test_sort_transactions_by_amount_descending(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        create_sample_transactions(session)

        transactions = get_transactions(
            session,
            sort_by="amount",
            descending=True,
        )

        amounts = [item.amount_paise for item in transactions]

        assert amounts == [5000000, 25000, 15000]

    finally:
        session.close()
        engine.dispose()


def test_sort_transactions_by_date_ascending(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        create_sample_transactions(session)

        transactions = get_transactions(
            session,
            sort_by="date",
            descending=False,
        )

        dates = [item.transaction_date for item in transactions]

        assert dates == sorted(dates)

    finally:
        session.close()
        engine.dispose()


def test_reject_invalid_sort_option(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        with pytest.raises(ValueError, match="Invalid sorting option"):
            get_transactions(session, sort_by="invalid")

    finally:
        session.close()
        engine.dispose()


def test_reject_invalid_date_range(tmp_path):
    engine, session = create_test_session(tmp_path)

    try:
        with pytest.raises(ValueError, match="Start date cannot be after"):
            get_transactions(
                session,
                start_date=date(2026, 11, 10),
                end_date=date(2026, 11, 1),
            )

    finally:
        session.close()
        engine.dispose()
