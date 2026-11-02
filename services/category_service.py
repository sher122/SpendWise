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

    
def create_category(
    session: Session,
    name: str,
    category_type: CategoryType,
) -> Category:
    """Create a custom income or expense category."""

    if not isinstance(category_type, CategoryType):
        raise ValueError("Invalid category type.")

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Category name cannot be empty.")

    name = name.strip()

    if len(name) > 100:
        raise ValueError("Category name cannot exceed 100 characters.")

    existing = session.scalar(
        select(Category).where(
            Category.name == name,
            Category.category_type == category_type,
        )
    )

    if existing is not None:
        raise ValueError("A category with this name already exists.")

    category = Category(
        name=name,
        category_type=category_type,
    )

    session.add(category)
    session.flush()

    return category


def create_subcategory(
    session: Session,
    name: str,
    category_id: int,
) -> Subcategory:
    """Create a subcategory under an active category."""

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Subcategory name cannot be empty.")

    name = name.strip()

    if len(name) > 100:
        raise ValueError("Subcategory name cannot exceed 100 characters.")

    category = session.get(Category, category_id)

    if category is None or not category.is_active:
        raise ValueError("Active category not found.")

    existing = session.scalar(
        select(Subcategory).where(
            Subcategory.name == name,
            Subcategory.category_id == category_id,
        )
    )

    if existing is not None:
        raise ValueError("This subcategory already exists.")

    subcategory = Subcategory(
        name=name,
        category_id=category_id,
    )

    session.add(subcategory)
    session.flush()

    return subcategory


def update_category(
    session: Session,
    category_id: int,
    new_name: str,
) -> Category:
    """Rename an existing category."""

    category = session.get(Category, category_id)

    if category is None:
        raise ValueError("Category not found.")

    if not isinstance(new_name, str) or not new_name.strip():
        raise ValueError("Category name cannot be empty.")

    new_name = new_name.strip()

    if len(new_name) > 100:
        raise ValueError("Category name cannot exceed 100 characters.")

    existing = session.scalar(
        select(Category).where(
            Category.name == new_name,
            Category.category_type == category.category_type,
            Category.id != category_id,
        )
    )

    if existing is not None:
        raise ValueError("A category with this name already exists.")

    category.name = new_name
    session.flush()

    return category


def update_subcategory(
    session: Session,
    subcategory_id: int,
    new_name: str,
) -> Subcategory:
    """Rename an existing subcategory."""

    subcategory = session.get(Subcategory, subcategory_id)

    if subcategory is None:
        raise ValueError("Subcategory not found.")

    if not isinstance(new_name, str) or not new_name.strip():
        raise ValueError("Subcategory name cannot be empty.")

    new_name = new_name.strip()

    if len(new_name) > 100:
        raise ValueError("Subcategory name cannot exceed 100 characters.")

    existing = session.scalar(
        select(Subcategory).where(
            Subcategory.name == new_name,
            Subcategory.category_id == subcategory.category_id,
            Subcategory.id != subcategory_id,
        )
    )

    if existing is not None:
        raise ValueError("This subcategory already exists.")

    subcategory.name = new_name
    session.flush()

    return subcategory
