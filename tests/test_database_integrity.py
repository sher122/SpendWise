import pytest

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError

from database.database import Base, enable_foreign_keys
import models


def create_test_engine(tmp_path):
    """Create an isolated SQLite database for integrity tests."""

    test_database = tmp_path / "test_integrity.db"

    test_engine = create_engine(
        f"sqlite:///{test_database}",
        connect_args={"check_same_thread": False},
    )

    # Reuse the application's foreign-key configuration.
    event.listen(test_engine, "connect", enable_foreign_keys)

    Base.metadata.create_all(bind=test_engine)

    return test_engine


def test_foreign_keys_are_enabled(tmp_path):
    """Verify that SQLite foreign-key enforcement is active."""

    test_engine = create_test_engine(tmp_path)

    try:
        with test_engine.connect() as connection:
            result = connection.execute(
                text("PRAGMA foreign_keys")
            ).scalar()

        assert result == 1

    finally:
        test_engine.dispose()


def test_invalid_category_reference_is_rejected(tmp_path):
    """Verify that a transaction cannot reference a nonexistent category."""

    test_engine = create_test_engine(tmp_path)

    try:
        with pytest.raises(IntegrityError):
            with test_engine.begin() as connection:
                connection.execute(
                    text("""
                        INSERT INTO transactions (
                            transaction_type,
                            amount_paise,
                            description,
                            transaction_date,
                            payment_method,
                            category_id,
                            subcategory_id
                        )
                        VALUES (
                            'EXPENSE',
                            50000,
                            'Test transaction',
                            '2026-11-02',
                            'CASH',
                            99999,
                            NULL
                        )
                    """)
                )

    finally:
        test_engine.dispose()

def test_non_positive_transaction_amount_is_rejected(tmp_path):
    """Verify that zero and negative transaction amounts are rejected."""

    test_engine = create_test_engine(tmp_path)

    try:
        with test_engine.begin() as connection:

            # Create a valid category first.
            result = connection.execute(
                text("""
                    INSERT INTO categories (name, category_type, is_active)
                    VALUES ('Food', 'EXPENSE', 1)
                """)
            )

            category_id = result.lastrowid

            # Try inserting zero and negative amounts.
            for invalid_amount in (0, -100):
                with pytest.raises(IntegrityError):
                    with connection.begin_nested():
                        connection.execute(
                            text("""
                                INSERT INTO transactions (
                                    transaction_type,
                                    amount_paise,
                                    description,
                                    transaction_date,
                                    payment_method,
                                    category_id,
                                    subcategory_id
                                )
                                VALUES (
                                    'EXPENSE',
                                    :amount,
                                    'Invalid transaction',
                                    '2026-11-02',
                                    'CASH',
                                    :category_id,
                                    NULL
                                )
                            """),
                            {
                                "amount": invalid_amount,
                                "category_id": category_id,
                            },
                        )

    finally:
        test_engine.dispose()

def test_duplicate_category_name_and_type_is_rejected(tmp_path):
    """Reject two categories with the same name and type."""

    test_engine = create_test_engine(tmp_path)

    try:
        with test_engine.begin() as connection:

            # Insert the first Food expense category.
            connection.execute(
                text("""
                    INSERT INTO categories (name, category_type, is_active)
                    VALUES ('Food', 'EXPENSE', 1)
                """)
            )

            # Attempt to insert the same category again.
            with pytest.raises(IntegrityError):
                with connection.begin_nested():
                    connection.execute(
                        text("""
                            INSERT INTO categories (
                                name, category_type, is_active
                            )
                            VALUES ('Food', 'EXPENSE', 1)
                        """)
                    )

    finally:
        test_engine.dispose()


def test_same_category_name_with_different_types_is_allowed(tmp_path):
    """Allow the same category name for income and expenses."""

    test_engine = create_test_engine(tmp_path)

    try:
        with test_engine.begin() as connection:

            connection.execute(
                text("""
                    INSERT INTO categories (name, category_type, is_active)
                    VALUES ('Other', 'EXPENSE', 1)
                """)
            )

            connection.execute(
                text("""
                    INSERT INTO categories (name, category_type, is_active)
                    VALUES ('Other', 'INCOME', 1)
                """)
            )

            result = connection.execute(
                text("SELECT COUNT(*) FROM categories WHERE name = 'Other'")
            ).scalar()

            assert result == 2

    finally:
        test_engine.dispose()


def test_different_category_names_with_same_type_are_allowed(tmp_path):
    """Allow different expense category names."""

    test_engine = create_test_engine(tmp_path)

    try:
        with test_engine.begin() as connection:

            connection.execute(
                text("""
                    INSERT INTO categories (name, category_type, is_active)
                    VALUES ('Food', 'EXPENSE', 1)
                """)
            )

            connection.execute(
                text("""
                    INSERT INTO categories (name, category_type, is_active)
                    VALUES ('Transport', 'EXPENSE', 1)
                """)
            )

            result = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM categories
                    WHERE category_type = 'EXPENSE'
                """)
            ).scalar()

            assert result == 2

    finally:
        test_engine.dispose()