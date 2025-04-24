"""
Docling PDF Processing Module

This module provides functionality for converting PDF documents to markdown format
using the Docling library. It supports OCR, table structure detection, formula
enrichment, and debug visualization features.
"""

from pathlib import Path
from typing import Tuple, List
import os

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

# Define constants
DOCLING_DEBUG_PATH = Path("/tmp/docling")

def initialize_docling_converter() -> DocumentConverter:
    """
    Initialize and configure the Docling document converter.
    
    Returns:
        DocumentConverter: Configured Docling converter instance
        
    Raises:
        RuntimeError: If initialization fails
    """
    try:
        logger.debug("Initializing Docling converter settings")
        
        # Configure accelerator options
        accelerator_options = AcceleratorOptions(
            num_threads=8,
            device=AcceleratorDevice.AUTO
        )
        
        # Configure pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.accelerator_options = accelerator_options
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.do_formula_enrichment = True
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = 2.0
        
        # Configure debug visualization settings
        settings.debug.debug_output_path = str(DOCLING_DEBUG_PATH)
        settings.debug.visualize_layout = True
        settings.debug.visualize_tables = True
        
        # Initialize converter
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                )
            }
        )
        logger.info("Docling converter initialized successfully")
        return converter
        
    except Exception as e:
        logger.error(f"Failed to initialize Docling converter: {str(e)}")
        raise RuntimeError(f"Docling initialization failed: {str(e)}")

# Initialize the converter
docling_converter = initialize_docling_converter()

def convert_docling(path: str, file_name: str) -> Tuple[str, List[Path]]:
    """
    Convert a PDF file to markdown format using Docling.
    
    Args:
        path (str): Path to the PDF file
        file_name (str): Name of the PDF file for debug output
        
    Returns:
        Tuple[str, List[Path]]: A tuple containing:
            - Converted markdown text with embedded images
            - List of debug image file paths if debug mode is enabled
            
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        Exception: For other processing errors
    """
    logger.info(f"Starting PDF conversion for file: {file_name}")
    
    # Input validation
    if not os.path.exists(path):
        logger.error(f"PDF file not found at path: {path}")
        raise FileNotFoundError(f"PDF file not found: {path}")
    
    try:
        # Convert document
        logger.debug(f"Converting PDF using Docling: {file_name}")
        result = docling_converter.convert(path)
        
        # Export to markdown
        logger.debug("Exporting to markdown with embedded images")
        text = result.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
        
        # Handle debug images
        debug_image_paths: List[Path] = []
        debug_image_dir = DOCLING_DEBUG_PATH / f"debug_{file_name}"
        
        if debug_image_dir.exists():
            logger.debug(f"Collecting debug images from: {debug_image_dir}")
            debug_image_paths = [
                path for path in debug_image_dir.iterdir() if path.suffix == ".png"
            ]
            logger.info(f"Found {len(debug_image_paths)} debug images")
        
        logger.info("PDF conversion completed successfully")
        return text, debug_image_paths
        
    except Exception as e:
        logger.error(f"Error converting PDF {file_name}: {str(e)}", exc_info=True)
        raise Exception(f"PDF conversion failed: {str(e)}")
