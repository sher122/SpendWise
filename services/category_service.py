from sqlalchemy import select
from sqlalchemy.orm import Session

from models.category import Category, CategoryType
from models.subcategory import Subcategory


# Default expense categories and their subcategories.
DEFAULT_EXPENSE_CATEGORIES = {
    "Food": ["Groceries", "Eating Out"],
    "Rent": ["Monthly Rent", "Other Housing Costs"],
    "Transport": ["Bus", "Cab", "Train", "Metro"],
    "Shopping": ["Clothing", "Electronics", "Personal Items", "Other"],
    "Bills": ["Electricity", "Water", "Internet", "Phone"],
    "Healthcare": ["Medicines", "Doctor", "Hospital", "Other"],
    "Education": ["Courses", "Books", "Fees", "Other"],
    "Entertainment": ["Movies", "Events", "Subscriptions", "Other"],
    "Insurance": ["Health", "Life", "Vehicle", "Other"],
    "Other": ["Miscellaneous"],
}

# Default income categories.
DEFAULT_INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Business",
    "Investment",
    "Other",
]


def seed_default_categories(session: Session) -> None:
    """
    Add default income and expense categories.

    Existing categories and subcategories are preserved.
    Running this function repeatedly will not create duplicates.

    The caller is responsible for committing or rolling back
    the database transaction.
    """

    # Create expense categories and their subcategories.
    for category_name, subcategory_names in DEFAULT_EXPENSE_CATEGORIES.items():

        statement = select(Category).where(
            Category.name == category_name,
            Category.category_type == CategoryType.EXPENSE,
        )

        category = session.scalar(statement)

        if category is None:
            category = Category(
                name=category_name,
                category_type=CategoryType.EXPENSE,
            )
            session.add(category)
            session.flush()

        # Add missing subcategories to the expense category.
        for subcategory_name in subcategory_names:

            statement = select(Subcategory).where(
                Subcategory.name == subcategory_name,
                Subcategory.category_id == category.id,
            )

            subcategory = session.scalar(statement)

            if subcategory is None:
                subcategory = Subcategory(
                    name=subcategory_name,
                    category_id=category.id,
                )
                session.add(subcategory)

    # Create income categories.
    for category_name in DEFAULT_INCOME_CATEGORIES:

        statement = select(Category).where(
            Category.name == category_name,
            Category.category_type == CategoryType.INCOME,
        )

        category = session.scalar(statement)

        if category is None:
            category = Category(
                name=category_name,
                category_type=CategoryType.INCOME,
            )
            session.add(category)

    # Send pending changes to the database without committing.
    session.flush()