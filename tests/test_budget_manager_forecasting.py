import unittest
import datetime
import os
import sys
import tempfile
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_handler import DatabaseHandler
from budget_manager import BudgetManager
from models import User, Category, Expense, Income

class TestBudgetManagerForecasting(unittest.TestCase):
    """Test cases for forecasting-related methods in BudgetManager class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create in-memory database
        self.db_handler = DatabaseHandler('sqlite:///:memory:')
        self.budget_manager = BudgetManager(self.db_handler)
        
        # Add test user
        self.test_user_id = self.db_handler.add_user('testuser', 'password')
        
        # Add test categories
        self.essentials_cat_id = self.db_handler.add_category('Essentials')
        self.debt_cat_id = self.db_handler.add_category('Debt')
        
        # Add test income
        self.today = datetime.date.today()
        self.db_handler.add_income(self.test_user_id, 3000.00, "Monthly Salary", self.today)
        
        # Add regular expenses
        self.db_handler.add_expense(
            self.test_user_id, self.essentials_cat_id, 1200.00, "Rent", self.today
        )
        
        # Add debt expense with APR
        self.db_handler.add_expense(
            self.test_user_id, self.debt_cat_id, 5000.00, "Credit Card", self.today,
            has_apr=True, apr=18.99
        )
    
    def test_get_debt_expenses(self):
        """Test getting debt-related expenses"""
        # Call the method
        debt_expenses = self.budget_manager.get_debt_expenses(self.test_user_id)
        
        # Verify result
        self.assertIsNotNone(debt_expenses)
        self.assertEqual(len(debt_expenses), 1)
        self.assertEqual(debt_expenses[0].amount, 5000.00)
        self.assertTrue(debt_expenses[0].has_apr)
        self.assertEqual(debt_expenses[0].apr, 18.99)
    
    def test_calculate_monthly_interest(self):
        """Test calculating monthly interest for a debt"""
        # Calculate interest on $1000 with 12% APR
        monthly_interest = self.budget_manager.calculate_monthly_interest(1000.00, 12.0)
        
        # Verify result (1000 * 0.12 / 12)
        self.assertAlmostEqual(monthly_interest, 10.0)
        
        # Test with zero amount
        self.assertEqual(self.budget_manager.calculate_monthly_interest(0.00, 12.0), 0.0)
        
        # Test with zero APR
        self.assertEqual(self.budget_manager.calculate_monthly_interest(1000.00, 0.0), 0.0)
    
    def test_get_expenses_by_category(self):
        """Test getting expenses grouped by category"""
        # Call the method
        start_date = datetime.date.today() - datetime.timedelta(days=30)
        end_date = datetime.date.today() + datetime.timedelta(days=1)
        expenses_by_cat = self.budget_manager.get_expenses_by_category(
            self.test_user_id, start_date, end_date
        )
        
        # Verify result
        self.assertIsNotNone(expenses_by_cat)
        self.assertIn('Essentials', expenses_by_cat)
        self.assertIn('Debt', expenses_by_cat)
        self.assertEqual(expenses_by_cat['Essentials'], 1200.00)
        self.assertEqual(expenses_by_cat['Debt'], 5000.00)
    
    def tearDown(self):
        """Clean up after each test"""
        # Close the session
        session = self.db_handler.get_session()
        session.close()


if __name__ == '__main__':
    unittest.main()
