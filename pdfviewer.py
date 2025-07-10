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
from stylesheets import button_style

class PDFViewer(QScrollArea):
    """PDF Viewer with zoom support."""
    def __init__(self, parent=None):
        super().__init__(parent)      
        self.setWidgetResizable(True)
        self.pdf_widget = QWidget()
        self.pdf_layout = QVBoxLayout(self.pdf_widget)
        self.setWidget(self.pdf_widget)

        self.zoom_factor = 1.0
        self.current_file = None

    def load_pdf(self, file_path):
        """Loads and displays the PDF with zoom scaling."""
        self.current_file = file_path
        self.render_pdf()

    def render_pdf(self):
        """Renders the PDF based on the current zoom factor."""
        try:
            if not self.current_file:
                return

            # Open the PDF file
            doc = pymupdf.open(self.current_file)
            self.clear_pdf()
            dpi = 72 * self.zoom_factor  # Adjust DPI based on zoom factor

            for page_number in range(len(doc)):
                page = doc[page_number]
                matrix = pymupdf.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=matrix)
                image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)

                label = QLabel()
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                self.pdf_layout.addWidget(label)
        except Exception as e:
            print(f"Error rendering PDF: {e}")
            label = QLabel("Unable to load PDF.")
            label.setAlignment(Qt.AlignCenter)
            self.pdf_layout.addWidget(label)

    def clear_pdf(self):
        """Clears the current PDF view."""
        while self.pdf_layout.count():
            widget = self.pdf_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def set_zoom(self, zoom_factor):
        """Updates the zoom factor and re-renders the PDF."""
        self.zoom_factor = zoom_factor
        self.render_pdf()  # Re-render the PDF with the updated zoom factor