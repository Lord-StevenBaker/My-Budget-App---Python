import datetime
from dateutil.relativedelta import relativedelta
import calendar
from db_handler import DatabaseHandler
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io

class BudgetManager:
    def __init__(self, db_handler=None, db_path='sqlite:///budget.db'):
        """Initialize the budget manager with a database handler.
        
        Args:
            db_handler: DatabaseHandler instance (for dependency injection/testing)
            db_path: Path to database file (only used if db_handler is None)
        """
        if db_handler is not None:
            self.db = db_handler
        else:
            self.db = DatabaseHandler(db_path)
        
    # User management
    def create_user(self, name, email):
        """Create a new user."""
        return self.db.create_user(name, email)
    
    def get_user(self, user_id):
        """Get user details."""
        return self.db.get_user(user_id)
    
    # Category management
    def update_expense(self, expense_id, amount, category_id=None, description=None, date=None, has_apr=None, apr=None):
        """Update an existing expense with all possible fields."""
        return self.db.update_expense(expense_id, amount, category_id, description, date, has_apr, apr)
    
    def create_category(self, name, description, category_type):
        """Create a new category."""
        return self.db.create_category(name, description, category_type)
    
    def get_income_categories(self):
        """Get all income categories."""
        return self.db.get_categories_by_type('income')
    
    def get_expense_categories(self):
        """Get all expense categories."""
        return self.db.get_categories_by_type('expense')
    
    # Income management
    def add_income(self, user_id, amount, description, date=None):
        """Add a new income record.
        
        Args:
            user_id: ID of the user who owns this income
            amount: Income amount
            description: Description of the income (e.g., 'Salary', 'Freelance work')
            date: Date of the income, defaults to today if not specified
        """
        if date is None:
            date = datetime.date.today()
            
        return self.db.add_income(user_id, amount, description, date)
    
    def get_total_income(self, user_id, start_date=None, end_date=None):
        """Get total income for a user within a date range."""
        if start_date is None:
            # Default to current month
            today = datetime.date.today()
            start_date = datetime.date(today.year, today.month, 1)
        
        if end_date is None:
            # Default to end of current month
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = datetime.date(today.year, today.month, last_day)
        
        incomes = self.db.get_incomes_by_date_range(user_id, start_date, end_date)
        return sum(income.amount for income in incomes)
    
    # Expense management
    def add_expense(self, user_id, category_id, amount, description="", date=None, has_apr=0, apr=0.0):
        """Add a new expense record."""
        return self.db.add_expense(user_id, category_id, amount, description, date, has_apr, apr)
        
    def calculate_monthly_interest(self, amount, apr):
        """Calculate the monthly interest amount based on APR."""
        # Convert annual rate to monthly
        monthly_rate = apr / 100 / 12
        return amount * monthly_rate
        
    def get_debt_expenses(self, user_id, start_date=None, end_date=None):
        """Get all APR-bearing expenses within a date range."""
        if start_date is None:
            # Default to current month
            today = datetime.date.today()
            start_date = datetime.date(today.year, today.month, 1)
        
        if end_date is None:
            # Default to end of current month
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = datetime.date(today.year, today.month, last_day)
        
        # Get all expenses in date range
        expenses = self.db.get_expenses_by_date_range(user_id, start_date, end_date)
        
        # Filter for only those with APR (has_apr is an Integer field, 1 = yes, 0 = no)
        debt_expenses = [expense for expense in expenses if expense.has_apr == 1]
        
        return debt_expenses
        
    def generate_debt_report(self, user_id, start_date=None, end_date=None):
        """Generate a detailed report of all debt expenses with APR."""
        if start_date is None:
            # Default to current month
            today = datetime.date.today()
            start_date = datetime.date(today.year, today.month, 1)
        
        if end_date is None:
            # Default to end of current month
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = datetime.date(today.year, today.month, last_day)
            
        # Use a single session for all database operations
        session = self.db.get_session()
        try:
            from sqlalchemy.orm import joinedload
            
            # Get all debt expenses with their categories in a single query
            expenses_query = session.query(self.db.Expense).\
                filter(self.db.Expense.user_id == user_id,
                       self.db.Expense.date >= start_date,
                       self.db.Expense.date <= end_date,
                       self.db.Expense.has_apr == 1).\
                options(joinedload(self.db.Expense.category))
                
            debt_expenses = expenses_query.all()
            
            data = []
            total_principal = 0
            total_monthly_interest = 0
            total_annual_interest = 0
            
            for expense in debt_expenses:
                # Get category name
                category_name = expense.category.name if expense.category else "Unknown"
                
                # Calculate interest
                monthly_interest = self.calculate_monthly_interest(expense.amount, expense.apr)
                annual_interest = monthly_interest * 12
                
                # Track totals
                total_principal += expense.amount
                total_monthly_interest += monthly_interest
                total_annual_interest += annual_interest
                
                data.append({
                    'id': expense.id,
                    'date': expense.date,
                    'description': expense.description,
                    'category': category_name,
                    'amount': expense.amount,
                    'apr': expense.apr,
                    'monthly_interest': monthly_interest,
                    'annual_interest': annual_interest
                })
            
            # Add summary row
            if data:
                data.append({
                    'id': 'TOTAL',
                    'date': None,
                    'description': 'TOTAL',
                    'category': '',
                    'amount': total_principal,
                    'apr': None,
                    'monthly_interest': total_monthly_interest,
                    'annual_interest': total_annual_interest
                })
            
            return pd.DataFrame(data)
        finally:
            session.close()
    
    def get_total_expense(self, user_id, start_date=None, end_date=None):
        """Get total expense for a user within a date range."""
        if start_date is None:
            # Default to current month
            today = datetime.date.today()
            start_date = datetime.date(today.year, today.month, 1)
        
        if end_date is None:
            # Default to end of current month
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = datetime.date(today.year, today.month, last_day)
        
        expenses = self.db.get_expenses_by_date_range(user_id, start_date, end_date)
        return sum(expense.amount for expense in expenses)
    
    def get_all_expenses(self, user_id):
        """Get all expenses for a user with categories preloaded.
        
        Args:
            user_id: ID of the user whose expenses to retrieve
            
        Returns:
            List of Expense objects with category relationships preloaded
        """
        # Use a single session for all database operations
        session = self.db.get_session()
        try:
            # Get all expenses with their categories in a single query
            from sqlalchemy.orm import joinedload
            expenses_query = session.query(self.db.Expense).\
                filter(self.db.Expense.user_id == user_id).\
                options(joinedload(self.db.Expense.category))
                
            return expenses_query.all()
        finally:
            session.close()
    
    def get_expenses_by_category(self, user_id, category_id):
        """Get all expenses for a specific category with category data preloaded.
        
        Args:
            user_id: ID of the user whose expenses to retrieve
            category_id: ID of the category to filter by
            
        Returns:
            List of Expense objects with category relationships preloaded
        """
        # Use a single session for all database operations
        session = self.db.get_session()
        try:
            # Get all expenses with their categories in a single query
            from sqlalchemy.orm import joinedload
            expenses_query = session.query(self.db.Expense).\
                filter(self.db.Expense.user_id == user_id,
                       self.db.Expense.category_id == category_id).\
                options(joinedload(self.db.Expense.category))
                
            return expenses_query.all()
        finally:
            session.close()
    
    def get_expenses_by_category_summary(self, user_id, start_date=None, end_date=None):
        """Get expenses grouped by category for a date range."""
        if start_date is None:
            # Default to current month
            today = datetime.date.today()
            start_date = datetime.date(today.year, today.month, 1)
        
        if end_date is None:
            # Default to end of current month
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = datetime.date(today.year, today.month, last_day)
        
        # Use a single session for all database operations
        session = self.db.get_session()
        try:
            # Get all expenses with their categories in a single query
            from sqlalchemy.orm import joinedload
            expenses_query = session.query(self.db.Expense).\
                filter(self.db.Expense.user_id == user_id,
                       self.db.Expense.date >= start_date,
                       self.db.Expense.date <= end_date).\
                options(joinedload(self.db.Expense.category))
                
            expenses = expenses_query.all()
            
            result = {}
            for expense in expenses:
                category_name = expense.category.name if expense.category else "Uncategorized"
                if category_name not in result:
                    result[category_name] = 0
                result[category_name] += expense.amount
            
            return result
        finally:
            session.close()
    
    # Budget management
    def set_budget(self, user_id, category_id, amount, month, year):
        """Set a budget for a category in a specific month and year."""
        return self.db.set_budget(user_id, category_id, amount, month, year)
    
    def get_budget_status(self, user_id, month=None, year=None):
        """Get budget status for a specific month and year."""
        if month is None or year is None:
            today = datetime.date.today()
            if month is None:
                month = today.month
            if year is None:
                year = today.year
        
        # Get start and end dates for the month
        start_date = datetime.date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime.date(year, month, last_day)
        
        # Use a single session for all operations
        session = self.db.get_session()
        try:
            from sqlalchemy.orm import joinedload
            
            # Get budgets for the month with categories pre-loaded
            budgets_query = session.query(self.db.Budget).\
                filter(self.db.Budget.user_id == user_id,
                      self.db.Budget.month == month,
                      self.db.Budget.year == year).\
                options(joinedload(self.db.Budget.category))
                
            budgets = budgets_query.all()
            
            result = {}
            for budget in budgets:
                if not budget.category:
                    continue
                    
                category_name = budget.category.name
                category_id = budget.category.id
                
                # Get actual expenses for this category
                expenses_query = session.query(self.db.Expense).\
                    filter(self.db.Expense.user_id == user_id,
                          self.db.Expense.category_id == category_id,
                          self.db.Expense.date >= start_date,
                          self.db.Expense.date <= end_date)
                          
                expenses = expenses_query.all()
                total_spent = sum(expense.amount for expense in expenses)
                
                # Calculate remaining budget
                remaining = budget.amount - total_spent
                percentage_used = (total_spent / budget.amount) * 100 if budget.amount > 0 else 0
                
                result[category_name] = {
                    'budget': budget.amount,
                    'spent': total_spent,
                    'remaining': remaining,
                    'percentage_used': percentage_used
                }
            
            return result
        finally:
            session.close()
    
    # Reporting and analytics
    def generate_expense_report(self, user_id, start_date=None, end_date=None):
        """Generate an expense report for a date range."""
        if start_date is None:
            # Default to last 3 months
            today = datetime.date.today()
            start_date = today - relativedelta(months=3)
        
        if end_date is None:
            end_date = datetime.date.today()
        
        expenses = self.db.get_expenses_by_date_range(user_id, start_date, end_date)
        
        data = []
        for expense in expenses:
            session = self.db.get_session()
            category = session.query(expense.category).first()
            data.append({
                'date': expense.date,
                'amount': expense.amount,
                'category': category.name,
                'description': expense.description
            })
            session.close()
        
        return pd.DataFrame(data)
    
    def generate_income_report(self, user_id, start_date=None, end_date=None):
        """Generate an income report for a date range."""
        if start_date is None:
            # Default to last 3 months
            today = datetime.date.today()
            start_date = today - relativedelta(months=3)
        
        if end_date is None:
            end_date = datetime.date.today()
        
        incomes = self.db.get_incomes_by_date_range(user_id, start_date, end_date)
        
        data = []
        for income in incomes:
            data.append({
                'date': income.date,
                'amount': income.amount,
                'source': income.source,
                'description': income.description
            })
        
        return pd.DataFrame(data)
    
    def generate_monthly_summary(self, user_id, months=12):
        """Generate a monthly summary of income and expenses."""
        today = datetime.date.today()
        end_date = today
        start_date = today - relativedelta(months=months)
        
        # Generate date range by month
        date_ranges = []
        for i in range(months):
            month_date = today - relativedelta(months=months-i-1)
            month_start = datetime.date(month_date.year, month_date.month, 1)
            month_end = datetime.date(
                month_date.year, 
                month_date.month, 
                calendar.monthrange(month_date.year, month_date.month)[1]
            )
            date_ranges.append((month_start, month_end, f"{month_date.year}-{month_date.month:02d}"))
        
        # Get incomes and expenses for each month
        monthly_data = []
        for start, end, month_label in date_ranges:
            income = self.get_total_income(user_id, start, end)
            expense = self.get_total_expense(user_id, start, end)
            savings = income - expense
            
            monthly_data.append({
                'month': month_label,
                'income': income,
                'expense': expense,
                'savings': savings
            })
        
        return pd.DataFrame(monthly_data)
    
    def create_expense_pie_chart(self, user_id, start_date=None, end_date=None):
        """Create a pie chart of expenses by category."""
        expenses_by_category = self.get_expenses_by_category_summary(user_id, start_date, end_date)
        
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        labels = list(expenses_by_category.keys())
        sizes = list(expenses_by_category.values())
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        ax.set_title('Expenses by Category')
        
        # Save to a BytesIO object
        buf = io.BytesIO()
        canvas = FigureCanvas(fig)
        canvas.print_png(buf)
        buf.seek(0)
        
        return buf
    
    def generate_monthly_summary(self, user_id, months=12):
        """Generate monthly summary of income, expenses, and savings."""
        today = datetime.date.today()
        data = []
        
        for i in range(months-1, -1, -1):
            # Calculate year and month
            month = today.month - i
            year = today.year
            
            while month <= 0:
                month += 12
                year -= 1
                
            # Get first and last day of month
            first_day = datetime.date(year, month, 1)
            last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
            period = first_day.strftime('%b %Y')
            
            # Use a single session for all database operations
            session = self.db.get_session()
            try:
                # Get incomes for this month
                income_query = session.query(self.db.Income).filter(
                    self.db.Income.user_id == user_id,
                    self.db.Income.date >= first_day,
                    self.db.Income.date <= last_day
                )
                total_income = sum(income.amount for income in income_query.all())
                
                # Get expenses for this month
                expense_query = session.query(self.db.Expense).filter(
                    self.db.Expense.user_id == user_id,
                    self.db.Expense.date >= first_day,
                    self.db.Expense.date <= last_day
                )
                total_expense = sum(expense.amount for expense in expense_query.all())
                
                # Get debt expenses
                debt_query = session.query(self.db.Expense).filter(
                    self.db.Expense.user_id == user_id,
                    self.db.Expense.date >= first_day,
                    self.db.Expense.date <= last_day,
                    self.db.Expense.has_apr == 1
                )
                debt_expenses = debt_query.all()
                total_debt = sum(expense.amount for expense in debt_expenses)
                total_interest = sum(self.calculate_monthly_interest(expense.amount, expense.apr) for expense in debt_expenses)
                
                # Calculate net savings
                net_savings = total_income - total_expense
                
                # Add to data
                data.append({
                    'Period': period,
                    'Month': month,
                    'Year': year,
                    'Total Income': round(total_income, 2),
                    'Total Expenses': round(total_expense, 2),
                    'Debt Principal': round(total_debt, 2),
                    'Interest Paid': round(total_interest, 2),
                    'Net Savings': round(net_savings, 2),
                })
            finally:
                session.close()
        
        # Create DataFrame from data
        return pd.DataFrame(data)
    
    def create_monthly_trend_chart(self, user_id, months=6):
        """Create a chart showing monthly income and expense trends"""
        try:
            # Get data for chart
            df = self.generate_monthly_summary(user_id, months)
            
            if df is None or df.empty:
                # Return an empty figure with a message if no data
                fig = Figure(figsize=(10, 6))
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, "No data available for monthly trends",
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax.transAxes, fontsize=14)
                ax.axis('off')
                fig.tight_layout()
                return fig
                
            # Verify that required columns exist
            required_cols = ['Period', 'Total Income', 'Total Expenses', 'Net Savings']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                # Create figure with error message if columns are missing
                fig = Figure(figsize=(10, 6))
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, f"Error: Missing columns in data: {', '.join(missing_cols)}",
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax.transAxes, fontsize=12)
                ax.set_title('Data Format Error')
                fig.tight_layout()
                return fig
            
            # Set up matplotlib figure
            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            
            # Get data for chart
            months = df['Period']
            income = df['Total Income']
            expense = df['Total Expenses']
            savings = df['Net Savings']
            
            # Create plot
            ax.plot(months, income, 'g-', label='Income')
            ax.plot(months, expense, 'r-', label='Expense')
            ax.plot(months, savings, 'b-', label='Savings')
            
            ax.set_xlabel('Month')
            ax.set_ylabel('Amount ($)')
            ax.set_title('Monthly Financial Trends')
            ax.legend()
            ax.grid(True)
            fig.tight_layout()
            
            return fig
            
        except Exception as e:
            # Log the error
            print(f"Error creating monthly trend chart: {e}")
            
            # Return a figure with error message
            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Error creating chart: {str(e)}",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, fontsize=12)
            ax.set_title('Chart Error')
            fig.tight_layout()
            return fig
