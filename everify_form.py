import os
import webbrowser
# IMPORT PYSIDE6 MODULES
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QSslConfiguration, QSslSocket, QNetworkReply

from qr_scanner_window import QRScannerWindow
from audit_logger import AuditLogger

from PySide6.QtWebEngineWidgets import QWebEngineView
import requests
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from db_config import POSTGRES_CONFIG
from datetime import datetime, timedelta 
from urllib.parse import urlparse
from flask_server.app import get_access_token

from stylesheets import *


class eVerifyForm(QWidget):
    fullNameVerified = Signal(str)
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.current_user = username
        self.qr_value = None
        self.face_liveness_session_id = None
        self.verification_type = None
        self.connection = None
        self.qr_scanner_window = None  # Initialize as None

        self.images_dir = os.path.join(os.path.dirname(__file__), "images", "faces")
        os.makedirs(self.images_dir, exist_ok=True)  

        self.setFixedSize(QSize(400, 250))

        self.setWindowTitle("eVerify")
        self.setWindowIcon(QIcon("icons/check.png"))

        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
            }
            QLineEdit {
                border: 1px solid #D1D0D0;
                background-color: #FFFFFF;
                border-radius: 4px;
                padding: 5px;
                color: #212121;
            }
            QLineEdit:focus {
                border: 1px solid #ce305e;
                background-color: #fef2f4;
            }
            QLabel {
                color: #212121;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #212121;
                border: 1px solid #D1D0D0;
                border-radius: 4px;
                padding: 5px;                
            }
            QComboBox::item {
                background-color: #FFFFFF;
                color: #212121;
            }
            QComboBox::item:hover {
                background-color: #ce305e;
                color: #FFFFFF;
            }
            QComboBox::item:selected {
                background-color: #ce305e;
                color: #FFFFFF;
            }
            QComboBox:focus {
                border: 1px solid #ce305e;
                background-color: #fef2f4;
            }
        """)

        self.tabs = QTabWidget()

        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                padding: 6px;
            }

            QTabBar::tab {
                background: #FFFFFF;
                color: #212121;
                padding: 10px;
                margin-right: 4px;
                border-top: 1px solid #FFFFFF;
                border-left: 1px solid #FFFFFF;
                border-right: 1px solid #FFFFFF;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }

            QTabBar::tab:selected {
                background: #ce305e;
                color: #FFFFFF;
            }

            QTabBar::tab:hover {
                background: #e0446a;
                color: #FFFFFF;
            }
        """)


        # Tab 1: Manual Entry
        self.manual_tab = QWidget()
        self.build_manual_tab()

        # Tab 2: QR Code
        self.qr_tab = QWidget()
        self.build_qr_tab()

        self.tabs.addTab(self.manual_tab, "Personal Information")
        self.tabs.addTab(self.qr_tab, "Scan QR Code")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)


    def build_manual_tab(self):
        self.first_name_input = QLineEdit()
        self.middle_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.suffix_input = QComboBox()
        self.suffix_input.addItems(["N/A", "JR", "SR", "II", "III", "IV"])
        self.suffix_input.setFixedWidth(60)
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDisplayFormat("MM/dd/yyyy")
        self.birth_date_input.setDate(QDate.currentDate())
        self.birth_date_input.setStyleSheet(date_picker_style)

        # Buttons
        self.continue_button = QPushButton("Continue")
        self.clear_button = QPushButton("Clear")

        self.continue_button.setStyleSheet(button_style)
        self.clear_button.setStyleSheet(button_style)

        # Form Layout
        form_layout = QFormLayout()
        form_layout.addRow("First Name:", self.first_name_input)
        form_layout.addRow("Middle Name (Optional):", self.middle_name_input)

        name_suffix_layout = QHBoxLayout()
        name_suffix_layout.addWidget(self.last_name_input)
        name_suffix_layout.addWidget(self.suffix_input)
        form_layout.addRow("Last Name + Suffix:", name_suffix_layout)
        form_layout.addRow("Birth Date:", self.birth_date_input)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.continue_button)
        button_layout.addWidget(self.clear_button)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        self.manual_tab.setLayout(layout)

        # Connect signals
        self.clear_button.clicked.connect(self.clear_form)
        self.continue_button.clicked.connect(self.manual_check_if_already_verified)

    def build_qr_tab(self):
        self.qr_button = QPushButton("Launch QR Scanner")
        self.qr_button.setStyleSheet(button_style)
        qr_layout = QVBoxLayout()
        qr_layout.addWidget(QLabel("Use this option to verify using a QR Code."))
        qr_layout.addWidget(self.qr_button)
        qr_layout.addStretch()
        self.qr_tab.setLayout(qr_layout)

        # Connect to your QR scanner logic
        self.qr_button.clicked.connect(self.launch_qr_scanner)

    def clear_form(self):
        self.first_name_input.clear()
        self.middle_name_input.clear()
        self.last_name_input.clear()
        self.suffix_input.setCurrentIndex(0)
        self.birth_date_input.setDate(QDate.currentDate())
    
    def create_connection(self):
        """Create a new PostgreSQL database connection"""
        if self.connection is None:
            self.connection = psycopg2.connect(**POSTGRES_CONFIG)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return self.connection

    def closeConnection(self):
        """Safely close the PostgreSQL connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def manual_check_if_already_verified(self):
        first_name = self.first_name_input.text().strip().upper()
        middle_name = self.middle_name_input.text().strip().upper() or None
        last_name = self.last_name_input.text().strip().upper()
        suffix = None if self.suffix_input.currentText().strip() == "N/A" else self.suffix_input.currentText().strip()
        birth_date = self.birth_date_input.date().toString("yyyy-MM-dd")

        conn = self.create_connection()
        cursor = None
        try:
            AuditLogger.log_action(
                conn,
                self.current_user,
                "eVERIFY_AUTHENTICATION_VIA_PERSONAL DETAILS_ATTEMPT",
                {
                    "first name": first_name,
                    "middle name": middle_name,
                    "last name": last_name,
                    "suffix": suffix,
                    "birth date": birth_date
                }
            )

            cursor = conn.cursor()
            # Debug: Print input values
            print(f"Searching with: first_name={first_name}, middle_name={middle_name}, last_name={last_name}, suffix={suffix}, birth_date={birth_date}")
            
            cursor.execute("""
                SELECT first_name, middle_name, last_name, suffix, gender, face_key, marital_status
                FROM verifications
                WHERE UPPER(COALESCE(first_name, '')) = %s
                AND (
                    (middle_name IS NULL AND %s IS NULL) OR 
                    UPPER(COALESCE(middle_name, '')) = COALESCE(%s, '')
                )
                AND UPPER(COALESCE(last_name, '')) = %s
                AND (
                    (suffix IS NULL AND %s IS NULL) OR 
                    UPPER(COALESCE(suffix, '')) = COALESCE(%s, '')
                )
                AND COALESCE(birth_date, '') = %s
            """, (first_name, middle_name, middle_name, last_name, suffix, suffix, birth_date))
            
            # Debug: Print query results
            row = cursor.fetchone()
            print(f"Query result: {row}")

            if row:
                f_name, m_name, l_name, suff, gender, face_url, marital_status = row
                name_parts = [f_name]
                if gender == 'Female' and marital_status == "Married":
                    name_parts.append(m_name)
                else:
                    name_parts.append(l_name)
                    if gender != 'Female' and suff:  # Only add suffix for males
                        name_parts.append(suff)
                full_name = " ".join(filter(None, name_parts))
                
                if face_url:
                    # QMessageBox.information(self, "Verified Already!", "Client is verified already. Proceed to Records Check.")
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Information)
                    box.setWindowTitle("Already Verified")
                    box.setText("This client has already been verified. Showing Face Key.")
                    box.setStandardButtons(QMessageBox.Ok)

                    box.setStyleSheet(message_box_style)
                    box.exec()

                    self.download_and_save_face(face_url, full_name)
                    AuditLogger.log_action(
                        conn,
                        self.current_user,
                        "eVERIFY_SUCCESS",
                        {"result": f"{full_name} already verified. Show Face Key"}
                    )
                    self.pass_full_name(full_name)
                    self.hide()
                else:
                    # QMessageBox.warning(self, "Missing Face URL!", f"Client {full_name} has no face URL.")
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Warning)
                    box.setWindowTitle("Missing Face URL!")
                    box.setText(f"Client {full_name} has no face URL.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                return
        except psycopg2.Error as e:
            # Create a new connection for error logging since the current one might be in a bad state
            error_conn = self.create_connection()
            try:
                print(f"Database error: {str(e)}")  # Debug: Print the error
                AuditLogger.log_action(
                    error_conn,
                    self.current_user,
                    "DB_ERROR",
                    {"method": "manual_check", "error": str(e)}
                )
            finally:
                error_conn.close()
            # QMessageBox.critical(self, "Database Error", f"Verification check failed: {str(e)}")
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle("Database Error")
            box.setText(f"Verification check failed: {str(e)}")
            box.setStandardButtons(QMessageBox.Ok)
            box.setStyleSheet(message_box_style)
            box.exec()
            return False
        finally:
            if cursor:
                cursor.close()
            self.closeConnection()

        # Create a new connection for the final audit log since the previous one was closed
        final_conn = self.create_connection()
        try:
            # Not yet verified - proceed to liveness check
            AuditLogger.log_action(
                final_conn,
                self.current_user,
                "USER NOT YET VERIFIED",
                {"action": "proceed to face liveness check"}
            )
            self.start_liveness_check()
        finally:
            final_conn.close()

    def qr_check_if_already_verified(self, qr_data):
        conn = self.create_connection()
        cursor = None
        try:
            AuditLogger.log_action(
                conn,
                self.current_user,
                "eVERIFY_AUTHENTICATION_VIA_QR_ATTEMPT",
                {"qr_data": qr_data}
            )
            
            # Step 1: Try to detect if it's JSON
            if qr_data.strip().startswith("{"):
                try:
                    qr_json = json.loads(qr_data)
                    reference_code = qr_json.get("reference_code")
                    if not reference_code:
                        QMessageBox.warning(self, "Invalid QR", "QR code is missing reference code")
                        return
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Invalid QR", "QR code is not in valid JSON format")
                    return
            else:
                # If not JSON, treat as direct reference code
                reference_code = qr_data
            
            reference_code = reference_code.replace("-", "")
            
            # Debug: Print the reference code being searched
            print(f"Searching with reference_code: {reference_code}")
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT first_name, middle_name, last_name, suffix, gender, face_key, marital_status
                FROM verifications
                WHERE COALESCE(reference, '') = COALESCE(%s, '')
            """, (reference_code,))
            
            # Debug: Print query results
            row = cursor.fetchone()
            print(f"Query result: {row}")

            if row:
                f_name, m_name, l_name, suff, gender, face_url, marital_status = row
                name_parts = [f_name]
                if gender == 'Female' and marital_status == "Married":
                    name_parts.append(m_name)
                else:
                    name_parts.append(l_name)
                    if gender != 'Female' and suff:  # Only add suffix for males
                        name_parts.append(suff)
                full_name = " ".join(filter(None, name_parts))
                
                if face_url: 
                    # QMessageBox.information(self, "Verified Already!", "Client is verified already. Proceed to Records Check.")
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Information)
                    box.setWindowTitle("Already Verified")
                    box.setText("This client has already been verified. Showing Face Key.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                    self.download_and_save_face(face_url, full_name)
                    
                    AuditLogger.log_action(
                        conn,
                        self.current_user,
                        "eVERIFY_SUCCESS",
                        {"result": f"{full_name} already verified. Show Face Key"}
                    )
                    self.pass_full_name(full_name)
                    self.hide()
                else:
                    # QMessageBox.warning(self, "Missing Face URL!", f"Client {full_name} has no face URL.")
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Warning)
                    box.setWindowTitle("Missing Face URL!")
                    box.setText(f"Client {full_name} has no face URL.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                return True
            else:
                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "USER NOT YET VERIFIED",
                    {"action": "proceed to face liveness check"}
                )
                return False
        except (json.JSONDecodeError, psycopg2.Error) as e:
            # Create a new connection for error logging since the current one might be in a bad state
            error_conn = self.create_connection()
            try:
                print(f"Database error: {str(e)}")  # Debug: Print the error
                AuditLogger.log_action(
                    error_conn,
                    self.current_user,
                    "DB_ERROR",
                    {"method": "qr_scan", "error": str(e)}
                )
            finally:
                error_conn.close()
            # QMessageBox.critical(self, "Database Error", f"QR verification check failed: {str(e)}")
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle("Database Error")
            box.setText(f"QR verification check failed: {str(e)}")
            box.setStandardButtons(QMessageBox.Ok)
            box.setStyleSheet(message_box_style)
            box.exec()
            return False
        finally:
            if cursor:
                cursor.close()
            self.closeConnection()

    def start_liveness_check(self):
        conn = self.create_connection()
        try:
            AuditLogger.log_action(
                conn,
                self.current_user,
                "FACE_LIVENESS_CHECK_INITIATED"
            )
            self.liveness_timer = QTimer()
            self.liveness_timer.timeout.connect(self.check_liveness_result)
            self.liveness_timer.start(2000)

            liveness_url = "http://localhost:5000/liveness"
            webbrowser.open(liveness_url)
        finally:
            self.closeConnection()
    
    def validate_qr_code(self, qr_data):
        try:
            if self.qr_check_if_already_verified(qr_data):
                return

            url = "http://127.0.0.1:5000/query/qr/check"
            payload = {"value": qr_data}
            response = requests.post(url, json=payload)

            conn = self.create_connection()
            try:
                if response.status_code == 200:
                    result = response.json()
                    data = result.get("data", None)

                    if data:
                        print("✅ QR Check Successful. Data:", data)
                        AuditLogger.log_action(
                            conn,
                            self.current_user,
                            "QR_VALIDATION_SUCCESS",
                            {"result": data}
                        )
                        conn.commit()

                        # QMessageBox.information(self, "QR Check Successful!", f"QR Check is successful. Proceed to Liveness Check.")
                        box = QMessageBox(self)
                        box.setIcon(QMessageBox.Information)
                        box.setWindowTitle("QR Check Successful!")
                        box.setText("QR Check is successful. Proceed to Liveness Check.")
                        box.setStandardButtons(QMessageBox.Ok)
                        box.setStyleSheet(message_box_style)
                        box.exec()
                        self.qr_value = qr_data  # Save for next steps
                        self.start_liveness_check()  # Proceed to Face Liveness
                        
                    else:
                        # QMessageBox.warning(self, "Invalid QR", "No data found in QR response.")
                        box = QMessageBox(self)
                        box.setIcon(QMessageBox.Warning)
                        box.setWindowTitle("Invalid QR")
                        box.setText("No data found in QR response.")
                        box.setStandardButtons(QMessageBox.Ok)
                        box.setStyleSheet(message_box_style)
                        box.exec()
                        AuditLogger.log_action(
                            conn,
                            self.current_user,
                            "QR_VALIDATION_FAILED",
                            {"error": "no data found"}
                        )
                        conn.commit()
                else:
                    # QMessageBox.warning(self, "Invalid QR", f"Server returned status {response.status_code}")
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Warning)
                    box.setWindowTitle("Invalid QR")
                    box.setText(f"Server returned status {response.status_code}")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                    AuditLogger.log_action(
                        conn,
                        self.current_user,
                        "INVALID_QR",
                        {"error": str(response.status_code)}
                    )
                    conn.commit()
            finally:
                self.closeConnection()
        except Exception as e:
            print("🚨 Error during QR validation:", e)
            conn = self.create_connection()
            try:
                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "QR_VALIDATION_ERROR",
                    {"error": str(e)}
                )
                conn.commit()
            finally:
                self.closeConnection()
            # QMessageBox.critical(self, "Error", "Failed to validate QR Code.")
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle("Error")
            box.setText("Failed to validate QR Code.")
            box.setStandardButtons(QMessageBox.Ok)
            box.setStyleSheet(message_box_style)
            box.exec()

    def launch_qr_scanner(self):
        # Launch your existing QR Scanner Window
        conn = self.create_connection()
        try:
            AuditLogger.log_action(conn, self.current_user, "QR_SCAN_INITIATED")
            self.qr_scanner_window = QRScannerWindow()
            self.qr_scanner_window.qr_scanned.connect(self.validate_qr_code)
            self.qr_scanner_window.show()
        finally:
            self.closeConnection()

    def final_verification(self):
        if not self.face_liveness_session_id:
            # QMessageBox.warning(self, "Missing Data", "QR or Liveness not completed yet.")
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle("Missing Data")
            box.setText("QR or Liveness not completed yet.")
            box.setStandardButtons(QMessageBox.Ok)
            box.setStyleSheet(message_box_style)
            box.exec()
            return
        
        conn = self.create_connection()
        try:
            if self.qr_value:
                # QR-based flow
                url = "http://127.0.0.1:5000/query/qr"
                payload = {
                    "value": self.qr_value,
                    "face_liveness_session_id": self.face_liveness_session_id
                }
                self.verification_type = "QR"
            else:
                # Manual flow
                url = "http://127.0.0.1:5000/query"
                payload = {
                    "first_name": self.first_name_input.text().strip(),
                    "middle_name": self.middle_name_input.text().strip(),
                    "last_name": self.last_name_input.text().strip(),
                    "suffix": self.suffix_input.currentText() if self.suffix_input.currentText() and self.suffix_input.currentText() != "N/A" else None,
                    "birth_date": self.birth_date_input.date().toString("yyyy-MM-dd"),
                    "face_liveness_session_id": self.face_liveness_session_id
                }  
                print(payload)
                self.verification_type = "Manual"

            response = requests.post(url, json=payload)                                                         

            if response.status_code == 200:
                data = response.json()
                print("✅ Final Verification Success:", data)

                person_data = data.get("data", {})

                if person_data.get("verified", "") == False:
                    # QMessageBox.warning(self, "Failed Verification", "Verification completed but no data found from server.")
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Warning)
                    box.setWindowTitle("Failed Verification")
                    box.setText("Verification completed but no data found from server.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                    AuditLogger.log_action(
                        conn,
                        self.current_user,
                        "eVERIFY_FAILED",
                        {"result": "no data found"}
                    )
                    conn.commit()
                else:
                    gender = person_data.get("gender", "")
                    marital_status = person_data.get("marital_status", "")
                    if gender == "Female":
                        if marital_status == "Married":
                            first_name = person_data.get("first_name", "").strip()
                            middle_name = person_data.get("middle_name", "").strip()
                            full_name = f"{first_name} {middle_name}".strip()
                        else:
                            first_name = person_data.get("first_name", "").strip()
                            last_name = person_data.get("last_name", "").strip()
                            full_name = f"{first_name} {last_name}".strip()
                    else:
                        first_name = person_data.get("first_name", "").strip()
                        last_name = person_data.get("last_name", "").strip()
                        suffix = person_data.get("suffix")  # Returns None if key doesn't exist
                        full_name = " ".join(filter(None, [first_name, last_name, suffix]))
                    
                    AuditLogger.log_action(
                        conn,
                        self.current_user,
                        "eVERIFY_SUCCESS",
                        {"result": f"{full_name} has a valid National ID"}
                    )
                    conn.commit()

                    print("🙌 Extracted full_name:", full_name)
                    success_msg_box = QMessageBox(self)
                    success_msg_box.setIcon(QMessageBox.Information)
                    success_msg_box.setWindowTitle("National ID Valid")
                    success_msg_box.setText(f"{full_name} has a valid National ID.")
                    success_msg_box.setWindowFlag(Qt.WindowStaysOnTopHint)
                    success_msg_box.setStyleSheet(message_box_style)
                    success_msg_box.exec()

                if full_name:
                    self.pass_full_name(full_name)
                    self.save_successful_verification(data)
                    self.hide()
            else:
                # QMessageBox.warning(self, "Verification Failed", "Invalid response from server.")
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Warning)
                box.setWindowTitle("Verification Failed")
                box.setText("Invalid response from server.")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "eVERIFY_FAILED",
                    {"result": "Invalid response from server."}
                )
                conn.commit()
        except Exception as e:
            print("🚨 Error in final verification:", e)
            AuditLogger.log_action(
                conn,
                self.current_user,
                "eVERIFY_ERROR",
                {"error": str(e)}
            )
            conn.commit()
            # QMessageBox.critical(self, "Error", "Failed to complete final verification.")
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle("Error")
            box.setText("Failed to complete final verification.")
            box.setStandardButtons(QMessageBox.Ok)
            box.setStyleSheet(message_box_style)
            box.exec()
        finally:
            # Clear liveness session on the server
            try:
                requests.delete("http://127.0.0.1:5000/liveness_result")
                print("🧹 Server liveness session ID cleared.")
            except Exception as e:
                print("⚠️ Could not clear server liveness session ID:", e)
            # ✅ Reset session ID regardless of success or failure
            self.face_liveness_session_id = None
            self.clear_form_inputs()
            self.closeConnection()

    def check_liveness_result(self):
        try:
            response = requests.get("http://127.0.0.1:5000/liveness_result")
            if response.status_code == 200:
                result = response.json()
                self.face_liveness_session_id = result.get("face_liveness_session_id")
                if self.face_liveness_session_id:
                    print("✅ Got face_liveness_session_id:", self.face_liveness_session_id)
                    conn = self.create_connection()
                    try:
                        AuditLogger.log_action(
                            conn,
                            self.current_user,
                            "FACE_LIVENESS_CHECK_SUCCESS",
                            {"result": str(self.face_liveness_session_id)}
                        )
                        conn.commit()
                        self.liveness_timer.stop()
                        self.final_verification()
                    finally:
                        self.closeConnection()
        except Exception as e:
            print("🔄 Waiting for liveness session id...", e)

    def pass_full_name(self, full_name):
        self.fullNameVerified.emit(full_name)
        print(f"Full name passed to search: {full_name}")

    def save_successful_verification(self, result_data, callback=None):
        try:
            response = requests.post(
                "http://127.0.0.1:5000/store_verification",
                json={"data": result_data},
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Verification saved successfully.")
                print(f"Response JSON: {response.json()}")
                if callback:
                    callback()
            else:
                print("❌ Failed to store verification:", response.text)
                print(f"Response JSON: {response.json()}")
        except Exception as e:
            print("🚨 Error sending verification:", e)

    def download_and_save_face(self, face_url, full_name):
        """Downloads image from URL and saves to local folder."""
        try:
            filename = os.path.basename(face_url.split('?')[0])  # Remove URL params
            local_path = os.path.join(self.images_dir, filename)
            
            if os.path.exists(local_path):
                self.show_local_face(local_path, full_name)
                return
                
            response = requests.get(face_url, stream=True)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            self.show_local_face(local_path, full_name)
            
        except Exception as e:
            # QMessageBox.warning(self, "Download Failed", f"Error: {str(e)}")
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle("Download Failed")
            box.setText(f"Error: {str(e)}")
            box.setStandardButtons(QMessageBox.Ok)
            box.setStyleSheet(message_box_style)
            box.exec()

    def show_local_face(self, image_path, full_name):
        """Displays an image from the local folder."""
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            # QMessageBox.warning(self, "Error", "Failed to load cached image.")
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle("Error")
            box.setText("Failed to load cached image.")
            box.setStandardButtons(QMessageBox.Ok)
            box.setStyleSheet(message_box_style)
            box.exec()
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Face Verification")
        msg_box.setText(f"Verified: {full_name}")
        msg_box.setIconPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
        msg_box.setStyleSheet(message_box_style)
        msg_box.exec_()
    

    def clear_form_inputs(self):
        self.first_name_input.clear()
        self.middle_name_input.clear()
        self.last_name_input.clear()
        self.suffix_input.setCurrentIndex(0)  # Assuming "N/A" or default is at index 0
        self.birth_date_input.setDate(QDate.currentDate())


    def closeEvent(self, event):
        conn = self.create_connection()
        try:
            AuditLogger.log_action(
                conn,
                self.current_user,
                "WINDOW_CLOSED",
                {"window": "eVerifyForm"}
            )
            conn.commit()
            
            self.clear_form_inputs()
            if self.qr_scanner_window is not None:
                self.qr_scanner_window.hide()
        finally:
            self.closeConnection()
            event.ignore()
            self.hide()
            


