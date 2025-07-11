#!/usr/bin/env python3
"""
Example: How to integrate the standalone eVerify into other Python applications
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QMessageBox
from PySide6.QtCore import QTimer

# Import the standalone eVerify
from everify_standalone import eVerifyStandaloneForm

class ExampleApp(QMainWindow):
    """Example application that integrates eVerify."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Example App with eVerify Integration")
        self.setGeometry(100, 100, 400, 300)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Add title
        title = QLabel("Example Application")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Add eVerify button
        self.everify_button = QPushButton("Launch eVerify")
        self.everify_button.setStyleSheet("""
            QPushButton {
                background-color: #ce305e;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0446a;
            }
        """)
        self.everify_button.clicked.connect(self.launch_everify)
        layout.addWidget(self.everify_button)
        
        # Add result display
        self.result_label = QLabel("No verification result yet")
        self.result_label.setStyleSheet("margin: 10px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.result_label)
        
        # Store eVerify window reference
        self.everify_window = None
        
        # Timer to check for results
        self.result_timer = QTimer()
        self.result_timer.timeout.connect(self.check_everify_result)
        
    def launch_everify(self):
        """Launch the eVerify standalone application."""
        try:
            # Create and show eVerify window
            self.everify_window = eVerifyStandaloneForm()
            self.everify_window.show()
            
            # Start timer to check for results
            self.result_timer.start(1000)  # Check every second
            
            print("✅ eVerify launched successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch eVerify: {str(e)}")
    
    def check_everify_result(self):
        """Check if eVerify has completed and get results."""
        if self.everify_window and not self.everify_window.isVisible():
            # eVerify window is closed, get results
            result = self.everify_window.get_verification_result()
            
            if result['full_name']:
                # Show success
                self.result_label.setText(f"✅ Verified: {result['full_name']}\nType: {result['verification_type']}\nTime: {result['timestamp']}")
                self.result_label.setStyleSheet("margin: 10px; padding: 10px; background-color: #d4edda; border-radius: 5px; color: #155724;")
                
                # You can now use the verification data in your application
                print(f"Verification successful: {result['full_name']}")
                print(f"Verification data: {result['verification_data']}")
                
                # Example: Update your application's database, UI, etc.
                self.update_application_with_verification(result)
                
            else:
                # No verification result
                self.result_label.setText("❌ No verification result")
                self.result_label.setStyleSheet("margin: 10px; padding: 10px; background-color: #f8d7da; border-radius: 5px; color: #721c24;")
            
            # Stop the timer
            self.result_timer.stop()
            self.everify_window = None
    
    def update_application_with_verification(self, result):
        """Example: Update your application with verification results."""
        # This is where you would integrate the verification result
        # into your application's business logic
        
        # Example: Update database, UI, or other application state
        print("📝 Updating application with verification result...")
        
        # Example: You might want to:
        # - Update a database record
        # - Enable certain features in your app
        # - Update UI elements
        # - Send notifications
        # - etc.
        
        QMessageBox.information(self, "Integration Success", 
                              f"Verification result integrated into application:\n{result['full_name']}")

def main():
    """Main function to run the example application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the example app
    window = ExampleApp()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 