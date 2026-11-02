"""Add category and subcategory uniqueness constraints."""

from typing import Sequence, Union

from alembic import op


# Revision identifiers.
revision: str = "d04eef867075"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraints to existing tables."""

    # Add uniqueness to category names by category type.
    with op.batch_alter_table("categories") as batch_op:
        batch_op.create_unique_constraint(
            "uq_category_name_type",
            ["name", "category_type"],
        )

    # Add uniqueness to subcategory names by parent category.
    with op.batch_alter_table("subcategories") as batch_op:
        batch_op.create_unique_constraint(
            "uq_subcategory_name_category",
            ["name", "category_id"],
        )


def downgrade() -> None:
    """Remove the unique constraints."""

    with op.batch_alter_table("subcategories") as batch_op:
        batch_op.drop_constraint(
            "uq_subcategory_name_category",
            type_="unique",
        )

    with op.batch_alter_table("categories") as batch_op:
        batch_op.drop_constraint(
            "uq_category_name_type",
            type_="unique",
        )