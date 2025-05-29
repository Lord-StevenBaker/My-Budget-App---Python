import os
import csv
import datetime
import pandas as pd
from pathlib import Path

class DataExporter:
    """Utility class for exporting budget data to various formats"""
    
    def __init__(self, budget_manager):
        """Initialize with a budget manager instance"""
        self.budget_manager = budget_manager
        # Create export directory if it doesn't exist
        self.export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_income_data(self, user_id, start_date=None, end_date=None, format='csv'):
        """Export income data to CSV or Excel"""
        # Generate income report
        income_df = self.budget_manager.generate_income_report(user_id, start_date, end_date)
        
        if income_df.empty:
            return None, "No income data available for the selected period."
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"income_data_{timestamp}.{format}"
        filepath = os.path.join(self.export_dir, filename)
        
        # Export based on format
        if format == 'csv':
            income_df.to_csv(filepath, index=False)
        elif format == 'excel':
            income_df.to_excel(filepath, index=False)
        else:
            return None, f"Unsupported format: {format}"
        
        return filepath, f"Income data exported successfully to {filename}"
    
    def export_expense_data(self, user_id, start_date=None, end_date=None, format='csv'):
        """Export expense data to CSV or Excel"""
        # Generate expense report
        expense_df = self.budget_manager.generate_expense_report(user_id, start_date, end_date)
        
        if expense_df.empty:
            return None, "No expense data available for the selected period."
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"expense_data_{timestamp}.{format}"
        filepath = os.path.join(self.export_dir, filename)
        
        # Export based on format
        if format == 'csv':
            expense_df.to_csv(filepath, index=False)
        elif format == 'excel':
            expense_df.to_excel(filepath, index=False)
        else:
            return None, f"Unsupported format: {format}"
        
        return filepath, f"Expense data exported successfully to {filename}"
    
    def export_budget_data(self, user_id, month=None, year=None, format='csv'):
        """Export budget vs actual data to CSV or Excel"""
        # Get budget data
        if month is None or year is None:
            today = datetime.date.today()
            month = month or today.month
            year = year or today.year
        
        budget_status = self.budget_manager.get_budget_status(user_id, month, year)
        
        if not budget_status:
            return None, "No budget data available for the selected period."
        
        # Convert to DataFrame
        budget_data = []
        for category, data in budget_status.items():
            budget_data.append({
                'Category': category,
                'Budget Amount': data['budget'],
                'Actual Spent': data['spent'],
                'Remaining': data['remaining'],
                'Percentage Used': data['percentage_used']
            })
        
        budget_df = pd.DataFrame(budget_data)
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"budget_data_{year}_{month:02d}_{timestamp}.{format}"
        filepath = os.path.join(self.export_dir, filename)
        
        # Export based on format
        if format == 'csv':
            budget_df.to_csv(filepath, index=False)
        elif format == 'excel':
            budget_df.to_excel(filepath, index=False)
        else:
            return None, f"Unsupported format: {format}"
        
        return filepath, f"Budget data exported successfully to {filename}"
    
    def export_debt_data(self, user_id, format='csv'):
        """Export debt analysis data to CSV or Excel"""
        # Get debt data
        debt_df, _, _ = self.budget_manager.debt_calculator.calculate_payoff_plan(user_id) if hasattr(self.budget_manager, 'debt_calculator') else (None, None, None)
        
        if debt_df is None or debt_df.empty:
            return None, "No debt data available or debt calculator not initialized."
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"debt_analysis_{timestamp}.{format}"
        filepath = os.path.join(self.export_dir, filename)
        
        # Export based on format
        if format == 'csv':
            debt_df.to_csv(filepath, index=False)
        elif format == 'excel':
            debt_df.to_excel(filepath, index=False)
        else:
            return None, f"Unsupported format: {format}"
        
        return filepath, f"Debt analysis data exported successfully to {filename}"
    
    def export_monthly_summary(self, user_id, months=12, format='csv'):
        """Export monthly summary data to CSV or Excel"""
        # Generate monthly summary
        summary_df = self.budget_manager.generate_monthly_summary(user_id, months)
        
        if summary_df.empty:
            return None, "No monthly summary data available."
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"monthly_summary_{timestamp}.{format}"
        filepath = os.path.join(self.export_dir, filename)
        
        # Export based on format
        if format == 'csv':
            summary_df.to_csv(filepath, index=False)
        elif format == 'excel':
            summary_df.to_excel(filepath, index=False)
        else:
            return None, f"Unsupported format: {format}"
        
        return filepath, f"Monthly summary exported successfully to {filename}"
