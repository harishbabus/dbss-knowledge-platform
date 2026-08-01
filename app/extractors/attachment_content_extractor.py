import json
import zipfile

from pathlib import Path
from app.models.content_type import ContentType
from app.models.extracted_content import ExtractedContent
from app.utils.logger import logger


class AttachmentContentExtractor:
    def __init__(self):
        self.download_folder = Path("downloads")
        self.extractors = self._build_extractor_registry()

    def _build_extractor_registry(self):
        """
        Maps file extensions to extractor functions.
        """

        return {
            ".xlsx": self._extract_excel,
            ".csv": self._extract_csv,
            ".json": self._extract_json,
            ".zip": self._extract_zip,
            ".pdf": self._extract_pdf,
            ".docx": self._extract_docx,
            ".pptx": self._extract_ppt,
            ".png": self._extract_image,
            ".jpg": self._extract_image,
            ".jpeg": self._extract_image,
            ".gif": self._extract_image,
            ".bmp": self._extract_image,
            ".tif": self._extract_image,
            ".tiff": self._extract_image,
        }

    def extract(self, attachment):
        filename = attachment.filename

        file_path = self.download_folder / filename

        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")

            return None

        try:
            extension = file_path.suffix.lower()

            extractor = self.extractors.get(extension)

            if extractor:
                return extractor(file_path)

            logger.warning(f"No extractor for {extension}")

            return None

        except Exception as e:
            logger.error(f"Failed extracting {filename}: {e}")

            return None

    def _extract_excel(self, file_path):
        logger.info(f"Reading Excel: {file_path}")

        from openpyxl import load_workbook

        workbook = load_workbook(filename=file_path, data_only=True)

        content = []

        for sheet in workbook.sheetnames:
            content.append(f"\nSheet: {sheet}\n")

            worksheet = workbook[sheet]

            for row in worksheet.iter_rows(values_only=True):
                values = [str(cell) for cell in row if cell is not None]

                if values:
                    content.append(" | ".join(values))

        return ExtractedContent(
            text="\n".join(content),
            content_type=ContentType.XLSX,
            file_path=str(file_path),
            metadata={},
        )

    def _extract_csv(self, file_path):
        logger.info(f"Reading CSV: {file_path}")

        text = file_path.read_text(encoding="utf-8", errors="ignore")

        return ExtractedContent(
            text=text,
            content_type=ContentType.CSV,
            file_path=str(file_path),
            metadata={},
        )

    def _extract_json(self, file_path):
        logger.info(f"Reading JSON: {file_path}")

        data = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))

        return ExtractedContent(
            text=json.dumps(data, indent=2),
            content_type=ContentType.JSON,
            file_path=str(file_path),
            metadata={},
        )

    def _extract_text(self, file_path):
        logger.info(f"Reading text: {file_path}")

        return ExtractedContent(
            text=file_path.read_text(encoding="utf-8", errors="ignore"),
            content_type=file_path.suffix.lower().replace(".", ""),
            file_path=str(file_path),
            metadata={},
        )

    def _extract_pdf(self, file_path):
        logger.info(f"Reading PDF: {file_path}")

        import fitz

        document = fitz.open(file_path)

        try:
            content = []

            for page in document:
                text = page.get_text()

                if text:
                    content.append(text)
        finally:
            document.close()

        return ExtractedContent(
            text="\n".join(content),
            content_type=ContentType.PDF,
            file_path=str(file_path),
            metadata={},
        )

    def _extract_docx(self, file_path):
        logger.info(f"Reading DOCX: {file_path}")

        from docx import Document

        document = Document(file_path)

        content = []

        for paragraph in document.paragraphs:
            if paragraph.text:
                content.append(paragraph.text)

        return ExtractedContent(
            text="\n".join(content),
            content_type=ContentType.DOCX,
            file_path=str(file_path),
            metadata={},
        )

    def _extract_pptx(self, file_path):
        logger.info(f"Reading PPTX: {file_path}")

        from pptx import Presentation

        presentation = Presentation(file_path)

        content = []

        for slide in presentation.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    if shape.text:
                        content.append(shape.text)

        return ExtractedContent(
            text="\n".join(content),
            content_type=ContentType.PPTX,
            file_path=str(file_path),
            metadata={},
        )

    def _extract_image(self, file_path):
        logger.info(f"Reading image: {file_path}")

        from PIL import Image
        import pytesseract

        image = Image.open(file_path)

        text = pytesseract.image_to_string(image)

        width, height = image.size

        return ExtractedContent(
            text=text,
            content_type=ContentType.IMAGE,
            file_path=str(file_path),
            metadata={"width": width, "height": height, "format": image.format},
        )

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

        return ExtractedContent(
            text="\n".join(content),
            content_type=ContentType.ZIP,
            file_path=str(file_path),
            metadata={},
        )
