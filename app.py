
from datetime import date
from decimal import Decimal, InvalidOperation

import streamlit as st
from sqlalchemy import func, select

from database.database import SessionLocal, init_db
from models.category import Category, CategoryType
from models.subcategory import Subcategory
from models.transaction import PaymentMethod, Transaction, TransactionType
from services.category_service import seed_default_categories
from services.transaction_service import (
    create_transaction,
    get_transactions,
    delete_transaction,
    update_transaction,
)

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
    [
    "Dashboard",
    "Transactions",
    "Transaction History",
    "Budgets",
    "Reports",
],
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
# Transaction History
# --------------------------------------------------

elif page == "Transaction History":

    st.header("Transaction History")
    st.write("View, search, filter and sort your saved transactions.")

    # Load categories for the category filter.
    with SessionLocal() as session:
        categories = session.scalars(
            select(Category).order_by(Category.name)
        ).all()

    # Search
    search_text = st.text_input(
        "Search by description",
        placeholder="Example: groceries, salary, electricity",
    )

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        type_filter = st.selectbox(
            "Transaction type",
            ["All", "Expense", "Income"],
        )

        category_options = [None] + categories

        selected_category = st.selectbox(
            "Category",
            category_options,
            format_func=lambda item: (
                "All categories" if item is None else item.name
            ),
        )

        start_date = st.date_input(
            "From date",
            value=None,
        )

    with col2:
        payment_options = [None] + list(PaymentMethod)

        selected_payment = st.selectbox(
            "Payment method",
            payment_options,
            format_func=lambda item: (
                "All payment methods"
                if item is None
                else item.value.replace("_", " ").title()
            ),
        )

        sort_label = st.selectbox(
            "Sort by",
            ["Date", "Amount", "Description"],
        )

        sort_direction = st.selectbox(
            "Sort order",
            ["Newest / Highest first", "Oldest / Lowest first"],
        )

        end_date = st.date_input(
            "To date",
            value=None,
        )

    # Convert UI selections into service parameters.
    selected_type = None

    if type_filter == "Expense":
        selected_type = TransactionType.EXPENSE
    elif type_filter == "Income":
        selected_type = TransactionType.INCOME

    sort_mapping = {
        "Date": "date",
        "Amount": "amount",
        "Description": "description",
    }

    descending = sort_direction == "Newest / Highest first"

    
    try:
        with SessionLocal() as session:

            transactions = get_transactions(
                session=session,
                transaction_type=selected_type,
                category_id=(
                    selected_category.id
                    if selected_category is not None
                    else None
                ),
                payment_method=selected_payment,
                start_date=start_date,
                end_date=end_date,
                search_text=search_text,
                sort_by=sort_mapping[sort_label],
                descending=descending,
            )

            transaction_rows = []
            transaction_options = {}

            for transaction in transactions:

                transaction_rows.append({
                    "Date": transaction.transaction_date.strftime("%d %b %Y"),
                    "Type": transaction.transaction_type.value.title(),
                    "Description": transaction.description,
                    "Category": transaction.category.name,
                    "Subcategory": (
                        transaction.subcategory.name
                        if transaction.subcategory is not None
                        else "-"
                    ),
                    "Payment Method": transaction.payment_method.value.replace(
                        "_", " "
                    ).title(),
                    "Amount (₹)": transaction.amount_paise / 100,
                })

                transaction_options[transaction.id] = (
                    f"#{transaction.id} | "
                    f"{transaction.description} | "
                    f"₹{transaction.amount_paise / 100:,.2f}"
                )

        st.divider()

        st.subheader(f"Results: {len(transaction_rows)} transaction(s)")

        if transaction_rows:

            st.dataframe(
                transaction_rows,
                use_container_width=True,
                hide_index=True,
            )

            st.divider()
            
            # ------------------------------------------
            # Edit a Transaction
            # ------------------------------------------

            st.subheader("Edit a Transaction")

            edit_transaction_id = st.selectbox(
                "Select transaction to edit",
                list(transaction_options.keys()),
                format_func=lambda transaction_id: (
                    transaction_options[transaction_id]
                ),
                key="edit_transaction_selection",
            )

            # Load the selected transaction and its related categories.
            with SessionLocal() as session:
                selected_transaction = session.get(
                    Transaction,
                    edit_transaction_id,
                )

                edit_categories = session.scalars(
                    select(Category)
                    .where(
                        Category.category_type
                        == selected_transaction.category.category_type,
                        Category.is_active.is_(True),
                    )
                    .order_by(Category.name)
                ).all()

                edit_subcategories = session.scalars(
                    select(Subcategory)
                    .where(
                        Subcategory.category_id
                        == selected_transaction.category_id,
                        Subcategory.is_active.is_(True),
                    )
                    .order_by(Subcategory.name)
                ).all()

                # Copy values before the session closes.
                current_type = selected_transaction.transaction_type
                current_amount = selected_transaction.amount_paise
                current_description = selected_transaction.description
                current_date = selected_transaction.transaction_date
                current_payment = selected_transaction.payment_method
                current_category_id = selected_transaction.category_id
                current_subcategory_id = selected_transaction.subcategory_id

            st.caption("Update the transaction details below.")

            edit_category_options = {
                category.id: category for category in edit_categories
            }

            edit_category_ids = list(edit_category_options.keys())

            default_category_index = edit_category_ids.index(
                current_category_id
            )

            edit_category_id = st.selectbox(
                "Edit category",
                edit_category_ids,
                index=default_category_index,
                format_func=lambda category_id: (
                    edit_category_options[category_id].name
                ),
                key="edit_category_selection",
            )

            # Reload subcategories when the edit category changes.
            with SessionLocal() as session:
                edit_subcategories = session.scalars(
                    select(Subcategory)
                    .where(
                        Subcategory.category_id == edit_category_id,
                        Subcategory.is_active.is_(True),
                    )
                    .order_by(Subcategory.name)
                ).all()

            edit_subcategory_options = {
                None: "None",
                **{
                    item.id: item.name
                    for item in edit_subcategories
                },
            }

            edit_subcategory_ids = list(edit_subcategory_options.keys())

            default_subcategory_index = (
                edit_subcategory_ids.index(current_subcategory_id)
                if current_subcategory_id in edit_subcategory_ids
                else 0
            )

            with st.form("edit_transaction_form"):

                edit_amount = st.text_input(
                    "Amount (₹)",
                    value=f"{current_amount / 100:.2f}",
                )

                edit_description = st.text_input(
                    "Description",
                    value=current_description,
                    max_chars=200,
                )

                edit_date = st.date_input(
                    "Transaction date",
                    value=current_date,
                )

                edit_payment = st.selectbox(
                    "Payment method",
                    list(PaymentMethod),
                    index=list(PaymentMethod).index(current_payment),
                    format_func=lambda item: (
                        item.value.replace("_", " ").title()
                    ),
                )

                edit_subcategory_id = st.selectbox(
                    "Subcategory (optional)",
                    edit_subcategory_ids,
                    index=default_subcategory_index,
                    format_func=lambda item: edit_subcategory_options[item],
                )

                save_edit = st.form_submit_button(
                    "Save Changes",
                    type="primary",
                )

            if save_edit:

                try:
                    edit_amount_decimal = Decimal(edit_amount.strip())

                    if not edit_amount_decimal.is_finite():
                        raise ValueError(
                            "Enter a valid transaction amount."
                        )

                    edit_amount_in_paise = edit_amount_decimal * 100

                    if (
                        edit_amount_in_paise
                        != edit_amount_in_paise.to_integral_value()
                    ):
                        raise ValueError(
                            "Amount can have a maximum of two decimal places."
                        )

                    with SessionLocal() as session:
                        update_transaction(
                            session=session,
                            transaction_id=edit_transaction_id,
                            transaction_type=current_type,
                            amount_paise=int(edit_amount_in_paise),
                            description=edit_description,
                            transaction_date=edit_date,
                            payment_method=edit_payment,
                            category_id=edit_category_id,
                            subcategory_id=edit_subcategory_id,
                        )

                        session.commit()

                    st.success("Transaction updated successfully!")
                    st.rerun()

                except (InvalidOperation, ValueError) as error:
                    st.error(str(error))

                except Exception:
                    st.error(
                        "Something went wrong while updating the transaction. "
                        "Please try again."
                    )

            st.subheader("Delete a Transaction")

            selected_transaction_id = st.selectbox(
                "Select transaction to delete",
                list(transaction_options.keys()),
                format_func=lambda transaction_id: (
                    transaction_options[transaction_id]
                ),
                key="delete_transaction_selection",
            )

            confirm_delete = st.checkbox(
                "I confirm that I want to permanently delete this transaction.",
                key="confirm_transaction_deletion",
            )

            if st.button(
                "Delete Selected Transaction",
                type="primary",
                disabled=not confirm_delete,
            ):

                with SessionLocal() as session:
                    delete_transaction(
                        session,
                        selected_transaction_id,
                    )
                    session.commit()

                st.success("Transaction deleted successfully!")

                # Clear the confirmation state after deletion.
                st.session_state["confirm_transaction_deletion"] = False

                st.rerun()

        else:
            st.info("No transactions match your selected filters.")

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Unable to load or update transaction history. "
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
