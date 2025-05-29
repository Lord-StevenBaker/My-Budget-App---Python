import sys
import traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from budget_manager import BudgetManager

def exception_hook(exctype, value, tb):
    """
    Custom exception hook to capture and print errors
    """
    print("Exception occurred:")
    print("Type:", exctype)
    print("Value:", value)
    print("Traceback:", "".join(traceback.format_tb(tb)))
    sys.__excepthook__(exctype, value, tb)

def main():
    """Main entry point with error capturing"""
    
    # Set global exception hook
    sys.excepthook = exception_hook
    
    # Set application attributes
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setStyle('Fusion')  # Use Fusion style for consistent look
    
    # Create application instance
    app = QApplication(sys.argv)
    app.setApplicationName("Personal Budget Manager")
    
    try:
        # Initialize budget manager
        budget_manager = BudgetManager()
        
        # Create and show main window
        window = MainWindow(budget_manager)
        window.show()
        
        # Start the application event loop
        sys.exit(app.exec_())
    except Exception as e:
        print(f"ERROR STARTING APPLICATION: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
