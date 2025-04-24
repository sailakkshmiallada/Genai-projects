"""
SmolDocling PDF Processing Module

This module provides functionality for converting PDF documents to markdown format
using the SmolDocling model, which uses AI-powered image-based extraction.
It supports batch processing of pages and handles CUDA acceleration when available.
"""

import os
import torch
from pdf2image import convert_from_path
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.document import DocTagsDocument
from transformers import AutoProcessor, AutoModelForVision2Seq
from transformers.image_utils import load_image
from typing import List, Tuple
import shutil
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

def convert_smoldocling(
    pdf_path: str,
    filename: str,
    batch_size: int = 3,
    dpi: int = 300,
    cleanup_images: bool = True
) -> Tuple[str, List]:
    """
    Convert a PDF to markdown format using image-based extraction via SmolDocling.
    
    Args:
        pdf_path (str): Path to the PDF file
        filename (str): Name of the input file for logging
        batch_size (int): Number of pages to process at once (max 3 recommended)
        dpi (int): DPI for PDF to image conversion
        cleanup_images (bool): Whether to delete temporary images after processing
        
    Returns:
        Tuple[str, List]: A tuple containing:
            - The markdown content
            - Empty list (images are embedded in markdown)
            
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        RuntimeError: If CUDA initialization fails
        Exception: For other processing errors
    """
    # Input validation
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at path: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        # Check for CUDA availability
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Step 1: Convert PDF pages to images
        logger.info(f"Converting PDF to images (DPI={dpi})...")
        pages = convert_from_path(pdf_path, dpi=dpi)
        temp_image_paths = []
        
        # Create a temporary directory for images
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save each page as an image
        for i, page in enumerate(pages):
            image_path = f"{temp_dir}/page_{i+1}.jpg"
            page.save(image_path, 'JPEG')
            temp_image_paths.append(image_path)
        
        logger.info(f"Converted {len(pages)} pages to images")
        
        # Step 2: Initialize the model and processor
        logger.debug("Loading SmolDocling model...")
        try:
            processor = AutoProcessor.from_pretrained("ds4sd/SmolDocling-256M-preview")
            model = AutoModelForVision2Seq.from_pretrained(
                "ds4sd/SmolDocling-256M-preview",
                torch_dtype=torch.bfloat16,
                attn_implementation="eager",  # for GPUs that don't support flash attention
            ).to(device)
            logger.debug("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SmolDocling model: {str(e)}")
            raise RuntimeError(f"Model initialization failed: {str(e)}")
        
        # Step 3: Process pages in batches
        markdown_parts = []
        total_batches = (len(temp_image_paths) + batch_size - 1) // batch_size
        
        for i in range(0, len(temp_image_paths), batch_size):
            batch_paths = temp_image_paths[i:i+batch_size]
            current_batch = i//batch_size + 1
            logger.info(f"Processing batch {current_batch}/{total_batches}: "
                       f"Pages {i+1}-{i+len(batch_paths)}")
            
            try:
                # Load images for this batch
                batch_images = [load_image(path) for path in batch_paths]
                all_doctags = []
                
                for j, image in enumerate(batch_images):
                    # Create input messages
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image"},
                                {"type": "text", "text": "convert this page to docling"}
                            ]
                        },
                    ]
                    
                    # Prepare inputs
                    logger.debug(f"Processing page {i+j+1}")
                    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
                    inputs = processor(text=prompt, images=[image], return_tensors="pt")
                    inputs = inputs.to(device)
                    
                    # Generate outputs
                    generated_ids = model.generate(**inputs, max_new_tokens=8192)
                    prompt_length = inputs.input_ids.shape[1]
                    trimmed_generated_ids = generated_ids[:, prompt_length:]
                    doctags = processor.batch_decode(
                        trimmed_generated_ids, skip_special_tokens=False,
                    )[0].lstrip()
                    
                    all_doctags.append(doctags)
                
                # Create DoclingDocument
                doctags_doc = DocTagsDocument.from_doctags_and_image_pairs(all_doctags, batch_images)
                doc = DoclingDocument(name=f"Batch {current_batch}")
                doc.load_from_doctags(doctags_doc)
                
                # Convert to markdown
                markdown_content = doc.export_to_markdown()
                markdown_parts.append(markdown_content)
                logger.debug(f"Completed batch {current_batch}")
                
            except Exception as e:
                logger.error(f"Error processing batch {current_batch}: {str(e)}")
                raise Exception(f"Batch processing failed: {str(e)}")
        
        # Combine all parts
        full_markdown = "\n\n---\n\n".join(markdown_parts)
        logger.info("PDF conversion completed successfully")
        
        # Clean up temporary images
        if cleanup_images:
            logger.debug("Cleaning up temporary images...")
            try:
                shutil.rmtree(temp_dir)
                logger.debug("Temporary images cleaned up successfully")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary images: {str(e)}")
        
        return full_markdown, []

    except Exception as e:
        logger.error(f"Error converting PDF {filename}: {str(e)}", exc_info=True)
        # Clean up temporary files in case of error
        if cleanup_images and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary images after error: {str(cleanup_error)}")
        raise Exception(f"PDF conversion failed: {str(e)}")