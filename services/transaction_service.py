"""
Service functions for creating and managing financial transactions.

This module contains business logic and database validation.
It does not contain Streamlit UI code.
"""

from datetime import date

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