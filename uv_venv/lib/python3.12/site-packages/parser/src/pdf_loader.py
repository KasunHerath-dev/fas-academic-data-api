import fitz  # PyMuPDF
import pdfplumber
import os

class PDFLoader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.doc = None
        self.plumber_pdf = None

    def load(self):
        self.doc = fitz.open(self.filepath)
        self.plumber_pdf = pdfplumber.open(self.filepath)

    def close(self):
        if self.doc:
            self.doc.close()
        if self.plumber_pdf:
            self.plumber_pdf.close()

    def get_metadata(self):
        if not self.doc:
            return {}
        return self.doc.metadata

    def get_page_count(self):
        if not self.doc:
            return 0
        return len(self.doc)

    def render_page_to_image(self, page_num, output_path, zoom_x=2.0, zoom_y=2.0):
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return False
        page = self.doc.load_page(page_num)
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat)
        pix.save(output_path)
        return True
