"""
Marker PDF Processing Module

This module provides functionality for converting PDF documents to markdown format
using the Marker library, with support for equation processing and image handling.
It includes utilities for converting images to HTML and embedding them in markdown.
"""

import base64
import io
import re
from pathlib import Path
from typing import Tuple, List, Dict, Any
from PIL.Image import Image

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered 
from marker.processors.equation import EquationProcessor
from marker.settings import settings

from .settings import ENABLE_DEBUG_MODE, ENABLE_FORMULA
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

# Marker initialization
logger.debug("Initializing Marker converter with settings: "
            f"ENABLE_FORMULA={ENABLE_FORMULA}, ENABLE_DEBUG_MODE={ENABLE_DEBUG_MODE}")

if not ENABLE_FORMULA:
    logger.info("Formula processing disabled, removing EquationProcessor")
    PdfConverter.default_processors = (
        processor
        for processor in PdfConverter.default_processors
        if processor != EquationProcessor
    )

marker_converter = PdfConverter(
    artifact_dict=create_model_dict(),
    config={
        "debug_pdf_images": ENABLE_DEBUG_MODE,
    },
)
logger.debug("Marker converter initialized successfully")


def img_to_html(img: Image, img_alt: str) -> str:
    """
    Convert a PIL Image to an HTML img tag with base64-encoded data.

    Args:
        img (Image): PIL Image object to convert
        img_alt (str): Alt text for the image

    Returns:
        str: HTML img tag with base64-encoded image data

    Raises:
        IOError: If image conversion fails
    """
    try:
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=settings.OUTPUT_IMAGE_FORMAT)
        img_bytes_value = img_bytes.getvalue()
        encoded = base64.b64encode(img_bytes_value).decode()
        img_html = (
            f'<img src="data:image/{settings.OUTPUT_IMAGE_FORMAT.lower()}'
            f';base64,{encoded}" alt="{img_alt}" style="max-width: 100%;">'
        )
        return img_html
    except Exception as e:
        logger.error(f"Failed to convert image to HTML: {str(e)}")
        raise IOError(f"Image conversion failed: {str(e)}")


def markdown_insert_images(markdown: str, images: Dict[str, Image]) -> str:
    """
    Replace markdown image references with embedded HTML images.

    Args:
        markdown (str): Markdown text containing image references
        images (Dict[str, Image]): Dictionary mapping image paths to PIL Image objects

    Returns:
        str: Markdown text with embedded HTML images

    Raises:
        ValueError: If markdown or images are invalid
    """
    if not isinstance(markdown, str) or not isinstance(images, dict):
        logger.error("Invalid input types for markdown_insert_images")
        raise ValueError("markdown must be str and images must be dict")

    try:
        image_tags = re.findall(
            r'(!\[(?P<image_title>[^\]]*)\]\((?P<image_path>[^\)"\s]+)\s*([^\)]*)\))',
            markdown,
        )

        for image in image_tags:
            image_markdown = image[0]
            image_alt = image[1]
            image_path = image[2]
            if image_path in images:
                logger.debug(f"Converting image: {image_path}")
                markdown = markdown.replace(
                    image_markdown, img_to_html(images[image_path], image_alt)
                )
        return markdown
    except Exception as e:
        logger.error(f"Error processing markdown images: {str(e)}")
        raise Exception(f"Image processing failed: {str(e)}")


def convert_marker(path: str, file_name: str) -> Tuple[str, List[Path]]:
    """
    Convert a PDF file to markdown format using Marker.

    Args:
        path (str): Path to the PDF file
        file_name (str): Name of the PDF file for logging purposes

    Returns:
        Tuple[str, List[Path]]: A tuple containing:
            - Converted markdown text with embedded images
            - List of debug image file paths if debug mode is enabled

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        Exception: For other processing errors
    """
    logger.info(f"Starting PDF conversion for file: {file_name}")

    if not Path(path).exists():
        logger.error(f"PDF file not found at path: {path}")
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        # Convert PDF using Marker
        logger.debug(f"Converting PDF using Marker: {file_name}")
        rendered = marker_converter(path)
        logger.debug("PDF conversion completed, extracting text and images")
        
        text, _, images = text_from_rendered(rendered)
        text = markdown_insert_images(text, images)
        
        # Handle debug images if enabled
        debug_image_dir = Path(rendered.metadata.get("debug_data_path"))
        debug_image_paths = []
        
        if debug_image_dir.exists():
            logger.debug(f"Processing debug images from: {debug_image_dir}")
            debug_image_paths = [
                path for path in debug_image_dir.iterdir() if "pdf_page" in path.stem
            ]
            logger.info(f"Found {len(debug_image_paths)} debug images")
        
        logger.info("PDF conversion completed successfully")
        return text, debug_image_paths

    except Exception as e:
        logger.error(f"Error processing PDF {file_name}: {str(e)}", exc_info=True)
        raise Exception(f"PDF processing failed: {str(e)}")
