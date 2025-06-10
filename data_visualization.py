"""
Data Visualization Module

This module provides functionality for creating visualizations of financial data
in the budget application, using matplotlib for chart generation.
"""

import datetime
import calendar
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import io
import os
from typing import Dict, List, Any, Optional, Tuple, Union, ByteString

class DataVisualizer:
    """Class that handles creating visualizations of budget data"""
    
    def __init__(self, budget_manager):
        """
        Initialize the DataVisualizer with a budget manager.
        
        Args:
            budget_manager: BudgetManager instance for accessing financial data
        """
        self.budget_manager = budget_manager
        self.default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        self.figure_dpi = 100  # Default DPI for generated figures
        
    def _get_default_date_range(self) -> Tuple[datetime.date, datetime.date]:
        """
        Get a default date range for charts (last 6 months)
        
        Returns:
            Tuple of (start_date, end_date)
        """
        today = datetime.date.today()
        # Start from 6 months ago
        month_6_ago = today.month - 6
        year_offset = 0
        if month_6_ago <= 0:
            month_6_ago += 12
            year_offset = -1
            
        start_date = datetime.date(today.year + year_offset, month_6_ago, 1)
        end_date = today
        
        return start_date, end_date
    
    def _get_month_range(self, start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
        """
        Get a list of first days of months in the given range
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of datetime.date objects representing first day of each month
        """
        months = []
        current = datetime.date(start_date.year, start_date.month, 1)  # First day of start month
        
        while current <= end_date:
            months.append(current)
            # Move to next month
            if current.month == 12:
                current = datetime.date(current.year + 1, 1, 1)
            else:
                current = datetime.date(current.year, current.month + 1, 1)
                
        return months
    
    def _figure_to_bytes(self, fig: plt.Figure) -> bytes:
        """
        Convert a matplotlib figure to bytes
        
        Args:
            fig: Matplotlib figure
            
        Returns:
            Bytes representation of the figure
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=self.figure_dpi)
        buf.seek(0)
        return buf.getvalue()
    
    def create_expense_by_category_chart(self, user_id: int,
                                     start_date: Optional[datetime.date] = None,
                                     end_date: Optional[datetime.date] = None,
                                     chart_type: str = 'pie') -> bytes:
        """
        Create a chart showing expenses by category.
        
        Args:
            user_id: User ID
            start_date: Start date for chart, defaults to 6 months ago
            end_date: End date for chart, defaults to today
            chart_type: Type of chart ('pie' or 'bar')
            
        Returns:
            Bytes containing the chart image
        """
        # Get date range
        if start_date is None or end_date is None:
            start_date, end_date = self._get_default_date_range()
        
        # Get expenses by category
        expenses_by_category = self.budget_manager.get_expenses_by_category_summary(user_id, start_date, end_date)
        
        # Filter out categories with zero spending
        expenses_by_category = {k: v for k, v in expenses_by_category.items() if v > 0}
        
        if not expenses_by_category:
            # Create empty chart with message if no data
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No expense data available for the selected period',
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=14, transform=ax.transAxes)
            ax.axis('off')
        elif chart_type.lower() == 'pie':
            # Create pie chart
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Get categories and amounts
            categories = list(expenses_by_category.keys())
            amounts = list(expenses_by_category.values())
            
            # Calculate percentages for labels
            total = sum(amounts)
            percentages = [amount / total * 100 for amount in amounts]
            
            # Create pie chart with percentages
            wedges, texts, autotexts = ax.pie(
                amounts, 
                labels=categories,
                autopct='%1.1f%%',
                startangle=90,
                shadow=False,
                colors=self.default_colors[:len(categories)],
                wedgeprops={'edgecolor': 'w', 'linewidth': 1}
            )
            
            # Style the labels and percentages
            for text in texts:
                text.set_fontsize(12)
            for autotext in autotexts:
                autotext.set_fontsize(10)
                autotext.set_fontweight('bold')
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            # Add title and legend
            plt.title('Expenses by Category', fontsize=16, pad=20)
            plt.legend(categories, loc='center left', bbox_to_anchor=(1, 0.5))
        else:  # bar chart
            # Create bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Get categories and amounts
            categories = list(expenses_by_category.keys())
            amounts = list(expenses_by_category.values())
            
            # Create horizontal bar chart
            y_pos = np.arange(len(categories))
            ax.barh(y_pos, amounts, align='center', 
                   color=self.default_colors[:len(categories)])
            
            # Set labels and title
            ax.set_yticks(y_pos)
            ax.set_yticklabels(categories)
            ax.invert_yaxis()  # Labels read top-to-bottom
            ax.set_xlabel('Amount ($)')
            ax.set_title('Expenses by Category', fontsize=16)
            
            # Add amount labels at the end of each bar
            for i, amount in enumerate(amounts):
                ax.text(amount + (max(amounts) * 0.01), y_pos[i], 
                       f'${amount:.2f}', va='center')
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert to bytes
        result = self._figure_to_bytes(fig)
        plt.close(fig)
        return result
    
    def create_income_expense_chart(self, user_id: int, 
                                  start_date: Optional[datetime.date] = None,
                                  end_date: Optional[datetime.date] = None) -> bytes:
        """
        Create an income vs expenses chart.
        
        Args:
            user_id: User ID
            start_date: Start date for chart, defaults to 6 months ago
            end_date: End date for chart, defaults to today
            
        Returns:
            Bytes containing the chart image
        """
        # Get date range
        if start_date is None or end_date is None:
            start_date, end_date = self._get_default_date_range()
        
        # Get month range
        months = self._get_month_range(start_date, end_date)
        
        # Create lists to hold data
        income_data = []
        expense_data = []
        net_data = []
        month_labels = []
        
        # Get data for each month
        for month_date in months:
            # Last day of month
            last_day = calendar.monthrange(month_date.year, month_date.month)[1]
            month_end = datetime.date(month_date.year, month_date.month, last_day)
            
            # Get income and expense totals
            income_total = self.budget_manager.get_total_income(user_id, month_date, month_end)
            expense_total = self.budget_manager.get_total_expense(user_id, month_date, month_end)
            
            # Calculate net
            net = income_total - expense_total
            
            # Add to data lists
            income_data.append(income_total)
            expense_data.append(expense_total)
            net_data.append(net)
            
            # Add month label
            month_labels.append(month_date.strftime('%b %Y'))
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # X positions
        x = np.arange(len(month_labels))
        width = 0.35
        
        # Plot income and expense bars
        income_bars = ax.bar(x - width/2, income_data, width, label='Income', color='green')
        expense_bars = ax.bar(x + width/2, expense_data, width, label='Expenses', color='red')
        
        # Plot net line
        ax.plot(x, net_data, 'bo-', label='Net', linewidth=2, markersize=6)
        
        # Add a horizontal line at y=0
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Add data labels
        for i, income in enumerate(income_data):
            ax.text(i - width/2, income + (max(income_data) * 0.02), 
                   f'${income:.0f}', ha='center', va='bottom', fontsize=8)
            
        for i, expense in enumerate(expense_data):
            ax.text(i + width/2, expense + (max(expense_data) * 0.02), 
                   f'${expense:.0f}', ha='center', va='bottom', fontsize=8)
            
        for i, net in enumerate(net_data):
            if net >= 0:
                y_offset = max(income_data) * 0.05
                va = 'bottom'
            else:
                y_offset = -max(income_data) * 0.05
                va = 'top'
            ax.text(i, net + y_offset, f'${net:.0f}', ha='center', va=va, fontsize=8)
        
        # Set up axes
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Amount ($)', fontsize=12)
        ax.set_title('Monthly Income vs Expenses', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(month_labels, rotation=45)
        
        # Add legend
        ax.legend()
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert to bytes
        result = self._figure_to_bytes(fig)
        plt.close(fig)
        return result

    def create_monthly_savings_chart(self, user_id: int,
                                   start_date: Optional[datetime.date] = None,
                                   end_date: Optional[datetime.date] = None) -> bytes:
        """
        Create a chart showing monthly savings and cumulative savings over time.
        
        Args:
            user_id: User ID
            start_date: Start date for chart, defaults to 6 months ago
            end_date: End date for chart, defaults to today
            
        Returns:
            Bytes containing the chart image
        """
        # Get date range
        if start_date is None or end_date is None:
            start_date, end_date = self._get_default_date_range()
        
        # Get month range
        months = self._get_month_range(start_date, end_date)
        
        # Create lists to hold data
        monthly_savings = []
        cumulative_savings = 0
        cumulative_data = []
        month_labels = []
        
        # Get data for each month
        for month_date in months:
            # Last day of month
            last_day = calendar.monthrange(month_date.year, month_date.month)[1]
            month_end = datetime.date(month_date.year, month_date.month, last_day)
            
            # Get income and expense totals
            income_total = self.budget_manager.get_total_income(user_id, month_date, month_end)
            expense_total = self.budget_manager.get_total_expense(user_id, month_date, month_end)
            
            # Calculate monthly savings
            month_savings = income_total - expense_total
            monthly_savings.append(month_savings)
            
            # Update cumulative savings
            cumulative_savings += month_savings
            cumulative_data.append(cumulative_savings)
            
            # Add month label
            month_labels.append(month_date.strftime('%b %Y'))
        
        # Create figure with two y-axes
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        # Set up second y-axis that shares x-axis
        ax2 = ax1.twinx()
        
        # X positions
        x = np.arange(len(month_labels))
        
        # Plot monthly savings as bars on left axis
        bars = ax1.bar(x, monthly_savings, width=0.6, alpha=0.7, color='green',
                       label='Monthly Savings')
        
        # Add data labels on top of bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height >= 0:
                va = 'bottom'
                offset = 3
            else:
                va = 'top'
                offset = -3
            ax1.text(bar.get_x() + bar.get_width()/2., height + offset,
                    f"${monthly_savings[i]:.0f}", ha='center', va=va, rotation=0,
                    fontsize=8)
        
        # Plot cumulative savings as line on right axis
        ax2.plot(x, cumulative_data, 'b-', marker='o', linewidth=2,
                 label='Cumulative Savings')
        
        # Add data labels to line
        for i, val in enumerate(cumulative_data):
            ax2.text(i, val + (max(cumulative_data) * 0.03), 
                    f"${val:.0f}", ha='center', fontsize=8)
        
        # Set up axes labels and title
        ax1.set_xlabel('Month', fontsize=12)
        ax1.set_ylabel('Monthly Savings ($)', fontsize=12, color='green')
        ax2.set_ylabel('Cumulative Savings ($)', fontsize=12, color='blue')
        
        # Set up x-ticks and grid
        ax1.set_xticks(x)
        ax1.set_xticklabels(month_labels, rotation=45)
        ax1.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        # Set title
        ax1.set_title('Monthly and Cumulative Savings', fontsize=14)
        
        # Add legends
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert to bytes
        result = self._figure_to_bytes(fig)
        plt.close(fig)
        return result

    def create_spending_trends_chart(self, user_id: int,
                                  start_date: Optional[datetime.date] = None,
                                  end_date: Optional[datetime.date] = None,
                                  categories: Optional[List[int]] = None) -> bytes:
        """
        Create a chart showing spending trends over time by category.
        
        Args:
            user_id: User ID
            start_date: Start date for chart, defaults to 6 months ago
            end_date: End date for chart, defaults to today
            categories: List of category IDs to include (defaults to all)
            
        Returns:
            Bytes containing the chart image
        """
        # Get date range
        if start_date is None or end_date is None:
            start_date, end_date = self._get_default_date_range()
        
        # Get month range
        months = self._get_month_range(start_date, end_date)
        
        # Get all categories or filter by provided category IDs
        session = self.budget_manager.db.get_session()
        try:
            if categories:
                db_categories = session.query(self.budget_manager.db.Category).\
                    filter(self.budget_manager.db.Category.id.in_(categories)).all()
            else:
                db_categories = session.query(self.budget_manager.db.Category).all()
                
            # Create dictionary to map category IDs to names
            category_names = {cat.id: cat.name for cat in db_categories}
        finally:
            session.close()
        
        # Create dictionary to track spending by category over time
        category_spending = {cat_id: [] for cat_id in category_names.keys()}
        month_labels = []
        
        # Get data for each month
        for month_date in months:
            # Last day of month
            last_day = calendar.monthrange(month_date.year, month_date.month)[1]
            month_end = datetime.date(month_date.year, month_date.month, last_day)
            
            # Get all expenses for the month
            session = self.budget_manager.db.get_session()
            try:
                expenses = session.query(self.budget_manager.db.Expense).\
                    filter(self.budget_manager.db.Expense.user_id == user_id,
                          self.budget_manager.db.Expense.date >= month_date,
                          self.budget_manager.db.Expense.date <= month_end).all()
                
                # Group expenses by category
                month_expenses = {cat_id: 0 for cat_id in category_names.keys()}
                for expense in expenses:
                    if expense.category_id in month_expenses:
                        month_expenses[expense.category_id] += expense.amount
                
                # Add to spending data
                for cat_id in category_names.keys():
                    category_spending[cat_id].append(month_expenses[cat_id])
            finally:
                session.close()
            
            # Add month label
            month_labels.append(month_date.strftime('%b %Y'))
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # X positions
        x = np.arange(len(month_labels))
        
        # Plot spending for each category as lines
        for i, (cat_id, spending) in enumerate(category_spending.items()):
            ax.plot(x, spending, marker='o', linewidth=2, 
                   label=category_names[cat_id],
                   color=self.default_colors[i % len(self.default_colors)])
        
        # Customize chart
        ax.set_title('Monthly Spending Trends by Category', fontsize=14)
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Amount ($)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(month_labels, rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add legend
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert to bytes
        result = self._figure_to_bytes(fig)
        plt.close(fig)
        return result

    def create_financial_dashboard(self, user_id: int,
                                start_date: Optional[datetime.date] = None,
                                end_date: Optional[datetime.date] = None) -> Dict[str, Any]:
        """
        Create a complete financial dashboard with multiple charts.
        
        Args:
            user_id: User ID
            start_date: Start date for charts, defaults to 6 months ago
            end_date: End date for charts, defaults to today
            
        Returns:
            Dictionary containing chart images and summary statistics
        """
        # Get date range
        if start_date is None or end_date is None:
            start_date, end_date = self._get_default_date_range()
        
        # Generate all charts
        income_expense_chart = self.create_income_expense_chart(
            user_id, start_date, end_date)
        category_distribution_chart = self.create_expense_by_category_chart(
            user_id, start_date, end_date)
        savings_chart = self.create_monthly_savings_chart(
            user_id, start_date, end_date)
        spending_trends_chart = self.create_spending_trends_chart(
            user_id, start_date, end_date)
        
        # Get summary statistics
        income_total = self.budget_manager.get_total_income(user_id, start_date, end_date)
        expense_total = self.budget_manager.get_total_expense(user_id, start_date, end_date)
        net_savings = income_total - expense_total
        savings_rate = (net_savings / income_total * 100) if income_total > 0 else 0
        
        # Create dashboard dictionary that matches test expectations
        dashboard = {
            'income_expense_chart': income_expense_chart,
            'category_distribution_chart': category_distribution_chart,
            'savings_chart': savings_chart,
            'spending_trends_chart': spending_trends_chart,
            'summary_stats': {
                'total_income': income_total,
                'total_expenses': expense_total,
                'net_savings': net_savings,
                'savings_rate': savings_rate,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
        }
        
        return dashboard

    def export_chart_to_file(self, chart_bytes: bytes, filename: str) -> bool:
        """
        Export a chart to a file.
        
        Args:
            chart_bytes: Bytes representation of the chart
            filename: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(filename)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
                
            # Write bytes to file
            with open(filename, 'wb') as f:
                f.write(chart_bytes)
                
            return True
        except Exception as e:
            print(f"Error exporting chart: {e}")
            return False
