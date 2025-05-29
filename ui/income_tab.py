from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                         QLineEdit, QDateEdit, QTableWidget, QTableWidgetItem,
                         QHeaderView, QFormLayout, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt, QDate
import datetime


class IncomeTab(QWidget):
    """Tab for managing income records"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        
        # Add Income Form
        form_layout = QFormLayout()
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount")
        form_layout.addRow("Amount ($):", self.amount_input)
        
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter source")
        form_layout.addRow("Source:", self.source_input)
        
        self.date_input = QDateEdit(calendarPopup=True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.date_input)
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Enter description (optional)")
        form_layout.addRow("Description:", self.description_input)
        
        # Add button
        add_button = QPushButton("Add Income")
        add_button.clicked.connect(self.add_income)
        
        form_section = QVBoxLayout()
        form_section.addLayout(form_layout)
        form_section.addWidget(add_button)
        
        main_layout.addLayout(form_section)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        self.filter_month = QComboBox()
        for i in range(1, 13):
            self.filter_month.addItem(datetime.date(2000, i, 1).strftime("%B"), i)
        self.filter_month.setCurrentIndex(datetime.date.today().month - 1)
        
        self.filter_year = QComboBox()
        current_year = datetime.date.today().year
        for year in range(current_year - 5, current_year + 1):
            self.filter_year.addItem(str(year), year)
        self.filter_year.setCurrentText(str(current_year))
        
        filter_button = QPushButton("Filter")
        filter_button.clicked.connect(self.refresh_data)
        
        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.filter_month)
        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.filter_year)
        filter_layout.addWidget(filter_button)
        filter_layout.addStretch()
        
        main_layout.addLayout(filter_layout)
        
        # Income table
        self.income_table = QTableWidget(0, 5)  # rows, columns
        self.income_table.setHorizontalHeaderLabels(["ID", "Date", "Source", "Amount", "Description"])
        self.income_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.income_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table read-only
        
        main_layout.addWidget(self.income_table)
        
        self.setLayout(main_layout)
        self.refresh_data()
    
    def add_income(self):
        """Add a new income record"""
        try:
            # Get form values
            amount_text = self.amount_input.text()
            source = self.source_input.text()
            date = self.date_input.date().toPyDate()
            description = self.description_input.text()
            
            # Validate input
            if not amount_text or not source:
                QMessageBox.warning(self, "Input Error", "Amount and source are required.")
                return
            
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Amount must be a positive number.")
                return
            
            # Add income to database
            income_id = self.budget_manager.add_income(
                self.user_id, amount, source, date, description
            )
            
            if income_id:
                # Clear form
                self.amount_input.clear()
                self.source_input.clear()
                self.date_input.setDate(QDate.currentDate())
                self.description_input.clear()
                
                # Refresh table
                self.refresh_data()
                
                QMessageBox.information(self, "Success", "Income added successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to add income.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def refresh_data(self):
        """Refresh the income table with latest data"""
        try:
            # Get filter values
            month = self.filter_month.currentData()
            year = self.filter_year.currentData()
            
            # Calculate date range for the selected month
            import calendar
            start_date = datetime.date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime.date(year, month, last_day)
            
            # Get income data
            incomes = self.budget_manager.db.get_incomes_by_date_range(
                self.user_id, start_date, end_date
            )
            
            # Update table
            self.income_table.setRowCount(0)
            for income in incomes:
                row_position = self.income_table.rowCount()
                self.income_table.insertRow(row_position)
                
                # Set cell values
                self.income_table.setItem(row_position, 0, QTableWidgetItem(str(income.id)))
                self.income_table.setItem(row_position, 1, QTableWidgetItem(income.date.strftime("%Y-%m-%d")))
                self.income_table.setItem(row_position, 2, QTableWidgetItem(income.source))
                self.income_table.setItem(row_position, 3, QTableWidgetItem(f"${income.amount:.2f}"))
                self.income_table.setItem(row_position, 4, QTableWidgetItem(income.description or ""))
                
            # Update summary
            total_income = self.budget_manager.get_total_income(self.user_id, start_date, end_date)
            self.income_table.setRowCount(self.income_table.rowCount() + 1)
            last_row = self.income_table.rowCount() - 1
            self.income_table.setItem(last_row, 2, QTableWidgetItem("Total:"))
            total_item = QTableWidgetItem(f"${total_income:.2f}")
            total_item.setFont(total_item.font())
            self.income_table.setItem(last_row, 3, total_item)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {str(e)}")
