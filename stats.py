import psycopg2
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdf_canvas
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon
from stylesheets import button_style, date_picker_style
from audit_logger import AuditLogger
from db_config import POSTGRES_CONFIG
from stylesheets import *




class StatisticsWindow(QWidget):
    # Key to column mapping - centralized to avoid duplication
    KEY_COLUMN_MAP = {
        # Live Birth
        "Name": "name",
        "Sex": "sex",
        "Place of Birth": "place_of_birth",
        "Name of Mother": "name_of_mother",
        "Name of Father": "name_of_father",
        "Nationality of Mother": "nationality_mother",
        "Nationality of Father": "nationality_father",
        "Attendant": "attendant",
        "Late Registration": "late_registration",
        "Type of Birth": "type_of_birth",
        # Death
        "Age": "age_years",
        "Civil Status": "civil_status",
        "Nationality": "nationality",
        "Place of Death": "place_of_death",
        "Cause of Death": "cause_of_death",
        "Corpse Disposal": "corpse_disposal",
        # Marriage
        "Husband Name": "husband_name",
        "Husband Age": "husband_age",
        "Husband Civil Status": "husb_civil_status",
        "Husband Nationality": "husb_nationality",
        "Wife Name": "wife_name",
        "Wife Age": "wife_age",
        "Wife Civil Status": "wife_civil_status",
        "Wife Nationality": "wife_nationality",
        "Place of Marriage": "place_of_marriage",
        "Ceremony Type": "ceremony_type",
    }

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.current_user = username
        self.connection = None
        self.setWindowTitle("Statistics Tool")
        self.setGeometry(200, 200, 600, 400)
        self.setWindowIcon(QIcon("icons/application.png"))
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
            }
        """)
        self.init_ui()

    def create_connection(self):
        if self.connection is None:
            self.connection = psycopg2.connect(**POSTGRES_CONFIG)
            self.connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        return self.connection

    def closeConnection(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

    def init_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        # Record type selection dropdown
        self.record_type_dropdown = QComboBox(self)
        self.record_type_dropdown.addItems(["Live Birth", "Death", "Marriage"])
        self.record_type_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                color: #212121;
                border-radius: 4px;
                padding: 4px;
                border: 1px solid #D1D0D0;
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
        self.record_type_dropdown.currentIndexChanged.connect(self.update_keys_for_record_type)
        left_layout.addWidget(self.record_type_dropdown)

        # Key selection dropdown
        self.key_dropdown = QComboBox(self)
        self.key_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                color: #212121;
                border-radius: 4px;
                padding: 4px;
                border: 1px solid #D1D0D0;
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
        self.key_dropdown.currentIndexChanged.connect(self.update_filter_input_state)
        left_layout.addWidget(self.key_dropdown)

        # Date range type selection dropdown
        self.date_range_type_dropdown = QComboBox(self)
        self.date_range_type_dropdown.addItems(["Date of Event", "Date of Registration"])
        self.date_range_type_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                color: #212121;
                border-radius: 4px;
                padding: 4px;
                border: 1px solid #D1D0D0;
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
        self.date_range_type_dropdown.currentIndexChanged.connect(self.update_date_range_visibility)
        left_layout.addWidget(self.date_range_type_dropdown)

        # Date range label
        self.date_label = QLabel("Date of Event Range:", self)
        self.date_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #212121;
                margin-top: 10px;
            }
        """)
        left_layout.addWidget(self.date_label)
        self.start_date_input = QDateEdit(self)
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_input.setStyleSheet(date_picker_style)
        left_layout.addWidget(self.start_date_input)

        self.end_date_input = QDateEdit(self)
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setStyleSheet(date_picker_style)
        left_layout.addWidget(self.end_date_input)

        # Registration date range
        self.reg_date_label = QLabel("Registration Date Range:", self)
        self.reg_date_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #212121;
                margin-top: 10px;
            }
        """)
        left_layout.addWidget(self.reg_date_label)
        self.reg_start_date_input = QDateEdit(self)
        self.reg_start_date_input.setCalendarPopup(True)
        self.reg_start_date_input.setDate(QDate.currentDate().addMonths(-1))
        self.reg_start_date_input.setStyleSheet(date_picker_style)
        left_layout.addWidget(self.reg_start_date_input)

        self.reg_end_date_input = QDateEdit(self)
        self.reg_end_date_input.setCalendarPopup(True)
        self.reg_end_date_input.setDate(QDate.currentDate())
        self.reg_end_date_input.setStyleSheet(date_picker_style)
        left_layout.addWidget(self.reg_end_date_input)

        # Filter value input container
        filter_container = QVBoxLayout()
        self.filter_label = QLabel("Filter by Value (Optional):", self)
        self.filter_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #212121;
                margin-top: 10px;
            }
        """)
        filter_container.addWidget(self.filter_label)

        # Filter value input
        self.filter_value_input = QLineEdit(self)
        self.filter_value_input.setPlaceholderText("Filter by Value (Optional): ")
        self.filter_value_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                color: #212121;
                border-radius: 4px;
                padding: 6px;
                border: 1px solid #D1D0D0;
            }
            QLineEdit:focus {
                border: 1px solid #ce305e;
                background-color: #fef2f4;
            }
        """)
        filter_container.addWidget(self.filter_value_input)

        # Age range inputs (hidden by default, shown for age fields)
        age_range_label = QLabel("Age Range:", self)
        age_range_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #212121;
                margin-top: 10px;
            }
        """)
        age_range_label.hide()
        self.age_range_label = age_range_label
        filter_container.addWidget(age_range_label)

        age_range_layout = QHBoxLayout()
        age_range_layout.setSpacing(10)
        
        self.min_age_input = QSpinBox(self)
        self.min_age_input.setMinimum(0)
        self.min_age_input.setMaximum(150)
        self.min_age_input.setValue(0)
        self.min_age_input.setPrefix("Min: ")
        self.min_age_input.setSuffix(" years")
        self.min_age_input.setStyleSheet("""
            QSpinBox {
                background-color: #FFFFFF;
                color: #212121;
                border-radius: 4px;
                padding: 6px;
                border: 1px solid #D1D0D0;
            }
            QSpinBox:focus {
                border: 1px solid #ce305e;
                background-color: #fef2f4;
            }
        """)
        self.min_age_input.hide()
        age_range_layout.addWidget(self.min_age_input)

        self.max_age_input = QSpinBox(self)
        self.max_age_input.setMinimum(0)
        self.max_age_input.setMaximum(150)
        self.max_age_input.setValue(150)
        self.max_age_input.setPrefix("Max: ")
        self.max_age_input.setSuffix(" years")
        self.max_age_input.setStyleSheet("""
            QSpinBox {
                background-color: #FFFFFF;
                color: #212121;
                border-radius: 4px;
                padding: 6px;
                border: 1px solid #D1D0D0;
            }
            QSpinBox:focus {
                border: 1px solid #ce305e;
                background-color: #fef2f4;
            }
        """)
        self.max_age_input.hide()
        age_range_layout.addWidget(self.max_age_input)

        filter_container.addLayout(age_range_layout)
        left_layout.addLayout(filter_container)

        # Resident filters (for birth and death records)
        resident_label = QLabel("Resident Filters (Optional):", self)
        resident_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #212121;
                margin-top: 10px;
            }
        """)
        left_layout.addWidget(resident_label)

        # Maasin resident checkbox
        self.maasin_resident_cb = QCheckBox("Maasin Resident", self)
        self.maasin_resident_cb.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #212121;
                margin-left: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
        """)
        left_layout.addWidget(self.maasin_resident_cb)

        # Soley te resident checkbox
        self.soleyte_resident_cb = QCheckBox("Soleyte Resident", self)
        self.soleyte_resident_cb.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #212121;
                margin-left: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
        """)
        left_layout.addWidget(self.soleyte_resident_cb)

        # Leyte resident checkbox
        self.leyte_resident_cb = QCheckBox("Leyte Resident", self)
        self.leyte_resident_cb.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #212121;
                margin-left: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
        """)
        left_layout.addWidget(self.leyte_resident_cb)

        # Connect record type change to show/hide resident filters
        self.record_type_dropdown.currentIndexChanged.connect(self.update_resident_filters_visibility)

        generate_btn = QPushButton("Generate Statistics", self)
        generate_btn.clicked.connect(self.generate_statistics)
        generate_btn.setStyleSheet(button_style)
        left_layout.addWidget(generate_btn)

        export_pdf_btn = QPushButton("Export Report as PDF", self)
        export_pdf_btn.clicked.connect(self.export_pdf_report)
        export_pdf_btn.setStyleSheet(button_style)
        left_layout.addWidget(export_pdf_btn)

        # Result display area
        result_label = QLabel("Total Count:", self)
        result_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #212121;
                margin-top: 20px;
            }
        """)
        left_layout.addWidget(result_label)

        self.result_display = QLabel("0", self)
        self.result_display.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #ce305e;
                padding: 20px;
                border: 2px solid #ce305e;
                border-radius: 8px;
                background-color: #fef2f4;
                min-height: 80px;
            }
        """)
        self.result_display.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.result_display)

        # Add spacer to push content to top
        left_layout.addStretch()

        main_layout.addLayout(left_layout)
        self.setLayout(main_layout)

        self.update_keys_for_record_type()  # Set initial keys
        self.update_filter_input_state()  # Set initial filter input state
        self.update_resident_filters_visibility()  # Set initial resident filters visibility
        self.update_date_range_visibility()  # Set initial date range visibility

    def update_date_range_visibility(self):
        """Show/hide date range inputs based on selected date range type."""
        date_range_type = self.date_range_type_dropdown.currentText()
        
        if date_range_type == "Date of Event":
            # Show event date range, hide registration date range
            self.date_label.show()
            self.start_date_input.show()
            self.end_date_input.show()
            self.reg_date_label.hide()
            self.reg_start_date_input.hide()
            self.reg_end_date_input.hide()
        else:  # Date of Registration
            # Hide event date range, show registration date range
            self.date_label.hide()
            self.start_date_input.hide()
            self.end_date_input.hide()
            self.reg_date_label.show()
            self.reg_start_date_input.show()
            self.reg_end_date_input.show()
        
        # Update the date labels to reflect current record type
        self.update_date_labels()
    
    def update_date_labels(self):
        """Update date labels based on record type and date range type selection."""
        record_type = self.record_type_dropdown.currentText()
        date_range_type = self.date_range_type_dropdown.currentText()
        
        # Map record type to date field names
        date_field_map = {
            "Live Birth": "Birth",
            "Death": "Death",
            "Marriage": "Marriage"
        }
        date_field = date_field_map.get(record_type, "Event")
        
        if date_range_type == "Date of Event":
            self.date_label.setText(f"Date of {date_field} Range:")
        else:  # Date of Registration
            self.reg_date_label.setText("Registration Date Range:")

    def update_resident_filters_visibility(self):
        """Show/hide resident filters based on record type."""
        record_type = self.record_type_dropdown.currentText()
        # Show resident filters for birth and death records, hide for marriage
        show_residents = record_type in ["Live Birth", "Death"]
        
        self.maasin_resident_cb.setVisible(show_residents)
        self.soleyte_resident_cb.setVisible(show_residents)
        self.leyte_resident_cb.setVisible(show_residents)
        
        # Also hide/show the resident label
        # Find the resident label in the layout
        for i in range(self.layout().itemAt(0).layout().count()):
            item = self.layout().itemAt(0).layout().itemAt(i)
            if item.widget() and hasattr(item.widget(), 'text') and item.widget().text() == "Resident Filters (Optional):":
                item.widget().setVisible(show_residents)
                break

    def update_filter_input_state(self):
        """Enable or disable filter input based on selected key."""
        selected_key = self.key_dropdown.currentText().strip()
        selected_key_lower = selected_key.lower()
        
        if selected_key == "Late Registration":
            # Hide text filter, show only age range (if applicable)
            self.filter_value_input.hide()
            self.filter_label.hide()
            # For late registration, let the date range type dropdown control visibility
            # The date_range_visibility is already managed by the date_range_type_dropdown
            self.age_range_label.hide()
            self.min_age_input.hide()
            self.max_age_input.hide()
        elif selected_key_lower in ["age", "husband age", "wife age"]:
            # Show age range inputs, hide text input
            self.filter_value_input.hide()
            self.filter_label.hide()
            self.age_range_label.show()
            self.min_age_input.show()
            self.max_age_input.show()
        else:
            # Show text input, hide age range inputs
            self.filter_value_input.show()
            self.filter_label.show()
            # The date range visibility is managed by the date_range_type_dropdown
            self.age_range_label.hide()
            self.min_age_input.hide()
            self.max_age_input.hide()

    def update_keys_for_record_type(self):
        record_type = self.record_type_dropdown.currentText()
        self.key_dropdown.clear()
        if record_type == "Live Birth":
            self.key_dropdown.addItems([
                "Name", "Sex", "Place of Birth", "Name of Mother", "Name of Father", "Nationality of Mother", "Nationality of Father", "Attendant", "Type of Birth", "Late Registration" 
            ])
        elif record_type == "Death":
            self.key_dropdown.addItems([
                "Name", "Sex", "Age", "Civil Status", "Nationality", "Place of Death", "Cause of Death", "Corpse Disposal", "Late Registration"
            ])
        elif record_type == "Marriage":
            self.key_dropdown.addItems([
                "Husband Name", "Husband Age", "Husband Civil Status", "Husband Nationality", "Wife Name", "Wife Age", "Wife Civil Status", "Wife Nationality", "Place of Marriage", "Ceremony Type", "Late Registration"
            ])
        
        # Update date labels based on record type change
        self.update_date_labels()

    def _get_table_and_date_field(self, record_type):
        """Get database table and date field name for a record type."""
        table_map = {
            "Live Birth": ("birth_index", "date_of_birth"),
            "Death": ("death_index", "date_of_death"),
            "Marriage": ("marriage_index", "date_of_marriage")
        }
        return table_map.get(record_type, ("birth_index", "date_of_birth"))

    def _build_query_with_filter(self, table, date_field, column, selected_key, record_type, start_date, end_date, filter_value=None, min_age=None, max_age=None, reg_start_date=None, reg_end_date=None, maasin_resident=None, soleyte_resident=None, leyte_resident=None, use_registration_date=False):
        """Build SQL query with scoped filters.
        
        Args:
            use_registration_date: If True, filters by registration date (date_of_reg) instead of event date
        """
        
        # Determine which date field to use
        if use_registration_date:
            active_date_field = "date_of_reg"
        else:
            active_date_field = date_field
        
        # CASE 1: Late Registration (Focuses primarily on the Registration Date)
        if selected_key == "Late Registration":
            query_params = [start_date, end_date]
            base_query = f'SELECT COUNT(*) FROM "{table}" WHERE DATE("{active_date_field}") BETWEEN %s::date AND %s::date'
            base_query += f' AND "{column}" = TRUE'
            return base_query, tuple(query_params)
        
        # CASE 2: Standard Key Filtering (Age, Name, etc.)
        query_params = [start_date, end_date]
        base_query = f'SELECT COUNT(*) FROM "{table}" WHERE DATE("{active_date_field}") BETWEEN %s::date AND %s::date'
        
        # Handle age range fields
        selected_key_lower = selected_key.lower()
        if selected_key_lower in ["age", "husband age", "wife age"]:
            if min_age is not None and max_age is not None:
                base_query += f' AND "{column}" BETWEEN %s AND %s'
                query_params.extend([min_age, max_age])
            return base_query, tuple(query_params)
        
        # Handle Text/Name Filters
        if filter_value:
            name_fields = {
                "Live Birth": ["Name", "Name of Mother", "Name of Father"],
                "Death": ["Name"],
                "Marriage": ["Husband Name", "Wife Name"]
            }
            
            if record_type in name_fields and selected_key in name_fields[record_type]:
                base_query += f' AND "{column}" ~* %s'
                query_params.append(rf'\y{filter_value}\y') 
            elif selected_key in ["Sex", "Type of Birth", "Civil Status"]:
                base_query += f' AND "{column}" ILIKE %s'
                query_params.append(filter_value)
            else:
                base_query += f' AND "{column}" ILIKE %s AND "{column}" IS NOT NULL'
                query_params.append(f'%{filter_value}%')
        
        # Apply resident filters (only for birth and death records)
        if record_type in ["Live Birth", "Death"]:
            if maasin_resident is True:
                base_query += f' AND "maasin_resident" = TRUE'
            if soleyte_resident is True:
                base_query += f' AND "soleyte_resident" = TRUE'
            if leyte_resident is True:
                base_query += f' AND "leyte_resident" = TRUE'
                
        return base_query, tuple(query_params)

    def generate_statistics(self):
        record_type = self.record_type_dropdown.currentText()
        selected_key = self.key_dropdown.currentText().strip()
        filter_value = self.filter_value_input.text().strip() if self.filter_value_input.isVisible() else None
        
        # Get age range values if age field is selected
        min_age = self.min_age_input.value() if "age" in selected_key.lower() else None
        max_age = self.max_age_input.value() if "age" in selected_key.lower() else None
        
        # Get resident filter values (only for birth and death records)
        maasin_resident = self.maasin_resident_cb.isChecked() if self.maasin_resident_cb.isVisible() else None
        soleyte_resident = self.soleyte_resident_cb.isChecked() if self.soleyte_resident_cb.isVisible() else None
        leyte_resident = self.leyte_resident_cb.isChecked() if self.leyte_resident_cb.isVisible() else None
        
        # Get date range based on user selection
        date_range_type = self.date_range_type_dropdown.currentText()
        if date_range_type == "Date of Event":
            start_date = self.start_date_input.date().toString("yyyy-MM-dd")
            end_date = self.end_date_input.date().toString("yyyy-MM-dd")
            reg_start_date = None
            reg_end_date = None
        else:  # Date of Registration
            start_date = self.reg_start_date_input.date().toString("yyyy-MM-dd")
            end_date = self.reg_end_date_input.date().toString("yyyy-MM-dd")
            reg_start_date = start_date
            reg_end_date = end_date

        conn = self.create_connection()
        try:
            if not selected_key:
                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "STATISTICS_GENERATION_FAILED",
                    {"reason": "no_key_selected"}
                )
                conn.commit()
                QMessageBox.warning(self, "Error", "Please select a valid key!")
                return

            AuditLogger.log_action(
                conn,
                self.current_user,
                "STATISTICS_GENERATION_STARTED",
                {
                    "record_type": record_type,
                    "key": selected_key,
                    "filter_value": filter_value if filter_value else None,
                    "min_age": min_age,
                    "max_age": max_age,
                    "start_date": start_date,
                    "end_date": end_date,
                    "reg_start_date": reg_start_date,
                    "reg_end_date": reg_end_date,
                    "maasin_resident": maasin_resident,
                    "soleyte_resident": soleyte_resident,
                    "leyte_resident": leyte_resident
                }
            )
            conn.commit()

            cursor = conn.cursor()

            # Get table and date field - validated against known values
            table, date_field = self._get_table_and_date_field(record_type)

            # Get column name - validated through KEY_COLUMN_MAP
            column = self.KEY_COLUMN_MAP.get(selected_key)
            if not column:
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Warning)
                box.setWindowTitle("Statistics Error")
                box.setText(f"No column mapping for key: {selected_key}")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                return

            # Validate table and column names to prevent SQL injection
            # Only allow alphanumeric and underscore characters
            if not all(c.isalnum() or c == '_' for c in table):
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle("Security Error")
                box.setText("Invalid table name")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                return
            if not all(c.isalnum() or c == '_' for c in column):
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle("Security Error")
                box.setText("Invalid column name")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                return
            if not all(c.isalnum() or c == '_' for c in date_field):
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle("Security Error")
                box.setText("Invalid date field name")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                return

            try:
                # Build query with optional filter value or age range
                # Determine if we should use registration date based on date_range_type
                use_registration_date = (date_range_type == "Date of Registration")
                try:
                    query, query_params = self._build_query_with_filter(
                        table, date_field, column, selected_key, record_type, start_date, end_date, 
                        filter_value, min_age, max_age, reg_start_date, reg_end_date,
                        maasin_resident, soleyte_resident, leyte_resident, use_registration_date
                    )
                except ValueError as ve:
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Warning)
                    box.setWindowTitle("Invalid Input")
                    box.setText(str(ve))
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                    return

                cursor.execute(query, query_params)
                result = cursor.fetchone()
                total_count = result[0] if result else 0

                if total_count == 0:
                    # Build filter info message
                    if selected_key in ["age", "husband age", "wife age"] and min_age is not None and max_age is not None:
                        filter_info = f" in age range {min_age}-{max_age}"
                    elif filter_value:
                        filter_info = f" matching '{filter_value}'"
                    else:
                        filter_info = ""
                    
                    AuditLogger.log_action(
                        conn,
                        self.current_user,
                        "STATISTICS_NO_DATA",
                        {
                            "record_type": record_type,
                            "key": selected_key,
                            "filter_value": filter_value if filter_value else None,
                            "min_age": min_age,
                            "max_age": max_age,
                            "start_date": start_date,
                            "end_date": end_date,
                            "reg_start_date": reg_start_date,
                            "reg_end_date": reg_end_date,
                            "maasin_resident": maasin_resident,
                            "soleyte_resident": soleyte_resident,
                            "leyte_resident": leyte_resident
                        }
                    )
                    conn.commit()
                    
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Information)
                    box.setWindowTitle("No Data")
                    box.setText(f"No records found for '{selected_key}'{filter_info} in the selected date range.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()

                    self.result_display.setText("0")
                else:
                    AuditLogger.log_action(
                        conn,
                        self.current_user,
                        "STATISTICS_GENERATED",
                        {
                            "record_type": record_type,
                            "key": selected_key,
                            "filter_value": filter_value if filter_value else None,
                            "min_age": min_age,
                            "max_age": max_age,
                            "record_count": total_count,
                            "start_date": start_date,
                            "end_date": end_date,
                            "reg_start_date": reg_start_date,
                            "reg_end_date": reg_end_date
                        }
                    )
                    conn.commit()
                    # Update display with total count
                    self.result_display.setText(str(total_count))

            except psycopg2.Error as e:
                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "DATABASE_ERROR",
                    {
                        "operation": "generate_statistics",
                        "error": str(e),
                        "key": selected_key,
                        "filter_value": filter_value if filter_value else None,
                        "min_age": min_age,
                        "max_age": max_age,
                        "reg_start_date": reg_start_date,
                        "reg_end_date": reg_end_date
                    }
                )
                conn.commit()
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle("Database Error")
                box.setText(f"An error occurred: {str(e)}")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                self.result_display.setText("0")

        finally:
            self.closeConnection()


    def export_pdf_report(self):
        record_type = self.record_type_dropdown.currentText()
        selected_key = self.key_dropdown.currentText().strip()
        filter_value = self.filter_value_input.text().strip() if self.filter_value_input.isVisible() else None
        
        # Get age range values if age field is selected
        selected_key_lower = selected_key.lower()
        min_age = None
        max_age = None
        if selected_key_lower in ["age", "husband age", "wife age"]:
            min_age = self.min_age_input.value()
            max_age = self.max_age_input.value()
        
        # Get resident filter values (only for birth and death records)
        maasin_resident = self.maasin_resident_cb.isChecked() if self.maasin_resident_cb.isVisible() else None
        soleyte_resident = self.soleyte_resident_cb.isChecked() if self.soleyte_resident_cb.isVisible() else None
        leyte_resident = self.leyte_resident_cb.isChecked() if self.leyte_resident_cb.isVisible() else None
        
        # Get date range based on user selection
        date_range_type = self.date_range_type_dropdown.currentText()
        if date_range_type == "Date of Event":
            start_date = self.start_date_input.date().toString("yyyy-MM-dd")
            end_date = self.end_date_input.date().toString("yyyy-MM-dd")
            reg_start_date = None
            reg_end_date = None
        else:  # Date of Registration
            start_date = self.reg_start_date_input.date().toString("yyyy-MM-dd")
            end_date = self.reg_end_date_input.date().toString("yyyy-MM-dd")
            reg_start_date = start_date
            reg_end_date = end_date

        conn = self.create_connection()
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", "", "PDF Files (*.pdf)")
            if not file_path:
                return

            if not selected_key:
                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "PDF_EXPORT_FAILED",
                    {"reason": "no_key_selected"}
                )
                conn.commit()
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Warning)
                box.setWindowTitle("Error")
                box.setText("Please select a valid key!")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                return

            # Get table and date field
            table, date_field = self._get_table_and_date_field(record_type)

            # Get column name
            column = self.KEY_COLUMN_MAP.get(selected_key)
            if not column:
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Warning)
                box.setWindowTitle("Error")
                box.setText(f"No column mapping for key: {selected_key}")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                return

            # Validate table and column names to prevent SQL injection
            if not all(c.isalnum() or c == '_' for c in table):
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle("Security Error")
                box.setText("Invalid table name")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                return
            if not all(c.isalnum() or c == '_' for c in column):
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle("Security Error")
                box.setText("Invalid column name")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                return
            if not all(c.isalnum() or c == '_' for c in date_field):
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle("Security Error")
                box.setText("Invalid date field name")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                return

            try:
                cursor = conn.cursor()
                # Build query with optional filter value or age range
                # Determine if we should use registration date based on date_range_type
                use_registration_date = (date_range_type == "Date of Registration")
                try:
                    query, query_params = self._build_query_with_filter(
                        table, date_field, column, selected_key, record_type, start_date, end_date, 
                        filter_value, min_age, max_age, reg_start_date, reg_end_date,
                        maasin_resident, soleyte_resident, leyte_resident, use_registration_date
                    )
                except ValueError as ve:
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Warning)
                    box.setWindowTitle("Invalid Input")
                    box.setText(str(ve))
                    box.setStandardButtons(QMessageBox.Ok)
                    box.setStyleSheet(message_box_style)
                    box.exec()
                    return

                cursor.execute(query, query_params)
                result = cursor.fetchone()
                total_count = result[0] if result else 0

                # Generate simple text-based PDF report
                c = pdf_canvas.Canvas(file_path, pagesize=letter)
                width, height = letter

                # Title
                c.setFont("Helvetica-Bold", 20)
                c.drawString(1 * inch, height - 1 * inch, "Statistics Report")

                # Report details
                y_position = height - 1.5 * inch
                c.setFont("Helvetica", 12)
                c.drawString(1 * inch, y_position, f"Record Type: {record_type}")
                y_position -= 0.3 * inch
                c.drawString(1 * inch, y_position, f"Selected Key: {selected_key}")
                y_position -= 0.3 * inch
                if selected_key_lower in ["age", "husband age", "wife age"] and min_age is not None and max_age is not None:
                    c.drawString(1 * inch, y_position, f"Age Range: {min_age} - {max_age} years")
                    y_position -= 0.3 * inch
                elif filter_value:
                    c.drawString(1 * inch, y_position, f"Filter Value: {filter_value}")
                    y_position -= 0.3 * inch
                c.drawString(1 * inch, y_position, f"Event Date Range: {start_date} to {end_date}")
                y_position -= 0.3 * inch
                if reg_start_date and reg_end_date:
                    c.drawString(1 * inch, y_position, f"Registration Date Range: {reg_start_date} to {reg_end_date}")
                    y_position -= 0.3 * inch
                y_position -= 0.5 * inch

                # Total count
                c.setFont("Helvetica-Bold", 16)
                c.drawString(1 * inch, y_position, "Total Count:")
                y_position -= 0.4 * inch
                c.setFont("Helvetica-Bold", 24)
                c.drawString(1 * inch, y_position, str(total_count))
                y_position -= 0.5 * inch

                # Footer
                c.setFont("Helvetica", 10)
                c.drawString(1 * inch, 0.5 * inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                c.drawString(1 * inch, 0.3 * inch, f"Generated by: {self.current_user}")

                c.save()

                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "PDF_EXPORT_SUCCESS",
                    {
                        "record_type": record_type,
                        "key": selected_key,
                        "filter_value": filter_value if filter_value else None,
                        "min_age": min_age,
                        "max_age": max_age,
                        "file_path": file_path,
                        "total_count": total_count,
                        "start_date": start_date,
                        "end_date": end_date,
                        "reg_start_date": reg_start_date,
                        "reg_end_date": reg_end_date
                    }
                )
                conn.commit()
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Information)
                box.setWindowTitle("Success")
                box.setText(f"PDF report exported successfully!\nTotal Count: {total_count}")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()
                

            except Exception as e:
                AuditLogger.log_action(
                    conn,
                    self.current_user,
                    "PDF_EXPORT_ERROR",
                    {
                        "error": str(e),
                        "record_type": record_type,
                        "key": selected_key,
                        "filter_value": filter_value if filter_value else None,
                        "min_age": min_age,
                        "max_age": max_age,
                        "reg_start_date": reg_start_date,
                        "reg_end_date": reg_end_date,
                        "file_path": file_path
                    }
                )
                conn.commit()
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle("Export Error")
                box.setText(f"Failed to export PDF: {str(e)}")
                box.setStandardButtons(QMessageBox.Ok)
                box.setStyleSheet(message_box_style)
                box.exec()

        finally:
            self.closeConnection()

    def showEvent(self, event):
        super().showEvent(event)
        conn = self.create_connection()
        try:
            AuditLogger.log_action(
                conn,
                self.current_user,
                "WINDOW_OPENED",
                {"window": "StatisticsWindow"}
            )
            conn.commit()
        finally:
            self.closeConnection()

    def closeEvent(self, event):
        conn = self.create_connection()
        try:
            AuditLogger.log_action(
                conn,
                self.current_user,
                "WINDOW_CLOSED",
                {"window": "StatisticsWindow"}
            )
            conn.commit()
        finally:
            self.closeConnection()
            event.ignore()
            self.hide()