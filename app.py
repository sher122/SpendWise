
from datetime import date
from decimal import Decimal, InvalidOperation

import streamlit as st
from sqlalchemy import func, select

from database.database import SessionLocal, init_db
from models.category import Category, CategoryType
from models.subcategory import Subcategory
from models.transaction import PaymentMethod, Transaction, TransactionType
from services.category_service import seed_default_categories
from services.transaction_service import create_transaction


# --------------------------------------------------
# Database initialization
# --------------------------------------------------

init_db()

# Seed default categories the first time the app runs.
with SessionLocal() as session:
    seed_default_categories(session)
    session.commit()


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="SpendWise | Personal Finance",
    layout="wide",
)

st.title("SpendWise")
st.caption("Your personal finance companion")

st.sidebar.title("SpendWise")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Transactions", "Budgets", "Reports"],
)


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

if page == "Dashboard":

    st.header("Financial Overview")
    st.write("Your financial summary based on saved transactions.")

    with SessionLocal() as session:

        income = session.scalar(
            select(func.coalesce(func.sum(Transaction.amount_paise), 0))
            .where(Transaction.transaction_type == TransactionType.INCOME)
        )

        expenses = session.scalar(
            select(func.coalesce(func.sum(Transaction.amount_paise), 0))
            .where(Transaction.transaction_type == TransactionType.EXPENSE)
        )

        income_rupees = income / 100
        expenses_rupees = expenses / 100
        balance_rupees = income_rupees - expenses_rupees

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Income", f"₹{income_rupees:,.2f}")
        col2.metric("Total Expenses", f"₹{expenses_rupees:,.2f}")
        col3.metric("Remaining Balance", f"₹{balance_rupees:,.2f}")

        st.divider()

        st.subheader("Getting started")

        transaction_count = session.scalar(
            select(func.count()).select_from(Transaction)
        )

        if transaction_count == 0:
            st.info(
                "No transactions yet. Open Transactions to record "
                "your first income or expense."
            )
        else:
            st.success(
                f"You have recorded {transaction_count} transaction(s)."
            )


# --------------------------------------------------
# Transactions
# --------------------------------------------------


elif page == "Transactions":

    st.header("Add a Transaction")
    st.write("Record your income and expenses.")

    transaction_type_label = st.radio(
        "Transaction type",
        ["Expense", "Income"],
        horizontal=True,
    )

    if transaction_type_label == "Expense":
        transaction_type = TransactionType.EXPENSE
        category_type = CategoryType.EXPENSE
    else:
        transaction_type = TransactionType.INCOME
        category_type = CategoryType.INCOME

    # Load active categories.
    with SessionLocal() as session:
        categories = session.scalars(
            select(Category)
            .where(
                Category.category_type == category_type,
                Category.is_active.is_(True),
            )
            .order_by(Category.name)
        ).all()

    if not categories:
        st.warning("No active categories are available.")

    else:
        # Keep category selection OUTSIDE the form.
        # This allows Streamlit to refresh subcategories immediately.
        category = st.selectbox(
            "Category",
            categories,
            format_func=lambda item: item.name,
            key="transaction_category",
        )

        # Fetch subcategories for the currently selected category.
        with SessionLocal() as session:
            subcategories = session.scalars(
                select(Subcategory)
                .where(
                    Subcategory.category_id == category.id,
                    Subcategory.is_active.is_(True),
                )
                .order_by(Subcategory.name)
            ).all()

        subcategory_options = [None] + subcategories

        # Keep subcategory selection OUTSIDE the form too.
        subcategory = st.selectbox(
            "Subcategory (optional)",
            subcategory_options,
            format_func=lambda item: (
                "None" if item is None else item.name
            ),
            key="transaction_subcategory",
        )

        # The remaining transaction details go inside the form.
        with st.form("transaction_form"):

            amount_input = st.text_input(
                "Amount (₹)",
                placeholder="Example: 1250.50",
            )

            description = st.text_input(
                "Description",
                placeholder="Example: Monthly groceries",
                max_chars=200,
            )

            transaction_date = st.date_input(
                "Transaction date",
                value=date.today(),
            )

            payment_method = st.selectbox(
                "Payment method",
                list(PaymentMethod),
                format_func=lambda item: item.value.replace(
                    "_", " "
                ).title(),
            )

            submitted = st.form_submit_button(
                "Save Transaction",
                type="primary",
            )

        if submitted:

            try:
                amount_decimal = Decimal(amount_input.strip())

                if not amount_decimal.is_finite():
                    raise ValueError("Enter a valid transaction amount.")

                amount_in_paise = amount_decimal * 100

                if amount_in_paise != amount_in_paise.to_integral_value():
                    raise ValueError(
                        "Amount can have a maximum of two decimal places."
                    )

                amount_paise = int(amount_in_paise)

                with SessionLocal() as session:

                    create_transaction(
                        session=session,
                        transaction_type=transaction_type,
                        amount_paise=amount_paise,
                        description=description,
                        transaction_date=transaction_date,
                        payment_method=payment_method,
                        category_id=category.id,
                        subcategory_id=(
                            subcategory.id
                            if subcategory is not None
                            else None
                        ),
                    )

                    session.commit()

                st.success("Transaction saved successfully! 🎉")

            except (InvalidOperation, ValueError) as error:
                st.error(str(error))

            except Exception:
                st.error(
                    "Something went wrong while saving the transaction. "
                    "Please try again."
                )

# --------------------------------------------------
# Budgets
# --------------------------------------------------

elif page == "Budgets":

    st.header("Budgets")
    st.info("Budget management is coming soon.")


# --------------------------------------------------
# Reports
# --------------------------------------------------

elif page == "Reports":

    st.header("Reports")
    st.info("Financial reports are coming soon.")
