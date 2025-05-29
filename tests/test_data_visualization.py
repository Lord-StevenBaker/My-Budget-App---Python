import unittest
import os
import sys
import tempfile
import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
import numpy as np
from unittest.mock import MagicMock, patch
from io import BytesIO
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_handler import DatabaseHandler
from budget_manager import BudgetManager
from data_visualization import DataVisualizer

class TestDataVisualization(unittest.TestCase):
    """Test cases for the DataVisualizer class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create in-memory database
        self.db_handler = DatabaseHandler('sqlite:///:memory:')
        self.budget_manager = BudgetManager(db_handler=self.db_handler)
        
        # Create visualizer
        self.visualizer = DataVisualizer(self.budget_manager)
        
        # Add test user
        self.test_user_id = self.db_handler.add_user('testuser', 'password')
        
        # Add test categories
        self.essentials_cat_id = self.db_handler.add_category('Essentials')
        self.discretionary_cat_id = self.db_handler.add_category('Discretionary')
        self.debt_cat_id = self.db_handler.add_category('Debt')
        self.savings_cat_id = self.db_handler.add_category('Savings')
        self.income_cat_id = self.db_handler.add_category('Income')
        
        # Test dates
        self.today = datetime.date.today()
        self.start_date = datetime.date(self.today.year, self.today.month - 2, 1)  # 2 months ago
        self.end_date = datetime.date(self.today.year, self.today.month + 1, 1)  # 1 month from now
        
        # Add test data (3 months of data)
        self._add_test_data()
    
    def _add_test_data(self):
        """Add test financial data spanning multiple months"""
        # Current month
        current_month = self.today.month
        current_year = self.today.year
        
        # Add data for last 3 months
        for month_offset in range(-2, 1):
            month = ((current_month + month_offset - 1) % 12) + 1  # Handle wrapping around December
            year = current_year if month <= current_month else current_year - 1
            
            # Date for this month's data
            date = datetime.date(year, month, 15)
            
            # Income
            self.budget_manager.add_income(
                self.test_user_id, 
                3000.00 + (month_offset * 100),  # Slight increase each month
                f"Salary {month}/{year}", 
                date
            )
            
            # Expenses with different categories
            self.budget_manager.add_expense(
                self.test_user_id, self.essentials_cat_id, 
                1200.00, f"Rent {month}/{year}", date
            )
            
            self.budget_manager.add_expense(
                self.test_user_id, self.essentials_cat_id, 
                300.00 + (month_offset * 10), f"Groceries {month}/{year}", date
            )
            
            self.budget_manager.add_expense(
                self.test_user_id, self.discretionary_cat_id, 
                200.00 - (month_offset * 5), f"Entertainment {month}/{year}", date
            )
            
            self.budget_manager.add_expense(
                self.test_user_id, self.debt_cat_id, 
                500.00, f"Loan Payment {month}/{year}", date,
                has_apr=True, apr=5.0
            )
            
            self.budget_manager.add_expense(
                self.test_user_id, self.savings_cat_id, 
                400.00 + (month_offset * 50), f"Savings {month}/{year}", date
            )
    
    def test_generate_income_expense_chart(self):
        """Test generating an income vs expense chart"""
        # Generate chart
        chart_bytes = self.visualizer.create_income_expense_chart(
            self.test_user_id, self.start_date, self.end_date
        )
        
        # Verify a non-empty bytes object was returned (valid image)
        self.assertIsInstance(chart_bytes, bytes)
        self.assertGreater(len(chart_bytes), 0)
        
        # Test with default date range
        default_chart = self.visualizer.create_income_expense_chart(self.test_user_id)
        self.assertIsInstance(default_chart, bytes)
        self.assertGreater(len(default_chart), 0)
    
    def test_generate_expense_by_category_chart(self):
        """Test generating an expense by category chart"""
        # Generate chart
        chart_bytes = self.visualizer.create_expense_by_category_chart(
            self.test_user_id, self.start_date, self.end_date, chart_type='pie'
        )
        
        # Verify valid image
        self.assertIsInstance(chart_bytes, bytes)
        self.assertGreater(len(chart_bytes), 0)
        
        # Test bar chart type
        bar_chart = self.visualizer.create_expense_by_category_chart(
            self.test_user_id, self.start_date, self.end_date, chart_type='bar'
        )
        self.assertIsInstance(bar_chart, bytes)
        self.assertGreater(len(bar_chart), 0)
    
    def test_generate_monthly_savings_chart(self):
        """Test generating a monthly savings chart"""
        # Generate chart
        chart_bytes = self.visualizer.create_monthly_savings_chart(
            self.test_user_id, self.start_date, self.end_date
        )
        
        # Verify valid image
        self.assertIsInstance(chart_bytes, bytes)
        self.assertGreater(len(chart_bytes), 0)
    
    def test_generate_spending_trends_chart(self):
        """Test generating a spending trends chart"""
        # Generate chart
        chart_bytes = self.visualizer.create_spending_trends_chart(
            self.test_user_id, self.start_date, self.end_date,
            categories=[self.essentials_cat_id, self.discretionary_cat_id]
        )
        
        # Verify valid image
        self.assertIsInstance(chart_bytes, bytes)
        self.assertGreater(len(chart_bytes), 0)
        
        # Test with all categories
        all_cats_chart = self.visualizer.create_spending_trends_chart(
            self.test_user_id, self.start_date, self.end_date
        )
        self.assertIsInstance(all_cats_chart, bytes)
        self.assertGreater(len(all_cats_chart), 0)
    
    def test_generate_financial_overview_dashboard(self):
        """Test generating a complete financial overview dashboard"""
        # Generate dashboard with multiple charts
        dashboard = self.visualizer.create_financial_dashboard(
            self.test_user_id, self.start_date, self.end_date
        )
        
        # Verify dashboard structure
        self.assertIsInstance(dashboard, dict)
        self.assertIn('income_expense_chart', dashboard)
        self.assertIn('category_distribution_chart', dashboard)
        self.assertIn('savings_chart', dashboard)
        self.assertIn('spending_trends_chart', dashboard)
        self.assertIn('summary_stats', dashboard)
        
        # Verify chart data
        for key in ['income_expense_chart', 'category_distribution_chart', 
                    'savings_chart', 'spending_trends_chart']:
            self.assertIsInstance(dashboard[key], bytes)
            self.assertGreater(len(dashboard[key]), 0)
        
        # Verify summary stats
        self.assertIsInstance(dashboard['summary_stats'], dict)
        self.assertIn('total_income', dashboard['summary_stats'])
        self.assertIn('total_expenses', dashboard['summary_stats'])
        self.assertIn('savings_rate', dashboard['summary_stats'])
    
    def test_export_chart_to_file(self):
        """Test exporting charts to files"""
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate chart
            chart_bytes = self.visualizer.create_income_expense_chart(
                self.test_user_id, self.start_date, self.end_date
            )
            
            # Export to file
            filename = os.path.join(temp_dir, 'test_chart.png')
            result = self.visualizer.export_chart_to_file(chart_bytes, filename)
            
            # Verify success
            self.assertTrue(result)
            self.assertTrue(os.path.exists(filename))
            self.assertGreater(os.path.getsize(filename), 0)
    
    def tearDown(self):
        """Clean up after each test"""
        plt.close('all')  # Close all figures
        session = self.db_handler.get_session()
        session.close()


if __name__ == '__main__':
    unittest.main()
