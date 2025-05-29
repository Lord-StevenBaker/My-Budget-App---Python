"""
Financial Goals Tab for the Budget Manager application.

This module provides UI components for creating, tracking, and managing financial goals.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QPushButton, QTableWidget, QTableWidgetItem,
                          QFormLayout, QLineEdit, QDateEdit, QComboBox,
                          QDialog, QMessageBox, QProgressBar, QHeaderView,
                          QFrame, QSplitter, QGroupBox, QDoubleSpinBox, QSpinBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from financial_goals import GoalTracker
import datetime

class GoalsTab(QWidget):
    """Tab for managing financial goals"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.goal_tracker = GoalTracker(budget_manager.db, budget_manager)
        self.selected_goal_id = None
        
        # Initialize UI components
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Header section
        header_layout = QHBoxLayout()
        title_label = QLabel("Financial Goals")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Create buttons
        self.add_goal_btn = QPushButton("Add New Goal")
        self.add_goal_btn.clicked.connect(self.show_add_goal_dialog)
        header_layout.addWidget(self.add_goal_btn)
        
        main_layout.addLayout(header_layout)
        
        # Add horizontal line separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Create splitter for table and details panel
        splitter = QSplitter(Qt.Horizontal)
        
        # Goals table
        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(6)
        self.goals_table.setHorizontalHeaderLabels([
            'Name', 'Target ($)', 'Current ($)', 'Progress', 'Target Date', 'Priority'
        ])
        self.goals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.goals_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.goals_table.setSelectionMode(QTableWidget.SingleSelection)
        self.goals_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.goals_table.cellClicked.connect(self.goal_selected)
        splitter.addWidget(self.goals_table)
        
        # Goal details panel
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        
        # Goal details group
        details_group = QGroupBox("Goal Details")
        goal_form = QFormLayout()
        
        self.goal_name_label = QLabel("Select a goal")
        self.goal_name_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        goal_form.addRow(self.goal_name_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label = QLabel("0%")
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        goal_form.addRow("Progress:", progress_layout)
        
        # Goal details
        self.current_amount_label = QLabel("$0.00")
        self.target_amount_label = QLabel("$0.00")
        self.remaining_amount_label = QLabel("$0.00")
        self.days_remaining_label = QLabel("0 days")
        self.monthly_needed_label = QLabel("$0.00/month")
        self.created_date_label = QLabel("")
        self.target_date_label = QLabel("")
        self.category_label = QLabel("")
        self.priority_label = QLabel("")
        self.feasibility_label = QLabel("")
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        
        goal_form.addRow("Current Amount:", self.current_amount_label)
        goal_form.addRow("Target Amount:", self.target_amount_label)
        goal_form.addRow("Remaining:", self.remaining_amount_label)
        goal_form.addRow("Days Left:", self.days_remaining_label)
        goal_form.addRow("Monthly Contribution:", self.monthly_needed_label)
        goal_form.addRow("Created:", self.created_date_label)
        goal_form.addRow("Target Date:", self.target_date_label)
        goal_form.addRow("Category:", self.category_label)
        goal_form.addRow("Priority:", self.priority_label)
        goal_form.addRow("Feasibility:", self.feasibility_label)
        goal_form.addRow("Description:", self.description_label)
        
        details_group.setLayout(goal_form)
        details_layout.addWidget(details_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.update_progress_btn = QPushButton("Update Progress")
        self.update_progress_btn.clicked.connect(self.show_update_progress_dialog)
        self.update_progress_btn.setEnabled(False)
        
        self.edit_goal_btn = QPushButton("Edit Goal")
        self.edit_goal_btn.clicked.connect(self.show_edit_goal_dialog)
        self.edit_goal_btn.setEnabled(False)
        
        self.delete_goal_btn = QPushButton("Delete Goal")
        self.delete_goal_btn.clicked.connect(self.delete_goal)
        self.delete_goal_btn.setEnabled(False)
        
        action_layout.addWidget(self.update_progress_btn)
        action_layout.addWidget(self.edit_goal_btn)
        action_layout.addWidget(self.delete_goal_btn)
        details_layout.addLayout(action_layout)
        
        details_layout.addStretch()
        splitter.addWidget(details_panel)
        
        # Set default splitter sizes
        splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        main_layout.addWidget(splitter)
        
        # Summary section
        summary_group = QGroupBox("Goals Summary")
        summary_layout = QHBoxLayout()
        
        self.total_goals_label = QLabel("Total Goals: 0")
        self.completed_goals_label = QLabel("Completed: 0")
        self.avg_progress_label = QLabel("Average Progress: 0%")
        self.total_goal_amount_label = QLabel("Total Target: $0.00")
        self.total_current_label = QLabel("Total Saved: $0.00")
        
        summary_layout.addWidget(self.total_goals_label)
        summary_layout.addWidget(self.completed_goals_label)
        summary_layout.addWidget(self.avg_progress_label)
        summary_layout.addWidget(self.total_goal_amount_label)
        summary_layout.addWidget(self.total_current_label)
        
        summary_group.setLayout(summary_layout)
        main_layout.addWidget(summary_group)
        
        self.setLayout(main_layout)
        
    def refresh_data(self):
        """Refresh the goals data from the database"""
        try:
            # Clear the table
            self.goals_table.setRowCount(0)
            
            # Get all goals for the user
            goals = self.goal_tracker.get_goals_by_user(self.user_id)
            
            if not goals:
                # No goals found, just update summary stats and return
                self.update_summary_stats()
                self.clear_details_panel()
                return
                
            # Set row count
            self.goals_table.setRowCount(len(goals))
            
            # Populate table
            for row, goal in enumerate(goals):
                try:
                    # Name
                    name_item = QTableWidgetItem(str(goal.name) if goal.name else "Unnamed Goal")
                    self.goals_table.setItem(row, 0, name_item)
                    
                    # Target amount
                    target_item = QTableWidgetItem(f"${goal.target_amount:.2f}")
                    target_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.goals_table.setItem(row, 1, target_item)
                    
                    # Current amount
                    current_item = QTableWidgetItem(f"${goal.current_amount:.2f}")
                    current_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.goals_table.setItem(row, 2, current_item)
                    
                    # Progress
                    progress = goal.progress_percentage
                    progress_item = QTableWidgetItem(f"{progress:.1f}%")
                    progress_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    # Color code based on progress
                    if progress >= 80:
                        progress_item.setBackground(QColor(200, 255, 200))  # Light green
                    elif progress >= 50:
                        progress_item.setBackground(QColor(255, 255, 200))  # Light yellow
                    else:
                        progress_item.setBackground(QColor(255, 200, 200))  # Light red
                        
                    self.goals_table.setItem(row, 3, progress_item)
                    
                    # Target date
                    try:
                        target_date_str = goal.target_date.strftime("%Y-%m-%d") if goal.target_date else "Not set"
                    except (AttributeError, ValueError):
                        target_date_str = "Invalid date"
                        
                    target_date_item = QTableWidgetItem(target_date_str)
                    
                    # Color code based on days remaining
                    days_left = getattr(goal, 'days_remaining', 0)
                    if days_left <= 30:
                        target_date_item.setForeground(QColor(255, 0, 0))  # Red text
                    elif days_left <= 90:
                        target_date_item.setForeground(QColor(255, 165, 0))  # Orange text
                    
                    self.goals_table.setItem(row, 4, target_date_item)
                    
                    # Priority
                    priority_text = str(goal.priority) if hasattr(goal, 'priority') and goal.priority else "Medium"
                    priority_item = QTableWidgetItem(priority_text)
                    if priority_text == "High":
                        priority_item.setForeground(QColor(255, 0, 0))
                    elif priority_text == "Medium":
                        priority_item.setForeground(QColor(0, 0, 255))
                    
                    self.goals_table.setItem(row, 5, priority_item)
                    
                    # Store goal ID in the first column's item
                    self.goals_table.item(row, 0).setData(Qt.UserRole, goal.id)
                except Exception as e:
                    print(f"Error displaying goal row {row}: {e}")
                    # Continue with next goal instead of crashing
                    continue
        except Exception as e:
            print(f"Error refreshing goals data: {e}")
            # Show error message to user
            QMessageBox.warning(self, "Data Error", 
                              f"Error loading financial goals data: {str(e)}\n\nThe application will continue to function, but some data may not be displayed correctly.")

        
        # Update goal summary statistics
        self.update_summary_stats()
        
        # Clear details panel if no selected goal
        if self.selected_goal_id is None:
            self.clear_details_panel()
    
    def goal_selected(self, row, column):
        """Handle goal selection from the table"""
        try:
            # Validate row and column
            if row < 0 or column < 0 or row >= self.goals_table.rowCount():
                return
                
            # Get goal ID from the selected row
            item = self.goals_table.item(row, 0)
            if not item:
                return
                
            goal_id = item.data(Qt.UserRole)
            if not goal_id:
                return
                
            self.selected_goal_id = goal_id
            
            # Enable buttons
            self.update_progress_btn.setEnabled(True)
            self.edit_goal_btn.setEnabled(True)
            self.delete_goal_btn.setEnabled(True)
            
            # Get goal details
            goal = self.goal_tracker.get_goal(goal_id)
            if not goal:
                self.clear_details_panel()
                return
                
            try:
                # Get projection details
                projection = self.goal_tracker.get_goal_projection(goal_id)
                
                # Update details panel
                self.goal_name_label.setText(str(goal.name) if goal.name else "Unnamed Goal")
                
                # Update progress bar - handle potential errors
                try:
                    progress = goal.progress_percentage
                    self.progress_bar.setValue(int(progress))
                    self.progress_label.setText(f"{progress:.1f}%")
                except (AttributeError, ValueError, TypeError) as e:
                    self.progress_bar.setValue(0)
                    self.progress_label.setText("0%")
                    print(f"Error calculating progress: {e}")
                
                # Update goal details with validation
                try:
                    self.current_amount_label.setText(f"${goal.current_amount:.2f}")
                    self.target_amount_label.setText(f"${goal.target_amount:.2f}")
                    
                    remaining = goal.target_amount - goal.current_amount
                    self.remaining_amount_label.setText(f"${remaining:.2f}")
                except (AttributeError, ValueError, TypeError) as e:
                    self.current_amount_label.setText("$0.00")
                    self.target_amount_label.setText("$0.00")
                    self.remaining_amount_label.setText("$0.00")
                    print(f"Error calculating amounts: {e}")
                
                # Days remaining and monthly contribution
                try:
                    self.days_remaining_label.setText(f"{goal.days_remaining} days")
                    self.monthly_needed_label.setText(f"${goal.monthly_contribution_needed:.2f}/month")
                except (AttributeError, ValueError, TypeError) as e:
                    self.days_remaining_label.setText("0 days")
                    self.monthly_needed_label.setText("$0.00/month")
                    print(f"Error calculating time projections: {e}")
                
                # Date formatting with validation
                try:
                    if hasattr(goal, 'created_date') and goal.created_date:
                        self.created_date_label.setText(goal.created_date.strftime("%Y-%m-%d"))
                    else:
                        self.created_date_label.setText("Not set")
                        
                    if hasattr(goal, 'target_date') and goal.target_date:
                        self.target_date_label.setText(goal.target_date.strftime("%Y-%m-%d"))
                    else:
                        self.target_date_label.setText("Not set")
                except (AttributeError, ValueError, TypeError) as e:
                    self.created_date_label.setText("Unknown")
                    self.target_date_label.setText("Unknown")
                    print(f"Error formatting dates: {e}")
                
                # Category and priority
                self.category_label.setText(str(goal.category) if hasattr(goal, 'category') and goal.category else "General")
                self.priority_label.setText(str(goal.priority) if hasattr(goal, 'priority') and goal.priority else "Medium")
                
                # Set feasibility label
                if projection and isinstance(projection, dict) and 'will_reach_target' in projection:
                    if projection['will_reach_target']:
                        self.feasibility_label.setText("On track")
                        self.feasibility_label.setStyleSheet("color: green;")
                    else:
                        self.feasibility_label.setText("Off track")
                        self.feasibility_label.setStyleSheet("color: red;")
                else:
                    self.feasibility_label.setText("Unknown")
                    self.feasibility_label.setStyleSheet("")
                
                # Set description with validation
                self.description_label.setText(goal.description if hasattr(goal, 'description') and goal.description else "No description")
                
            except Exception as e:
                print(f"Error displaying goal details: {e}")
                # Don't clear everything, just show error in description
                self.description_label.setText(f"Error loading some goal details: {str(e)}")
                
        except Exception as e:
            print(f"Error in goal selection: {e}")
            # Keep the UI functioning
            self.clear_details_panel()
    
    def clear_details_panel(self):
        """Clear the goal details panel"""
        self.goal_name_label.setText("Select a goal")
        self.progress_bar.setValue(0)
        self.progress_label.setText("0%")
        self.current_amount_label.setText("$0.00")
        self.target_amount_label.setText("$0.00")
        self.remaining_amount_label.setText("$0.00")
        self.days_remaining_label.setText("0 days")
        self.monthly_needed_label.setText("$0.00/month")
        self.created_date_label.setText("")
        self.target_date_label.setText("")
        self.category_label.setText("")
        self.priority_label.setText("")
        self.feasibility_label.setText("")
        self.description_label.setText("")
        
        # Disable action buttons
        self.update_progress_btn.setEnabled(False)
        self.edit_goal_btn.setEnabled(False)
        self.delete_goal_btn.setEnabled(False)
    
    def update_summary_stats(self):
        """Update the summary statistics for goals"""
        stats = self.goal_tracker.get_goal_summary_stats(self.user_id)
        
        self.total_goals_label.setText(f"Total Goals: {stats['total_goals']}")
        self.completed_goals_label.setText(f"Completed: {stats['completed_goals']}")
        self.avg_progress_label.setText(f"Average Progress: {stats['average_progress']:.1f}%")
        self.total_goal_amount_label.setText(f"Total Target: ${stats['total_target_amount']:.2f}")
        self.total_current_label.setText(f"Total Saved: ${stats['total_current_amount']:.2f}")
    
    def show_add_goal_dialog(self):
        """Show dialog to add a new financial goal"""
        dialog = AddGoalDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Get data from the dialog
            name = dialog.name_edit.text()
            description = dialog.description_edit.text()
            target_amount = dialog.target_amount_spin.value()
            target_date = dialog.target_date_edit.date().toPyDate()
            category = dialog.category_combo.currentText()
            priority = dialog.priority_combo.currentText()
            
            # Create the goal
            self.goal_tracker.create_goal(
                self.user_id,
                name,
                target_amount,
                target_date,
                description,
                category,
                priority
            )
            
            # Refresh data
            self.refresh_data()
    
    def show_edit_goal_dialog(self):
        """Show dialog to edit an existing financial goal"""
        if not self.selected_goal_id:
            return
        
        # Get current goal data
        goal = self.goal_tracker.get_goal(self.selected_goal_id)
        if not goal:
            return
        
        dialog = EditGoalDialog(self, goal)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Get data from the dialog
            updates = {
                'name': dialog.name_edit.text(),
                'description': dialog.description_edit.text(),
                'target_amount': dialog.target_amount_spin.value(),
                'target_date': dialog.target_date_edit.date().toPyDate(),
                'category': dialog.category_combo.currentText(),
                'priority': dialog.priority_combo.currentText()
            }
            
            # Update the goal
            self.goal_tracker.update_goal_details(self.selected_goal_id, **updates)
            
            # Refresh data
            self.refresh_data()
            
            # Re-select the goal
            self.goal_selected(self.goals_table.currentRow(), 0)
    
    def show_update_progress_dialog(self):
        """Show dialog to update progress on a goal"""
        if not self.selected_goal_id:
            return
        
        # Get current goal data
        goal = self.goal_tracker.get_goal(self.selected_goal_id)
        if not goal:
            return
        
        dialog = UpdateProgressDialog(self, goal)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Get amount from the dialog
            amount = dialog.amount_spin.value()
            
            # Update goal progress
            self.goal_tracker.update_goal_progress(self.selected_goal_id, amount)
            
            # Refresh data
            self.refresh_data()
            
            # Re-select the goal
            self.goal_selected(self.goals_table.currentRow(), 0)
    
    def delete_goal(self):
        """Delete the selected financial goal"""
        if not self.selected_goal_id:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 'Delete Goal',
            'Are you sure you want to delete this goal?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete the goal
            self.goal_tracker.delete_goal(self.selected_goal_id)
            
            # Clear selection and refresh
            self.selected_goal_id = None
            self.clear_details_panel()
            self.refresh_data()


class AddGoalDialog(QDialog):
    """Dialog for adding a new financial goal"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Goal")
        self.setMinimumWidth(400)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI components"""
        layout = QFormLayout(self)
        
        # Goal name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter goal name")
        layout.addRow("Name:", self.name_edit)
        
        # Target amount
        self.target_amount_spin = QDoubleSpinBox()
        self.target_amount_spin.setRange(0, 1000000)
        self.target_amount_spin.setDecimals(2)
        self.target_amount_spin.setSingleStep(100)
        self.target_amount_spin.setValue(1000)
        self.target_amount_spin.setPrefix("$")
        layout.addRow("Target Amount:", self.target_amount_spin)
        
        # Target date
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setCalendarPopup(True)
        today = QDate.currentDate()
        one_year_later = today.addYears(1)
        self.target_date_edit.setDate(one_year_later)
        self.target_date_edit.setMinimumDate(today)
        layout.addRow("Target Date:", self.target_date_edit)
        
        # Category
        self.category_combo = QComboBox()
        default_categories = ["Savings", "Emergency Fund", "Home", "Car", "Education", 
                             "Vacation", "Retirement", "Electronics", "Other"]
        for category in default_categories:
            self.category_combo.addItem(category)
        layout.addRow("Category:", self.category_combo)
        
        # Priority
        self.priority_combo = QComboBox()
        priorities = ["High", "Medium", "Low"]
        for priority in priorities:
            self.priority_combo.addItem(priority)
        self.priority_combo.setCurrentText("Medium")
        layout.addRow("Priority:", self.priority_combo)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description")
        layout.addRow("Description:", self.description_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.check_and_accept)
        self.save_btn.setDefault(True)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addRow("", btn_layout)
    
    def check_and_accept(self):
        """Validate inputs before accepting"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Goal name is required.")
            return
            
        if self.target_amount_spin.value() <= 0:
            QMessageBox.warning(self, "Invalid Input", "Target amount must be greater than zero.")
            return
            
        self.accept()


class EditGoalDialog(QDialog):
    """Dialog for editing an existing financial goal"""
    
    def __init__(self, parent=None, goal=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Goal")
        self.setMinimumWidth(400)
        self.goal = goal
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI components"""
        layout = QFormLayout(self)
        
        # Goal name
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.goal.name)
        layout.addRow("Name:", self.name_edit)
        
        # Target amount
        self.target_amount_spin = QDoubleSpinBox()
        self.target_amount_spin.setRange(self.goal.current_amount, 1000000)
        self.target_amount_spin.setDecimals(2)
        self.target_amount_spin.setSingleStep(100)
        self.target_amount_spin.setValue(self.goal.target_amount)
        self.target_amount_spin.setPrefix("$")
        layout.addRow("Target Amount:", self.target_amount_spin)
        
        # Target date
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setCalendarPopup(True)
        today = QDate.currentDate()
        goal_date = QDate(self.goal.target_date.year, self.goal.target_date.month, self.goal.target_date.day)
        self.target_date_edit.setDate(goal_date)
        self.target_date_edit.setMinimumDate(today)
        layout.addRow("Target Date:", self.target_date_edit)
        
        # Category
        self.category_combo = QComboBox()
        default_categories = ["Savings", "Emergency Fund", "Home", "Car", "Education", 
                             "Vacation", "Retirement", "Electronics", "Other"]
        for category in default_categories:
            self.category_combo.addItem(category)
        
        # Set current category if it exists in the list, otherwise add it
        index = self.category_combo.findText(self.goal.category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.addItem(self.goal.category)
            self.category_combo.setCurrentText(self.goal.category)
        
        layout.addRow("Category:", self.category_combo)
        
        # Priority
        self.priority_combo = QComboBox()
        priorities = ["High", "Medium", "Low"]
        for priority in priorities:
            self.priority_combo.addItem(priority)
        self.priority_combo.setCurrentText(self.goal.priority)
        layout.addRow("Priority:", self.priority_combo)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setText(self.goal.description if self.goal.description else "")
        layout.addRow("Description:", self.description_edit)
        
        # Current amount display (not editable)
        current_amount_label = QLabel(f"${self.goal.current_amount:.2f}")
        layout.addRow("Current Amount:", current_amount_label)
        
        # Progress display
        progress_label = QLabel(f"{self.goal.progress_percentage:.1f}%")
        layout.addRow("Progress:", progress_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.check_and_accept)
        self.save_btn.setDefault(True)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addRow("", btn_layout)
    
    def check_and_accept(self):
        """Validate inputs before accepting"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Goal name is required.")
            return
            
        if self.target_amount_spin.value() < self.goal.current_amount:
            QMessageBox.warning(self, "Invalid Input", "Target amount cannot be less than current amount.")
            return
            
        self.accept()


class UpdateProgressDialog(QDialog):
    """Dialog for updating progress on a financial goal"""
    
    def __init__(self, parent=None, goal=None):
        super().__init__(parent)
        self.setWindowTitle("Update Goal Progress")
        self.goal = goal
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI components"""
        layout = QFormLayout(self)
        
        # Header
        header = QLabel(f"<h3>{self.goal.name}</h3>")
        layout.addRow(header)
        
        # Current amount
        current_amount = QLabel(f"${self.goal.current_amount:.2f}")
        layout.addRow("Current Amount:", current_amount)
        
        # Target amount
        target_amount = QLabel(f"${self.goal.target_amount:.2f}")
        layout.addRow("Target Amount:", target_amount)
        
        # Remaining amount
        remaining = self.goal.target_amount - self.goal.current_amount
        remaining_amount = QLabel(f"${remaining:.2f}")
        layout.addRow("Remaining:", remaining_amount)
        
        # Amount to add
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, remaining)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSingleStep(50)
        self.amount_spin.setValue(min(100, remaining))
        self.amount_spin.setPrefix("$")
        layout.addRow("Add Amount:", self.amount_spin)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.update_btn = QPushButton("Update")
        self.update_btn.clicked.connect(self.accept)
        self.update_btn.setDefault(True)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.update_btn)
        
        layout.addRow("", btn_layout)
