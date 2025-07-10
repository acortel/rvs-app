import sqlite3
import os
import pymupdf  
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QPixmap, QImage, QIcon
# from stylesheets import button_style
# from tagging import TaggingWindow
# from stats import StatisticsWindow

class StatsDatabase(QMainWindow):
    """Main window to navigate between Tagging and Statistics."""
    def __init__(self):
        super().__init__()
        # self.init_ui()
        self.db = self.init_db()

    # def init_ui(self):
    #     self.setWindowTitle("Statistics Tools")
    #     self.setGeometry(100, 100, 400, 50)

    #     self.setMaximumSize(self.size())

    #     self.setWindowIcon(QIcon("icons/analytics.png"))

    #     layout = QVBoxLayout()

    #     tagging_btn = QPushButton("Open Tagging Section", self)
    #     tagging_btn.clicked.connect(self.open_tagging_window)
    #     layout.addWidget(tagging_btn)

    #     icon1 = QIcon("icons/tags.png")  
    #     tagging_btn.setIcon(icon1)
    #     tagging_btn.setStyleSheet(button_style)

    #     stats_btn = QPushButton("Open Statistics Section", self)
    #     stats_btn.clicked.connect(self.open_statistics_window)
    #     layout.addWidget(stats_btn)

    #     icon2 = QIcon("icons/generate.png")  
    #     stats_btn.setIcon(icon2)
    #     stats_btn.setStyleSheet(button_style)

    #     container = QWidget()
    #     container.setLayout(layout)
    #     self.setCentralWidget(container)

    def init_db(self):
        conn = sqlite3.connect("stats_index.db")  # Connect to new database
        cursor = conn.cursor()

        # Create the 'stats_index_birth' table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats_index_birth (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE,
                date TEXT,
                sex TEXT,
                place_of_birth TEXT,
                twin INTEGER,
                age_of_mother INTEGER,
                legitimate INTEGER
            );
        """)

        # Create the 'stats_index_death' table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats_index_death (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE,
                date TEXT,
                sex TEXT,
                place_of_death TEXT,
                cause_of_death TEXT
            );
        """)

        # Create the 'stats_index_marriage' table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats_index_marriage (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE,
                date TEXT,
                place_of_marriage TEXT,
                age_of_husband INTEGER,
                age_of_wife INTEGER,
                religious INTEGER
            );
        """)

        conn.commit()
        return conn

    # def open_tagging_window(self):
    #     self.tagging_window = TaggingWindow(self.db)
    #     self.tagging_window.showMaximized()

    # def open_statistics_window(self):
    #     self.statistics_window = StatisticsWindow(self.db)
    #     self.statistics_window.showMaximized()

    # def closeEvent(self, event):
    #     if self.tagging_window:
    #         self.tagging_window.close()
    #     if self.statistics_window:
    #         self.statistics_window.close()
    #     super().closeEvent(event)