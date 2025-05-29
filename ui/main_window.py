from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                         QLabel, QPushButton, QApplication, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont

from ui.dashboard_tab import DashboardTab
from ui.income_tab import IncomeTab
from ui.expense_tab import ExpenseTab
from ui.budget_tab import BudgetTab
from ui.reports_tab import ReportsTab
from ui.debt_payoff_tab import DebtPayoffTab
from ui.export_tab import ExportTab
from ui.goals_tab import GoalsTab
from ui.backup_tab import BackupTab


class MainWindow(QMainWindow):
    """Main application window with tab navigation"""
    
    def __init__(self, budget_manager):
        super().__init__()
        self.budget_manager = budget_manager
        self.user_id = 1  # Default user for now
        
        # Create user if not exists
        if not self.budget_manager.get_user(self.user_id):
            self.budget_manager.create_user("Default User", "user@example.com")
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Personal Budget Manager")
        self.setGeometry(100, 100, 1000, 700)
        self.setup_tabs()
        
        # Set the central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        
        # Add a status bar for messages
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Welcome to Personal Budget Manager")
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def setup_tabs(self):
        """Setup the tab navigation"""
        self.tabs = QTabWidget()
        
        # Create tabs
        self.dashboard_tab = DashboardTab(self.budget_manager, self.user_id)
        self.income_tab = IncomeTab(self.budget_manager, self.user_id)
        self.expense_tab = ExpenseTab(self.budget_manager, self.user_id)
        self.budget_tab = BudgetTab(self.budget_manager, self.user_id)
        self.reports_tab = ReportsTab(self.budget_manager, self.user_id)
        self.debt_payoff_tab = DebtPayoffTab(self.budget_manager, self.user_id)
        self.goals_tab = GoalsTab(self.budget_manager, self.user_id)
        self.export_tab = ExportTab(self.budget_manager, self.user_id)
        self.backup_tab = BackupTab(self.budget_manager, self.user_id)
        
        # Add tabs to widget
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.income_tab, "Income")
        self.tabs.addTab(self.expense_tab, "Expenses")
        self.tabs.addTab(self.budget_tab, "Budget")
        self.tabs.addTab(self.reports_tab, "Reports")
        self.tabs.addTab(self.debt_payoff_tab, "Debt Payoff")
        self.tabs.addTab(self.goals_tab, "Financial Goals")
        self.tabs.addTab(self.export_tab, "Export")
        self.tabs.addTab(self.backup_tab, "Backup & Restore")
        
        # Connect tab changed signal
        self.tabs.currentChanged.connect(self.tab_changed)
    
    def tab_changed(self, index):
        """Handle tab change events"""
        # Refresh data when switching tabs
        tab_widget = self.tabs.widget(index)
        if hasattr(tab_widget, 'refresh_data'):
            tab_widget.refresh_data()
    
    def show_message(self, title, message, icon=QMessageBox.Information):
        """Show a message dialog"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    
    def closeEvent(self, event):
        """Handle application close event"""
        reply = QMessageBox.question(self, 'Exit', 
                                    'Are you sure you want to exit?',
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
