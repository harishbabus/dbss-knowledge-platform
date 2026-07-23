import json
import zipfile

from pathlib import Path

from openpyxl import load_workbook


import fitz
from docx import Document
from pptx import Presentation
from PIL import Image
import pytesseract

from app.utils.logger import logger


class AttachmentContentExtractor:

    def __init__(self):

        self.download_folder = Path("downloads")

    def extract(self, attachment):

        filename = attachment.filename

        file_path = self.download_folder / filename

        if not file_path.exists():

            logger.warning(f"File not found: {file_path}")

            return None

        media_type = attachment.media_type or ""

        try:

            extension = file_path.suffix.lower()

            if extension == ".xlsx":

                return self._extract_excel(file_path)

            if extension == ".csv":

                return self._extract_csv(file_path)

            if extension == ".json":

                return self._extract_json(file_path)

            if extension == ".zip":

                return self._extract_zip(file_path)

            if extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:

                return self._extract_image(file_path)

            if extension == ".pdf":

                return self._extract_pdf(file_path)

            if extension == ".docx":

                return self._extract_docx(file_path)

            if extension == ".pptx":

                return self._extract_pptx(file_path)

            if extension in [".ldif", ".txt", ".xml"]:

                return self._extract_text(file_path)

            if media_type == "application/octet-stream":

                return self._extract_text(file_path)

            logger.warning(f"Unsupported attachment type: {media_type}")

            return None

        except Exception as e:

            logger.error(f"Failed extracting {filename}: {e}")

            return None

    def _extract_excel(self, file_path):

        logger.info(f"Reading Excel: {file_path}")

        workbook = load_workbook(filename=file_path, data_only=True)

        content = []

        for sheet in workbook.sheetnames:

            content.append(f"\nSheet: {sheet}\n")

            worksheet = workbook[sheet]

            for row in worksheet.iter_rows(values_only=True):

                values = [str(cell) for cell in row if cell is not None]

                if values:

                    content.append(" | ".join(values))

        return {"text": "\n".join(content), "content_type": "excel"}

    def _extract_csv(self, file_path):

        logger.info(f"Reading CSV: {file_path}")

        text = file_path.read_text(encoding="utf-8", errors="ignore")

        return {"text": text, "content_type": "csv"}

    def _extract_json(self, file_path):

        logger.info(f"Reading JSON: {file_path}")

        data = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))

        return {"text": json.dumps(data, indent=2), "content_type": "json"}

    def _extract_text(self, file_path):

        logger.info(f"Reading text: {file_path}")

        return {
            "text": file_path.read_text(encoding="utf-8", errors="ignore"),
            "content_type": file_path.suffix.lower().replace(".", ""),
        }

    def _extract_pdf(self, file_path):

        logger.info(f"Reading PDF: {file_path}")

        document = fitz.open(file_path)

        content = []

        for page in document:

            text = page.get_text()

            if text:

                content.append(text)

        return {"text": "\n".join(content), "content_type": "pdf"}

    def _extract_docx(self, file_path):

        logger.info(f"Reading DOCX: {file_path}")

        document = Document(file_path)

        content = []

        for paragraph in document.paragraphs:

            if paragraph.text:

                content.append(paragraph.text)

        return {"text": "\n".join(content), "content_type": "docx"}

    def _extract_pptx(self, file_path):

        logger.info(f"Reading PPTX: {file_path}")

        presentation = Presentation(file_path)

        content = []

        for slide in presentation.slides:

            for shape in slide.shapes:

                if hasattr(shape, "text"):

                    if shape.text:

                        content.append(shape.text)

        return {"text": "\n".join(content), "content_type": "pptx"}

    def _extract_image(self, file_path):

        logger.info(f"Reading image: {file_path}")

        image = Image.open(file_path)

        text = pytesseract.image_to_string(image)

        width, height = image.size

        return {
            "text": text,
            "content_type": "image",
            "file_path": str(file_path),
            "metadata": {"width": width, "height": height, "format": image.format},
        }

    def _extract_zip(self, file_path):

        logger.info(f"Reading ZIP: {file_path}")

        content = []

        with zipfile.ZipFile(file_path, "r") as zip_file:

            for name in zip_file.namelist():

                if name.endswith("/"):

                    continue

                try:

                    data = zip_file.read(name).decode("utf-8", errors="ignore")

                    content.append(f"\nFILE: {name}\n")

                    content.append(data)

                except Exception:

                    logger.warning(f"Skipping binary file in zip: {name}")

                    continue

        return {"text": "\n".join(content), "content_type": "zip"}
