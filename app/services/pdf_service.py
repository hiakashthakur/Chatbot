from app import container
from pathlib import Path
from typing import List, Dict

from pypdf import PdfReader

from app.logger import logger
from app.exceptions.pdf_exception import (
    PDFNotFoundException,
    EmptyPDFException
)


class PDFService:
    """
    Service responsible for loading and extracting
    text from PDF files.
    """

    def load_pdf(
        self,
        pdf_path: str
    ) -> PdfReader:
        """
        Load PDF and return PdfReader object.
        """

        if not Path(pdf_path).exists():

            raise PDFNotFoundException(
                f"{pdf_path} not found."
            )

        logger.info(
            f"Loading PDF : {pdf_path}"
        )

        try:

            return PdfReader(pdf_path)

        except Exception as e:

            logger.exception(
                "Failed to load PDF"
            )

            raise PDFNotFoundException(
                str(e)
            ) from e

    def extract_pages(
        self,
        reader: PdfReader
    ) -> List[Dict]:
        """
        Extract page-wise text.
        """

        logger.info(
            "Extracting PDF pages"
        )

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            page_text = page.extract_text()

            if page_text and page_text.strip():

                pages.append(
                    {
                        "page": page_number,
                        "text": page_text.strip()
                    }
                )

        if not pages:

            raise EmptyPDFException(
                "No extractable text found."
            )

        logger.info(
            f"Extracted {len(pages)} pages"
        )

        return pages

    def get_filename(
        self,
        pdf_path: str
    ) -> str:
        """
        Return PDF filename.
        """

        return Path(pdf_path).name

    # -----------------------------------
    # Backward Compatibility
    # -----------------------------------

    def extract_text(
        self,
        pdf_path: str
    ) -> str:
        """
        Return complete text.
        Existing code will continue to work.
        """

        reader = self.load_pdf(
            pdf_path
        )

        pages = self.extract_pages(
            reader
        )

        return "\n".join(
            page["text"]
            for page in pages
        )