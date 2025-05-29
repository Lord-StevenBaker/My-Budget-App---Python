import unittest
import datetime
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_handler import DatabaseHandler
from budget_manager import BudgetManager
from financial_goals import FinancialGoal, GoalTracker

class TestFinancialGoals(unittest.TestCase):
    """Test cases for Financial Goal Tracking functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create in-memory database
        self.db_handler = DatabaseHandler('sqlite:///:memory:')
        self.budget_manager = BudgetManager(self.db_handler)
        
        # Create goal tracker
        self.goal_tracker = GoalTracker(self.db_handler, self.budget_manager)
        
        # Add test user
        self.test_user_id = self.db_handler.add_user('testuser', 'password')
        
        # Test dates
        self.today = datetime.date.today()
        self.future_date = self.today + datetime.timedelta(days=365)  # 1 year in future
        
    def test_create_goal(self):
        """Test creating a new financial goal"""
        # Create a new goal
        goal_id = self.goal_tracker.create_goal(
            user_id=self.test_user_id,
            name="Emergency Fund",
            target_amount=10000.00,
            target_date=self.future_date,
            priority="High",
            category="Savings"
        )
        
        # Verify goal was created
        self.assertIsNotNone(goal_id)
        
        # Retrieve the goal and check properties
        goal = self.goal_tracker.get_goal(goal_id)
        self.assertEqual(goal.name, "Emergency Fund")
        self.assertEqual(goal.target_amount, 10000.00)
        self.assertEqual(goal.target_date, self.future_date)
        self.assertEqual(goal.current_amount, 0.0)  # Initial amount is zero
        self.assertEqual(goal.priority, "High")
        self.assertEqual(goal.category, "Savings")
        
    def test_update_goal_progress(self):
        """Test updating goal progress"""
        # Create a goal
        goal_id = self.goal_tracker.create_goal(
            user_id=self.test_user_id,
            name="Vacation Fund",
            target_amount=2000.00,
            target_date=self.future_date,
            category="Travel"
        )
        
        # Update progress
        self.goal_tracker.update_goal_progress(goal_id, 500.00)
        
        # Check progress
        goal = self.goal_tracker.get_goal(goal_id)
        self.assertEqual(goal.current_amount, 500.00)
        self.assertEqual(goal.progress_percentage, 25.0)  # 500/2000 * 100
        
        # Update progress again (should be cumulative)
        self.goal_tracker.update_goal_progress(goal_id, 300.00)
        
        # Check updated progress
        goal = self.goal_tracker.get_goal(goal_id)
        self.assertEqual(goal.current_amount, 800.00)
        self.assertEqual(goal.progress_percentage, 40.0)  # 800/2000 * 100
        
    def test_get_goals_by_user(self):
        """Test retrieving all goals for a user"""
        # Create multiple goals
        self.goal_tracker.create_goal(
            user_id=self.test_user_id,
            name="Emergency Fund",
            target_amount=10000.00,
            target_date=self.future_date
        )
        
        self.goal_tracker.create_goal(
            user_id=self.test_user_id,
            name="Vacation",
            target_amount=2000.00,
            target_date=self.future_date
        )
        
        # Create goal for another user
        other_user_id = self.db_handler.add_user('otheruser', 'password')
        self.goal_tracker.create_goal(
            user_id=other_user_id,
            name="Other user goal",
            target_amount=5000.00,
            target_date=self.future_date
        )
        
        # Get goals for test user
        goals = self.goal_tracker.get_goals_by_user(self.test_user_id)
        
        # Verify only the test user's goals are returned
        self.assertEqual(len(goals), 2)
        self.assertIn("Emergency Fund", [goal.name for goal in goals])
        self.assertIn("Vacation", [goal.name for goal in goals])
        self.assertNotIn("Other user goal", [goal.name for goal in goals])
    
    def test_get_goal_projections(self):
        """Test getting goal projections"""
        # Create a goal
        goal_id = self.goal_tracker.create_goal(
            user_id=self.test_user_id,
            name="Down Payment",
            target_amount=50000.00,
            target_date=self.future_date
        )
        
        # Add some progress
        self.goal_tracker.update_goal_progress(goal_id, 10000.00)
        
        # Get projections
        projection = self.goal_tracker.get_goal_projection(goal_id)
        
        # Verify projection data
        self.assertIsNotNone(projection)
        self.assertIn('monthly_contribution_needed', projection)
        self.assertIn('will_reach_target', projection)
        self.assertIn('projected_completion_date', projection)
        
        # Calculate expected monthly contribution (remaining amount / months)
        remaining_amount = 50000.00 - 10000.00
        months_to_target = (self.future_date - self.today).days / 30.0
        expected_monthly = remaining_amount / months_to_target
        
        self.assertAlmostEqual(projection['monthly_contribution_needed'], expected_monthly, delta=1.0)
    
    def test_delete_goal(self):
        """Test deleting a financial goal"""
        # Create a goal
        goal_id = self.goal_tracker.create_goal(
            user_id=self.test_user_id,
            name="Temporary Goal",
            target_amount=1000.00,
            target_date=self.future_date
        )
        
        # Verify it exists
        goal = self.goal_tracker.get_goal(goal_id)
        self.assertIsNotNone(goal)
        
        # Delete the goal
        result = self.goal_tracker.delete_goal(goal_id)
        self.assertTrue(result)
        
        # Verify it no longer exists
        goal = self.goal_tracker.get_goal(goal_id)
        self.assertIsNone(goal)
    
    def tearDown(self):
        """Clean up after each test"""
        session = self.db_handler.get_session()
        session.close()


if __name__ == '__main__':
    unittest.main()
