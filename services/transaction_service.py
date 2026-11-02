"""
Service functions for creating and managing financial transactions.

This module contains business logic and database validation.
It does not contain Streamlit UI code.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session
from models.category import Category, CategoryType
from models.subcategory import Subcategory
from models.transaction import (
    PaymentMethod,
    Transaction,
    TransactionType,
)


def create_transaction(
    session: Session,
    transaction_type: TransactionType,
    amount_paise: int,
    description: str,
    transaction_date: date,
    payment_method: PaymentMethod,
    category_id: int,
    subcategory_id: int | None = None,
) -> Transaction:
    """
    Validate and add a transaction to the database session.

    The caller is responsible for committing or rolling back
    the database transaction.

    Args:
        session: Active SQLAlchemy database session.
        transaction_type: INCOME or EXPENSE.
        amount_paise: Positive transaction amount in paise.
        description: Short transaction description.
        transaction_date: Date of the transaction.
        payment_method: CASH, UPI, CARD, or BANK_TRANSFER.
        category_id: ID of the selected category.
        subcategory_id: Optional ID of the selected subcategory.

    Returns:
        The newly created Transaction object.

    Raises:
        ValueError: If any transaction details are invalid.
    """

    # 1. Validate the transaction type.
    if not isinstance(transaction_type, TransactionType):
        raise ValueError("Invalid transaction type.")

    # 2. Validate the amount.
    # bool is excluded because True and False are technically integers in Python.
    if isinstance(amount_paise, bool) or not isinstance(amount_paise, int):
        raise ValueError("Amount must be a whole number of paise.")

    if amount_paise <= 0:
        raise ValueError("Amount must be greater than zero.")

    # 3. Validate the description.
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Description cannot be empty.")

    description = description.strip()

    if len(description) > 200:
        raise ValueError("Description cannot exceed 200 characters.")

    # 4. Validate the transaction date.
    if not isinstance(transaction_date, date):
        raise ValueError("Invalid transaction date.")

    # 5. Validate the payment method.
    if not isinstance(payment_method, PaymentMethod):
        raise ValueError("Invalid payment method.")

    # 6. Find and validate the category.
    category = session.get(Category, category_id)

    if category is None:
        raise ValueError("Selected category does not exist.")

    if not category.is_active:
        raise ValueError("Selected category is inactive.")

    # Income transactions must use income categories.
    # Expense transactions must use expense categories.
    if category.category_type.value != transaction_type.value:
        raise ValueError(
            "Selected category does not match the transaction type."
        )

    # 7. Validate the optional subcategory.
    if subcategory_id is not None:
        subcategory = session.get(Subcategory, subcategory_id)

        if subcategory is None:
            raise ValueError("Selected subcategory does not exist.")

        if not subcategory.is_active:
            raise ValueError("Selected subcategory is inactive.")

        if subcategory.category_id != category_id:
            raise ValueError(
                "Selected subcategory does not belong to this category."
            )

    # 8. Create the transaction.
    transaction = Transaction(
        transaction_type=transaction_type,
        amount_paise=amount_paise,
        description=description,
        transaction_date=transaction_date,
        payment_method=payment_method,
        category_id=category_id,
        subcategory_id=subcategory_id,
    )

    # Add and flush, but do not commit.
    # This lets the caller control the database transaction.
    session.add(transaction)
    session.flush()

    return transaction


def get_transactions(
    session: Session,
    transaction_type: TransactionType | None = None,
    category_id: int | None = None,
    payment_method: PaymentMethod | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    search_text: str | None = None,
    sort_by: str = "date",
    descending: bool = True,
) -> list[Transaction]:
    """
    Retrieve transactions with optional filters and sorting.

    Args:
        session: Active SQLAlchemy database session.
        transaction_type: Optional income or expense filter.
        category_id: Optional category filter.
        payment_method: Optional payment method filter.
        start_date: Optional beginning date (inclusive).
        end_date: Optional ending date (inclusive).
        search_text: Optional description search.
        sort_by: Sort by 'date', 'amount', or 'description'.
        descending: Whether to sort in descending order.

    Returns:
        A list of matching transactions.
    """

    if transaction_type is not None and not isinstance(
        transaction_type, TransactionType
    ):
        raise ValueError("Invalid transaction type.")

    if payment_method is not None and not isinstance(
        payment_method, PaymentMethod
    ):
        raise ValueError("Invalid payment method.")

    if start_date is not None and not isinstance(start_date, date):
        raise ValueError("Invalid start date.")

    if end_date is not None and not isinstance(end_date, date):
        raise ValueError("Invalid end date.")

    if start_date and end_date and start_date > end_date:
        raise ValueError("Start date cannot be after end date.")

    sort_columns = {
        "date": Transaction.transaction_date,
        "amount": Transaction.amount_paise,
        "description": Transaction.description,
    }

    if sort_by not in sort_columns:
        raise ValueError("Invalid sorting option.")

    statement = select(Transaction)

    # Apply optional filters.
    if transaction_type is not None:
        statement = statement.where(
            Transaction.transaction_type == transaction_type
        )

    if category_id is not None:
        statement = statement.where(
            Transaction.category_id == category_id
        )

    if payment_method is not None:
        statement = statement.where(
            Transaction.payment_method == payment_method
        )

    if start_date is not None:
        statement = statement.where(
            Transaction.transaction_date >= start_date
        )

    if end_date is not None:
        statement = statement.where(
            Transaction.transaction_date <= end_date
        )

    if search_text and search_text.strip():
        statement = statement.where(
            Transaction.description.ilike(
                f"%{search_text.strip()}%"
            )
        )

    # Apply sorting.
    sort_column = sort_columns[sort_by]

    if descending:
        statement = statement.order_by(
            sort_column.desc(),
            Transaction.id.desc(),
        )
    else:
        statement = statement.order_by(
            sort_column.asc(),
            Transaction.id.asc(),
        )

    return list(session.scalars(statement).all())
