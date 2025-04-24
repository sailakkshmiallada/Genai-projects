"""
DocTR PDF Processing Module

This module provides functionality for performing OCR on PDF documents using the DocTR library.
It includes robust error handling and logging for production use.
"""

from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import os
from typing import Optional, Any
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

def convert_doctr(pdf_path: str) -> Optional[Any]:
    """
    Performs OCR on a given PDF file using DocTR's OCR predictor model.

    Args:
        pdf_path (str): Path to the input PDF file

    Returns:
        Optional[Any]: The OCR result object from the predictor, or None if an error occurs

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If the PDF path is invalid
        Exception: For other processing errors
    """
    logger.info(f"Starting OCR processing for file: {os.path.basename(pdf_path)}")

    # Validate input
    if not pdf_path or not isinstance(pdf_path, str):
        logger.error("Invalid PDF path provided")
        raise ValueError("PDF path must be a non-empty string")

    # Check if the PDF file exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at {pdf_path}")
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")

    try:
        # Load the document
        logger.debug(f"Loading PDF document: {pdf_path}")
        doc = DocumentFile.from_pdf(pdf_path)
        logger.info(f"Successfully loaded PDF with {len(doc)} page(s)")

        # Initialize predictor
        logger.debug("Initializing OCR predictor")
        predictor_instance = ocr_predictor(
            pretrained=True,
            export_as_straight_boxes=True,
            detect_orientation=True,
            detect_language=True
        )
        logger.debug("Predictor initialized successfully")

        # Run OCR prediction
        logger.info("Running OCR prediction...")
        result = predictor_instance(doc)
        logger.info("OCR prediction completed successfully")
        
        return result

    except Exception as e:
        logger.error(f"Error during OCR processing: {str(e)}", exc_info=True)
        raise Exception(f"OCR processing failed: {str(e)}")

