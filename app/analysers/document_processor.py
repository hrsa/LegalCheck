import os
import subprocess

import ezodf
import fitz
import docx
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


class DocumentProcessor:
    def __init__(self):
        pass

    def process_document(self, file_path) -> str:
        extension = os.path.splitext(file_path)[1].lower()

        if extension in [".pdf"]:
            text = self.process_pdf(file_path)
        elif extension in [".txt"]:
            text = self.process_txt(file_path)
        elif extension in [".doc", ".docx"]:
            text = self.process_doc(file_path)
        elif extension in [".odt"]:
            text = self.process_odt(file_path)
        elif extension in [".jpg", ".jpeg", ".png"]:
            text = self.process_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")

        if not text.strip():
            raise ValueError(f"No text extracted from document: {file_path}")

        print(text)
        return text

    @staticmethod
    def process_pdf(file_path):
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()

        if text.strip():
            return text.strip()

        # PDF likely image-based: OCR needed
        images = convert_from_path(file_path)
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img)
        return ocr_text.strip()

    @staticmethod
    def process_txt(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()

    @staticmethod
    def process_doc(file_path):
        if file_path.lower().endswith(".docx"):
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs]).strip()
        elif file_path.lower().endswith(".doc"):
            try:
                process = subprocess.run(['antiword', file_path], capture_output=True, text=True, check=True)
                text = process.stdout
                return text.strip()
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"antiword failed: {e}")
        else:
            raise ValueError("Unsupported Word format.")

    @staticmethod
    def process_odt(file_path):
        odt_doc = ezodf.opendoc(file_path)
        doc_text = []
        for elem in odt_doc.body:
            if elem.text:
                doc_text.append(elem.text)
        return "\n".join(doc_text).strip()


    @staticmethod
    def process_image(file_path):
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text.strip()