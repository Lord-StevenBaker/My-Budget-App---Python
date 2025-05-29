import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

def main():
    # Create application
    app = QApplication(sys.argv)
    
    # Create window
    window = QWidget()
    window.setWindowTitle("PyQt5 Test Window")
    window.setGeometry(100, 100, 400, 200)  # x, y, width, height
    
    # Create layout
    layout = QVBoxLayout()
    
    # Add a label
    label = QLabel("If you can see this window, PyQt5 is working correctly!")
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("font-size: 16px;")
    layout.addWidget(label)
    
    # Set the layout
    window.setLayout(layout)
    
    # Show window
    window.show()
    window.raise_()  # Bring window to front
    window.activateWindow()  # Make it the active window
    
    # Start the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
