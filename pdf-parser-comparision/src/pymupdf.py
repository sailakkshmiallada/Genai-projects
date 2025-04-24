"""
PyMuPDF Processing Module

This module provides functionality for converting PDF documents to markdown format
using the pymupdf4llm library, which is optimized for LLM processing.
"""

import pymupdf4llm
import os
from typing import Tuple, List
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

def convert_pymupdf(path: str, file_name: str) -> Tuple[str, List]:
    """
    Convert a PDF file to markdown format using PyMuPDF.

    Args:
        path (str): Path to the PDF file
        file_name (str): Name of the PDF file for logging purposes

    Returns:
        Tuple[str, List]: A tuple containing:
            - Converted markdown text
            - Empty list (images are embedded in markdown)

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If the input parameters are invalid
        Exception: For other processing errors
    """
    logger.info(f"Starting PDF to markdown conversion for file: {file_name}")

    # Input validation
    if not os.path.exists(path):
        logger.error(f"PDF file not found at path: {path}")
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        # Convert PDF to markdown with embedded images
        logger.debug(f"Converting PDF to markdown: {file_name}")
        text = pymupdf4llm.to_markdown(
            path,
            embed_images=True,
        )
        logger.info("PDF to markdown conversion completed successfully")
        
        return text, []

    except Exception as e:
        logger.error(f"Error converting PDF {file_name} to markdown: {str(e)}", exc_info=True)
        raise Exception(f"PDF conversion failed: {str(e)}")