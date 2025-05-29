import unittest
import os
import datetime
import pandas as pd
import tempfile
import shutil
from unittest.mock import MagicMock, patch
import sys

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export_utils import DataExporter
from budget_manager import BudgetManager


class TestDataExporter(unittest.TestCase):
    """Test cases for DataExporter class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Mock the budget manager
        self.budget_manager = MagicMock(spec=BudgetManager)
        
        # Create a temporary directory for exports
        self.test_export_dir = tempfile.mkdtemp()
        
        # Create exporter instance with test directory
        self.exporter = DataExporter(self.budget_manager)
        self.exporter.export_dir = self.test_export_dir
        
        # Test user id
        self.test_user_id = 1
        
        # Test date range
        self.start_date = datetime.date(2025, 1, 1)
        self.end_date = datetime.date(2025, 1, 31)
    
    def test_export_income_data_csv(self):
        """Test exporting income data to CSV"""
        # Mock income data
        mock_income_df = pd.DataFrame({
            'date': ['2025-01-15', '2025-01-30'],
            'description': ['Salary', 'Freelance'],
            'amount': [3000.00, 500.00]
        })
        self.budget_manager.generate_income_report.return_value = mock_income_df
        
        # Export data
        filepath, message = self.exporter.export_income_data(
            self.test_user_id, self.start_date, self.end_date, format='csv'
        )
        
        # Verify export was successful
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.csv'))
        self.assertIn('Income data exported successfully', message)
        
        # Verify file contents
        exported_df = pd.read_csv(filepath)
        self.assertEqual(len(exported_df), 2)
        self.assertEqual(exported_df['amount'].sum(), 3500.00)
    
    def test_export_expense_data_csv(self):
        """Test exporting expense data to CSV"""
        # Mock expense data
        mock_expense_df = pd.DataFrame({
            'date': ['2025-01-10', '2025-01-20'],
            'description': ['Groceries', 'Rent'],
            'category': ['Food', 'Housing'],
            'amount': [150.00, 1200.00]
        })
        self.budget_manager.generate_expense_report.return_value = mock_expense_df
        
        # Export data
        filepath, message = self.exporter.export_expense_data(
            self.test_user_id, self.start_date, self.end_date, format='csv'
        )
        
        # Verify export was successful
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.csv'))
        self.assertIn('Expense data exported successfully', message)
        
        # Verify file contents
        exported_df = pd.read_csv(filepath)
        self.assertEqual(len(exported_df), 2)
        self.assertEqual(exported_df['amount'].sum(), 1350.00)
    
    def test_export_budget_data_csv(self):
        """Test exporting budget data to CSV"""
        # Mock budget data
        mock_budget_status = {
            'Food': {
                'budget': 300.00,
                'spent': 150.00,
                'remaining': 150.00,
                'percentage_used': 50.0
            },
            'Housing': {
                'budget': 1500.00,
                'spent': 1200.00,
                'remaining': 300.00,
                'percentage_used': 80.0
            }
        }
        self.budget_manager.get_budget_status.return_value = mock_budget_status
        
        # Export data
        filepath, message = self.exporter.export_budget_data(
            self.test_user_id, month=1, year=2025, format='csv'
        )
        
        # Verify export was successful
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.csv'))
        self.assertIn('Budget data exported successfully', message)
        
        # Verify file contents
        exported_df = pd.read_csv(filepath)
        self.assertEqual(len(exported_df), 2)
        categories = exported_df['Category'].tolist()
        self.assertIn('Food', categories)
        self.assertIn('Housing', categories)
    
    def test_export_debt_data_csv(self):
        """Test exporting debt data to CSV"""
        # Mock debt data
        mock_debt_df = pd.DataFrame({
            'Description': ['Credit Card 1', 'Credit Card 2'],
            'Principal': [5000.00, 3000.00],
            'APR': [18.99, 15.99],
            'Monthly Interest': [79.13, 39.98],
            'Payoff Date': ['2026-01-15', '2025-08-20']
        })
        
        # Mock the debt calculator
        self.budget_manager.debt_calculator = MagicMock()
        self.budget_manager.debt_calculator.calculate_payoff_plan.return_value = (mock_debt_df, None, None)
        
        # Export data
        filepath, message = self.exporter.export_debt_data(
            self.test_user_id, format='csv'
        )
        
        # Verify export was successful
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.csv'))
        self.assertIn('Debt analysis data exported successfully', message)
        
        # Verify file contents
        exported_df = pd.read_csv(filepath)
        self.assertEqual(len(exported_df), 2)
        self.assertEqual(exported_df['Principal'].sum(), 8000.00)
    
    def test_export_monthly_summary_csv(self):
        """Test exporting monthly summary to CSV"""
        # Mock monthly summary data
        mock_summary_df = pd.DataFrame({
            'Period': ['Jan 2025', 'Feb 2025', 'Mar 2025'],
            'Total Income': [3500.00, 3500.00, 3700.00],
            'Total Expenses': [1350.00, 1400.00, 1500.00],
            'Debt Principal': [8000.00, 7800.00, 7600.00],
            'Interest Paid': [119.11, 116.40, 113.62],
            'Net Savings': [2150.00, 2100.00, 2200.00]
        })
        self.budget_manager.generate_monthly_summary.return_value = mock_summary_df
        
        # Export data
        filepath, message = self.exporter.export_monthly_summary(
            self.test_user_id, months=3, format='csv'
        )
        
        # Verify export was successful
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.csv'))
        self.assertIn('Monthly summary exported successfully', message)
        
        # Verify file contents
        exported_df = pd.read_csv(filepath)
        self.assertEqual(len(exported_df), 3)
        self.assertEqual(exported_df['Total Income'].sum(), 10700.00)
    
    def test_export_empty_data(self):
        """Test exporting when no data is available"""
        # Mock empty DataFrame
        empty_df = pd.DataFrame()
        self.budget_manager.generate_expense_report.return_value = empty_df
        
        # Export data
        filepath, message = self.exporter.export_expense_data(
            self.test_user_id, self.start_date, self.end_date
        )
        
        # Verify export failed with appropriate message
        self.assertIsNone(filepath)
        self.assertIn('No expense data available', message)
    
    def test_export_unsupported_format(self):
        """Test exporting with unsupported format"""
        # Mock income data
        mock_income_df = pd.DataFrame({
            'date': ['2025-01-15'],
            'description': ['Salary'],
            'amount': [3000.00]
        })
        self.budget_manager.generate_income_report.return_value = mock_income_df
        
        # Export data with unsupported format
        filepath, message = self.exporter.export_income_data(
            self.test_user_id, self.start_date, self.end_date, format='pdf'
        )
        
        # Verify export failed with appropriate message
        self.assertIsNone(filepath)
        self.assertIn('Unsupported format', message)
    
    def tearDown(self):
        """Clean up after each test"""
        # Remove temporary export directory
        shutil.rmtree(self.test_export_dir)


if __name__ == '__main__':
    unittest.main()
