"""
Financial Goals Tab for the Budget Manager application.

This module provides UI components for creating, tracking, and managing financial goals.
Version: 2.0 - Complete redesign with modern UI and better user experience
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTableWidget, QTableWidgetItem,
                           QFormLayout, QLineEdit, QDateEdit, QComboBox,
                           QDialog, QMessageBox, QProgressBar, QHeaderView,
                           QFrame, QSplitter, QGroupBox, QDoubleSpinBox, QSpinBox,
                           QMenu, QAction, QTabWidget, QScrollArea, QSizePolicy,
                           QStyleFactory, QApplication, QStyle, QToolBar)
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QMargins
from PyQt5.QtGui import QColor, QPalette, QIcon, QFont, QPixmap, QBrush
from financial_goals import GoalTracker
import datetime
import sys
import os

class GoalsTab(QWidget):
    """Tab for managing financial goals - modern UI redesign"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.goal_tracker = GoalTracker(budget_manager.db, budget_manager)
        self.selected_goal_id = None
        self.selected_row = -1  # Track the selected row for highlighting
        
        # Initialize UI components
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize the user interface components with modern design"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header section with modern style
        header_layout = QHBoxLayout()
        title_label = QLabel("Financial Goals")
        title_label.setStyleSheet("font-size: 22pt; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Modern toolbar with action buttons
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar { 
                background-color: #f8f9fa; 
                border-radius: 5px; 
                padding: 5px;
            }
            QToolButton { 
                background-color: #ffffff; 
                border: 1px solid #e1e4e8; 
                border-radius: 4px; 
                padding: 5px; 
                margin: 2px;
            }
            QToolButton:hover { 
                background-color: #e9ecef; 
            }
            QToolButton:pressed { 
                background-color: #dee2e6; 
            }
        """)
        
        # Add buttons to toolbar
        self.add_goal_btn = QPushButton("Add New Goal")
        self.add_goal_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.add_goal_btn.clicked.connect(self.show_add_goal_dialog)
        header_layout.addWidget(self.add_goal_btn)
        
        main_layout.addLayout(header_layout)
        
        # Modern separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e1e4e8; min-height: 1px; margin: 10px 0px;")
        main_layout.addWidget(separator)
        
        # Create panels layout with a splitter for main content area
        content_area = QSplitter(Qt.Horizontal)
        content_area.setStyleSheet("QSplitter::handle { background-color: #e1e4e8; width: 2px; }")        
        
        # Left panel - Goals table with modern styling
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Table header with filter options
        table_header = QWidget()
        table_header_layout = QHBoxLayout(table_header)
        table_header_layout.setContentsMargins(5, 5, 5, 5)
        
        table_header_layout.addWidget(QLabel("<b>Your Goals</b>"))
        table_header_layout.addStretch()
        
        # Category filter
        filter_label = QLabel("Category:")
        self.category_filter_combo = QComboBox()  # Renamed to match usage in methods
        self.category_filter_combo.addItem("All Categories")
        self.category_filter_combo.setMinimumWidth(150)  # Make it wide enough to show categories
        self.category_filter_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
            }
        """)
        # Will be connected in update_category_filter_options method
        
        table_header_layout.addWidget(filter_label)
        table_header_layout.addWidget(self.category_filter_combo)
        
        # Search/refresh area
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QApplication.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_btn.setToolTip("Refresh Goals List")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """)
        table_header_layout.addWidget(self.refresh_btn)
        
        # Add header widget to layout
        left_layout.addWidget(table_header)
        
        # Add a table to display goals - customize for modern look
        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(7)
        self.goals_table.setHorizontalHeaderLabels(["ID", "Name", "Target", "Current", "Progress", "Target Date", "Priority"])
        self.goals_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.goals_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.goals_table.setSelectionMode(QTableWidget.SingleSelection)
        self.goals_table.setAlternatingRowColors(True)
        self.goals_table.verticalHeader().setVisible(False)
        self.goals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.goals_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # ID column fixed width
        self.goals_table.horizontalHeader().resizeSection(0, 0)  # Hide ID column by setting width to 0
        self.goals_table.setColumnHidden(0, True)  # Actually hide the ID column
        self.goals_table.setSortingEnabled(True)  # Enable sorting
        self.goals_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                selection-background-color: #e3f2fd;
                selection-color: black;
                border: 1px solid #e1e4e8;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #e1e4e8;
                padding: 4px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f1f1f1;
            }
        """)
        self.goals_table.itemSelectionChanged.connect(lambda: self.goal_selected(self.goals_table.currentRow(), 0))
        self.goals_table.cellClicked.connect(self.goal_selected)
        self.goals_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.goals_table.customContextMenuRequested.connect(self.show_goals_context_menu)

        left_layout.addWidget(self.goals_table)
        content_area.addWidget(left_panel)
        
        # Right panel - Goal details with modern styling and action buttons area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # === DEDICATED ACTION BUTTONS AREA ===
        action_panel = QWidget()
        action_panel.setStyleSheet("""
            QWidget { 
                background-color: #f8f9fa; 
                border: 1px solid #e1e4e8;
                border-radius: 5px;
            }
            QPushButton { 
                padding: 8px 16px; 
                border-radius: 4px; 
                font-weight: bold;
                margin: 5px;
            }
        """)
        action_layout = QHBoxLayout(action_panel)
        
        # Add the three main action buttons requested by the user
        self.edit_goal_btn = QPushButton("Edit Goal")
        self.edit_goal_btn.setStyleSheet("""
            QPushButton { 
                background-color: #17a2b8; 
                color: white; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #138496; 
            }
            QPushButton:disabled { 
                background-color: #89d1de; 
            }
        """)
        self.edit_goal_btn.setEnabled(False)
        self.edit_goal_btn.clicked.connect(self.show_edit_goal_dialog)
        
        self.update_progress_btn = QPushButton("Update Progress")
        self.update_progress_btn.setStyleSheet("""
            QPushButton { 
                background-color: #007bff; 
                color: white; 
                border: none; 
            }
            QPushButton:hover { 
                background-color: #0069d9; 
            }
            QPushButton:disabled { 
                background-color: #80bdff; 
            }
        """)
        self.update_progress_btn.setEnabled(False)
        self.update_progress_btn.clicked.connect(self.show_update_progress_dialog)
        
        self.delete_goal_btn = QPushButton("Delete Goal")
        self.delete_goal_btn.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                border: none; 
            }
            QPushButton:hover { 
                background-color: #c82333; 
            }
            QPushButton:disabled { 
                background-color: #ed969e; 
            }
        """)
        self.delete_goal_btn.setEnabled(False)
        self.delete_goal_btn.clicked.connect(self.delete_goal)
        
        action_layout.addWidget(self.edit_goal_btn)
        action_layout.addWidget(self.update_progress_btn)
        action_layout.addWidget(self.delete_goal_btn)
        
        right_layout.addWidget(action_panel)
        
        # Goal details section with card-like design
        details_card = QGroupBox("Goal Details")
        details_card.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #e1e4e8;
                border-radius: 5px;
                margin-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel { padding: 3px 0; }
        """)
        
        goal_form = QFormLayout()
        goal_form.setLabelAlignment(Qt.AlignRight)
        goal_form.setSpacing(10)
        
        # Goal name with larger display
        self.goal_name_label = QLabel("Select a goal from the list")
        self.goal_name_label.setStyleSheet("font-weight: bold; font-size: 16pt; color: #212529; padding: 5px 0;")
        self.goal_name_label.setWordWrap(True)
        self.goal_name_label.setAlignment(Qt.AlignCenter)
        goal_form.addRow(self.goal_name_label)
        
        # Modern separator under the name
        name_separator = QFrame()
        name_separator.setFrameShape(QFrame.HLine)
        name_separator.setFrameShadow(QFrame.Sunken)
        name_separator.setStyleSheet("background-color: #e9ecef; min-height: 1px; margin: 5px 0 15px 0;")
        goal_form.addRow(name_separator)
        
        # Progress bar with more modern design
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: #f8f9fa;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        self.progress_label = QLabel("0%")
        self.progress_label.setStyleSheet("font-weight: bold; color: #28a745;")
        
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        goal_form.addRow("<b>Progress:</b>", progress_layout)
        
        # Goal details with better formatting
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
        self.description_label.setStyleSheet("font-style: italic; color: #6c757d;")
        
        # Apply styling to all detail labels
        detail_label_style = "color: #495057; font-weight: normal;"
        for label in [self.current_amount_label, self.target_amount_label, self.remaining_amount_label,
                    self.days_remaining_label, self.monthly_needed_label, self.created_date_label,
                    self.target_date_label, self.category_label, self.priority_label, self.feasibility_label]:
            label.setStyleSheet(detail_label_style)
        
        goal_form.addRow("<b>Current Amount:</b>", self.current_amount_label)
        goal_form.addRow("<b>Target Amount:</b>", self.target_amount_label)
        goal_form.addRow("<b>Remaining:</b>", self.remaining_amount_label)
        goal_form.addRow("<b>Days Left:</b>", self.days_remaining_label)
        goal_form.addRow("<b>Monthly Contribution:</b>", self.monthly_needed_label)
        goal_form.addRow("<b>Created:</b>", self.created_date_label)
        goal_form.addRow("<b>Target Date:</b>", self.target_date_label)
        goal_form.addRow("<b>Category:</b>", self.category_label)
        goal_form.addRow("<b>Priority:</b>", self.priority_label)
        goal_form.addRow("<b>Feasibility:</b>", self.feasibility_label)
        
        # Description separator
        desc_separator = QFrame()
        desc_separator.setFrameShape(QFrame.HLine)
        desc_separator.setFrameShadow(QFrame.Sunken)
        desc_separator.setStyleSheet("background-color: #e9ecef; min-height: 1px; margin: 10px 0;")
        goal_form.addRow(desc_separator)
        
        goal_form.addRow("<b>Description:</b>", self.description_label)
        
        details_card.setLayout(goal_form)
        right_layout.addWidget(details_card)
        
        # Add the right panel to the content area
        content_area.addWidget(right_panel)
        
        # Set default splitter sizes
        content_area.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        main_layout.addWidget(content_area)
        
        # Modern summary section with statistics cards
        summary_container = QWidget()
        summary_container.setStyleSheet("""
            QWidget { 
                background-color: #f8f9fa; 
                border: 1px solid #e1e4e8;
                border-radius: 5px;
                padding: 5px;
                margin-top: 10px;
            }
            QLabel { padding: 3px; }
        """)
        summary_layout = QHBoxLayout(summary_container)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        summary_layout.setSpacing(15)
        
        # Create stat cards with modern styling
        stats = [
            {"name": "total_goals", "title": "Total Goals", "value": "0", "color": "#007bff"},
            {"name": "completed_goals", "title": "Completed", "value": "0", "color": "#28a745"},
            {"name": "avg_progress", "title": "Avg Progress", "value": "0%", "color": "#17a2b8"},
            {"name": "total_target", "title": "Total Target", "value": "$0.00", "color": "#6f42c1"},
            {"name": "total_saved", "title": "Total Saved", "value": "$0.00", "color": "#fd7e14"}
        ]
        
        self.stat_labels = {}
        
        for stat in stats:
            # Create card widget
            card = QGroupBox(stat["title"])
            card.setStyleSheet(f"""
                QGroupBox {{ 
                    background-color: white; 
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    border-left: 4px solid {stat['color']};
                    font-weight: bold;
                    margin-top: 12px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: {stat['color']};
                }}
            """)
            
            # Card layout
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 15, 10, 10)
            
            # Value label
            value_label = QLabel(stat["value"])
            value_label.setStyleSheet(f"""
                font-size: 16pt; 
                font-weight: bold;
                color: #212529;
                qproperty-alignment: AlignCenter;
            """)
            card_layout.addWidget(value_label)
            
            # Store reference to label for updates
            self.stat_labels[stat["name"]] = value_label
            
            # Add card to summary layout
            summary_layout.addWidget(card)
        
        # Set references to specific labels for use in update_summary_stats
        self.total_goals_label = self.stat_labels["total_goals"]
        self.completed_goals_label = self.stat_labels["completed_goals"]
        self.avg_progress_label = self.stat_labels["avg_progress"]
        self.total_goal_amount_label = self.stat_labels["total_target"]
        self.total_current_label = self.stat_labels["total_saved"]
        
        main_layout.addWidget(summary_container)
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def refresh_data(self):
        """Refresh the goals data from the database"""
        try:
            # Clear the table
            self.goals_table.setRowCount(0)
            
            # Ensure goal tracker is initialized
            if not hasattr(self, 'goal_tracker') or self.goal_tracker is None:
                print("Goal tracker not initialized, trying to recreate it")
                self.goal_tracker = GoalTracker(self.budget_manager.db, self.budget_manager)
                
            # Get all goals for the user
            print(f"Attempting to fetch goals for user {self.user_id}")
            goals = self.goal_tracker.get_goals_by_user(self.user_id)
            print(f"Retrieved {len(goals) if goals else 0} goals")
            
            if not goals:
                # No goals found, show a user-friendly message
                print("No goals found for user")
                self.update_summary_stats()
                self.clear_details_panel()
                self.goals_table.setRowCount(1)
                info_item = QTableWidgetItem("No financial goals found. Click 'Add New Goal' to create your first goal.")
                info_item.setTextAlignment(Qt.AlignCenter)
                self.goals_table.setItem(0, 1, info_item)
                # Merge cells to make the message span multiple columns
                self.goals_table.setSpan(0, 1, 1, self.goals_table.columnCount() - 1)
                return
                
            # Set row count
            self.goals_table.setRowCount(len(goals))
            
            # Populate table
            for row, goal in enumerate(goals):
                try:
                    # Name - store goal ID as a hidden column in the table
                    # Create a custom QTableWidgetItem to store the goal ID
                    goal_id_item = QTableWidgetItem(str(goal.id))
                    self.goals_table.setItem(row, 0, goal_id_item)
                    
                    # Name item is now in column 1
                    name_item = QTableWidgetItem(str(goal.name) if goal.name else "Unnamed Goal")
                    self.goals_table.setItem(row, 1, name_item)
                    
                    # Target amount
                    target_item = QTableWidgetItem(f"${goal.target_amount:.2f}")
                    target_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.goals_table.setItem(row, 2, target_item)
                    
                    # Current amount
                    current_item = QTableWidgetItem(f"${goal.current_amount:.2f}")
                    current_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.goals_table.setItem(row, 3, current_item)
                    
                    # Progress
                    progress = goal.progress_percentage
                    progress_item = QTableWidgetItem(f"{progress:.1f}%")
                    progress_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    # Color code based on progress
                    if progress >= 100:
                        # Completed
                        progress_item.setForeground(QColor(0, 128, 0))  # Green
                    elif progress >= 75:
                        # Almost there
                        progress_item.setForeground(QColor(0, 128, 128))  # Teal
                    elif progress >= 50:
                        # Halfway
                        progress_item.setForeground(QColor(0, 0, 255))  # Blue
                    elif progress >= 25:
                        # Started
                        progress_item.setForeground(QColor(255, 140, 0))  # Orange
                    else:
                        # Just beginning
                        progress_item.setForeground(QColor(255, 0, 0))  # Red
                        
                    self.goals_table.setItem(row, 4, progress_item)
                    
                    # Target date
                    try:
                        target_date_str = goal.target_date.strftime("%Y-%m-%d") if goal.target_date else "Not set"
                    except (AttributeError, ValueError):
                        target_date_str = "Invalid date"
                        
                    target_date_item = QTableWidgetItem(target_date_str)
                    
                    # Color code based on days remaining
                    days_left = getattr(goal, 'days_remaining', 0)
                    if days_left <= 30:
                        # Less than a month
                        target_date_item.setBackground(QColor(255, 200, 200))  # Light red
                    elif days_left <= 90:
                        # Less than 3 months
                        target_date_item.setBackground(QColor(255, 255, 200))  # Light yellow
                    
                    self.goals_table.setItem(row, 5, target_date_item)
                    
                    # Priority
                    priority = getattr(goal, 'priority', "Medium")
                    priority_item = QTableWidgetItem(str(priority))
                    
                    # Color code based on priority
                    if priority.lower() == "high":
                        priority_item.setBackground(QColor(255, 200, 200))  # Light red
                    elif priority.lower() == "medium":
                        priority_item.setBackground(QColor(255, 255, 200))  # Light yellow
                    else:  # Low priority
                        priority_item.setBackground(QColor(200, 255, 200))  # Light green
                        
                    self.goals_table.setItem(row, 6, priority_item)
                    
                    # Add action buttons directly to the table
                    # Edit button
                    edit_btn = QPushButton("Edit")
                    # Use a fixed goal_id variable to avoid late binding issues in lambda
                    goal_id_for_edit = goal.id
                    edit_btn.clicked.connect(lambda checked, gid=goal_id_for_edit: self.direct_edit_goal(gid))
                    self.goals_table.setCellWidget(row, 7, edit_btn)
                    
                    # Update button
                    update_btn = QPushButton("Update")
                    goal_id_for_update = goal.id
                    update_btn.clicked.connect(lambda checked, gid=goal_id_for_update: self.direct_update_progress(gid))
                    self.goals_table.setCellWidget(row, 8, update_btn)
                    
                    # Delete button
                    delete_btn = QPushButton("Delete")
                    goal_id_for_delete = goal.id
                    delete_btn.clicked.connect(lambda checked, gid=goal_id_for_delete: self.direct_delete_goal(gid))
                    delete_btn.setStyleSheet("background-color: #ffcccc;")
                    self.goals_table.setCellWidget(row, 9, delete_btn)
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
    
    def show_goals_context_menu(self, position):
        """Show context menu for the goals table"""
        # Get the row under the mouse
        row = self.goals_table.rowAt(position.y())
        if row < 0:
            return  # No row under the mouse
            
        # Get the goal ID from the ID column
        id_item = self.goals_table.item(row, 0)
        if not id_item:
            return  # No valid item
            
        try:
            goal_id = int(id_item.text())
            if not goal_id:
                return  # Invalid ID
        except (ValueError, TypeError):
            return  # Not a valid integer
            
        # Create context menu
        context_menu = QMenu(self)
        
        # Add actions
        edit_action = context_menu.addAction("Edit Goal")
        update_action = context_menu.addAction("Update Progress")
        context_menu.addSeparator()
        delete_action = context_menu.addAction("Delete Goal")
        
        # Set delete action style
        delete_action_font = delete_action.font()
        delete_action_font.setBold(True)
        delete_action.setFont(delete_action_font)
        
        # Show menu and get selected action
        action = context_menu.exec_(self.goals_table.mapToGlobal(position))
        
        # Process selected action
        if action == edit_action:
            self.context_edit_goal(goal_id)
        elif action == update_action:
            self.context_update_progress(goal_id)
        elif action == delete_action:
            self.context_delete_goal(goal_id)
    
    def context_edit_goal(self, goal_id):
        """Edit a goal from the context menu"""
        print(f"Context menu - editing goal: {goal_id}")
        
        # Get the goal data directly from the database
        try:
            # Create a fresh session
            session = self.goal_tracker.db.get_session()
            goal = session.query(self.goal_tracker.db.FinancialGoal).filter_by(id=goal_id).first()
            
            if not goal:
                QMessageBox.information(self, "Goal Not Found", "The selected goal could not be found. It may have been deleted or the database connection failed.")
                return
                
            # Create a fresh dialog with the goal data
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Edit Goal: {goal.name}")
            dialog.setMinimumWidth(400)
            
            layout = QFormLayout(dialog)
            
            # Goal name
            name_edit = QLineEdit()
            name_edit.setText(goal.name)
            layout.addRow("Name:", name_edit)
            
            # Target amount
            target_amount_spin = QDoubleSpinBox()
            target_amount_spin.setRange(goal.current_amount, 1000000)
            target_amount_spin.setDecimals(2)
            target_amount_spin.setSingleStep(100)
            target_amount_spin.setValue(goal.target_amount)
            target_amount_spin.setPrefix("$")
            layout.addRow("Target Amount:", target_amount_spin)
            
            # Target date
            target_date_edit = QDateEdit()
            target_date_edit.setCalendarPopup(True)
            today = QDate.currentDate()
            goal_date = QDate(goal.target_date.year, goal.target_date.month, goal.target_date.day)
            target_date_edit.setDate(goal_date)
            target_date_edit.setMinimumDate(today)
            layout.addRow("Target Date:", target_date_edit)
            
            # Category
            category_combo = QComboBox()
            default_categories = ["Savings", "Emergency Fund", "Home", "Car", "Education", 
                                "Vacation", "Retirement", "Electronics", "Other"]
            for category in default_categories:
                category_combo.addItem(category)
            
            # Set current category if it exists in the list, otherwise add it
            index = category_combo.findText(goal.category)
            if index >= 0:
                category_combo.setCurrentIndex(index)
            else:
                category_combo.addItem(goal.category)
                category_combo.setCurrentText(goal.category)
            
            layout.addRow("Category:", category_combo)
            
            # Priority
            priority_combo = QComboBox()
            priorities = ["High", "Medium", "Low"]
            for priority in priorities:
                priority_combo.addItem(priority)
            priority_combo.setCurrentText(goal.priority)
            layout.addRow("Priority:", priority_combo)
            
            # Description
            description_edit = QLineEdit()
            description_edit.setText(goal.description if goal.description else "")
            layout.addRow("Description:", description_edit)
            
            # Buttons
            btn_layout = QHBoxLayout()
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            save_btn = QPushButton("Save Changes")
            save_btn.setDefault(True)
            
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(save_btn)
            
            layout.addRow("", btn_layout)
            
            # Connect save button after layout is complete
            save_btn.clicked.connect(lambda: self.save_edited_goal(dialog, goal_id, name_edit, description_edit, target_amount_spin, target_date_edit, category_combo, priority_combo))
            
            # Show the dialog
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while editing the goal: {str(e)}")
            print(f"Exception in context_edit_goal: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if 'session' in locals():
                session.close()
    
    def save_edited_goal(self, dialog, goal_id, name_edit, description_edit, target_amount_spin, target_date_edit, category_combo, priority_combo):
        """Save the edited goal data"""
        try:
            # Validate inputs
            if not name_edit.text().strip():
                QMessageBox.warning(dialog, "Invalid Input", "Goal name is required.")
                return
                
            # Get data from the form
            updates = {
                'name': name_edit.text(),
                'description': description_edit.text(),
                'target_amount': target_amount_spin.value(),
                'target_date': target_date_edit.date().toPyDate(),
                'category': category_combo.currentText(),
                'priority': priority_combo.currentText()
            }
            
            print(f"Saving updates to goal {goal_id}: {updates}")
            
            # Update directly using SQLAlchemy session
            session = self.goal_tracker.db.get_session()
            try:
                goal = session.query(self.goal_tracker.db.FinancialGoal).filter_by(id=goal_id).first()
                if not goal:
                    QMessageBox.warning(dialog, "Error", "Goal not found")
                    return
                    
                # Update fields
                for field, value in updates.items():
                    setattr(goal, field, value)
                    
                session.commit()
                QMessageBox.information(dialog, "Success", "Goal updated successfully!")
                dialog.accept()
                
                # Refresh the data
                self.refresh_data()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(dialog, "Error", f"Failed to update goal: {str(e)}")
            finally:
                session.close()
                
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"An error occurred: {str(e)}")
            print(f"Exception in save_edited_goal: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def context_update_progress(self, goal_id):
        """Update progress on a goal from the context menu"""
        print(f"Context menu - updating progress for goal: {goal_id}")
        
        try:
            # Create a fresh session
            session = self.goal_tracker.db.get_session()
            goal = session.query(self.goal_tracker.db.FinancialGoal).filter_by(id=goal_id).first()
            
            if not goal:
                QMessageBox.information(self, "Goal Not Found", "The selected goal could not be found. It may have been deleted or the database connection failed.")
                return
                
            # Create a dialog for updating progress
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Update Progress: {goal.name}")
            dialog.setMinimumWidth(350)
            
            layout = QFormLayout(dialog)
            
            # Header
            header = QLabel(f"<h3>{goal.name}</h3>")
            layout.addRow(header)
            
            # Current amount
            current_amount = QLabel(f"${goal.current_amount:.2f}")
            layout.addRow("Current Amount:", current_amount)
            
            # Target amount
            target_amount = QLabel(f"${goal.target_amount:.2f}")
            layout.addRow("Target Amount:", target_amount)
            
            # Remaining amount
            remaining = goal.target_amount - goal.current_amount
            remaining_amount = QLabel(f"${remaining:.2f}")
            layout.addRow("Remaining:", remaining_amount)
            
            # Amount to add
            amount_spin = QDoubleSpinBox()
            amount_spin.setRange(0, remaining)
            amount_spin.setDecimals(2)
            amount_spin.setSingleStep(50)
            amount_spin.setValue(min(100, remaining))
            amount_spin.setPrefix("$")
            layout.addRow("Add Amount:", amount_spin)
            
            # Buttons
            btn_layout = QHBoxLayout()
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            update_btn = QPushButton("Update Progress")
            update_btn.setDefault(True)
            
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(update_btn)
            
            layout.addRow("", btn_layout)
            
            # Connect update button
            update_btn.clicked.connect(lambda: self.save_progress_update(dialog, goal_id, amount_spin.value()))
            
            # Show the dialog
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while updating progress: {str(e)}")
            print(f"Exception in context_update_progress: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if 'session' in locals():
                session.close()
    
    def save_progress_update(self, dialog, goal_id, amount):
        """Save the progress update"""
        try:
            if amount <= 0:
                QMessageBox.warning(dialog, "Invalid Input", "Amount must be greater than zero.")
                return
                
            print(f"Updating progress for goal {goal_id} with amount: ${amount}")
            
            # Update directly using SQLAlchemy session
            session = self.goal_tracker.db.get_session()
            try:
                goal = session.query(self.goal_tracker.db.FinancialGoal).filter_by(id=goal_id).first()
                if not goal:
                    QMessageBox.warning(dialog, "Error", "Goal not found")
                    return
                    
                # Update current amount
                goal.current_amount += amount
                
                # Check if goal is completed
                if goal.current_amount >= goal.target_amount:
                    goal.is_completed = True
                    
                session.commit()
                QMessageBox.information(dialog, "Success", "Progress updated successfully!")
                dialog.accept()
                
                # Refresh the data
                self.refresh_data()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(dialog, "Error", f"Failed to update progress: {str(e)}")
            finally:
                session.close()
                
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"An error occurred: {str(e)}")
            print(f"Exception in save_progress_update: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def context_delete_goal(self, goal_id):
        """Delete a goal from the context menu"""
        print(f"Context menu - deleting goal: {goal_id}")
        
        try:
            # Get the goal name for confirmation
            session = self.goal_tracker.db.get_session()
            goal = session.query(self.goal_tracker.db.FinancialGoal).filter_by(id=goal_id).first()
            
            if not goal:
                QMessageBox.information(self, "Goal Not Found", "The selected goal could not be found. It may have been deleted or the database connection failed.")
                return
                
            goal_name = goal.name
            session.close()
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 'Delete Goal',
                f'Are you sure you want to delete the goal "{goal_name}"?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Delete directly using SQLAlchemy session
                session = self.goal_tracker.db.get_session()
                try:
                    goal = session.query(self.goal_tracker.db.FinancialGoal).filter_by(id=goal_id).first()
                    if not goal:
                        QMessageBox.warning(self, "Error", "Goal not found")
                        return
                        
                    session.delete(goal)
                    session.commit()
                    QMessageBox.information(self, "Success", "Goal deleted successfully!")
                    
                    # Refresh the data
                    self.refresh_data()
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(self, "Error", f"Failed to delete goal: {str(e)}")
                finally:
                    session.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while deleting the goal: {str(e)}")
            print(f"Exception in context_delete_goal: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def select_goal_by_id(self, goal_id):
        """Select a goal in the table by its ID"""
        try:
            print(f"[DEBUG] Attempting to select goal by ID: {goal_id}")
            # Find the goal in the table
            for row in range(self.goals_table.rowCount()):
                id_item = self.goals_table.item(row, 0)
                if id_item and int(id_item.text()) == goal_id:
                    # Select the row
                    print(f"[DEBUG] Found goal ID {goal_id} at row {row}, selecting")
                    self.goals_table.selectRow(row)
                    # Update goal details display
                    self.goal_selected(row, 0)
                    return True
            
            print(f"[DEBUG] Could not find goal with ID {goal_id} in the table")
            return False
        except Exception as e:
            print(f"[DEBUG] Error in select_goal_by_id: {str(e)}")
            return False
    
    def goal_selected(self, row, column):
        """Handle selection of a goal in the table with highlighting"""
        try:
            if row < 0 or column < 0 or row >= self.goals_table.rowCount():
                print(f"Invalid row or column: {row}, {column}")
                return
            
            # Clear previous selection highlight - reset row colors
            if self.selected_row >= 0 and self.selected_row < self.goals_table.rowCount():
                for col in range(self.goals_table.columnCount()):
                    if col == 0:  # Skip hidden ID column
                        continue
                    item = self.goals_table.item(self.selected_row, col)
                    if item:
                        # Reset to default background (keep any existing foreground color)
                        fore_color = item.foreground().color()
                        item.setBackground(QBrush())  # Default background
                        item.setForeground(fore_color)  # Keep existing text color
                        
            # Store the new selected row
            self.selected_row = row
            
            # Get goal ID
            id_item = self.goals_table.item(row, 0)
            if not id_item:
                print(f"No ID item found at row {row}, column 0")
                return
                
            try:
                goal_id = int(id_item.text())
                self.selected_goal_id = goal_id
                print(f"Selected goal ID: {goal_id}")
            except (ValueError, TypeError) as e:
                print(f"Invalid goal ID: {id_item.text() if id_item else 'None'}, Error: {e}")
                return
            
            # Apply highlight to the selected row - make it visually stand out
            highlight_color = QColor("#e3f2fd")  # Light blue background
            for col in range(self.goals_table.columnCount()):
                if col == 0:  # Skip hidden ID column
                    continue
                item = self.goals_table.item(row, col)
                if item:
                    # Set the highlight background while preserving text color
                    fore_color = item.foreground().color()
                    item.setBackground(highlight_color)
                    item.setForeground(fore_color)  # Keep existing text color
                
            # Get the goal data for the selected row
            goal = self.goal_tracker.get_goal(goal_id)
            
            if not goal:
                QMessageBox.warning(self, "Data Error", "Could not find goal data.")
                return
                
            # Update the goal details panel with the selected goal
            self.goal_name_label.setText(goal.name)
            
            # Update progress bar and label
            progress = goal.progress_percentage
            self.progress_bar.setValue(int(progress))
            self.progress_label.setText(f"{progress:.1f}%")
            
            # Color code the progress bar
            if progress >= 100:
                # Completed
                self.progress_bar.setStyleSheet("""
                    QProgressBar::chunk { 
                        background-color: #28a745; 
                        border-radius: 3px;
                    }
                """)
            elif progress >= 75:
                # Almost there
                self.progress_bar.setStyleSheet("""
                    QProgressBar::chunk { 
                        background-color: #17a2b8; 
                        border-radius: 3px;
                    }
                """)
            elif progress >= 50:
                # Halfway
                self.progress_bar.setStyleSheet("""
                    QProgressBar::chunk { 
                        background-color: #007bff; 
                        border-radius: 3px;
                    }
                """)
            elif progress >= 25:
                # Started
                self.progress_bar.setStyleSheet("""
                    QProgressBar::chunk { 
                        background-color: #ffc107; 
                        border-radius: 3px;
                    }
                """)
            else:
                # Just beginning
                self.progress_bar.setStyleSheet("""
                    QProgressBar::chunk { 
                        background-color: #dc3545; 
                        border-radius: 3px;
                    }
                """)
            
            # Update amount details
            self.current_amount_label.setText(f"${goal.current_amount:.2f}")
            self.target_amount_label.setText(f"${goal.target_amount:.2f}")
            
            # Calculate remaining amount
            remaining = goal.target_amount - goal.current_amount
            self.remaining_amount_label.setText(f"${remaining:.2f}")
            
            # Days remaining
            days_remaining = goal.days_remaining
            if days_remaining is not None and days_remaining > 0:
                self.days_remaining_label.setText(f"{days_remaining} days")
            elif days_remaining == 0:
                self.days_remaining_label.setText("Due today!")
            else:
                self.days_remaining_label.setText("Overdue")
            
            # Monthly contribution needed
            monthly_needed = goal.monthly_contribution_needed if hasattr(goal, 'monthly_contribution_needed') else 0
            self.monthly_needed_label.setText(f"${monthly_needed:.2f}/month")
            
            # Created date
            created_date = goal.created_date.strftime("%Y-%m-%d") if goal.created_date else "Unknown"
            self.created_date_label.setText(created_date)
            
            # Target date
            target_date = goal.target_date.strftime("%Y-%m-%d") if goal.target_date else "Not set"
            self.target_date_label.setText(target_date)
            
            # Category and priority
            self.category_label.setText(goal.category if goal.category else "General")
            self.priority_label.setText(goal.priority if goal.priority else "Medium")
            
            # Feasibility
            if not hasattr(goal, 'monthly_contribution_needed') or not hasattr(goal, 'days_remaining'):
                self.feasibility_label.setText("N/A")
            elif goal.monthly_contribution_needed <= 0 or goal.is_completed:
                self.feasibility_label.setText("Completed")
                self.feasibility_label.setStyleSheet("color: #28a745; font-weight: bold;")  # Green
            elif goal.monthly_contribution_needed > (goal.target_amount * 0.5):
                self.feasibility_label.setText("Challenging")
                self.feasibility_label.setStyleSheet("color: #dc3545; font-weight: bold;")  # Red
            elif goal.monthly_contribution_needed > (goal.target_amount * 0.2):
                self.feasibility_label.setText("Moderate")
                self.feasibility_label.setStyleSheet("color: #fd7e14; font-weight: bold;")  # Orange
            else:
                self.feasibility_label.setText("Feasible")
                self.feasibility_label.setStyleSheet("color: #28a745; font-weight: bold;")  # Green
            
            # Description
            self.description_label.setText(goal.description if goal.description else "No description provided.")
            
            # Enable buttons in the dedicated action button area
            self.edit_goal_btn.setEnabled(True)
            self.update_progress_btn.setEnabled(True)
            self.delete_goal_btn.setEnabled(True)
            
            print(f"Successfully updated details panel for goal: {goal.name}")
            
        except Exception as e:
            print(f"Error in goal selection: {e}")
            # Keep the UI functioning
            self.clear_details_panel()
    
    def clear_details_panel(self):
        """Clear and reset the goal details panel"""
        # Clear all labels in the details panel with placeholder text
        self.goal_name_label.setText("Select a goal")
        self.progress_bar.setValue(0)
        self.progress_label.setText("0.0%")
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk { 
                background-color: #dee2e6;
                border-radius: 3px;
            }
        """)
        
        # Reset all data fields
        self.current_amount_label.setText("$0.00")
        self.target_amount_label.setText("$0.00")
        self.remaining_amount_label.setText("$0.00")
        self.days_remaining_label.setText("0 days")
        self.monthly_needed_label.setText("$0.00/month")
        self.created_date_label.setText("Not set")
        self.target_date_label.setText("Not set")
        self.category_label.setText("None")
        self.priority_label.setText("None")
        self.feasibility_label.setText("N/A")
        self.feasibility_label.setStyleSheet("color: #6c757d;")  # Gray
        self.description_label.setText("No description provided.")
        
        # Disable action buttons
        self.edit_goal_btn.setEnabled(False)
        self.update_progress_btn.setEnabled(False)
        self.delete_goal_btn.setEnabled(False)
        
        # Clear selection tracking
        self.selected_goal_id = None
        self.selected_row = -1
    
    def update_summary_stats(self):
        """Update the summary statistics for goals in modern UI cards"""
        stats = self.goal_tracker.get_goal_summary_stats(self.user_id)
        
        # Update our modern stats cards with just the values (no labels since they're in the card titles)
        self.total_goals_label.setText(f"{stats['total_goals']}")
        self.completed_goals_label.setText(f"{stats['completed_goals']}")
        self.avg_progress_label.setText(f"{stats['average_progress']:.1f}%")
        self.total_goal_amount_label.setText(f"${stats['total_target_amount']:.2f}")
        self.total_current_label.setText(f"${stats['total_current_amount']:.2f}")
        
        # Also update category filter options
        self.update_category_filter_options()
        
    def update_category_filter_options(self, goals=None):
        """Update the category filter dropdown with available categories"""
        try:
            # Save current selection if any
            current_category = self.category_filter_combo.currentText() if self.category_filter_combo.currentIndex() > 0 else None
            
            # Disconnect signal temporarily to avoid triggering filter while updating
            try:
                self.category_filter_combo.currentIndexChanged.disconnect()
            except Exception:
                pass  # It's okay if it wasn't connected
            
            # Clear and add the default "All Categories" option
            self.category_filter_combo.clear()
            self.category_filter_combo.addItem("All Categories")
            
            if not goals:
                # Get fresh list of goals if not provided
                if not hasattr(self, 'goal_tracker') or self.goal_tracker is None:
                    return
                goals = self.goal_tracker.get_goals_by_user(self.user_id)
                
            # Extract unique categories
            categories = set()
            for goal in goals:
                if goal.category and goal.category.strip():
                    categories.add(goal.category)
            
            # Add categories to combo box
            for category in sorted(categories):
                self.category_filter_combo.addItem(category)
            
            # Restore previous selection if it exists
            if current_category:
                index = self.category_filter_combo.findText(current_category)
                if index >= 0:
                    self.category_filter_combo.setCurrentIndex(index)
            
            # Reconnect signal
            self.category_filter_combo.currentIndexChanged.connect(self.filter_by_category)
            
        except Exception as e:
            print(f"Error updating category filter options: {e}")
            
    def filter_by_category(self):
        """Filter the goals table by the selected category"""
        try:
            selected_category = self.category_filter_combo.currentText()
            
            # If "All Categories" is selected, refresh with all goals
            if selected_category == "All Categories" or self.category_filter_combo.currentIndex() == 0:
                # Just refresh all data
                self.refresh_data()
                return
            
            # Otherwise filter by the selected category
            if not hasattr(self, 'goal_tracker') or self.goal_tracker is None:
                print("Goal tracker not initialized, trying to recreate it")
                self.goal_tracker = GoalTracker(self.budget_manager.db, self.budget_manager)
                
            # Get filtered goals
            goals = self.goal_tracker.get_goals_by_user(self.user_id, category=selected_category)
            
            # Clear current table
            self.goals_table.setRowCount(0)
            
            if not goals:
                # No goals found in this category
                self.goals_table.setRowCount(1)
                info_item = QTableWidgetItem(f"No goals found in category: {selected_category}")
                info_item.setTextAlignment(Qt.AlignCenter)
                self.goals_table.setItem(0, 1, info_item)
                self.goals_table.setSpan(0, 1, 1, self.goals_table.columnCount() - 1)
                
                # Update summary stats
                self.update_summary_stats()
                
                # Clear details panel since no goals are displayed
                self.clear_details_panel()
                return
                
            # Populate table with filtered goals
            self.goals_table.setRowCount(len(goals))
            for row, goal in enumerate(goals):
                try:
                    # Populate row similar to refresh_data method
                    goal_id_item = QTableWidgetItem(str(goal.id))
                    self.goals_table.setItem(row, 0, goal_id_item)
                    
                    name_item = QTableWidgetItem(str(goal.name) if goal.name else "Unnamed Goal")
                    self.goals_table.setItem(row, 1, name_item)
                    
                    target_item = QTableWidgetItem(f"${goal.target_amount:.2f}")
                    target_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.goals_table.setItem(row, 2, target_item)
                    
                    current_item = QTableWidgetItem(f"${goal.current_amount:.2f}")
                    current_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.goals_table.setItem(row, 3, current_item)
                    
                    progress = goal.progress_percentage
                    progress_item = QTableWidgetItem(f"{progress:.1f}%")
                    progress_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    # Color coding based on progress
                    if progress >= 100:
                        # Completed
                        progress_item.setForeground(QColor(0, 128, 0))  # Green
                    elif progress >= 75:
                        # Almost there
                        progress_item.setForeground(QColor(0, 128, 128))  # Teal
                    elif progress >= 50:
                        # Halfway
                        progress_item.setForeground(QColor(0, 0, 255))  # Blue
                    elif progress >= 25:
                        # Started
                        progress_item.setForeground(QColor(255, 140, 0))  # Orange
                    else:
                        # Just beginning
                        progress_item.setForeground(QColor(255, 0, 0))  # Red
                    
                    self.goals_table.setItem(row, 4, progress_item)
                    
                    try:
                        target_date_str = goal.target_date.strftime("%Y-%m-%d") if goal.target_date else "Not set"
                    except (AttributeError, ValueError):
                        target_date_str = "Invalid date"
                        
                    target_date_item = QTableWidgetItem(target_date_str)
                    self.goals_table.setItem(row, 5, target_date_item)
                    
                    priority = getattr(goal, 'priority', "Medium")
                    priority_item = QTableWidgetItem(str(priority))
                    self.goals_table.setItem(row, 6, priority_item)
                    
                except Exception as e:
                    print(f"Error displaying filtered goal row {row}: {e}")
                    continue
                    
            # Update summary stats with filtered goals only
            self.update_summary_stats()
            
        except Exception as e:
            print(f"Error filtering by category: {e}")
            QMessageBox.warning(self, "Filter Error", f"Error filtering goals by category: {str(e)}")
            # Revert to showing all categories
            self.category_filter_combo.setCurrentIndex(0)
    
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
    
    def direct_edit_goal(self, goal_id):
        """Edit a goal directly using its ID"""
        print(f"[DEBUG] Direct edit goal: {goal_id}")
        
        try:
            # Use direct database access instead of the goal_tracker method
            session = self.goal_tracker.db.get_session()
            if not session:
                QMessageBox.warning(self, "Database Error", "Could not connect to the database.")
                print(f"[DEBUG] Failed to get database session")
                return
            
            # Query the goal directly
            goal = session.query(self.goal_tracker.db.FinancialGoal).filter_by(id=goal_id).first()
            if not goal:
                QMessageBox.information(self, "Goal Not Found", "The goal could not be found in the database.")
                print(f"[DEBUG] Could not find goal with ID {goal_id} in database")
                return
                
            # Create a detached copy for the dialog
            goal_copy = type('GoalCopy', (), {})()
            goal_copy.id = goal.id
            goal_copy.name = goal.name
            goal_copy.description = goal.description or ""
            goal_copy.target_amount = goal.target_amount
            goal_copy.current_amount = goal.current_amount
            goal_copy.created_date = goal.created_date
            goal_copy.target_date = goal.target_date
            goal_copy.category = goal.category
            goal_copy.priority = goal.priority
            goal_copy.is_completed = goal.is_completed
            
            # Calculate progress percentage
            if goal_copy.target_amount > 0:
                goal_copy.progress_percentage = (goal_copy.current_amount / goal_copy.target_amount) * 100
            else:
                goal_copy.progress_percentage = 0
            
            print(f"[DEBUG] Retrieved goal: {goal_copy.name}, Target: ${goal_copy.target_amount}, Current: ${goal_copy.current_amount}")
            
            dialog = EditGoalDialog(self, goal_copy)
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
                
                print(f"[DEBUG] Updating goal {goal_id} with values: {updates}")
                
                try:
                    # Direct database update instead of using goal_tracker method
                    # Find the goal again in the session scope
                    db_goal = session.query(self.goal_tracker.db.FinancialGoal).filter_by(id=goal_id).first()
                    if not db_goal:
                        print(f"[DEBUG] Goal {goal_id} disappeared from database during edit")
                        QMessageBox.warning(self, "Update Failed", "The goal could not be found in the database.")
                        return
                    
                    # Update goal attributes
                    for key, value in updates.items():
                        setattr(db_goal, key, value)
                    
                    # Save changes
                    session.commit()
                    print(f"[DEBUG] Successfully updated goal {goal_id} in database")
                    
                    # Refresh UI
                    self.refresh_data()
                    self.update_summary_stats()
                    # Select the goal again if it was previously selected
                    self.select_goal_by_id(goal_id)
                except Exception as ex:
                    session.rollback()
                    print(f"[DEBUG] Database error updating goal {goal_id}: {str(ex)}")
                    QMessageBox.warning(self, "Update Failed", f"Could not update the goal: {str(ex)}")
                
        except Exception as e:
            print(f"[DEBUG] Error in direct_edit_goal: {str(e)}")
            QMessageBox.warning(self, "Edit Error", f"An error occurred while editing the goal: {str(e)}")
        finally:
            if session:
                session.close()
                print(f"[DEBUG] Database session closed")
            import traceback
            traceback.print_exc()
    
    def direct_update_progress(self, goal_id):
        """Update progress on a goal directly using its ID"""
        print(f"Direct update progress: {goal_id}")
        
        try:
            # Get current goal data
            goal = self.goal_tracker.get_goal(goal_id)
            if not goal:
                QMessageBox.information(self, "Goal Not Found", "The selected goal could not be found. It may have been deleted or the database connection failed.")
                print(f"Could not find goal with ID {goal_id}")
                return
            
            print(f"Retrieved goal for progress update: {goal.name}, Target: ${goal.target_amount}, Current: ${goal.current_amount}")
                
            dialog = UpdateProgressDialog(self, goal)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Get amount from the dialog
                amount = dialog.amount_spin.value()
                print(f"Updating goal {goal_id} progress with amount: ${amount}")
                
                # Update goal progress
                success = self.goal_tracker.update_goal_progress(goal_id, amount)
                
                if success:
                    QMessageBox.information(self, "Success", "Progress updated successfully!")
                    print(f"Progress for goal {goal_id} updated successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to update progress")
                    print(f"Failed to update progress for goal {goal_id}")
                
                # Refresh data
                self.refresh_data()
        except Exception as e:
            print(f"Exception in direct_update_progress: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def direct_delete_goal(self, goal_id):
        """Delete a goal directly using its ID"""
        print(f"Direct delete goal: {goal_id}")
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 'Delete Goal',
            'Are you sure you want to delete this goal?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete the goal
            success = self.goal_tracker.delete_goal(goal_id)
            
            if success:
                QMessageBox.information(self, "Success", "Goal deleted successfully")
            else:
                print(f"[DEBUG] Failed to delete goal {goal_id}")
                QMessageBox.warning(self, "Error", "Failed to delete goal")
                
            # Refresh data
            self.refresh_data()
    
    def delete_goal(self):
        """Delete the selected financial goal"""
        print(f"[DEBUG] Delete goal button clicked")
        if not self.selected_goal_id:
            print("[DEBUG] No goal selected when Delete button was clicked")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 'Delete Goal',
            'Are you sure you want to delete this goal?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print(f"[DEBUG] Delete goal confirmed")
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
