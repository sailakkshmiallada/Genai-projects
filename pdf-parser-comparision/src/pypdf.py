"""
PyPDF Processing Module

This module provides functionality for extracting text and images from PDF documents
using the PyPDF library. It handles both text extraction with layout preservation
and image extraction from PDF pages.
"""

from pypdf import PdfReader
from typing import Tuple, List, Optional
import os
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

def convert_pypdf(path: str, file_name: str) -> Tuple[str, List[bytes]]:
    """
    Extract text and images from a PDF file using PyPDF.

    Args:
        path (str): Path to the PDF file
        file_name (str): Name of the PDF file for logging purposes

    Returns:
        Tuple[str, List[bytes]]: A tuple containing:
            - Extracted text with preserved layout
            - List of image data as bytes

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If the input parameters are invalid
        Exception: For other processing errors
    """
    logger.info(f"Starting PDF conversion for file: {file_name}")

    # Input validation
    if not os.path.exists(path):
        logger.error(f"PDF file not found at path: {path}")
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        # Initialize PDF reader
        logger.debug(f"Initializing PdfReader for {file_name}")
        reader = PdfReader(path)
        logger.info(f"Successfully loaded PDF with {len(reader.pages)} pages")

        # Extract text with layout preservation
        logger.debug("Extracting text from PDF pages")
        text = ""
        for page_num, page in enumerate(reader.pages, 1):
            try:
                page_text = page.extract_text(extraction_mode="layout")
                text += page_text + "\n\n"
                logger.debug(f"Successfully extracted text from page {page_num}")
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {str(e)}")

        # Extract images
        logger.debug("Starting image extraction")
        images = []
        for page_index, page in enumerate(reader.pages, 1):
            try:
                for image_index, image_file_object in enumerate(page.images, 1):
                    image_data = image_file_object.data
                    images.append(image_data)
                    logger.debug(f"Extracted image {image_index} from page {page_index}")
            except Exception as e:
                logger.warning(f"Error extracting images from page {page_index}: {str(e)}")

        logger.info(f"PDF conversion completed. Extracted {len(images)} images")
        return text, images

    except Exception as e:
        logger.error(f"Error processing PDF {file_name}: {str(e)}", exc_info=True)
        raise Exception(f"PDF processing failed: {str(e)}")