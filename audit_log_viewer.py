from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, QLabel, QLineEdit, 
                            QPushButton, QDateTimeEdit, QComboBox, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QColor, QIcon
import psycopg2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from db_config import POSTGRES_CONFIG
from datetime import datetime, timedelta
from audit_logger import AuditLogger
from stylesheets import message_box_style, table_style, date_picker_style, combo_box_style

folio = (8.5 * inch, 13 * inch)

class AuditLogViewer(QMainWindow):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audit Logbook")
        self.setMinimumSize(1000, 600)
        self.current_user = username
        self.icon = QIcon('icons/profile.png')
        self.setWindowIcon(self.icon)
        
        # Set the style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QLabel {
                font-weight: bold;
                color: #212121;
            }
            QLineEdit, QComboBox, QDateTimeEdit {
                padding: 5px;
                border: 1px solid #D1D0D0;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #212121;
            }
            QLineEdit:focus {
                border: 1px solid #ce305e;
                background-color: #fef2f4;
            }
            QComboBox:focus {
                border: 1px solid #ce305e;
                background-color: #fef2f4;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QPushButton#filter {
                background-color: #ce305e;  
                color: #FFFFFF;
            }
            QPushButton#filter:hover {
                background-color: #e0446a;
                color: #FFFFFF;
            }
            QPushButton#reset {
                background-color: #ce305e;
                color: #FFFFFF;
            }
            QPushButton#reset:hover {
                background-color: #e0446a;
                color: #FFFFFF;
            }
        """)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 8, 10, 10)
        
        # Create filter section
        filter_layout = QVBoxLayout()
        filter_layout.setSpacing(5)
        
        # Username filter with horizontal layout for spacer
        username_layout = QHBoxLayout()
        username_layout.setContentsMargins(0, 0, 0, 0)
        self.username_filter = QLineEdit()
        self.username_filter.setPlaceholderText("Username")
        self.username_filter.setFixedWidth(300)  # Set fixed width
        username_layout.addWidget(self.username_filter)
        username_layout.addStretch()  # Add spacer
        filter_layout.addLayout(username_layout)
        
        # Action filter with horizontal layout for spacer
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_filter = QComboBox()
        self.action_filter.setEditable(True)
        self.action_filter.setPlaceholderText("Action")
        self.action_filter.setFixedWidth(300)  # Set fixed width
        self.action_filter.setStyleSheet(combo_box_style)
        action_layout.addWidget(self.action_filter)
        action_layout.addStretch()  # Add spacer
        filter_layout.addLayout(action_layout)
        
        # Date range filter with horizontal layout and spacer
        date_range_layout = QHBoxLayout()
        date_range_layout.setSpacing(3)
        date_range_layout.setContentsMargins(0, 0, 0, 0)
        
        self.start_date = QDateTimeEdit()
        self.start_date.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("MM/dd/yyyy hh:mm AP")
        self.start_date.setFixedWidth(145)  # Set fixed width
        self.start_date.setStyleSheet(date_picker_style)

        self.end_date = QDateTimeEdit()
        self.end_date.setDateTime(QDateTime.currentDateTime())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("MM/dd/yyyy hh:mm AP")
        self.end_date.setFixedWidth(145)  # Set fixed width
        self.end_date.setStyleSheet(date_picker_style)

        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(QLabel("to"))
        date_range_layout.addWidget(self.end_date)
        date_range_layout.addStretch()  # Add spacer
        filter_layout.addLayout(date_range_layout)
        
        # Buttons in horizontal layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(3)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filter button
        self.filter_button = QPushButton("Apply Filters")
        self.filter_button.setObjectName("filter")
        self.filter_button.clicked.connect(self.apply_filters)
        button_layout.addWidget(self.filter_button)
        
        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("reset")
        self.reset_button.clicked.connect(self.reset_filters)
        button_layout.addWidget(self.reset_button)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("filter")  # Use same style as filter button
        self.refresh_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.refresh_button)

        # Export PDF button
        self.export_pdf_button = QPushButton("Export PDF")
        self.export_pdf_button.setObjectName("filter")  # Use same style as filter button
        self.export_pdf_button.clicked.connect(self.export_pdf)
        button_layout.addWidget(self.export_pdf_button)
        
        button_layout.addStretch()  # Add spacer
        
        filter_layout.addLayout(button_layout)
        layout.addLayout(filter_layout)
        
        # Add minimal spacing before the table
        layout.addSpacing(3)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Action", "Details", "Timestamp"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(table_style)
        layout.addWidget(self.table)
        
        # Load initial data
        self.load_action_types()
        self.load_data()
        
    def create_connection(self):
        """Create a new PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            return conn
        except psycopg2.Error as e:
            print(f"Error creating connection: {str(e)}")
            return None

    def closeConnection(self, conn=None):
        """Safely close the database connection"""
        if conn:
            try:
                conn.close()
            except Exception as e:
                print(f"Error closing connection: {str(e)}")
        
    def load_action_types(self):
        """Load unique action types for the action filter dropdown"""
        conn = self.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT action FROM audit_log ORDER BY action")
            actions = [row[0] for row in cursor.fetchall()]
            self.action_filter.addItems(actions)
            
            AuditLogger.log_action(
                conn,
                self.current_user,
                "ACTION_TYPES_LOADED",
                {"count": len(actions)}
            )
            conn.commit()
        except psycopg2.Error as e:
            print(f"Error loading action types: {str(e)}")
        finally:
            self.closeConnection(conn)
    
    def load_data(self):
        """Load audit log data with current filters"""
        conn = self.create_connection()
        try:
            cursor = conn.cursor()
            
            # Build query with filters
            query = "SELECT id, username, action, details, timestamp FROM audit_log WHERE 1=1"
            params = []
            filter_details = {}
            
            # Username filter
            if self.username_filter.text():
                query += " AND username ILIKE %s"
                params.append(f"%{self.username_filter.text()}%")
                filter_details["username"] = self.username_filter.text()
            
            # Action filter
            if self.action_filter.currentText():
                query += " AND action = %s"
                params.append(self.action_filter.currentText())
                filter_details["action"] = self.action_filter.currentText()
            
            # Date range filter
            query += " AND timestamp BETWEEN %s AND %s"
            start_date = self.start_date.dateTime().toPython()
            end_date = self.end_date.dateTime().toPython()
            params.extend([start_date, end_date])
            filter_details.update({
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            })
            
            # Order by timestamp desc
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Log the data load
            AuditLogger.log_action(
                conn,
                self.current_user,
                "AUDIT_LOGS_LOADED",
                {
                    "filters": filter_details,
                    "rows_returned": len(rows)
                }
            )
            conn.commit()
            
            # Update table
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    if isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make cell read-only
                    
                    # Color-code certain actions
                    if j == 2:  # Action column
                        if "ERROR" in str(value) or "FAILED" in str(value):
                            item.setForeground(QColor("#dc3545"))  # Red for errors
                        elif "SUCCESS" in str(value):
                            item.setForeground(QColor("#28a745"))  # Green for success
                    
                    self.table.setItem(i, j, item)
            
            # Adjust column widths
            self.table.resizeColumnsToContents()
            
        except psycopg2.Error as e:
            print(f"Error loading data: {str(e)}")
            if conn:
                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "AUDIT_LOGS_LOAD_ERROR",
                    {"error": str(e)}
                )
                conn.commit()
        finally:
            self.closeConnection(conn)
    
    def apply_filters(self):
        """Apply the current filters and reload data"""
        conn = self.create_connection()
        try:
            AuditLogger.log_action(
                conn,
                self.current_user,
                "AUDIT_FILTERS_APPLIED",
                {
                    "username_filter": self.username_filter.text(),
                    "action_filter": self.action_filter.currentText(),
                    "start_date": self.start_date.dateTime().toPython().isoformat(),
                    "end_date": self.end_date.dateTime().toPython().isoformat()
                }
            )
            conn.commit()
        finally:
            self.closeConnection(conn)
            
        self.load_data()
    
    def reset_filters(self):
        """Reset all filters to default values"""
        conn = self.create_connection()
        try:
            AuditLogger.log_action(
                conn,
                self.current_user,
                "AUDIT_FILTERS_RESET",
                {"message": "All filters reset to default values"}
            )
            conn.commit()
        finally:
            self.closeConnection(conn)
            
        self.username_filter.clear()
        self.action_filter.setCurrentIndex(-1)
        self.start_date.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.end_date.setDateTime(QDateTime.currentDateTime())
        self.load_data()

    def draw_wrapped_text(self, canvas, text, x, y, max_width, line_height=10, font_name="Helvetica", font_size=8):
        words = text.split()
        line = ""
        lines = []

        for word in words:
            test_line = line + word + " "
            if pdfmetrics.stringWidth(test_line, font_name, font_size) <= max_width:
                line = test_line
            else:
                lines.append(line.strip())
                line = word + " "
        if line:
            lines.append(line.strip())

        for line in lines:
            canvas.drawString(x, y, line)
            y -= line_height

        return y

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "AuditLogbook.pdf", "PDF files (*.pdf)")
        if not path:
            return

        try:
            c = canvas.Canvas(path, pagesize=landscape(folio))
            width, height = landscape(folio) 
            c.setFont("Helvetica", 10)
            margin = 40
            y = height - margin

            c.drawString(margin, y, "Audit Log Report")
            y -= 20

            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            col_offsets = []
            col_widths = []

            # Define custom widths: 2nd and 5th columns are wider
            for i in range(self.table.columnCount()):
                if i == 2 or i == 3:
                    col_widths.append(180)
                else:
                    col_widths.append(75)

            x = margin
            for width in col_widths:
                col_offsets.append(x)
                x += width

            c.setFont("Helvetica-Bold", 9)
            for i, header in enumerate(headers):
                c.drawString(col_offsets[i], y, header)
            y -= 15

            c.setFont("Helvetica", 8)
            for row in range(self.table.rowCount()):
                min_y = y  # Track min y for multi-line rows
                max_lines_used = 1
                line_y = y

                for col in range(self.table.columnCount()):
                    text = self.table.item(row, col).text() if self.table.item(row, col) else ""
                    if col == 2 or col == 3:  # 2nd and 5th columns
                        new_y = self.draw_wrapped_text(c, text, col_offsets[col], line_y, col_widths[col])
                        lines_used = int((line_y - new_y) / 10)
                        max_lines_used = max(max_lines_used, lines_used)
                    else:
                        c.drawString(col_offsets[col], line_y, text)

                y -= 10 * max_lines_used
                if y < 50:
                    c.showPage()
                    y = height - margin
                    c.setFont("Helvetica", 8)

            c.save()
            box = QMessageBox()
            box.setIcon(QMessageBox.Information)
            box.setText(f"PDF saved to:\n{path}")
            box.setWindowTitle("Export Successful")
            box.setStandardButtons(QMessageBox.Ok)
            box.setStyleSheet(message_box_style)
            box.exec()

        except Exception as e:
            box = QMessageBox()
            box.setIcon(QMessageBox.Critical)
            box.setText(f"An error occurred:\n{str(e)}")
            box.setWindowTitle("Export Failed")
            box.setStandardButtons(QMessageBox.Ok)
            box.setStyleSheet(message_box_style)
            box.exec()

    def closeEvent(self, event):
        """Handle window close event"""
        conn = self.create_connection()
        try:
            AuditLogger.log_action(
                conn,
                self.current_user,
                "AUDIT_VIEWER_CLOSED",
                {"message": "Audit Log Viewer window closed"}
            )
            conn.commit()
        finally:
            self.closeConnection(conn)
            event.ignore()
            self.hide()