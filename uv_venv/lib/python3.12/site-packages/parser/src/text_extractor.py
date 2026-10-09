import fitz

class TextExtractor:
    def __init__(self, loader):
        self.loader = loader

    def get_blocks(self, page_num):
        page = self.loader.doc.load_page(page_num)
        return page.get_text("blocks")

    def get_words(self, page_num):
        page = self.loader.doc.load_page(page_num)
        return page.get_text("words")

    def get_dict(self, page_num):
        page = self.loader.doc.load_page(page_num)
        return page.get_text("dict")
        
    def get_drawings(self, page_num):
        page = self.loader.doc.load_page(page_num)
        return page.get_drawings()
        
    def get_page_dimensions(self, page_num):
        page = self.loader.doc.load_page(page_num)
        return {"width": page.rect.width, "height": page.rect.height}
