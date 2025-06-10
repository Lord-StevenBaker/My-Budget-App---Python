import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import io
import copy
import logging
from models import Category  # Import Category model


class DebtPayoffCalculator:
    """A calculator for debt payoff strategies and timelines."""
    
    def __init__(self, budget_manager):
        """Initialize the debt payoff calculator with a budget manager."""
        self.budget_manager = budget_manager
    
    def calculate_payoff_plan(self, user_id, additional_payment=0.0, strategy="highest_interest"):
        """Calculate debt payoff timeline with different strategies.
        
        Args:
            user_id: The user ID
            additional_payment: Additional monthly payment beyond minimums
            strategy: Strategy to use - 'highest_interest', 'lowest_balance', 'snowball', 'avalanche'
        
        Returns:
            DataFrame with payoff details, summary dict, and debts list
        """
        # Get all debt expenses
        today = datetime.date.today()
        # Get expenses from last 3 months to capture all relevant debts
        start_date = today - relativedelta(months=3)
        debt_expenses = self.budget_manager.get_debt_expenses(user_id, start_date, today)
        
        if not debt_expenses:
            return pd.DataFrame(), {}, []
        
        session = self.budget_manager.db.get_session()
        
        debts = []
        for expense in debt_expenses:
            # Get category name
            try:
                category = session.query(Category).filter(Category.id == expense.category_id).first()
                category_name = category.name if category else "Unknown"
            except Exception as e:
                logging.error(f"Error fetching category for expense {expense.id}: {str(e)}")
                category_name = "Unknown"
            
            # Calculate interest
            monthly_rate = expense.apr / 100 / 12
            
            # Assume minimum payment is 2% of balance or $25, whichever is higher
            min_payment = max(expense.amount * 0.02, 25)
            
            debts.append({
                'id': expense.id,
                'description': expense.description,
                'category': category_name,
                'balance': expense.amount,
                'apr': expense.apr,
                'monthly_rate': monthly_rate,
                'min_payment': min_payment
            })
        
        session.close()
        
        # Sort debts according to strategy
        if strategy == "highest_interest":
            debts = sorted(debts, key=lambda x: x['apr'], reverse=True)
        elif strategy == "lowest_balance":
            debts = sorted(debts, key=lambda x: x['balance'])
        elif strategy == "snowball":
            # Snowball: Pay minimum on all, then extra on lowest balance
            debts = sorted(debts, key=lambda x: x['balance'])
        elif strategy == "avalanche":
            # Avalanche: Pay minimum on all, then extra on highest interest
            debts = sorted(debts, key=lambda x: x['apr'], reverse=True)
        
        # Calculate payoff timeline
        results = []
        remaining_debts = len(debts)
        current_month = 0
        total_initial_balance = sum(debt['balance'] for debt in debts)
        extra_payment = additional_payment
        
        # Make a deep copy of debts for calculation
        calculation_debts = copy.deepcopy(debts)
        
        while remaining_debts > 0 and current_month < 600:  # Limit to 50 years (600 months)
            current_month += 1
            total_payment = 0
            total_interest = 0
            
            for i, debt in enumerate(calculation_debts):
                if debt['balance'] <= 0:
                    continue
                
                # Calculate interest for this month
                interest = debt['balance'] * debt['monthly_rate']
                total_interest += interest
                
                # Determine payment for this debt
                if i == 0 and extra_payment > 0:
                    # Apply extra payment to first debt in list (based on strategy)
                    payment = debt['min_payment'] + extra_payment
                else:
                    payment = debt['min_payment']
                
                # Ensure we don't overpay
                payment = min(payment, debt['balance'] + interest)
                
                # Apply payment
                debt['balance'] = debt['balance'] + interest - payment
                total_payment += payment
                
                # Check if debt is paid off
                if debt['balance'] <= 0.01:  # Allow small rounding error
                    debt['balance'] = 0
                    debt['payoff_month'] = current_month
            
            # Recount remaining debts
            remaining_debts = sum(1 for debt in calculation_debts if debt['balance'] > 0)
            
            # Reorder debts for next payment according to strategy
            if strategy in ["highest_interest", "avalanche"]:
                calculation_debts = sorted(calculation_debts, 
                                           key=lambda x: (-1 if x['balance'] <= 0 else x['apr']),
                                           reverse=True)
            elif strategy in ["lowest_balance", "snowball"]:
                calculation_debts = sorted(calculation_debts,
                                           key=lambda x: (float('inf') if x['balance'] <= 0 else x['balance']))
            
            # Calculate total remaining balance
            total_remaining = sum(debt['balance'] for debt in calculation_debts)
            
            # Add this month to results
            results.append({
                'month': current_month,
                'payment': total_payment,
                'interest': total_interest,
                'remaining_balance': total_remaining,
                'remaining_debts': remaining_debts,
                'percent_paid': (1 - total_remaining / total_initial_balance) * 100 if total_initial_balance > 0 else 100
            })
        
        # Process debt data for return
        summary = {
            'total_months': current_month,
            'total_interest_paid': sum(month['interest'] for month in results),
            'total_amount_paid': sum(month['payment'] for month in results),
            'original_balance': total_initial_balance,
            'monthly_payment': sum(debt['min_payment'] for debt in debts) + additional_payment
        }
        
        # Add payoff order to original debts
        for i, orig_debt in enumerate(debts):
            for calc_debt in calculation_debts:
                if orig_debt['id'] == calc_debt['id']:
                    orig_debt['payoff_month'] = calc_debt.get('payoff_month', current_month)
        
        # Sort debts by payoff date for display
        debts = sorted(debts, key=lambda x: x.get('payoff_month', float('inf')))
        
        # Prepare return values
        return pd.DataFrame(results), summary, debts
    
    def create_payoff_chart(self, user_id, additional_payment=0.0, strategy="highest_interest"):
        """Create a chart showing debt payoff progress over time."""
        results_df, summary, _ = self.calculate_payoff_plan(user_id, additional_payment, strategy)
        
        if results_df.empty:
            return None
        
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Plot balance over time
        months = results_df['month']
        balance = results_df['remaining_balance']
        
        ax.plot(months, balance, 'b-', linewidth=2)
        ax.fill_between(months, balance, alpha=0.3)
        
        # Add annotations for key points
        if len(months) > 0:
            # Mark halfway point if we have enough points
            if len(months) > 2:
                middle_idx = len(months) // 2
                ax.annotate(f"50% paid\nMonth {months.iloc[middle_idx]}",
                           xy=(months.iloc[middle_idx], balance.iloc[middle_idx]),
                           xytext=(months.iloc[middle_idx], balance.iloc[middle_idx] * 1.2),
                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
            
            # Mark final point
            if len(months) > 1:
                ax.annotate(f"Debt free\nMonth {months.iloc[-1]}",
                          xy=(months.iloc[-1], 0),
                          xytext=(months.iloc[-1] * 0.9, balance.iloc[0] * 0.3),
                          arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
        
        ax.set_xlabel('Month')
        ax.set_ylabel('Remaining Balance ($)')
        ax.set_title(f'Debt Payoff Plan - {strategy.replace("_", " ").title()} Strategy')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Save to a BytesIO object
        buf = io.BytesIO()
        canvas = FigureCanvas(fig)
        canvas.print_png(buf)
        buf.seek(0)
        
        return buf
    
    def compare_strategies(self, user_id, additional_payment=0.0):
        """Compare different payoff strategies."""
        strategies = {
            'highest_interest': 'Highest Interest First',
            'lowest_balance': 'Lowest Balance First',
            'avalanche': 'Debt Avalanche',
            'snowball': 'Debt Snowball'
        }
        
        results = {}
        for strategy_key, strategy_name in strategies.items():
            _, summary, _ = self.calculate_payoff_plan(user_id, additional_payment, strategy_key)
            if summary:  # Only add non-empty results
                results[strategy_name] = {
                    'months': summary['total_months'],
                    'interest': summary['total_interest_paid'],
                    'total_paid': summary['total_amount_paid']
                }
        
        return results
    
    def create_comparison_chart(self, user_id, additional_payment=0.0):
        """Create a chart comparing different payoff strategies."""
        strategy_results = self.compare_strategies(user_id, additional_payment)
        
        if not strategy_results:
            return None
        
        fig = Figure(figsize=(10, 8))
        
        # Create a bar chart for months to payoff
        ax1 = fig.add_subplot(211)
        strategies = list(strategy_results.keys())
        months = [data['months'] for data in strategy_results.values()]
        interest = [data['interest'] for data in strategy_results.values()]
        
        bars = ax1.bar(strategies, months, color='skyblue')
        ax1.set_ylabel('Months to Payoff')
        ax1.set_title('Payoff Time by Strategy')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{int(height)} months',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        # Create a bar chart for interest paid
        ax2 = fig.add_subplot(212)
        bars = ax2.bar(strategies, interest, color='salmon')
        ax2.set_ylabel('Total Interest Paid ($)')
        ax2.set_title('Interest Cost by Strategy')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'${int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        fig.tight_layout()
        
        # Save to a BytesIO object
        buf = io.BytesIO()
        canvas = FigureCanvas(fig)
        canvas.print_png(buf)
        buf.seek(0)
        
        return buf
