from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Category, Income, Expense, Budget
import datetime
import hashlib

class DatabaseHandler:
    def __init__(self, db_path='sqlite:///budget.db'):
        """Initialize the database handler with the specified database path.
        
        For in-memory database, use 'sqlite:///:memory:'
        For file-based database, use 'sqlite:///filename.db'
        """
        # Normalize in-memory database path for SQLAlchemy
        if db_path == ':memory:':
            db_path = 'sqlite:///:memory:'
        
        # Import all models for direct access
        self.User = User
        self.Category = Category
        self.Income = Income
        self.Expense = Expense
        self.Budget = Budget
        
        # Create engine with appropriate settings for SQLite
        if 'sqlite' in db_path:
            # SQLite specific settings
            self.engine = create_engine(
                db_path,
                connect_args={'timeout': 30},  # SQLite timeout in seconds
                pool_pre_ping=True  # Verify connections before using them
            )
        else:
            # Settings for other database types
            self.engine = create_engine(
                db_path,
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Verify connections before using them
                pool_size=5,         # Maintain a pool of connections
                max_overflow=10       # Allow up to 10 overflow connections
            )
        
        # Create all tables if they don't exist
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            print(f"Error creating database schema: {e}")
            raise
            
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get a new session for database operations."""
        try:
            return self.Session()
        except Exception as e:
            print(f"Error creating database session: {e}")
            raise
    
    # User operations
    def add_user(self, username, password):
        """Add a new user to the database with hashed password."""
        session = self.get_session()
        # Hash password for security
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        user = User(username=username, password=password_hash)
        session.add(user)
        session.commit()
        user_id = user.id
        session.close()
        return user_id
    
    def authenticate_user(self, username, password):
        """Authenticate a user with username and password.
        Returns user_id if successful, None if not."""
        session = None
        try:
            session = self.get_session()
            # Hash password for comparison
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            user = session.query(User).filter(
                User.username == username,
                User.password == password_hash
            ).first()
            
            return user.id if user else None
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
        finally:
            # Always close the session, even if an exception occurs
            if session:
                session.close()
        
    def create_user(self, username, email=None, password=None, name=None):
        """Create a new user in the database."""
        session = self.get_session()
        
        # If password is provided, hash it
        password_hash = None
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user with provided data
        user = User(
            username=username,
            password=password_hash or "default_password_hash",  # Default hash if none provided
            email=email,
            name=name
        )
        
        session.add(user)
        session.commit()
        user_id = user.id
        session.close()
        return user_id
    
    def get_user(self, user_id):
        """Get user by ID."""
        session = self.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        session.close()
        return user
    
    # Category operations
    def add_category(self, name, description=None, category_type=None):
        """Add a new category."""
        session = self.get_session()
        category = Category(name=name, description=description or "", category_type=category_type)
        session.add(category)
        session.commit()
        category_id = category.id
        session.close()
        return category_id
        
    def create_category(self, name, description="", category_type=None):
        """Create a new category with type."""
        return self.add_category(name, description, category_type)
        
    def get_categories(self):
        """Get all categories."""
        session = self.get_session()
        categories = session.query(Category).all()
        session.close()
        return categories
    
    def get_categories_by_type(self, category_type):
        """Get all categories of a specific type."""
        session = self.get_session()
        categories = session.query(Category).filter(Category.category_type == category_type).all()
        session.close()
        return categories
    
    # Income operations
    def add_income(self, user_id, amount, description, date):
        """Add a new income record."""
        session = self.get_session()
        income = Income(
            user_id=user_id,
            amount=amount,
            description=description,
            date=date
        )
        session.add(income)
        session.commit()
        income_id = income.id
        session.close()
        return income_id
    
    def get_income(self, income_id):
        """Get income by ID."""
        session = self.get_session()
        income = session.query(Income).filter(Income.id == income_id).first()
        session.close()
        return income
    
    def get_incomes_by_user(self, user_id):
        """Get all incomes for a specific user."""
        session = self.get_session()
        incomes = session.query(Income).filter(Income.user_id == user_id).all()
        session.close()
        return incomes
    
    def get_incomes_by_date_range(self, user_id, start_date, end_date):
        """Get all incomes within a date range for a specific user."""
        session = self.get_session()
        incomes = session.query(Income).filter(
            Income.user_id == user_id,
            Income.date >= start_date,
            Income.date <= end_date
        ).all()
        session.close()
        return incomes
    
    # Expense operations
    def add_expense(self, user_id, category_id, amount, description, date, has_apr=False, apr=0.0):
        """Add a new expense record with optional APR for debt tracking."""
        session = self.get_session()
        expense = Expense(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            description=description,
            date=date,
            has_apr=has_apr,
            apr=apr
        )
        session.add(expense)
        session.commit()
        expense_id = expense.id
        session.close()
        return expense_id
        
    def get_expense(self, expense_id):
        """Get a specific expense by ID."""
        session = self.get_session()
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        session.close()
        return expense
        
    def update_expense(self, expense_id, amount, category_id=None, description=None, date=None, has_apr=None, apr=None):
        """Update an existing expense with provided values."""
        session = self.get_session()
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        
        if not expense:
            session.close()
            return False
            
        # Update the expense with new values if provided
        if amount is not None:
            expense.amount = amount
        if category_id is not None:
            expense.category_id = category_id
        if description is not None:
            expense.description = description
        if date is not None:
            expense.date = date
        if has_apr is not None:
            expense.has_apr = has_apr
        if apr is not None:
            expense.apr = apr
            
        try:
            session.commit()
            success = True
        except Exception as e:
            session.rollback()
            success = False
            
        session.close()
        return success
    
    def get_expenses_by_date_range(self, user_id, start_date, end_date):
        """Get all expenses within a date range for a specific user."""
        session = self.get_session()
        expenses = session.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).all()
        session.close()
        return expenses
    
    def get_expenses_by_category(self, user_id, category_id):
        """Get all expenses for a specific category and user."""
        session = self.get_session()
        expenses = session.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.category_id == category_id
        ).all()
        session.close()
        return expenses
    
    # Budget operations
    def set_budget(self, user_id, category_id, amount, month, year):
        """Set a budget for a specific category, month and year."""
        session = self.get_session()
        # Check if budget already exists
        existing_budget = session.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.month == month,
            Budget.year == year
        ).first()
        
        if existing_budget:
            existing_budget.amount = amount
            budget_id = existing_budget.id
        else:
            budget = Budget(
                user_id=user_id,
                category_id=category_id,
                amount=amount,
                month=month,
                year=year
            )
            session.add(budget)
            session.flush()
            budget_id = budget.id
            
        session.commit()
        session.close()
        return budget_id
    
    def get_budget(self, budget_id):
        """Get budget by ID."""
        session = self.get_session()
        budget = session.query(Budget).filter(Budget.id == budget_id).first()
        session.close()
        return budget
    
    def get_budgets_by_month_year(self, user_id, month, year):
        """Get all budgets for a specific month and year."""
        session = self.get_session()
        budgets = session.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.year == year
        ).all()
        session.close()
        return budgets
