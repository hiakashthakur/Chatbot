class PDFException(Exception):
    """Base exception for PDF errors."""
    pass


class PDFNotFoundException(PDFException):
    pass


class EmptyPDFException(PDFException):
    pass