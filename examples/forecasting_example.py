"""
Budget Forecasting Example Script

This script demonstrates how to use the Budget Forecaster to:
1. Project monthly cash flow
2. Calculate debt payoff timelines
3. Estimate time to reach savings goals
4. Forecast spending by category

Run this script after setting up your budget with income and expenses.
"""

import os
import sys
import datetime
import pandas as pd
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from db_handler import DatabaseHandler
from budget_manager import BudgetManager
from budget_forecaster import BudgetForecaster

def print_dataframe(df, title):
    """Helper function to print DataFrames with formatting"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 120)
    print(df)
    print("=" * 80 + "\n")

def main():
    # Connect to the database
    db_path = os.path.join(Path(__file__).parent.parent, "budget.db")
    db_handler = DatabaseHandler(f"sqlite:///{db_path}")
    budget_manager = BudgetManager(db_handler)
    
    # Create the forecaster
    forecaster = BudgetForecaster(budget_manager)
    
    # Get first user in database for demo purposes
    session = db_handler.get_session()
    users = session.query(db_handler.User).all()
    
    if not users:
        print("No users found in database. Please create a user first.")
        return
    
    user = users[0]
    user_id = user.id
    
    print(f"Generating forecasts for user: {user.username}")
    
    # 1. Monthly Cash Flow Forecast (6 months)
    try:
        cash_flow = forecaster.forecast_monthly_cash_flow(user_id, months=6)
        print_dataframe(cash_flow, "6-MONTH CASH FLOW FORECAST")
        
        # Calculate total projected savings
        total_savings = cash_flow['Net Cash Flow'].sum()
        print(f"Total projected savings over 6 months: ${total_savings:.2f}")
    except Exception as e:
        print(f"Error generating cash flow forecast: {e}")
    
    # 2. Debt Payoff Forecast (with $200 extra monthly payment)
    try:
        debt_payoff = forecaster.forecast_with_debt_payoff(user_id, months=24, extra_payment=200)
        if not debt_payoff.empty:
            print_dataframe(debt_payoff, "DEBT PAYOFF FORECAST (WITH $200 EXTRA PAYMENT)")
            
            # Show remaining months to debt freedom
            months_to_freedom = len(debt_payoff)
            final_month = debt_payoff['Month'].iloc[-1]
            print(f"Debt-free date: {final_month} ({months_to_freedom} months)")
            print(f"Total interest saved with extra payments: ${debt_payoff['Interest Paid'].sum():.2f}")
        else:
            print("No debt found for this user or debt is already paid off.")
    except Exception as e:
        print(f"Error generating debt payoff forecast: {e}")
    
    # 3. Savings Goal Forecast ($10,000 emergency fund)
    try:
        months, savings_plan = forecaster.forecast_savings_goal(user_id, target_amount=10000)
        if months != float('inf'):
            print_dataframe(savings_plan, "$10,000 EMERGENCY FUND SAVINGS PLAN")
            print(f"Time to reach $10,000 emergency fund: {months} months")
        else:
            print("Cannot currently reach savings goal with current cash flow.")
    except Exception as e:
        print(f"Error generating savings goal forecast: {e}")
    
    # 4. Spending by Category Forecast (12 months)
    try:
        category_forecast = forecaster.forecast_spending_categories(user_id, months=12)
        
        print("\n" + "=" * 80)
        print(" 12-MONTH SPENDING BY CATEGORY FORECAST ".center(80, "="))
        print("=" * 80)
        
        total_annual = 0
        for category, data in sorted(category_forecast.items()):
            monthly = data['Monthly']
            annual = data['Projected']
            total_annual += annual
            print(f"{category:<20} ${monthly:>10,.2f}/month    ${annual:>12,.2f}/year")
        
        print("-" * 80)
        print(f"TOTAL PROJECTED EXPENSES:{' ':>12}${total_annual:>12,.2f}/year")
        print("=" * 80 + "\n")
    except Exception as e:
        print(f"Error generating category forecast: {e}")

if __name__ == "__main__":
    main()
