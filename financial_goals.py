"""
Financial Goal Tracking Module

This module provides functionality for defining, tracking, and reporting on
financial goals such as emergency funds, down payments, vacations, etc.
"""

import datetime
import logging
from typing import List, Dict, Optional, Union, Any, Tuple
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy.exc import SQLAlchemyError
import math

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('financial_goals')

# Import Base from models
from models import Base

class FinancialGoal(Base):
    """Model representing a financial goal"""
    __tablename__ = 'financial_goals'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    description = Column(String)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    created_date = Column(Date, default=datetime.date.today)
    target_date = Column(Date, nullable=False)
    category = Column(String)
    priority = Column(String, default="Medium")  # High, Medium, Low
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="financial_goals")
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress as a percentage"""
        if self.target_amount <= 0:
            return 0.0
        
        percentage = (self.current_amount / self.target_amount) * 100
        return round(percentage, 1)
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining until target date"""
        if self.is_completed:
            return 0
            
        today = datetime.date.today()
        if self.target_date <= today:
            return 0
            
        return (self.target_date - today).days
    
    @property
    def months_remaining(self) -> float:
        """Calculate months remaining until target date"""
        return self.days_remaining / 30.0  # Approximate months
    
    @property
    def monthly_contribution_needed(self) -> float:
        """Calculate required monthly contribution to meet goal"""
        if self.is_completed or self.months_remaining <= 0:
            return 0.0
            
        remaining_amount = self.target_amount - self.current_amount
        if remaining_amount <= 0:
            return 0.0
            
        return remaining_amount / self.months_remaining


