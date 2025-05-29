import unittest
import datetime
import os
import sqlite3
import sys

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_handler import DatabaseHandler
from models import User, Category, Income, Expense, Budget


class TestDatabaseHandler(unittest.TestCase):
    """Test cases for DatabaseHandler class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Use in-memory database for testing
        self.db_handler = DatabaseHandler(':memory:')
        
        # Set up test dates
        self.today = datetime.date.today()
    
    def test_add_user(self):
        """Test adding a user to the database"""
        user_id = self.db_handler.add_user('testuser', 'password')
        
        # Verify user was added
        self.assertIsNotNone(user_id)
        
        # Get user and verify details
        session = self.db_handler.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        session.close()
        
        self.assertEqual(user.username, 'testuser')
        # Password should be hashed, not stored as plaintext
        self.assertNotEqual(user.password, 'password')
    
    def test_authenticate_user(self):
        """Test user authentication"""
        user_id = self.db_handler.add_user('testuser', 'password')
        
        # Test correct credentials
        auth_user_id = self.db_handler.authenticate_user('testuser', 'password')
        self.assertEqual(auth_user_id, user_id)
        
        # Test incorrect password
        auth_user_id = self.db_handler.authenticate_user('testuser', 'wrongpassword')
        self.assertIsNone(auth_user_id)
        
        # Test non-existent user
        auth_user_id = self.db_handler.authenticate_user('nonexistentuser', 'password')
        self.assertIsNone(auth_user_id)
    
    def test_add_category(self):
        """Test adding a category"""
        category_id = self.db_handler.add_category('Groceries')
        
        # Verify category was added
        self.assertIsNotNone(category_id)
        
        # Get category and verify details
        session = self.db_handler.get_session()
        category = session.query(Category).filter(Category.id == category_id).first()
        session.close()
        
        self.assertEqual(category.name, 'Groceries')
    
    def test_get_categories(self):
        """Test retrieving all categories"""
        # Add multiple categories
        cat1_id = self.db_handler.add_category('Groceries')
        cat2_id = self.db_handler.add_category('Rent')
        cat3_id = self.db_handler.add_category('Entertainment')
        
        # Get all categories
        categories = self.db_handler.get_categories()
        
        # Verify categories were retrieved
        self.assertEqual(len(categories), 3)
        category_names = [cat.name for cat in categories]
        self.assertIn('Groceries', category_names)
        self.assertIn('Rent', category_names)
        self.assertIn('Entertainment', category_names)
    
    def test_add_income(self):
        """Test adding income"""
        user_id = self.db_handler.add_user('testuser', 'password')
        
        income_id = self.db_handler.add_income(user_id, 1000.00, 'Salary', self.today)
        
        # Verify income was added
        self.assertIsNotNone(income_id)
        
        # Get income and verify details
        session = self.db_handler.get_session()
        income = session.query(Income).filter(Income.id == income_id).first()
        session.close()
        
        self.assertEqual(income.user_id, user_id)
        self.assertEqual(income.amount, 1000.00)
        self.assertEqual(income.description, 'Salary')
        self.assertEqual(income.date, self.today)
    
    def test_add_expense_with_apr(self):
        """Test adding an expense with APR"""
        user_id = self.db_handler.add_user('testuser', 'password')
        cat_id = self.db_handler.add_category('Credit Card')
        
        expense_id = self.db_handler.add_expense(
            user_id, cat_id, 500.00, 'Credit Card Payment', 
            self.today, has_apr=True, apr=18.99
        )
        
        # Verify expense was added
        self.assertIsNotNone(expense_id)
        
        # Get expense and verify details
        session = self.db_handler.get_session()
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        session.close()
        
        self.assertEqual(expense.user_id, user_id)
        self.assertEqual(expense.category_id, cat_id)
        self.assertEqual(expense.amount, 500.00)
        self.assertEqual(expense.description, 'Credit Card Payment')
        self.assertEqual(expense.date, self.today)
        self.assertEqual(expense.has_apr, True)
        self.assertEqual(expense.apr, 18.99)
    
    def test_get_expenses_by_date_range(self):
        """Test getting expenses by date range"""
        user_id = self.db_handler.add_user('testuser', 'password')
        cat_id = self.db_handler.add_category('Groceries')
        
        # Add expenses with different dates
        date1 = datetime.date(2025, 1, 15)
        date2 = datetime.date(2025, 2, 15)
        date3 = datetime.date(2025, 3, 15)
        
        expense1_id = self.db_handler.add_expense(user_id, cat_id, 100.00, 'Expense 1', date1)
        expense2_id = self.db_handler.add_expense(user_id, cat_id, 200.00, 'Expense 2', date2)
        expense3_id = self.db_handler.add_expense(user_id, cat_id, 300.00, 'Expense 3', date3)
        
        # Test date range that includes all expenses
        start_date = datetime.date(2025, 1, 1)
        end_date = datetime.date(2025, 3, 31)
        expenses = self.db_handler.get_expenses_by_date_range(user_id, start_date, end_date)
        
        self.assertEqual(len(expenses), 3)
        
        # Test date range that includes only the second expense
        start_date = datetime.date(2025, 2, 1)
        end_date = datetime.date(2025, 2, 28)
        expenses = self.db_handler.get_expenses_by_date_range(user_id, start_date, end_date)
        
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0].id, expense2_id)
    
    def test_get_expenses_by_category(self):
        """Test getting expenses by category"""
        user_id = self.db_handler.add_user('testuser', 'password')
        cat1_id = self.db_handler.add_category('Groceries')
        cat2_id = self.db_handler.add_category('Rent')
        
        # Add expenses with different categories
        expense1_id = self.db_handler.add_expense(user_id, cat1_id, 100.00, 'Groceries', self.today)
        expense2_id = self.db_handler.add_expense(user_id, cat1_id, 200.00, 'More Groceries', self.today)
        expense3_id = self.db_handler.add_expense(user_id, cat2_id, 1000.00, 'Rent', self.today)
        
        # Get expenses for category 1
        expenses = self.db_handler.get_expenses_by_category(user_id, cat1_id)
        
        self.assertEqual(len(expenses), 2)
        expense_ids = [expense.id for expense in expenses]
        self.assertIn(expense1_id, expense_ids)
        self.assertIn(expense2_id, expense_ids)
        self.assertNotIn(expense3_id, expense_ids)
    
    def tearDown(self):
        """Clean up after each test"""
        # Close database connections
        session = self.db_handler.get_session()
        session.close()


if __name__ == '__main__':
    unittest.main()
