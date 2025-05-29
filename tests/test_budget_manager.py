import unittest
import datetime
import os
import sqlite3
import pandas as pd
from unittest.mock import MagicMock, patch
import sys

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from budget_manager import BudgetManager
from db_handler import DatabaseHandler
from models import User, Category, Income, Expense, Budget


class TestBudgetManager(unittest.TestCase):
    """Test cases for BudgetManager class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create in-memory database for testing
        self.db_handler = DatabaseHandler(':memory:')
        self.budget_manager = BudgetManager(db_handler=self.db_handler)
        
        # Add a test user
        self.test_user_id = self.db_handler.add_user('testuser', 'password')
        
        # Add test categories
        self.groceries_cat_id = self.db_handler.add_category('Groceries')
        self.rent_cat_id = self.db_handler.add_category('Rent')
        self.debt_cat_id = self.db_handler.add_category('Credit Card')
        
        # Set up test dates
        self.today = datetime.date.today()
        self.start_of_month = datetime.date(self.today.year, self.today.month, 1)
        self.end_of_month = datetime.date(
            self.today.year, self.today.month, 
            [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][self.today.month - 1]
        )
        if self.today.month == 2 and (self.today.year % 4 == 0 and self.today.year % 100 != 0 or self.today.year % 400 == 0):
            self.end_of_month = datetime.date(self.today.year, self.today.month, 29)
    
    def test_add_income(self):
        """Test adding income"""
        income_id = self.budget_manager.add_income(
            self.test_user_id, 1000.00, 'Salary', self.today
        )
        
        # Verify income was added
        self.assertIsNotNone(income_id)
        
        # Get income and verify details
        session = self.db_handler.get_session()
        income = session.query(Income).filter(Income.id == income_id).first()
        session.close()
        
        self.assertEqual(income.user_id, self.test_user_id)
        self.assertEqual(income.amount, 1000.00)
        self.assertEqual(income.description, 'Salary')
        self.assertEqual(income.date, self.today)
    
    def test_add_expense_without_apr(self):
        """Test adding an expense without APR"""
        expense_id = self.budget_manager.add_expense(
            self.test_user_id, self.groceries_cat_id, 50.00, 'Groceries', self.today
        )
        
        # Verify expense was added
        self.assertIsNotNone(expense_id)
        
        # Get expense and verify details
        session = self.db_handler.get_session()
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        session.close()
        
        self.assertEqual(expense.user_id, self.test_user_id)
        self.assertEqual(expense.category_id, self.groceries_cat_id)
        self.assertEqual(expense.amount, 50.00)
        self.assertEqual(expense.description, 'Groceries')
        self.assertEqual(expense.date, self.today)
        self.assertEqual(expense.has_apr, False)
        self.assertEqual(expense.apr, 0.0)
    
    def test_add_expense_with_apr(self):
        """Test adding an expense with APR"""
        expense_id = self.budget_manager.add_expense(
            self.test_user_id, self.debt_cat_id, 500.00, 'Credit Card Payment', self.today,
            has_apr=True, apr=18.99
        )
        
        # Verify expense was added
        self.assertIsNotNone(expense_id)
        
        # Get expense and verify details
        session = self.db_handler.get_session()
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        session.close()
        
        self.assertEqual(expense.user_id, self.test_user_id)
        self.assertEqual(expense.category_id, self.debt_cat_id)
        self.assertEqual(expense.amount, 500.00)
        self.assertEqual(expense.description, 'Credit Card Payment')
        self.assertEqual(expense.date, self.today)
        self.assertEqual(expense.has_apr, True)
        self.assertEqual(expense.apr, 18.99)
    
    def test_calculate_monthly_interest(self):
        """Test calculation of monthly interest on debt"""
        # Test with $1000 at 12% APR
        monthly_interest = self.budget_manager.calculate_monthly_interest(1000.00, 12.0)
        self.assertAlmostEqual(monthly_interest, 10.0)  # 1000 * 0.12 / 12 = 10
        
        # Test with $500 at 24% APR
        monthly_interest = self.budget_manager.calculate_monthly_interest(500.00, 24.0)
        self.assertAlmostEqual(monthly_interest, 10.0)  # 500 * 0.24 / 12 = 10
        
        # Test with zero principal
        monthly_interest = self.budget_manager.calculate_monthly_interest(0.00, 18.0)
        self.assertAlmostEqual(monthly_interest, 0.0)
        
        # Test with zero APR
        monthly_interest = self.budget_manager.calculate_monthly_interest(1000.00, 0.0)
        self.assertAlmostEqual(monthly_interest, 0.0)
    
    def test_get_debt_expenses(self):
        """Test retrieving debt expenses"""
        # Add some expenses, both with and without APR
        self.budget_manager.add_expense(
            self.test_user_id, self.groceries_cat_id, 50.00, 'Groceries', self.today
        )
        debt_expense_id = self.budget_manager.add_expense(
            self.test_user_id, self.debt_cat_id, 500.00, 'Credit Card Payment', self.today,
            has_apr=True, apr=18.99
        )
        
        # Get debt expenses
        debt_expenses = self.budget_manager.get_debt_expenses(self.test_user_id)
        
        # Verify only one expense is returned and it's the debt expense
        self.assertEqual(len(debt_expenses), 1)
        self.assertEqual(debt_expenses[0].id, debt_expense_id)
        self.assertEqual(debt_expenses[0].has_apr, True)
        self.assertEqual(debt_expenses[0].apr, 18.99)
    
    def test_generate_debt_report(self):
        """Test generating a debt report"""
        # Add some expenses, both with and without APR
        self.budget_manager.add_expense(
            self.test_user_id, self.groceries_cat_id, 50.00, 'Groceries', self.today
        )
        self.budget_manager.add_expense(
            self.test_user_id, self.debt_cat_id, 1000.00, 'Credit Card 1', self.today,
            has_apr=True, apr=12.0
        )
        self.budget_manager.add_expense(
            self.test_user_id, self.debt_cat_id, 500.00, 'Credit Card 2', self.today,
            has_apr=True, apr=24.0
        )
        
        # Generate debt report
        report_df = self.budget_manager.generate_debt_report(self.test_user_id)
        
        # Verify report format and contents
        self.assertIsInstance(report_df, pd.DataFrame)
        self.assertEqual(len(report_df), 3)  # 2 debt entries + 1 total row
        
        # Check totals row
        totals = report_df[report_df['id'] == 'TOTAL']
        self.assertEqual(len(totals), 1)
        self.assertEqual(totals['amount'].values[0], 1500.0)  # 1000 + 500
        self.assertAlmostEqual(totals['monthly_interest'].values[0], 20.0)  # (1000 * 0.12 + 500 * 0.24) / 12
        self.assertAlmostEqual(totals['annual_interest'].values[0], 240.0)  # 20 * 12
    
    def tearDown(self):
        """Clean up after each test"""
        # Close database connections
        session = self.db_handler.get_session()
        session.close()


if __name__ == '__main__':
    unittest.main()
