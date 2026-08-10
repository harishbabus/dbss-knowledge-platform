from enum import StrEnum


class ContentType(StrEnum):
    """
    Supported document/content types extracted from attachments.
    """

    PDF = "pdf"
    DOCX = "docx"
    XLSX = "excel"
    CSV = "csv"
    JSON = "json"
    ZIP = "zip"
    IMAGE = "image"
    PPTX = "pptx"
    TEXT = "text"
    LDIF = "ldif"
    RAR = "rar"
    XML = "xml"
    HTML = "html"
    UNKNOWN = "unknown"
