"""
MarkItDown PDF Processing Module

This module provides functionality for converting PDF documents to markdown format
using the MarkItDown library. It supports basic PDF to markdown conversion with
optional plugin support.
"""

from markitdown import MarkItDown
from typing import Tuple, List
import os
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

def convert_markit(path: str, file_name: str) -> Tuple[str, List]:
    """
    Convert a PDF file to markdown format using MarkItDown.

    Args:
        path (str): Path to the PDF file
        file_name (str): Name of the PDF file for logging purposes

    Returns:
        Tuple[str, List]: A tuple containing:
            - Converted markdown text
            - Empty list (no separate image handling)

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        Exception: For other processing errors
    """
    logger.info(f"Starting PDF to markdown conversion for file: {file_name}")

    # Input validation
    if not os.path.exists(path):
        logger.error(f"PDF file not found at path: {path}")
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        # Initialize MarkItDown converter
        logger.debug("Initializing MarkItDown converter with plugins disabled")
        md = MarkItDown(enable_plugins=False)  # Set to True to enable plugins
        
        # Convert PDF to markdown
        logger.debug(f"Converting PDF to markdown: {file_name}")
        result = md.convert(path)
        logger.info("PDF to markdown conversion completed successfully")
        
        return result.text_content, []

    except Exception as e:
        logger.error(f"Error converting PDF {file_name} to markdown: {str(e)}", exc_info=True)
        raise Exception(f"PDF conversion failed: {str(e)}")