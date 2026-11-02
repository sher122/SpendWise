
from datetime import date
from decimal import Decimal, InvalidOperation

import streamlit as st
import pandas as pd
import plotly.express as px

from sqlalchemy import func, select

from database.database import SessionLocal, init_db
from models.category import Category, CategoryType
from models.subcategory import Subcategory
from models.transaction import PaymentMethod, Transaction, TransactionType
from services.category_service import seed_default_categories
from services.category_service import (
    seed_default_categories,
    create_category,
    create_subcategory,
    update_category,
    update_subcategory,
    
)

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
    "Manage Categories",
    "Budgets",
    "Reports",
],
)


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

if page == "Dashboard":

    st.header("Financial Overview")
    st.write(
        "Understand your income, expenses, savings and spending patterns."
    )

    with SessionLocal() as session:

        # ------------------------------------------
        # 1. FINANCIAL SUMMARY
        # ------------------------------------------

        income_paise = session.scalar(
            select(
                func.coalesce(func.sum(Transaction.amount_paise), 0)
            ).where(
                Transaction.transaction_type == TransactionType.INCOME
            )
        )

        expenses_paise = session.scalar(
            select(
                func.coalesce(func.sum(Transaction.amount_paise), 0)
            ).where(
                Transaction.transaction_type == TransactionType.EXPENSE
            )
        )

        transaction_count = session.scalar(
            select(func.count()).select_from(Transaction)
        )

        # ------------------------------------------
        # 2. CATEGORY-WISE EXPENSES
        # ------------------------------------------

        category_rows = session.execute(
            select(
                Category.name,
                func.sum(Transaction.amount_paise).label("total"),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .where(
                Transaction.transaction_type == TransactionType.EXPENSE
            )
            .group_by(Category.id, Category.name)
            .order_by(func.sum(Transaction.amount_paise).desc())
        ).all()

        # ------------------------------------------
        # 3. MONTHLY INCOME AND EXPENSES
        # ------------------------------------------

        month_expression = func.strftime(
            "%Y-%m",
            Transaction.transaction_date,
        )

        monthly_rows = session.execute(
            select(
                month_expression.label("month"),
                Transaction.transaction_type,
                func.sum(Transaction.amount_paise).label("total"),
            )
            .group_by(
                month_expression,
                Transaction.transaction_type,
            )
            .order_by(month_expression)
        ).all()

    # ------------------------------------------
    # DISPLAY FINANCIAL KPIs
    # ------------------------------------------

    income_rupees = income_paise / 100
    expenses_rupees = expenses_paise / 100
    balance_rupees = income_rupees - expenses_rupees

    # Savings rate = (Income - Expenses) / Income * 100
    savings_rate = (
        (income_paise - expenses_paise) / income_paise * 100
        if income_paise > 0
        else 0
    )

    st.subheader("Financial Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Income",
        f"₹{income_rupees:,.2f}",
    )

    col2.metric(
        "Total Expenses",
        f"₹{expenses_rupees:,.2f}",
    )

    col3.metric(
        "Remaining Balance",
        f"₹{balance_rupees:,.2f}",
    )

    col4.metric(
        "Savings Rate",
        f"{savings_rate:.2f}%",
        help="Percentage of recorded income remaining after expenses.",
    )

    st.caption(
        f"Based on {transaction_count} recorded transaction(s)."
    )

    if income_paise == 0:
        st.info(
            "Add income transactions to calculate a meaningful savings rate."
        )

    st.divider()

    # ------------------------------------------
    # MONTHLY INCOME VS EXPENSE CHART
    # ------------------------------------------

    st.subheader("Monthly Income vs Expenses")

    monthly_chart_data = [
        {
            "Month": row.month,
            "Type": row.transaction_type.value.title(),
            "Amount": row.total / 100,
        }
        for row in monthly_rows
    ]

    if monthly_chart_data:

        monthly_df = pd.DataFrame(monthly_chart_data)

        monthly_figure = px.bar(
            monthly_df,
            x="Month",
            y="Amount",
            color="Type",
            barmode="group",
            title="Monthly Financial Performance",
            labels={
                "Month": "Month",
                "Amount": "Amount (₹)",
                "Type": "Transaction Type",
            },
        )

        monthly_figure.update_layout(
            xaxis_title="Month",
            yaxis_title="Amount (₹)",
            legend_title="Transaction Type",
            hovermode="x unified",
        )

        st.plotly_chart(
            monthly_figure,
            use_container_width=True,
        )

    else:
        st.info(
            "Add transactions to see your monthly financial performance."
        )

    st.divider()

    # ------------------------------------------
    # CATEGORY-WISE EXPENSE BREAKDOWN
    # ------------------------------------------

    st.subheader("Expense Breakdown by Category")

    category_chart_data = [
        {
            "Category": row.name,
            "Amount": row.total / 100,
        }
        for row in category_rows
    ]

    if category_chart_data:

        category_df = pd.DataFrame(category_chart_data)

        col1, col2 = st.columns(2)

        with col1:

            category_figure = px.pie(
                category_df,
                names="Category",
                values="Amount",
                hole=0.5,
                title="Where Your Money Goes",
            )

            category_figure.update_traces(
                textposition="inside",
                textinfo="percent+label",
            )

            st.plotly_chart(
                category_figure,
                use_container_width=True,
            )

        # ------------------------------------------
        # TOP FIVE SPENDING CATEGORIES
        # ------------------------------------------

        with col2:

            st.subheader("Top 5 Spending Categories")

            top_categories_df = (
                category_df
                .head(5)
                .sort_values("Amount", ascending=True)
            )

            top_figure = px.bar(
                top_categories_df,
                x="Amount",
                y="Category",
                orientation="h",
                title="Highest Expense Categories",
                labels={
                    "Amount": "Amount (₹)",
                    "Category": "Category",
                },
                text="Amount",
            )

            top_figure.update_traces(
                texttemplate="₹%{text:,.2f}",
                textposition="outside",
            )

            top_figure.update_layout(
                yaxis_title="",
                xaxis_title="Amount (₹)",
            )

            st.plotly_chart(
                top_figure,
                use_container_width=True,
            )

        # Category-wise numerical summary.
        st.subheader("Category Spending Details")

        display_category_df = category_df.copy()

        display_category_df["Amount"] = (
            display_category_df["Amount"].map(
                lambda amount: f"₹{amount:,.2f}"
            )
        )

        st.dataframe(
            display_category_df,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "No expense transactions available for category analysis."
        )

    st.divider()

    # ------------------------------------------
    # GETTING STARTED
    # ------------------------------------------

    st.subheader("Getting Started")

    if transaction_count == 0:

        st.info(
            "No transactions yet. Open Transactions to record "
            "your first income or expense."
        )

    else:

        st.success(
            f"SpendWise currently contains {transaction_count} "
            "recorded transaction(s)."
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

            except Exception as error:
                st.error(
                    f"Transaction save failed: {type(error).__name__}: {error}"
                )
                st.exception(error)


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

                except Exception as error:
                    st.error(
                        f"Transaction history failed: {type(error).__name__}: {error}"
                    )
                    st.exception(error)

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
# Manage Categories
# --------------------------------------------------

elif page == "Manage Categories":

    st.header("Manage Categories")
    st.write(
        "Create, rename and deactivate your income and expense categories."
    )

    # CREATE CATEGORY
    st.subheader("Create a Category")

    with st.form("create_category_form"):
        new_category_name = st.text_input(
            "Category name",
            max_chars=100,
        )

        new_category_type_label = st.selectbox(
            "Category type",
            ["Expense", "Income"],
        )

        create_category_button = st.form_submit_button(
            "Create Category",
            type="primary",
        )

    if create_category_button:
        try:
            selected_type = (
                CategoryType.EXPENSE
                if new_category_type_label == "Expense"
                else CategoryType.INCOME
            )

            with SessionLocal() as session:
                create_category(
                    session,
                    new_category_name,
                    selected_type,
                )
                session.commit()

            st.success("Category created successfully!")
            st.rerun()

        except ValueError as error:
            st.error(str(error))

        except Exception:
            st.error("Unable to create the category. Please try again.")

    st.divider()

    # LOAD ACTIVE CATEGORIES
    with SessionLocal() as session:
        active_categories = session.scalars(
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.name)
        ).all()

        category_data = [
            {
                "id": item.id,
                "name": item.name,
                "type": item.category_type.value.title(),
            }
            for item in active_categories
        ]

    st.subheader("Active Categories")

    if category_data:
        st.dataframe(
            category_data,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No active categories available.")

    st.divider()

    # CREATE SUBCATEGORY
    st.subheader("Create a Subcategory")

    if active_categories:
        category_lookup = {
            item.id: item for item in active_categories
        }

        with st.form("create_subcategory_form"):
            parent_category_id = st.selectbox(
                "Parent category",
                list(category_lookup.keys()),
                format_func=lambda item: category_lookup[item].name,
            )

            new_subcategory_name = st.text_input(
                "Subcategory name",
                max_chars=100,
            )

            create_subcategory_button = st.form_submit_button(
                "Create Subcategory",
                type="primary",
            )

        if create_subcategory_button:
            try:
                with SessionLocal() as session:
                    create_subcategory(
                        session,
                        new_subcategory_name,
                        parent_category_id,
                    )
                    session.commit()

                st.success("Subcategory created successfully!")
                st.rerun()

            except ValueError as error:
                st.error(str(error))

            except Exception:
                st.error(
                    "Unable to create the subcategory. Please try again."
                )
    else:
        st.info("Create an active category before adding subcategories.")

    st.divider()

    # RENAME CATEGORY
    st.subheader("Rename a Category")

    if active_categories:
        with st.form("rename_category_form"):
            rename_category_id = st.selectbox(
                "Select category to rename",
                list(category_lookup.keys()),
                format_func=lambda item: category_lookup[item].name,
            )

            renamed_category = st.text_input(
                "New category name",
                max_chars=100,
            )

            rename_category_button = st.form_submit_button(
                "Rename Category",
            )

        if rename_category_button:
            try:
                with SessionLocal() as session:
                    update_category(
                        session,
                        rename_category_id,
                        renamed_category,
                    )
                    session.commit()

                st.success("Category renamed successfully!")
                st.rerun()

            except ValueError as error:
                st.error(str(error))

            except Exception:
                st.error("Unable to rename the category.")
    else:
        st.info("No active categories available to rename.")

    st.divider()

    # RENAME SUBCATEGORY
    st.subheader("Rename a Subcategory")

    with SessionLocal() as session:
        active_subcategories = session.scalars(
            select(Subcategory)
            .join(Category)
            .where(
                Subcategory.is_active.is_(True),
                Category.is_active.is_(True),
            )
            .order_by(Subcategory.name)
        ).all()

        subcategory_data = {
            item.id: f"{item.name} — {item.category.name}"
            for item in active_subcategories
        }

    if active_subcategories:
        with st.form("rename_subcategory_form"):
            rename_subcategory_id = st.selectbox(
                "Select subcategory",
                list(subcategory_data.keys()),
                format_func=lambda item: subcategory_data[item],
            )

            renamed_subcategory = st.text_input(
                "New subcategory name",
                max_chars=100,
            )

            rename_subcategory_button = st.form_submit_button(
                "Rename Subcategory",
            )

        if rename_subcategory_button:
            try:
                with SessionLocal() as session:
                    update_subcategory(
                        session,
                        rename_subcategory_id,
                        renamed_subcategory,
                    )
                    session.commit()

                st.success("Subcategory renamed successfully!")
                st.rerun()

            except ValueError as error:
                st.error(str(error))

            except Exception:
                st.error("Unable to rename the subcategory.")
    else:
        st.info("No active subcategories available.")

    st.divider()

   
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
