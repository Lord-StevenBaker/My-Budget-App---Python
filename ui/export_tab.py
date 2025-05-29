import os
import datetime
import calendar
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QComboBox, QDateEdit, QGroupBox, QRadioButton, QMessageBox,
                            QFileDialog, QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, QDate
from export_utils import DataExporter


class ExportTab(QWidget):
    """Tab for exporting budget data to different formats"""
    
    def __init__(self, budget_manager, user_id):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = user_id
        self.exporter = DataExporter(self.budget_manager)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Export Data")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Export your financial data to various formats for further analysis.")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 10pt; margin-bottom: 20px;")
        main_layout.addWidget(desc_label)
        
        # Export type selection
        type_group = self._create_export_type_group()
        main_layout.addWidget(type_group)
        
        # Time period selection
        period_group = self._create_time_period_group()
        main_layout.addWidget(period_group)
        
        # Format selection
        format_group = self._create_format_group()
        main_layout.addWidget(format_group)
        
        # Export button
        button_layout = QHBoxLayout()
        export_button = QPushButton("Export Data")
        export_button.setStyleSheet("font-size: 12pt; padding: 10px;")
        export_button.clicked.connect(self.export_data)
        button_layout.addStretch(1)
        button_layout.addWidget(export_button)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)
        
        # Add spacer at the bottom
        main_layout.addStretch(1)
        
        self.setLayout(main_layout)
    
    def _create_export_type_group(self):
        """Create the export type selection group"""
        group_box = QGroupBox("Select Data to Export")
        layout = QVBoxLayout()
        
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems(["Income Data", "Expense Data", "Budget Data", 
                                        "Debt Analysis", "Monthly Summary"])
        self.export_type_combo.currentTextChanged.connect(self.on_export_type_changed)
        
        layout.addWidget(self.export_type_combo)
        group_box.setLayout(layout)
        
        return group_box
    
    def _create_time_period_group(self):
        """Create time period selection group"""
        self.period_group = QGroupBox("Select Time Period")
        layout = QVBoxLayout()
        
        # Date range selection
        date_layout = QHBoxLayout()
        
        start_date_label = QLabel("Start Date:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        
        end_date_label = QLabel("End Date:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        
        date_layout.addWidget(start_date_label)
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(end_date_label)
        date_layout.addWidget(self.end_date_edit)
        
        layout.addLayout(date_layout)
        
        # Month selection for budget data
        month_layout = QHBoxLayout()
        month_label = QLabel("Month:")
        self.month_combo = QComboBox()
        for i in range(1, 13):
            self.month_combo.addItem(calendar.month_name[i], i)
        self.month_combo.setCurrentIndex(datetime.date.today().month - 1)
        
        year_label = QLabel("Year:")
        self.year_combo = QComboBox()
        current_year = datetime.date.today().year
        for year in range(current_year - 5, current_year + 2):
            self.year_combo.addItem(str(year), year)
        self.year_combo.setCurrentText(str(current_year))
        
        month_layout.addWidget(month_label)
        month_layout.addWidget(self.month_combo)
        month_layout.addWidget(year_label)
        month_layout.addWidget(self.year_combo)
        
        # Container for month selection (hidden by default)
        self.month_container = QWidget()
        self.month_container.setLayout(month_layout)
        self.month_container.setVisible(False)
        
        layout.addWidget(self.month_container)
        
        # Number of months for summary
        months_layout = QHBoxLayout()
        months_label = QLabel("Number of months:")
        self.months_combo = QComboBox()
        for i in [3, 6, 12, 24, 36]:
            self.months_combo.addItem(f"{i} months", i)
        self.months_combo.setCurrentText("12 months")
        
        months_layout.addWidget(months_label)
        months_layout.addWidget(self.months_combo)
        months_layout.addStretch(1)
        
        # Container for months selection (hidden by default)
        self.months_container = QWidget()
        self.months_container.setLayout(months_layout)
        self.months_container.setVisible(False)
        
        layout.addWidget(self.months_container)
        
        self.period_group.setLayout(layout)
        
        return self.period_group
    
    def _create_format_group(self):
        """Create format selection group"""
        group_box = QGroupBox("Select Export Format")
        layout = QHBoxLayout()
        
        self.csv_radio = QRadioButton("CSV")
        self.excel_radio = QRadioButton("Excel")
        self.csv_radio.setChecked(True)
        
        layout.addWidget(self.csv_radio)
        layout.addWidget(self.excel_radio)
        layout.addStretch(1)
        
        group_box.setLayout(layout)
        
        return group_box
    
    def on_export_type_changed(self, text):
        """Handle export type selection changes"""
        # Show/hide appropriate date widgets based on selection
        is_budget = text == "Budget Data"
        is_summary = text == "Monthly Summary"
        is_debt = text == "Debt Analysis"
        
        # Show regular date range for income/expense data
        self.start_date_edit.setVisible(not is_budget and not is_summary and not is_debt)
        self.end_date_edit.setVisible(not is_budget and not is_summary and not is_debt)
        
        # Show month/year selector for budget data
        self.month_container.setVisible(is_budget)
        
        # Show months selector for monthly summary
        self.months_container.setVisible(is_summary)
        
        # For debt analysis, no date range needed
        self.period_group.setVisible(not is_debt)
    
    def export_data(self):
        """Export data based on user selections"""
        export_type = self.export_type_combo.currentText()
        export_format = 'excel' if self.excel_radio.isChecked() else 'csv'
        
        try:
            filepath = None
            message = ""
            
            if export_type == "Income Data":
                start_date = self.start_date_edit.date().toPyDate()
                end_date = self.end_date_edit.date().toPyDate()
                filepath, message = self.exporter.export_income_data(
                    self.user_id, start_date, end_date, export_format
                )
            
            elif export_type == "Expense Data":
                start_date = self.start_date_edit.date().toPyDate()
                end_date = self.end_date_edit.date().toPyDate()
                filepath, message = self.exporter.export_expense_data(
                    self.user_id, start_date, end_date, export_format
                )
            
            elif export_type == "Budget Data":
                month = self.month_combo.currentData()
                year = self.year_combo.currentData()
                filepath, message = self.exporter.export_budget_data(
                    self.user_id, month, year, export_format
                )
            
            elif export_type == "Debt Analysis":
                filepath, message = self.exporter.export_debt_data(
                    self.user_id, export_format
                )
            
            elif export_type == "Monthly Summary":
                months = self.months_combo.currentData()
                filepath, message = self.exporter.export_monthly_summary(
                    self.user_id, months, export_format
                )
            
            # Show result message
            if filepath:
                open_file = QMessageBox.question(
                    self, "Export Successful", 
                    f"{message}\n\nWould you like to open this file now?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if open_file == QMessageBox.Yes:
                    # Open file with default application
                    os.startfile(filepath)
            else:
                QMessageBox.warning(self, "Export Warning", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"An error occurred during export: {str(e)}")
