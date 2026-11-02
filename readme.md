# SpendWise – Personal Finance & Transaction Analyzer

**SpendWise** is a Python-based personal finance application that helps users record, organize and analyze their income and expenses through an interactive dashboard.

Built with Python, Streamlit and SQLite, the application provides transaction management, customizable categories, financial summaries and interactive spending visualizations.

The project focuses on clean code organization, database management, input validation and automated testing.

## Features

### 1. Transaction Management
- Record income and expense transactions.
- Edit and delete existing transactions.
- View transaction history.
- Search transactions by description.
- Filter by transaction type, category, payment method and date.
- Sort transactions by date, amount or description.

### 2. Category Management
- Create custom income and expense categories.
- Create subcategories.
- Rename existing categories and subcategories.
- Prevent duplicate category names.
- Organize transactions using categories and subcategories.

### 3. Financial Dashboard
- View total income and expenses.
- Calculate remaining balance.
- Calculate savings rate.
- Visualize monthly income versus expenses.
- Analyze spending by category.
- Identify the top five spending categories.

### 4. Data Management
- Store financial records locally using SQLite.
- Maintain relationships between transactions, categories and subcategories.
- Use database constraints to protect data integrity.
- Store monetary values as integer paise to avoid floating-point precision issues.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application development |
| Streamlit | Interactive web interface |
| SQLite | Local database |
| SQLAlchemy | ORM and database operations |
| Alembic | Database migrations |
| Pandas | Data processing |
| Plotly | Interactive visualizations |
| Pytest | Automated testing |
| Git & GitHub | Version control |

## Application Architecture

The project follows a modular structure that separates the user interface, business logic, database operations and data models.

```text
SpendWise/
│
├── app.py
│
├── database/
│   └── database.py
│
├── models/
│   ├── __init__.py
│   ├── transaction.py
│   ├── category.py
│   └── subcategory.py
│
├── services/
│   ├── transaction_service.py
│   └── category_service.py
│
├── migrations/
│   └── versions/
│
├── tests/
│   ├── test_transactions.py
│   ├── test_category_service.py
│   ├── test_database_integrity.py
│   ├── test_transaction_service.py
│   ├── test_transaction_history.py
│   ├── test_transaction_delete.py
│   ├── test_transaction_update.py
│   └── test_category_management.py
│
├── data/
│
├── requirements.txt
├── alembic.ini
└── README.md
```

### Architecture Overview

- **Presentation Layer:** Streamlit handles user interaction and application pages.
- **Service Layer:** Contains business logic, validation and transaction/category operations.
- **Model Layer:** Defines database entities, relationships and constraints using SQLAlchemy.
- **Database Layer:** Manages SQLite connections and database initialization.
- **Testing Layer:** Uses pytest to verify business logic and database behaviour.

## Getting Started

### Prerequisites

- Python 3.14.7 (or a compatible Python version)
- Git
- Visual Studio Code (recommended)

### 1. Clone the repository

```bash
git clone https://github.com/sher122/SpendWise.git
cd SpendWise
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
py -3.14 -m venv .venv
```

### 3. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, you can use the virtual environment's Python executable directly instead.

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Run the application

```powershell
python -m streamlit run app.py
```

Open the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

## Running Tests

Run the complete automated test suite:

```powershell
python -m pytest -v
```

The tests cover transaction operations, category management, validation, database relationships and data integrity.

## Database Design

SpendWise uses SQLite with SQLAlchemy ORM.

The main entities are:

- **Transaction:** Stores transaction type, amount, description, date and payment method.
- **Category:** Organizes transactions into income or expense categories.
- **Subcategory:** Provides more detailed classification within a category.

Database relationships and constraints help maintain consistent financial records.

## Design Decisions

- **Integer-based monetary storage:** Amounts are stored in paise rather than floating-point rupees to avoid precision errors.
- **Service-layer validation:** Business rules are handled separately from the user interface.
- **Database transactions:** Changes are committed explicitly by the application.
- **Local-first storage:** Financial records remain in the local SQLite database.
- **Automated testing:** Pytest helps identify regressions as new features are introduced.

## Future Enhancements

- Monthly budget management and budget alerts.
- CSV transaction import and export.
- Duplicate transaction detection during import.
- Month-over-month financial comparisons.
- Advanced spending insights and reports.
- Improved dashboard filtering and user experience.

## Author

**Sher**

GitHub: [github.com/sher122](https://github.com/sher122)

---

*SpendWise is a personal software engineering project developed to demonstrate Python development, database design, backend business logic, data analysis and automated testing.*