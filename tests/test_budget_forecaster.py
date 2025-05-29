import unittest
import datetime
import pandas as pd
import os
import sys
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from budget_forecaster import BudgetForecaster
from budget_manager import BudgetManager
from db_handler import DatabaseHandler

class TestBudgetForecaster(unittest.TestCase):
    """Test cases for BudgetForecaster class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.db_handler = DatabaseHandler('sqlite:///:memory:')
        self.budget_manager = BudgetManager(db_handler=self.db_handler)
        
        # Create the forecaster with our manager
        self.forecaster = BudgetForecaster(self.budget_manager)
        
        # Add a test user
        self.test_user_id = self.db_handler.add_user('testuser', 'password')
        
        # Add test categories
        self.essentials_cat_id = self.db_handler.add_category('Essentials')
        self.discretionary_cat_id = self.db_handler.add_category('Discretionary')
        self.debt_cat_id = self.db_handler.add_category('Debt')
        
        # Set up test dates
        self.today = datetime.date.today()
        self.future_date = self.today + datetime.timedelta(days=180)  # 6 months in future
        
        # Add test data
        # Income - regular monthly income
        self.budget_manager.add_income(
            self.test_user_id, 3000.00, "Monthly Salary", self.today
        )
        
        # Regular expenses
        self.budget_manager.add_expense(
            self.test_user_id, self.essentials_cat_id, 1200.00, "Rent", self.today
        )
        self.budget_manager.add_expense(
            self.test_user_id, self.essentials_cat_id, 300.00, "Groceries", self.today
        )
        self.budget_manager.add_expense(
            self.test_user_id, self.discretionary_cat_id, 200.00, "Entertainment", self.today
        )
        
        # Debt expense with APR
        self.budget_manager.add_expense(
            self.test_user_id, self.debt_cat_id, 5000.00, "Credit Card", self.today,
            has_apr=True, apr=18.99
        )
    
    def test_forecast_monthly_cash_flow(self):
        """Test forecasting monthly cash flow"""
        # Generate a 6-month forecast
        forecast = self.forecaster.forecast_monthly_cash_flow(self.test_user_id, 6)
        
        # Check forecast format
        self.assertIsInstance(forecast, pd.DataFrame)
        self.assertEqual(len(forecast), 6)  # 6 months of data
        
        # Check forecast contains expected columns
        expected_columns = ['Month', 'Income', 'Expenses', 'Debt Payment', 'Interest Paid', 'Net Cash Flow']
        for col in expected_columns:
            self.assertIn(col, forecast.columns)
        
        # Check first month calculations
        first_month = forecast.iloc[0]
        self.assertEqual(first_month['Income'], 3000.00)  # Monthly income
        self.assertEqual(first_month['Expenses'], 1700.00)  # Regular expenses (1200 + 300 + 200)
        self.assertGreater(first_month['Net Cash Flow'], 0)  # Should be positive
    
    def test_forecast_with_debt_payoff(self):
        """Test forecasting with debt payoff calculations"""
        # Generate a 12-month forecast with debt payoff calculation
        forecast = self.forecaster.forecast_with_debt_payoff(
            self.test_user_id, 12, extra_payment=300.00
        )
        
        # Check forecast format
        self.assertIsInstance(forecast, pd.DataFrame)
        self.assertGreaterEqual(len(forecast), 1)  # At least 1 month
        
        # Check forecast contains expected columns
        expected_columns = ['Month', 'Debt Balance', 'Regular Payment', 'Extra Payment', 
                           'Interest Paid', 'Principal Paid', 'Remaining Balance']
        for col in expected_columns:
            self.assertIn(col, forecast.columns)
        
        # Check debt is decreasing
        self.assertGreater(forecast.iloc[0]['Debt Balance'], forecast.iloc[-1]['Debt Balance'])
        
        # Check extra payment is applied
        self.assertEqual(forecast.iloc[0]['Extra Payment'], 300.00)
    
    def test_forecast_savings_goal(self):
        """Test forecasting time to reach a savings goal"""
        target_amount = 10000.00
        
        # Calculate time to reach savings goal
        months, forecast = self.forecaster.forecast_savings_goal(
            self.test_user_id, target_amount
        )
        
        # Check we got valid results
        self.assertIsInstance(months, int)
        self.assertIsInstance(forecast, pd.DataFrame)
        self.assertGreater(months, 0)
        
        # Check forecast shows progression to goal
        self.assertEqual(len(forecast), months)
        self.assertLess(forecast.iloc[0]['Savings Balance'], target_amount)
        self.assertGreaterEqual(forecast.iloc[-1]['Savings Balance'], target_amount)
    
    def test_forecast_spending_categories(self):
        """Test forecasting spending by category"""
        # Get categorical spending forecast
        forecast = self.forecaster.forecast_spending_categories(self.test_user_id, 6)
        
        # Verify format
        self.assertIsInstance(forecast, dict)
        self.assertIn('Essentials', forecast)
        self.assertIn('Discretionary', forecast)
        
        # Check category values
        self.assertEqual(forecast['Essentials']['Monthly'], 1500.00)  # 1200 + 300
        self.assertEqual(forecast['Discretionary']['Monthly'], 200.00)
        
        # Check 6-month projections
        self.assertEqual(forecast['Essentials']['Projected'], 1500.00 * 6)
        self.assertEqual(forecast['Discretionary']['Projected'], 200.00 * 6)
    
    def tearDown(self):
        """Clean up after each test"""
        # Close database connections
        session = self.db_handler.get_session()
        session.close()


if __name__ == '__main__':
    unittest.main()
