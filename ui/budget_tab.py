from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                         QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, 
                         QFormLayout, QMessageBox, QComboBox, QProgressBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import datetime
import calendar


class BudgetTab(QWidget):
    """Tab for setting and managing budget goals"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        
        # Budget Form
        form_layout = QFormLayout()
        
        # Category dropdown
        self.category_combo = QComboBox()
        self.load_categories()
        form_layout.addRow("Category:", self.category_combo)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter budget amount")
        form_layout.addRow("Budget Amount ($):", self.amount_input)
        
        # Month and Year selection
        self.month_combo = QComboBox()
        for i in range(1, 13):
            self.month_combo.addItem(datetime.date(2000, i, 1).strftime("%B"), i)
        self.month_combo.setCurrentIndex(datetime.date.today().month - 1)
        
        self.year_combo = QComboBox()
        current_year = datetime.date.today().year
        for year in range(current_year - 1, current_year + 2):
            self.year_combo.addItem(str(year), year)
        self.year_combo.setCurrentText(str(current_year))
        
        month_year_layout = QHBoxLayout()
        month_year_layout.addWidget(self.month_combo)
        month_year_layout.addWidget(self.year_combo)
        
        form_layout.addRow("Month/Year:", month_year_layout)
        
        # Set Budget button
        set_budget_button = QPushButton("Set Budget")
        set_budget_button.clicked.connect(self.set_budget)
        
        # Form section
        form_section = QVBoxLayout()
        form_section.addLayout(form_layout)
        form_section.addWidget(set_budget_button)
        
        main_layout.addLayout(form_section)
        
        # Filter controls for viewing budgets
        filter_layout = QHBoxLayout()
        
        self.filter_month = QComboBox()
        for i in range(1, 13):
            self.filter_month.addItem(datetime.date(2000, i, 1).strftime("%B"), i)
        self.filter_month.setCurrentIndex(datetime.date.today().month - 1)
        
        self.filter_year = QComboBox()
        for year in range(current_year - 1, current_year + 2):
            self.filter_year.addItem(str(year), year)
        self.filter_year.setCurrentText(str(current_year))
        
        filter_button = QPushButton("View Budgets")
        filter_button.clicked.connect(self.refresh_data)
        
        filter_layout.addWidget(QLabel("View budgets for:"))
        filter_layout.addWidget(self.filter_month)
        filter_layout.addWidget(self.filter_year)
        filter_layout.addWidget(filter_button)
        filter_layout.addStretch()
        
        main_layout.addLayout(filter_layout)
        
        # Budget table
        self.budget_table = QTableWidget(0, 5)  # rows, columns
        self.budget_table.setHorizontalHeaderLabels(["Category", "Budget", "Spent", "Remaining", "Progress"])
        self.budget_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.budget_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table read-only
        
        main_layout.addWidget(self.budget_table)
        
        self.setLayout(main_layout)
        self.refresh_data()
    
    def load_categories(self):
        """Load expense categories into combobox"""
        self.category_combo.clear()
        
        categories = self.budget_manager.get_expense_categories()
        for category in categories:
            self.category_combo.addItem(category.name, category.id)
    
    def set_budget(self):
        """Set a budget for a category in the selected month/year"""
        try:
            # Get form values
            category_id = self.category_combo.currentData()
            amount_text = self.amount_input.text()
            month = self.month_combo.currentData()
            year = self.year_combo.currentData()
            
            # Validate input
            if not amount_text:
                QMessageBox.warning(self, "Input Error", "Budget amount is required.")
                return
            
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Budget amount must be a positive number.")
                return
            
            # Set budget in database
            budget_id = self.budget_manager.set_budget(
                self.user_id, category_id, amount, month, year
            )
            
            if budget_id:
                # Clear form
                self.amount_input.clear()
                
                # Refresh table
                self.refresh_data()
                
                QMessageBox.information(self, "Success", "Budget set successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to set budget.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def refresh_data(self):
        """Refresh the budget table with latest data"""
        try:
            # Get filter values
            month = self.filter_month.currentData()
            year = self.filter_year.currentData()
            
            # Get budget data
            budget_status = self.budget_manager.get_budget_status(self.user_id, month, year)
            
            # Update table
            self.budget_table.setRowCount(0)
            
            if not budget_status:
                self.budget_table.setRowCount(1)
                self.budget_table.setSpan(0, 0, 1, 5)
                self.budget_table.setItem(0, 0, QTableWidgetItem("No budgets set for this month."))
                return
            
            # Calculate date range for the selected month
            start_date = datetime.date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime.date(year, month, last_day)
            
            # Get total income and expense for the month
            total_income = self.budget_manager.get_total_income(self.user_id, start_date, end_date)
            total_expense = self.budget_manager.get_total_expense(self.user_id, start_date, end_date)
            
            for category, data in budget_status.items():
                row_position = self.budget_table.rowCount()
                self.budget_table.insertRow(row_position)
                
                # Create progress bar
                progress_bar = QProgressBar()
                progress_bar.setValue(int(data['percentage_used']))
                progress_bar.setFormat("%.1f%%" % data['percentage_used'])
                
                # Set color based on budget status
                if data['percentage_used'] < 75:
                    progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
                elif data['percentage_used'] < 100:
                    progress_bar.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
                else:
                    progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
                
                # Set cell values
                self.budget_table.setItem(row_position, 0, QTableWidgetItem(category))
                self.budget_table.setItem(row_position, 1, QTableWidgetItem(f"${data['budget']:.2f}"))
                self.budget_table.setItem(row_position, 2, QTableWidgetItem(f"${data['spent']:.2f}"))
                
                remaining_item = QTableWidgetItem(f"${data['remaining']:.2f}")
                if data['remaining'] < 0:
                    remaining_item.setForeground(QColor("red"))
                self.budget_table.setItem(row_position, 3, remaining_item)
                
                # Add progress bar
                self.budget_table.setCellWidget(row_position, 4, progress_bar)
            
            # Add summary row
            self.budget_table.setRowCount(self.budget_table.rowCount() + 2)
            summary_row = self.budget_table.rowCount() - 2
            income_row = self.budget_table.rowCount() - 1
            
            self.budget_table.setItem(summary_row, 0, QTableWidgetItem("Total Expenses:"))
            self.budget_table.setItem(summary_row, 1, QTableWidgetItem(f"${total_expense:.2f}"))
            
            self.budget_table.setItem(income_row, 0, QTableWidgetItem("Total Income:"))
            self.budget_table.setItem(income_row, 1, QTableWidgetItem(f"${total_income:.2f}"))
            
            savings = total_income - total_expense
            self.budget_table.setItem(income_row, 3, QTableWidgetItem("Savings:"))
            savings_item = QTableWidgetItem(f"${savings:.2f}")
            if savings < 0:
                savings_item.setForeground(QColor("red"))
            else:
                savings_item.setForeground(QColor("green"))
            self.budget_table.setItem(income_row, 4, savings_item)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {str(e)}")
