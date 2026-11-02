
from datetime import date
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class PaymentMethod(str, Enum):
    CASH = "cash"
    UPI = "upi"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class Transaction(Base):
    __tablename__ = "transactions"

    __table_args__ = (
        CheckConstraint(
            "amount_paise > 0",
            name="check_transaction_amount_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLAlchemyEnum(TransactionType),
        nullable=False,
    )

    amount_paise: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )

    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLAlchemyEnum(PaymentMethod),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
    )

    subcategory_id: Mapped[int | None] = mapped_column(
        ForeignKey("subcategories.id"),
        nullable=True,
    )
        # Link this transaction to its main category.
    category: Mapped["Category"] = relationship(
        back_populates="transactions"
    )

    # Link this transaction to its subcategory, if one is selected.
    subcategory: Mapped["Subcategory | None"] = relationship(
        back_populates="transactions"
    )