class GoalTracker:
    """Class to track and manage financial goals
    
    The GoalTracker provides functionality to create, update, and track progress
    toward financial goals. It integrates with the budget manager to provide
    realistic projections based on the user's current financial situation.
    
    Typical usage example:
    
    ```python
    tracker = GoalTracker(db_handler, budget_manager)
    goal_id = tracker.create_goal(user_id, "Emergency Fund", 10000, target_date)
    tracker.update_goal_progress(goal_id, 1000)  # Add $1000 to progress
    projection = tracker.get_goal_projection(goal_id)
    ```
    """
    
    def __init__(self, db_handler, budget_manager=None):
        """
        Initialize the GoalTracker with database and budget manager.
        
        Args:
            db_handler: Database handler instance
            budget_manager: Optional BudgetManager instance for advanced projections
        """
        self.db = db_handler
        self.budget_manager = budget_manager
        
        # Ensure financial_goals table exists
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema for financial goals"""
        # Create the financial_goals table if it doesn't exist
        try:
            Base.metadata.create_all(self.db.engine)
            # Log successful initialization
            logger.info("Financial Goals database schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Financial Goals database schema: {e}")
            # In a production environment, we might want to re-raise or handle this differently
            # For now, we'll just log the error but continue execution
    
    def create_goal(self, user_id: int, name: str, target_amount: float, target_date: datetime.date,
                    description: str = "", category: str = "General", priority: str = "Medium") -> int:
        """
        Create a new financial goal.
        
        Args:
            user_id: ID of the user who owns this goal
            name: Name of the goal
            target_amount: Target amount to save
            target_date: Target date to reach the goal
            description: Optional description of the goal
            category: Category of the goal (e.g., 'Savings', 'Home', 'Travel')
            priority: Priority level (High, Medium, Low)
            
        Returns:
            ID of the newly created goal
        """
        session = self.db.get_session()
        try:
            # Create new goal
            goal = FinancialGoal(
                user_id=user_id,
                name=name,
                description=description,
                target_amount=target_amount,
                target_date=target_date,
                category=category,
                priority=priority,
                current_amount=0.0,
                created_date=datetime.date.today(),
                is_completed=False
            )
            
            # Add to database
            session.add(goal)
            session.commit()
            
            return goal.id
        finally:
            session.close()
    
    def update_goal_progress(self, goal_id: int, amount: float) -> bool:
        """
        Update progress on a financial goal by adding to current amount.
        
        Args:
            goal_id: ID of the goal to update
            amount: Amount to add to current progress
            
        Returns:
            True if successful, False otherwise
        """
        session = self.db.get_session()
        try:
            # Get the goal
            goal = session.query(FinancialGoal).filter_by(id=goal_id).first()
            
            if not goal:
                return False
                
            # Update current amount
            goal.current_amount += amount
            
            # Check if goal is completed
            if goal.current_amount >= goal.target_amount:
                goal.is_completed = True
            
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    # Custom goal class for UI display with calculated properties
    class GoalDisplayObject:
        def __init__(self, goal):
            # Copy all attributes from the SQLAlchemy model
            self.id = goal.id
            self.user_id = goal.user_id
            self.name = goal.name
            self.description = goal.description or ""
            self.target_amount = goal.target_amount
            self.current_amount = goal.current_amount
            self.created_date = goal.created_date
            self.target_date = goal.target_date
            self.category = goal.category
            self.priority = goal.priority
            self.is_completed = goal.is_completed
            
            # Calculate additional properties
            # Progress percentage
            if self.target_amount > 0:
                self.progress_percentage = (self.current_amount / self.target_amount) * 100
            else:
                self.progress_percentage = 0.0
            
            # Days remaining
            today = datetime.date.today()
            if self.target_date and self.target_date > today:
                self.days_remaining = (self.target_date - today).days
            else:
                self.days_remaining = 0
                
            # Monthly contribution needed
            if self.days_remaining > 0:
                remaining_amount = self.target_amount - self.current_amount
                months_remaining = self.days_remaining / 30  # Approximate
                if months_remaining > 0:
                    self.monthly_contribution_needed = remaining_amount / months_remaining
                else:
                    self.monthly_contribution_needed = remaining_amount
            else:
                self.monthly_contribution_needed = 0.0
    
    def get_goal(self, goal_id: int):
        """Get a financial goal by its ID with calculated properties
        
        Args:
            goal_id: ID of the goal
            
        Returns:
            GoalDisplayObject with calculated properties or None if not found
        """
        print(f"[DEBUG] get_goal called with goal_id: {goal_id}")
        if not goal_id:
            logger.error(f"Invalid goal ID: {goal_id}")
            print(f"[DEBUG] Invalid goal ID: {goal_id}")
            return None
            
        session = None
        try:
            print(f"[DEBUG] Attempting to get database session")
            session = self.db.get_session()
            print(f"[DEBUG] Session created: {session is not None}")
            if not session:
                logger.error("Failed to get database session")
                print(f"[DEBUG] Failed to get database session")
                return None
                
            print(f"[DEBUG] Querying for goal with ID: {goal_id}")
            goal = session.query(FinancialGoal).filter_by(id=goal_id).first()
            print(f"[DEBUG] Query result: {goal is not None}")
            if not goal:
                logger.warning(f"Goal with ID {goal_id} not found")
                print(f"[DEBUG] Goal with ID {goal_id} not found in database")
                return None
                
            # Create a custom object with calculated properties
            goal_display_obj = self.GoalDisplayObject(goal)
            print(f"[DEBUG] Created goal display object with ID: {goal_display_obj.id}")
            
            logger.info(f"Retrieved goal: {goal_display_obj.name}")
            print(f"[DEBUG] Successfully retrieved goal with ID {goal_id}")
            return goal_display_obj
        except Exception as e:
            logger.error(f"Error retrieving goal with ID {goal_id}: {str(e)}")
            print(f"[DEBUG] Error in get_goal: {str(e)}")
            return None
        finally:
            if session:
                session.close()
    
    def get_goals_by_user(self, user_id: int, filter_completed: bool = False, 
                         category: str = None, order_by: str = 'target_date') -> List[FinancialGoal]:
        """
        Get all financial goals for a user with optional filtering and sorting.
        
        Args:
            user_id: ID of the user
            filter_completed: If True, only returns incomplete goals
            category: Optional category to filter by
            order_by: Field to sort by ('target_date', 'priority', 'name')
            
        Returns:
            List of FinancialGoal objects
        """
        session = None
        try:
            # Get database session
            session = self.db.get_session()
            if session is None:
                logger.error(f"Could not create database session for user {user_id}")
                return []
                
            # Check if financial_goals table exists
            try:
                # Start with basic query
                query = session.query(FinancialGoal).filter_by(user_id=user_id)
                
                # Apply filters
                if filter_completed:
                    query = query.filter_by(is_completed=False)
                
                if category:
                    query = query.filter_by(category=category)
                
                # Apply sorting
                if order_by == 'priority':
                    # Custom priority ordering (High, Medium, Low)
                    priority_case = {
                        'High': 1,
                        'Medium': 2,
                        'Low': 3
                    }
                    query = query.order_by(
                        # This is a simplification - in a real app, we'd use case statements in SQL
                        FinancialGoal.priority
                    )
                elif order_by == 'name':
                    query = query.order_by(FinancialGoal.name)
                else:  # Default to target_date
                    query = query.order_by(FinancialGoal.target_date)
                
                goals = query.all()
                logger.info(f"Retrieved {len(goals)} goals for user {user_id}")
                return goals
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error retrieving goals for user {user_id}: {e}")
                # Try to reinitialize the database
                self._init_db()
                return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving goals for user {user_id}: {e}")
            return []
        finally:
            if session:
                session.close()
    
    def get_goal_projection(self, goal_id: int) -> Dict[str, Union[float, bool, datetime.date]]:
        """
        Get projection details for a goal.
        
        Args:
            goal_id: ID of the goal
            
        Returns:
            Dictionary with projection details
        """
        session = self.db.get_session()
        try:
            goal = session.query(FinancialGoal).filter_by(id=goal_id).first()
            
            if not goal:
                return {}
            
            # Calculate monthly contribution needed
            monthly_needed = goal.monthly_contribution_needed
            
            # Determine if goal can be met on time
            remaining_amount = goal.target_amount - goal.current_amount
            
            # If we have a budget manager, use it to determine available funds
            available_monthly = 0
            will_reach_target = False
            projected_completion_date = None
            
            if self.budget_manager and goal.user_id:
                # Calculate monthly available funds from cash flow
                cash_flow = self.budget_manager.get_total_income(goal.user_id) - \
                           self.budget_manager.get_total_expense(goal.user_id)
                available_monthly = max(0, cash_flow)
                
                will_reach_target = available_monthly >= monthly_needed
                
                # Calculate projected completion date
                if available_monthly > 0:
                    months_needed = remaining_amount / available_monthly
                    days_needed = math.ceil(months_needed * 30)
                    projected_completion_date = datetime.date.today() + datetime.timedelta(days=days_needed)
            
            return {
                'monthly_contribution_needed': monthly_needed,
                'will_reach_target': will_reach_target,
                'projected_completion_date': projected_completion_date,
                'remaining_amount': remaining_amount,
                'available_monthly': available_monthly
            }
        finally:
            session.close()
    
    def delete_goal(self, goal_id: int) -> bool:
        """
        Delete a financial goal.
        
        Args:
            goal_id: ID of the goal to delete
            
        Returns:
            True if successful, False otherwise
        """
        session = self.db.get_session()
        try:
            goal = session.query(FinancialGoal).filter_by(id=goal_id).first()
            
            if not goal:
                return False
            
            session.delete(goal)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def update_goal_details(self, goal_id: int, **kwargs) -> bool:
        """
        Update details of a financial goal.
        
        Args:
            goal_id: ID of the goal to update
            **kwargs: Fields to update (name, target_amount, target_date, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        session = self.db.get_session()
        try:
            goal = session.query(FinancialGoal).filter_by(id=goal_id).first()
            
            if not goal:
                return False
            
            # Update fields
            for field, value in kwargs.items():
                if hasattr(goal, field):
                    setattr(goal, field, value)
            
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
            
    def get_goal_summary_stats(self, user_id: int) -> Dict[str, Any]:
        """Get summary statistics for a user's financial goals.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with summary statistics:
            - total_goals: Total number of goals
            - completed_goals: Number of completed goals
            - total_target_amount: Sum of all target amounts
            - total_current_amount: Sum of all current amounts
            - average_progress: Average progress percentage across all goals
            - nearest_deadline: Date of the closest upcoming deadline
        """
        session = self.db.get_session()
        try:
            goals = session.query(FinancialGoal).filter_by(user_id=user_id).all()
            
            if not goals:
                return {
                    'total_goals': 0,
                    'completed_goals': 0,
                    'total_target_amount': 0.0,
                    'total_current_amount': 0.0,
                    'average_progress': 0.0,
                    'nearest_deadline': None
                }
            
            # Count total and completed goals
            total_goals = len(goals)
            completed_goals = sum(1 for goal in goals if goal.is_completed)
            
            # Calculate financial totals
            total_target_amount = sum(goal.target_amount for goal in goals)
            total_current_amount = sum(goal.current_amount for goal in goals)
            
            # Calculate average progress
            progress_values = [goal.progress_percentage for goal in goals]
            average_progress = sum(progress_values) / len(progress_values) if progress_values else 0.0
            
            # Find nearest deadline for incomplete goals
            incomplete_goals = [goal for goal in goals if not goal.is_completed]
            nearest_deadline = min((goal.target_date for goal in incomplete_goals), default=None)
            
            return {
                'total_goals': total_goals,
                'completed_goals': completed_goals,
                'total_target_amount': total_target_amount,
                'total_current_amount': total_current_amount,
                'average_progress': average_progress,
                'nearest_deadline': nearest_deadline
            }
        except Exception as e:
            logger.error(f"Error getting goal summary stats: {e}")
            return {}
        finally:
            session.close()
            
    def analyze_goal_feasibility(self, goal_id: int) -> Dict[str, Any]:
        """Analyze the feasibility of meeting a goal by its target date.
        
        This method uses the budget manager to analyze whether the goal
        can realistically be met based on current financial situation.
        
        Args:
            goal_id: ID of the goal to analyze
            
        Returns:
            Dictionary with feasibility analysis
        """
        session = self.db.get_session()
        try:
            goal = session.query(FinancialGoal).filter_by(id=goal_id).first()
            
            if not goal or not self.budget_manager:
                return {}
                
            # Get free cash flow from budget manager
            monthly_income = self.budget_manager.get_total_income(goal.user_id)
            monthly_expenses = self.budget_manager.get_total_expense(goal.user_id)
            free_cash_flow = monthly_income - monthly_expenses
            
            # Calculate amount needed
            remaining_amount = goal.target_amount - goal.current_amount
            
            # Calculate months needed with current cash flow
            if free_cash_flow <= 0:
                months_needed = float('inf')  # Cannot reach goal with negative cash flow
                feasible = False
            else:
                months_needed = remaining_amount / free_cash_flow
                months_to_deadline = goal.months_remaining
                feasible = months_needed <= months_to_deadline
            
            # Calculate required monthly savings to meet goal
            if goal.months_remaining <= 0:
                required_monthly = float('inf')  # Past deadline
            else:
                required_monthly = remaining_amount / goal.months_remaining
            
            return {
                'free_cash_flow': free_cash_flow,
                'months_needed': months_needed,
                'months_to_deadline': goal.months_remaining,
                'required_monthly': required_monthly,
                'feasible': feasible,
                'percentage_of_income': (required_monthly / monthly_income * 100) if monthly_income > 0 else float('inf'),
                'remaining_amount': remaining_amount
            }
        except Exception as e:
            logger.error(f"Error analyzing goal feasibility: {e}")
            return {}
        finally:
            session.close()
