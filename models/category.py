
from enum import Enum

from sqlalchemy import (
    Boolean,
    Enum as SQLAlchemyEnum,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    category_type: Mapped[CategoryType] = mapped_column(
        SQLAlchemyEnum(CategoryType),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


    # Transactions belonging to this category.
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="category"
    )


    # Subcategories belonging to this category.
    subcategories: Mapped[list["Subcategory"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )
    
        # Transactions belonging to this category.
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="category"
    )

    # Subcategories belonging to this category.
    subcategories: Mapped[list["Subcategory"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )