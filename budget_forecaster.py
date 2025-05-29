import datetime
import calendar
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Tuple, Dict, List, Optional, Union

class BudgetForecaster:
    """
    Class for forecasting budget scenarios based on current financial data.
    Provides methods to forecast cash flow, debt payoff, savings goals,
    and spending by category.
    """
    
    def __init__(self, budget_manager):
        """
        Initialize the BudgetForecaster with a BudgetManager instance.
        
        Args:
            budget_manager: A BudgetManager instance to access financial data
        """
        self.budget_manager = budget_manager
        self.DEFAULT_FORECAST_MONTHS = 12
        self.DEFAULT_EXTRA_PAYMENT = 100.00
        self.DEFAULT_MIN_PAYMENT_PERCENT = 0.03
        self.ABSOLUTE_MIN_PAYMENT = 25.00  # Minimum $25 payment
    
    def _get_current_financial_snapshot(self, user_id):
        """Get a snapshot of the user's current financial situation.
        
        Args:
            user_id: User ID to get data for
            
        Returns:
            tuple: (monthly_income, regular_expenses, total_debt, monthly_debt_payment, monthly_interest)
        """
        # Calculate date range for current month
        today = datetime.date.today()
        start_date = datetime.date(today.year, today.month, 1)
        end_date = datetime.date(
            today.year, today.month,
            calendar.monthrange(today.year, today.month)[1]
        )
        
        # Get income
        monthly_income = self.budget_manager.get_total_income(user_id, start_date, end_date)
        
        # Get expenses by category
        expense_by_category = self.budget_manager.get_expenses_by_category(user_id, start_date, end_date)
        
        # Sum up non-debt expenses 
        regular_expenses = 0
        for category, amount in expense_by_category.items():
            if 'Debt' not in category:
                regular_expenses += amount
        
        # Get debt-related data
        debt_expenses = self.budget_manager.get_debt_expenses(user_id)
        total_debt = sum(expense.amount for expense in debt_expenses)
        
        # Calculate minimum monthly payment
        monthly_debt_payment = max(total_debt * 0.03, 25.00) if total_debt > 0 else 0
        
        # Calculate monthly interest
        monthly_interest = sum(
            self.budget_manager.calculate_monthly_interest(expense.amount, expense.apr)
            for expense in debt_expenses
        )
        
        return monthly_income, regular_expenses, total_debt, monthly_debt_payment, monthly_interest
        
    def forecast_monthly_cash_flow(self, user_id, months=12) -> pd.DataFrame:
        """Forecast monthly cash flow for the specified number of months."""
        """
        Forecast monthly cash flow for the specified number of months.
        
        Args:
            user_id: User ID to generate forecast for
            months: Number of months to forecast (default: 12)
            
        Returns:
            DataFrame with monthly cash flow projections
        """
        # Get current financial data
        monthly_income, regular_expenses, total_debt, monthly_debt_payment, monthly_interest = (
            self._get_current_financial_snapshot(user_id)
        )
        
        today = datetime.date.today()
        
        # Create forecast data
        forecast_data = []
        
        for i in range(months):
            # Calculate month and year
            future_month = (today.month + i) % 12 or 12  # Convert 0 to 12
            future_year = today.year + (today.month + i - 1) // 12
            month_name = f"{calendar.month_name[future_month]} {future_year}"
            
            # Assume income and regular expenses remain constant
            # This can be enhanced with trend analysis in future versions
            projected_income = monthly_income
            projected_expenses = regular_expenses
            projected_debt_payment = monthly_debt_payment
            projected_interest = monthly_interest
            
            # Calculate net cash flow
            net_cash_flow = projected_income - projected_expenses - projected_debt_payment
            
            forecast_data.append({
                'Month': month_name,
                'Income': projected_income,
                'Expenses': projected_expenses,
                'Debt Payment': projected_debt_payment,
                'Interest Paid': projected_interest,
                'Net Cash Flow': net_cash_flow
            })
        
        return pd.DataFrame(forecast_data)
    
    def forecast_with_debt_payoff(self, user_id, months=24, extra_payment=0.0) -> pd.DataFrame:
        """Forecast debt payoff with optional extra monthly payment."""
        """
        Forecast debt payoff with optional extra monthly payment.
        
        Args:
            user_id: User ID to generate forecast for
            months: Maximum number of months to forecast (default: 24)
            extra_payment: Additional monthly payment to apply to debt (default: 0.0)
            
        Returns:
            DataFrame with debt payoff projections
        """
        # Get current financial data
        _, _, total_debt, min_monthly_payment, monthly_interest = (
            self._get_current_financial_snapshot(user_id)
        )
        
        # If no debt, return empty DataFrame
        if total_debt <= 0:
            return pd.DataFrame()
            
        # Calculate weighted average APR
        debt_expenses = self.budget_manager.get_debt_expenses(user_id)
        weighted_apr = sum(
            expense.amount * expense.apr for expense in debt_expenses
        ) / total_debt
        
        # Create forecast data
        forecast_data = []
        remaining_balance = total_debt
        month = 0
        
        today = datetime.date.today()
        
        while remaining_balance > 0 and month < months:
            # Calculate month and year
            future_month = (today.month + month) % 12 or 12
            future_year = today.year + (today.month + month - 1) // 12
            month_name = f"{calendar.month_name[future_month]} {future_year}"
            
            # Calculate interest for the month
            monthly_interest = remaining_balance * (weighted_apr / 100) / 12
            
            # Apply regular payment + extra payment
            total_payment = min(remaining_balance + monthly_interest, min_monthly_payment + extra_payment)
            principal_payment = total_payment - monthly_interest
            
            # Update remaining balance
            remaining_balance -= principal_payment
            
            forecast_data.append({
                'Month': month_name,
                'Debt Balance': remaining_balance + principal_payment,
                'Regular Payment': min_monthly_payment,
                'Extra Payment': extra_payment,
                'Interest Paid': monthly_interest,
                'Principal Paid': principal_payment,
                'Remaining Balance': remaining_balance
            })
            
            month += 1
        
        return pd.DataFrame(forecast_data)
    
    def forecast_savings_goal(self, user_id, target_amount, monthly_contribution=None) -> Tuple[int, pd.DataFrame]:
        """Forecast time to reach a savings goal."""
        """
        Forecast time to reach a savings goal.
        
        Args:
            user_id: User ID to generate forecast for
            target_amount: Target savings amount
            monthly_contribution: Monthly amount to save (default: calculated from cash flow)
            
        Returns:
            tuple(months_to_goal, DataFrame): Months to reach goal and forecast DataFrame
        """
        # Determine monthly contribution if not specified
        if monthly_contribution is None:
            # Get current month's cash flow
            cash_flow = self.forecast_monthly_cash_flow(user_id, 1)
            monthly_contribution = max(cash_flow['Net Cash Flow'].iloc[0], 0)
            
            # If no positive cash flow, assume minimum contribution
            if monthly_contribution <= 0:
                monthly_contribution = 100.00  # Default minimum contribution
        
        # Calculate months to reach goal (simple linear projection)
        # In a real implementation, we could factor in interest/returns
        if monthly_contribution <= 0:
            return float('inf'), pd.DataFrame()  # Can't reach goal
            
        months_to_goal = int(np.ceil(target_amount / monthly_contribution))
        
        # Create forecast data
        forecast_data = []
        current_savings = 0
        today = datetime.date.today()
        
        for month in range(months_to_goal):
            # Calculate month and year
            future_month = (today.month + month) % 12 or 12
            future_year = today.year + (today.month + month - 1) // 12
            month_name = f"{calendar.month_name[future_month]} {future_year}"
            
            # Update savings balance
            current_savings += monthly_contribution
            
            forecast_data.append({
                'Month': month_name,
                'Monthly Contribution': monthly_contribution,
                'Savings Balance': current_savings,
                'Progress': min(current_savings / target_amount * 100, 100.0)
            })
        
        return months_to_goal, pd.DataFrame(forecast_data)
    
    def forecast_spending_categories(self, user_id, months=6) -> Dict[str, Dict[str, float]]:
        """Forecast spending by category for the specified number of months."""
        """
        Forecast spending by category for the specified number of months.
        
        Args:
            user_id: User ID to generate forecast for
            months: Number of months to forecast (default: 6)
            
        Returns:
            Dictionary of category forecasts
        """
        # Get categories with their current month spending
        today = datetime.date.today()
        start_date = datetime.date(today.year, today.month, 1)
        end_date = datetime.date(
            today.year, today.month,
            calendar.monthrange(today.year, today.month)[1]
        )
        
        # Get expenses by category
        expenses_by_category = self.budget_manager.get_expenses_by_category(user_id, start_date, end_date)
        
        # Create forecast
        forecast = {}
        for category, amount in expenses_by_category.items():
            forecast[category] = {
                'Monthly': amount,
                'Projected': amount * months
            }
        
        return forecast
