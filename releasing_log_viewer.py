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
from db_config import POSTGRES_CONFIG
from datetime import datetime, timedelta
from audit_logger import AuditLogger
from stylesheets import message_box_style, table_style, date_picker_style, combo_box_style

folio = (8.5 * inch, 13 * inch)

class ReleasingLogViewer(QMainWindow):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Releasing Logbook")
        self.setMinimumSize(1200, 600)
        self.current_user = username
        
        # Set window icon
        self.icon = QIcon('icons/handover.png')
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
            }
            QPushButton#filter:hover {
                background-color: #e0446a;
            }
            QPushButton#reset {
                background-color: #ce305e;
            }
            QPushButton#reset:hover {
                background-color: #e0446a;
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
        
        # Document Owner filter
        owner_layout = QHBoxLayout()
        owner_layout.setContentsMargins(0, 0, 0, 0)
        self.owner_filter = QLineEdit()
        self.owner_filter.setPlaceholderText("Document Owner")
        self.owner_filter.setFixedWidth(300)
        owner_layout.addWidget(self.owner_filter)
        owner_layout.addStretch()
        filter_layout.addLayout(owner_layout)
        
        # Document Type filter
        type_layout = QHBoxLayout()
        type_layout.setContentsMargins(0, 0, 0, 0)
        self.type_filter = QComboBox()
        self.type_filter.setEditable(True)
        self.type_filter.setPlaceholderText("Document Type")
        self.type_filter.setFixedWidth(300)
        self.type_filter.setStyleSheet(combo_box_style)
        type_layout.addWidget(self.type_filter)
        type_layout.addStretch()
        filter_layout.addLayout(type_layout)
        
        # Released By filter
        released_by_layout = QHBoxLayout()
        released_by_layout.setContentsMargins(0, 0, 0, 0)
        self.released_by_filter = QLineEdit()
        self.released_by_filter.setPlaceholderText("Released By")
        self.released_by_filter.setFixedWidth(300)
        released_by_layout.addWidget(self.released_by_filter)
        released_by_layout.addStretch()
        filter_layout.addLayout(released_by_layout)
        
        # Received By filter
        received_by_layout = QHBoxLayout()
        received_by_layout.setContentsMargins(0, 0, 0, 0)
        self.received_by_filter = QLineEdit()
        self.received_by_filter.setPlaceholderText("Received By")
        self.received_by_filter.setFixedWidth(300)
        received_by_layout.addWidget(self.received_by_filter)
        received_by_layout.addStretch()
        filter_layout.addLayout(received_by_layout)
        
        # Date range filter
        date_range_layout = QHBoxLayout()
        date_range_layout.setSpacing(3)
        date_range_layout.setContentsMargins(0, 0, 0, 0)
        
        self.start_date = QDateTimeEdit()
        self.start_date.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("MM/dd/yyyy hh:mm AP")
        self.start_date.setFixedWidth(145)
        self.start_date.setStyleSheet(date_picker_style)

        self.end_date = QDateTimeEdit()
        self.end_date.setDateTime(QDateTime.currentDateTime())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("MM/dd/yyyy hh:mm AP")
        self.end_date.setFixedWidth(145)
        self.end_date.setStyleSheet(date_picker_style)

        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(QLabel("to"))
        date_range_layout.addWidget(self.end_date)
        date_range_layout.addStretch()
        filter_layout.addLayout(date_range_layout)
        
        # Buttons
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
        
        button_layout.addStretch()
        
        filter_layout.addLayout(button_layout)
        layout.addLayout(filter_layout)
        
        # Add minimal spacing before the table
        layout.addSpacing(3)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Document Owner", "Document Type", "Copy No.", 
            "Received By", "Released By", "Timestamp"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(table_style)
        layout.addWidget(self.table)
        
        # Load initial data
        self.load_document_types()
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
        
    def load_document_types(self):
        """Load unique document types for the type filter dropdown"""
        conn = self.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT doc_type FROM releasing_log ORDER BY doc_type")
            types = [row[0] for row in cursor.fetchall()]
            self.type_filter.addItems(types)
            
            AuditLogger.log_action(
                conn,
                self.current_user,
                "DOCUMENT_TYPES_LOADED",
                {"count": len(types)}
            )
            conn.commit()
        except psycopg2.Error as e:
            print(f"Error loading document types: {str(e)}")
        finally:
            self.closeConnection(conn)
    
    def load_data(self):
        """Load releasing log data with current filters"""
        conn = self.create_connection()
        try:
            cursor = conn.cursor()
            
            # Build query with filters
            query = """
                SELECT id, doc_owner, doc_type, copy_no, 
                       received_by, released_by, timestamp 
                FROM releasing_log 
                WHERE 1=1
            """
            params = []
            filter_details = {}
            
            # Document Owner filter
            if self.owner_filter.text():
                query += " AND doc_owner ILIKE %s"
                params.append(f"%{self.owner_filter.text()}%")
                filter_details["doc_owner"] = self.owner_filter.text()
            
            # Document Type filter
            if self.type_filter.currentText():
                query += " AND doc_type = %s"
                params.append(self.type_filter.currentText())
                filter_details["doc_type"] = self.type_filter.currentText()
            
            # Released By filter
            if self.released_by_filter.text():
                query += " AND released_by ILIKE %s"
                params.append(f"%{self.released_by_filter.text()}%")
                filter_details["released_by"] = self.released_by_filter.text()
            
            # Received By filter
            if self.received_by_filter.text():
                query += " AND received_by ILIKE %s"
                params.append(f"%{self.received_by_filter.text()}%")
                filter_details["received_by"] = self.received_by_filter.text()
            
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
                "RELEASE_LOGS_LOADED",
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
                    self.table.setItem(i, j, item)
            
            # Adjust column widths
            self.table.resizeColumnsToContents()
            
        except psycopg2.Error as e:
            print(f"Error loading data: {str(e)}")
            if conn:
                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "RELEASE_LOGS_LOAD_ERROR",
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
                "RELEASE_FILTERS_APPLIED",
                {
                    "doc_owner": self.owner_filter.text(),
                    "doc_type": self.type_filter.currentText(),
                    "released_by": self.released_by_filter.text(),
                    "received_by": self.received_by_filter.text(),
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
                "RELEASE_FILTERS_RESET",
                {"message": "All filters reset to default values"}
            )
            conn.commit()
        finally:
            self.closeConnection(conn)
            
        self.owner_filter.clear()
        self.type_filter.setCurrentIndex(-1)
        self.released_by_filter.clear()
        self.received_by_filter.clear()
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
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "ReleasingLogbook.pdf", "PDF files (*.pdf)")
        if not path:
            return

        try:
            c = canvas.Canvas(path, pagesize=landscape(folio))
            width, height = landscape(folio) 
            c.setFont("Helvetica", 10)
            margin = 40
            y = height - margin

            c.drawString(margin, y, "Releasing Logbook")
            y -= 20

            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            col_offsets = []
            col_widths = []

            # Define custom widths: 2nd and 5th columns are wider
            for i in range(self.table.columnCount()):
                if i == 1 or i == 4 or i == 5:
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
                    if col == 1 or col == 4:  # 2nd and 5th columns
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
                "RELEASE_VIEWER_CLOSED",
                {"message": "Document Release Log Viewer window closed"}
            )
            conn.commit()
        finally:
            self.closeConnection(conn)
            event.ignore()
            self.hide()

# if __name__ == "__main__":
#     from PySide6.QtWidgets import QApplication
#     import sys
    
#     app = QApplication(sys.argv)
#     window = ReleasingLogViewer("test_user")  # For testing purposes
#     window.show()
#     sys.exit(app.exec()) 