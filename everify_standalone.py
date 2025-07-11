import os
import webbrowser
import sys
# IMPORT PYSIDE6 MODULES
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QSslConfiguration, QSslSocket, QNetworkReply

# Import the new everify package
from everify import EVerifyClient, EVerifyDB, validate_config

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

from stylesheets import *


class eVerifyStandaloneForm(QWidget):
    def __init__(self, username="default_user", parent=None):
        super().__init__(parent)
        self.current_user = username
        self.qr_value = None
        self.face_liveness_session_id = None
        self.verification_type = None
        self.connection = None
        self.qr_scanner_window = None  # Initialize as None
        
        # Initialize the everify client
        try:
            config = validate_config()
            self.everify_client = EVerifyClient(
                client_id=config['CLIENT_ID'],
                client_secret=config['CLIENT_SECRET']
            )
            self.everify_db = EVerifyDB()
            print("✅ eVerify client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize eVerify client: {e}")
            QMessageBox.critical(self, "Configuration Error", 
                               f"Failed to initialize eVerify client: {e}\n\nPlease check your environment variables.")
            return

        self.images_dir = os.path.join(os.path.dirname(__file__), "images", "faces")
        os.makedirs(self.images_dir, exist_ok=True)  

        self.setFixedSize(QSize(400, 250))

        self.setWindowTitle("eVerify - Standalone")
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
    
    def manual_check_if_already_verified(self):
        first_name = self.first_name_input.text().strip().upper()
        middle_name = self.middle_name_input.text().strip().upper() or None
        last_name = self.last_name_input.text().strip().upper()
        suffix = None if self.suffix_input.currentText().strip() == "N/A" else self.suffix_input.currentText().strip()
        birth_date = self.birth_date_input.date().toString("yyyy-MM-dd")

        try:
            # Use the everify package instead of direct database calls
            verification = self.everify_db.get_verification(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                suffix=suffix,
                birth_date=birth_date
            )

            if verification:
                # Person already verified
                f_name = verification.get('first_name', '')
                m_name = verification.get('middle_name', '')
                l_name = verification.get('last_name', '')
                suff = verification.get('suffix', '')
                gender = verification.get('gender', '')
                marital_status = verification.get('marital_status', '')
                face_key = verification.get('face_key', '')

                # Build full name based on gender and marital status
                name_parts = [f_name]
                if gender == 'Female' and marital_status == "Married":
                    name_parts.append(m_name)
                else:
                    name_parts.append(l_name)
                    if gender != 'Female' and suff:  # Only add suffix for males
                        name_parts.append(suff)
                full_name = " ".join(filter(None, name_parts))
                
                if face_key:
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Information)
                    box.setWindowTitle("Already Verified")
                    box.setText("This client has already been verified. Showing Face Key.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()

                    # Show the face image if available
                    face_path = os.path.join(self.images_dir, face_key)
                    if os.path.exists(face_path):
                        self.show_local_face(face_path, full_name)
                    else:
                        QMessageBox.information(self, "Face Image", f"Face image for {full_name} not found locally.")
                    
                    # Store result for parent applications
                    self.store_verification_result(full_name, verification)
                    self.close()
                else:
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Warning)
                    box.setWindowTitle("Missing Face URL!")
                    box.setText(f"Client {full_name} has no face URL.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                    self.close()
                return
            else:
                # Not yet verified - proceed to liveness check
                self.start_liveness_check()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Verification check failed: {str(e)}")
            return

    def start_liveness_check(self):
        try:
            # Check if liveness server is available
            if self.everify_client.is_liveness_server_available():
                url = self.everify_client.start_liveness_check()
                if url:
                    print(f"✅ Liveness check started at: {url}")
                    # Start polling for results
                    self.liveness_timer = QTimer()
                    self.liveness_timer.timeout.connect(self.check_liveness_result)
                    self.liveness_timer.start(2000)
                else:
                    QMessageBox.warning(self, "Liveness Error", "Failed to start liveness check.")
            else:
                QMessageBox.warning(self, "Liveness Server", "Liveness server is not available. Please start the Flask server first.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start liveness check: {str(e)}")

    def check_liveness_result(self):
        try:
            result = self.everify_client.get_liveness_result()
            if "face_liveness_session_id" in result:
                self.face_liveness_session_id = result["face_liveness_session_id"]
                print("✅ Got face_liveness_session_id:", self.face_liveness_session_id)
                self.liveness_timer.stop()
                self.final_verification()
            elif "error" in result:
                print("🔄 Waiting for liveness session id...")
        except Exception as e:
            print("🔄 Waiting for liveness session id...", e)

    def final_verification(self):
        if not self.face_liveness_session_id:
            QMessageBox.warning(self, "Missing Data", "QR or Liveness not completed yet.")
            return
        
        try:
            if self.qr_value:
                # QR-based flow
                payload = {
                    "value": self.qr_value,
                    "face_liveness_session_id": self.face_liveness_session_id
                }
                result = self.everify_client.verify_qr(payload)
                self.verification_type = "QR"
            else:
                # Manual flow
                payload = {
                    "first_name": self.first_name_input.text().strip(),
                    "middle_name": self.middle_name_input.text().strip(),
                    "last_name": self.last_name_input.text().strip(),
                    "suffix": self.suffix_input.currentText() if self.suffix_input.currentText() and self.suffix_input.currentText() != "N/A" else None,
                    "birth_date": self.birth_date_input.date().toString("yyyy-MM-dd"),
                    "face_liveness_session_id": self.face_liveness_session_id
                }
                result = self.everify_client.verify_person(payload)
                self.verification_type = "Manual"

            if "error" in result:
                QMessageBox.warning(self, "Verification Failed", f"Verification failed: {result['error']}")
                return

            # Process successful verification
            data = result.get("data", {})
            if data.get("verified", False):
                # Extract person data and build full name
                person_data = data
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
                    suffix = person_data.get("suffix")
                    full_name = " ".join(filter(None, [first_name, last_name, suffix]))
                
                # Store verification in database
                try:
                    self.everify_db.store_verification(person_data)
                    print("✅ Verification stored successfully")
                except Exception as e:
                    print(f"⚠️ Failed to store verification: {e}")

                # Store result for parent applications
                self.store_verification_result(full_name, person_data)

                # Show success message
                success_msg_box = QMessageBox(self)
                success_msg_box.setIcon(QMessageBox.Information)
                success_msg_box.setWindowTitle("National ID Valid")
                success_msg_box.setText(f"{full_name} has a valid National ID.")
                success_msg_box.setWindowFlag(Qt.WindowStaysOnTopHint)
                success_msg_box.setStyleSheet(message_box_style)
                success_msg_box.exec()

                # Close the window
                self.close()
            else:
                QMessageBox.warning(self, "Failed Verification", "Verification completed but no data found from server.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to complete final verification: {str(e)}")
        finally:
            # Clear liveness session
            try:
                self.everify_client.delete_liveness_result()
                print("🧹 Server liveness session ID cleared.")
            except Exception as e:
                print("⚠️ Could not clear server liveness session ID:", e)
            self.face_liveness_session_id = None
            self.clear_form_inputs()

    def launch_qr_scanner(self):
        try:
            self.qr_scanner_window = QRScannerWindow()
            self.qr_scanner_window.qr_scanned.connect(self.validate_qr_code)
            self.qr_scanner_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch QR scanner: {str(e)}")

    def validate_qr_code(self, qr_data):
        try:
            # First check if already verified
            if self.qr_check_if_already_verified(qr_data):
                return

            # Use the everify package for QR validation
            result = self.everify_client.check_qr({"value": qr_data})
            
            if "error" in result:
                QMessageBox.warning(self, "Invalid QR", f"QR validation failed: {result['error']}")
                return

            data = result.get("data")
            if data:
                print("✅ QR Check Successful. Data:", data)
                QMessageBox.information(self, "QR Check Successful!", "QR Check is successful. Proceed to Liveness Check.")
                self.qr_value = qr_data
                self.start_liveness_check()
            else:
                QMessageBox.warning(self, "Invalid QR", "No data found in QR response.")
                
        except Exception as e:
            print("🚨 Error during QR validation:", e)
            QMessageBox.critical(self, "Error", "Failed to validate QR Code.")

    def qr_check_if_already_verified(self, qr_data):
        try:
            # Parse QR data to get reference code
            if qr_data.strip().startswith("{"):
                try:
                    qr_json = json.loads(qr_data)
                    reference_code = qr_json.get("reference_code")
                    if not reference_code:
                        QMessageBox.warning(self, "Invalid QR", "QR code is missing reference code")
                        return True
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Invalid QR", "QR code is not in valid JSON format")
                    return True
            else:
                reference_code = qr_data
            
            reference_code = reference_code.replace("-", "")
            
            # Check if already verified using the everify package
            verification = self.everify_db.get_verification(reference=reference_code)
            
            if verification:
                # Already verified - show face image
                f_name = verification.get('first_name', '')
                m_name = verification.get('middle_name', '')
                l_name = verification.get('last_name', '')
                suff = verification.get('suffix', '')
                gender = verification.get('gender', '')
                marital_status = verification.get('marital_status', '')
                face_key = verification.get('face_key', '')

                name_parts = [f_name]
                if gender == 'Female' and marital_status == "Married":
                    name_parts.append(m_name)
                else:
                    name_parts.append(l_name)
                    if gender != 'Female' and suff:
                        name_parts.append(suff)
                full_name = " ".join(filter(None, name_parts))
                
                if face_key:
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Information)
                    box.setWindowTitle("Already Verified")
                    box.setText("This client has already been verified. Showing Face Key.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                    
                    face_path = os.path.join(self.images_dir, face_key)
                    if os.path.exists(face_path):
                        self.show_local_face(face_path, full_name)
                    else:
                        QMessageBox.information(self, "Face Image", f"Face image for {full_name} not found locally.")
                    
                    # Store result for parent applications
                    self.store_verification_result(full_name, verification)
                    self.close()
                else:
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Warning)
                    box.setWindowTitle("Missing Face URL!")
                    box.setText(f"Client {full_name} has no face URL.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                    self.close()
                return True
            else:
                return False
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"QR verification check failed: {str(e)}")
            return False

    def show_local_face(self, image_path, full_name):
        """Displays an image from the local folder."""
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", "Failed to load cached image.")
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
        self.suffix_input.setCurrentIndex(0)
        self.birth_date_input.setDate(QDate.currentDate())

    def closeEvent(self, event):
        try:
            self.clear_form_inputs()
            if self.qr_scanner_window is not None:
                self.qr_scanner_window.hide()
        except:
            pass
        event.accept()  # Accept the close event

    def get_verification_result(self):
        """Get the last verification result. Can be called by parent applications."""
        return {
            'full_name': getattr(self, 'last_verification_full_name', None),
            'verification_data': getattr(self, 'last_verification_data', None),
            'verification_type': getattr(self, 'verification_type', None),
            'timestamp': getattr(self, 'last_verification_timestamp', None)
        }

    def store_verification_result(self, full_name, verification_data):
        """Store verification result for parent applications to access."""
        self.last_verification_full_name = full_name
        self.last_verification_data = verification_data
        self.last_verification_timestamp = datetime.now()


# Standalone launcher
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = eVerifyStandaloneForm()
    window.show()
    sys.exit(app.exec()) 