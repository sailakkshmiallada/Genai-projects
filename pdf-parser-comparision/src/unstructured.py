"""
Unstructured PDF Processing Module

This module provides functionality for converting PDF documents to markdown format
using the unstructured library. It handles various document elements including
titles, list items, tables, and images with high-resolution extraction strategy.
"""

import functools
from pathlib import Path
from typing import List, Tuple, Any
from matplotlib import font_manager
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.pdf_image.analysis import bbox_visualisation

from .settings import ENABLE_DEBUG_MODE
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

# Define constants
UNSTRUCTURED_DEBUG_PATH = Path("/tmp/unstructured")

def convert_elements_to_markdown(elements: List[Any]) -> str:
    """
    Convert unstructured document elements to markdown format.

    Args:
        elements (List[Any]): List of unstructured document elements

    Returns:
        str: Converted markdown text with embedded images and tables

    Raises:
        ValueError: If elements list is invalid
    """
    if not elements:
        logger.warning("No elements provided for conversion")
        return ""

    try:
        logger.debug("Converting elements to markdown")
        lines = []

        for e in elements:
            if e.category == "Title":
                line = f"\n# {e.text}\n"
            elif e.category == "ListItem":
                line = f"- {e.text}"
            elif e.category == "Table":
                line = f"\n{e.metadata.text_as_html}\n"
            elif e.category == "UncategorizedText":
                line = ""
            elif e.category == "Image":
                line = (f"![{e.text}](data:image/jpeg;base64,"
                       f"{e.metadata.image_base64})")
            else:
                line = e.text

            lines.append(line)

        md = "\n".join(lines)
        logger.debug("Elements converted to markdown successfully")
        return md

    except Exception as e:
        logger.error(f"Error converting elements to markdown: {str(e)}")
        raise ValueError(f"Markdown conversion failed: {str(e)}")


@functools.lru_cache(maxsize=None)
def get_font() -> str:
    """
    Get a system font for text rendering, with preference for Arial or DejaVu Sans.

    Returns:
        str: Path to the selected font file

    Raises:
        ValueError: If no system fonts are available
    """
    try:
        logger.debug("Searching for system fonts")
        preferred_fonts = ["Arial.ttf", "DejaVuSans.ttf"]
        available_fonts = font_manager.findSystemFonts()
        
        if not available_fonts:
            logger.error("No system fonts available")
            raise ValueError("No fonts available")
            
        for font in preferred_fonts:
            for available_font in available_fonts:
                if font in available_font:
                    logger.debug(f"Using preferred font: {font}")
                    return available_font

        logger.info("Preferred fonts not found, using first available font")
        return available_fonts[0]

    except Exception as e:
        logger.error(f"Error finding system font: {str(e)}")
        raise ValueError(f"Font selection failed: {str(e)}")


# Monkey patch bbox_visualisation with our font getter
bbox_visualisation.get_font = get_font


def convert_unstructured(path: str, file_name: str) -> Tuple[str, List[Path]]:
    """
    Convert a PDF file to markdown format using unstructured library.

    Args:
        path (str): Path to the PDF file
        file_name (str): Name of the PDF file for debug output

    Returns:
        Tuple[str, List[Path]]: A tuple containing:
            - Converted markdown text with embedded images and tables
            - List of debug image file paths if debug mode is enabled

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        Exception: For other processing errors
    """
    logger.info(f"Starting PDF conversion for file: {file_name}")

    # Input validation
    if not Path(path).exists():
        logger.error(f"PDF file not found at path: {path}")
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        # Convert PDF using unstructured
        logger.debug(f"Partitioning PDF with hi_res strategy: {file_name}")
        elements = partition_pdf(
            filename=path,
            strategy="hi_res",  # mandatory for high-quality extraction
            infer_table_structure=True,
            extract_image_block_types=["Image", "Table"],
            extract_image_block_to_payload=True,
            analysis=ENABLE_DEBUG_MODE,
            analyzed_image_output_dir_path=UNSTRUCTURED_DEBUG_PATH,
        )
        
        # Convert elements to markdown
        logger.debug("Converting extracted elements to markdown")
        text = convert_elements_to_markdown(elements)
        
        # Handle debug images
        debug_image_paths: List[Path] = []
        debug_image_dir = UNSTRUCTURED_DEBUG_PATH / "analysis" / file_name / "bboxes"
        
        if debug_image_dir.exists():
            logger.debug(f"Collecting debug images from: {debug_image_dir}")
            debug_image_paths = [
                path for path in debug_image_dir.iterdir() if "od_model" in path.stem
            ]
            logger.info(f"Found {len(debug_image_paths)} debug images")
        
        logger.info("PDF conversion completed successfully")
        return text, debug_image_paths

    except Exception as e:
        logger.error(f"Error converting PDF {file_name}: {str(e)}", exc_info=True)
        raise Exception(f"PDF conversion failed: {str(e)}")
