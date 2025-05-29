"""
Financial Goals Example Script

This script demonstrates how to use the Financial Goals tracking feature to:
1. Create and manage financial goals
2. Track progress toward goals
3. Analyze goal feasibility
4. Generate goal summary statistics

The example creates several goals (emergency fund, vacation, home down payment)
and shows how to track them over time.
"""

import os
import sys
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from db_handler import DatabaseHandler
from budget_manager import BudgetManager
from financial_goals import FinancialGoal, GoalTracker

def print_goal_details(goal, feasibility=None):
    """Helper function to print goal details in a formatted way"""
    print("\n" + "=" * 80)
    print(f" GOAL: {goal.name} ".center(80, "="))
    print("=" * 80)
    print(f"Target Amount:      ${goal.target_amount:,.2f}")
    print(f"Current Progress:   ${goal.current_amount:,.2f} ({goal.progress_percentage:.1f}%)")
    print(f"Days Remaining:     {goal.days_remaining} days ({goal.months_remaining:.1f} months)")
    print(f"Monthly Needed:     ${goal.monthly_contribution_needed:,.2f}")
    
    if feasibility:
        print("\n" + "-" * 80)
        print(" FEASIBILITY ANALYSIS ".center(80, "-"))
        print(f"Free Monthly Cash Flow:   ${feasibility['free_cash_flow']:,.2f}")
        print(f"Months Needed:            {feasibility['months_needed']:.1f}")
        print(f"Months to Deadline:       {feasibility['months_to_deadline']:.1f}")
        print(f"Required Monthly Savings: ${feasibility['required_monthly']:,.2f}")
        print(f"Percentage of Income:     {feasibility['percentage_of_income']:.1f}%")
        print(f"Feasible by Deadline:     {'YES' if feasibility['feasible'] else 'NO'}")
    print("=" * 80)

def main():
    # Connect to the database
    db_path = os.path.join(Path(__file__).parent.parent, "budget.db")
    db_handler = DatabaseHandler(f"sqlite:///{db_path}")
    budget_manager = BudgetManager(db_handler)
    
    # Create the goal tracker
    goal_tracker = GoalTracker(db_handler, budget_manager)
    
    # Get first user in database for demo purposes
    session = db_handler.get_session()
    users = session.query(db_handler.User).all()
    
    if not users:
        print("No users found in database. Please create a user first.")
        return
    
    user = users[0]
    user_id = user.id
    
    print(f"Demonstrating Financial Goals feature for user: {user.username}")
    
    # Create some example goals
    print("\nCreating financial goals...")
    
    # 1. Emergency Fund (6 months of expenses)
    today = datetime.date.today()
    six_months_expenses = budget_manager.get_total_expense(user_id) * 6
    
    # Target date - 1 year from now
    one_year_later = today.replace(year=today.year + 1)
    emergency_fund_id = goal_tracker.create_goal(
        user_id=user_id,
        name="Emergency Fund",
        target_amount=six_months_expenses,
        target_date=one_year_later,
        description="6 months worth of living expenses",
        category="Savings",
        priority="High"
    )
    
    # 2. Vacation Fund
    six_months_later = today + datetime.timedelta(days=180)
    vacation_fund_id = goal_tracker.create_goal(
        user_id=user_id,
        name="Summer Vacation",
        target_amount=2500.00,
        target_date=six_months_later,
        description="Trip to the beach",
        category="Travel",
        priority="Medium"
    )
    
    # 3. Home Down Payment
    five_years_later = today.replace(year=today.year + 5)
    down_payment_id = goal_tracker.create_goal(
        user_id=user_id,
        name="Home Down Payment",
        target_amount=50000.00,
        target_date=five_years_later,
        description="20% down payment for a house",
        category="Housing",
        priority="High"
    )
    
    # Update some progress
    print("\nUpdating goal progress...")
    
    # Add $1,000 to emergency fund
    goal_tracker.update_goal_progress(emergency_fund_id, 1000.00)
    
    # Add $800 to vacation fund
    goal_tracker.update_goal_progress(vacation_fund_id, 800.00)
    
    # Add $5,000 to down payment
    goal_tracker.update_goal_progress(down_payment_id, 5000.00)
    
    # Get all goals for the user
    print("\nRetrieving all financial goals...")
    goals = goal_tracker.get_goals_by_user(user_id, order_by='priority')
    
    # Display each goal with feasibility analysis
    for goal in goals:
        feasibility = goal_tracker.analyze_goal_feasibility(goal.id)
        print_goal_details(goal, feasibility)
    
    # Show goal summary statistics
    summary = goal_tracker.get_goal_summary_stats(user_id)
    
    print("\n" + "=" * 80)
    print(" FINANCIAL GOALS SUMMARY ".center(80, "="))
    print("=" * 80)
    print(f"Total Goals:                {summary['total_goals']}")
    print(f"Completed Goals:            {summary['completed_goals']}")
    print(f"Total Target Amount:        ${summary['total_target_amount']:,.2f}")
    print(f"Total Current Progress:     ${summary['total_current_amount']:,.2f}")
    print(f"Overall Progress:           {summary['average_progress']:.1f}%")
    
    if summary['nearest_deadline']:
        print(f"Next Deadline:              {summary['nearest_deadline']}")
    print("=" * 80)
    
    # Demo updating a goal
    print("\nUpdating vacation goal target amount...")
    goal_tracker.update_goal_details(
        vacation_fund_id,
        target_amount=3000.00,
        description="Trip to the beach plus some shopping"
    )
    
    updated_goal = goal_tracker.get_goal(vacation_fund_id)
    print(f"Updated vacation goal target: ${updated_goal.target_amount:,.2f}")
    print(f"Updated progress percentage: {updated_goal.progress_percentage:.1f}%")
    
    print("\nFinancial Goals demo completed!\n")


if __name__ == "__main__":
    main()
