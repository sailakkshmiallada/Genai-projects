import logfire
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, List, Union
import os
import math  # Add math for ceiling division
import asyncio  # Add asyncio for sleep
from src.utils.logger import get_logger
from src.generator import generate_synthetic_data

# Initialize logger
logger = get_logger(__name__)

app = FastAPI(
    title="Synthetic Data Generator API",
    description="API for generating synthetic data using LLM models",
    version="1.0.0"
)

load_dotenv()

# Logfire will be configured by our logger, no need to call configure() here
logfire.instrument_fastapi(app, capture_headers=True)

logger.info("Starting application")

# Define request and response models
class HealthResponse(BaseModel):
    status: str
    version: str

class GenerateDataRequest(BaseModel):
    template_name: str
    count: int = 10
    output_format: Optional[str] = None

# Request model for batch generation
class GenerateBatchDataRequest(BaseModel):
    template_name: str
    count: int = 10
    output_format: Optional[str] = None
    batch: bool = False

class GenerateDataResponse(BaseModel):
    status: str
    output_path: str
    count: int
    template_name: str
    output_format: str

# Response model for batch generation
class GenerateBatchDataResponse(BaseModel):
    status: str
    output_path: Union[str, List[str]]
    requested_count: int
    generated_count: int
    template_name: str
    output_format: str
    batch_mode: bool

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API is functioning correctly.
    """
    logger.info("Health check endpoint called")
    return {
        "status": "ok",
        "version": "1.0.0"
    }

@app.post("/generate", response_model=GenerateDataResponse, tags=["Data Generation"])
async def generate_data(request: GenerateDataRequest):
    """
    Generate synthetic data using the specified template.
    
    - **template_name**: The template to use (emails or products)
    - **count**: Number of items to generate (default: 10)
    - **output_format**: Output format (json or csv)
    """
    logger.info(f"Data generation endpoint called with: {request.model_dump()}")
    
    # Validate template name
    valid_templates = ["emails", "products"]
    if request.template_name not in valid_templates:
        logger.error(f"Invalid template name: {request.template_name}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid template name. Must be one of: {valid_templates}"
        )
    
    # Validate output format if provided
    valid_formats = ["json", "csv"]
    if request.output_format is not None and request.output_format not in valid_formats:
        logger.error(f"Invalid output format: {request.output_format}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid output format. Must be one of: {valid_formats}"
        )
    
    # Configure the path for the configuration file
    config_path = "config/system_config.yaml"
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise HTTPException(
            status_code=500,
            detail="System configuration file not found"
        )
    
    try:
        # Generate the data
        logger.info(f"Generating {request.count} {request.template_name} using {request.output_format or 'default'} format")
        output_path = generate_synthetic_data(
            config_path=config_path,
            template_name=request.template_name,
            count=request.count,
            output_format=request.output_format
        )
        
        # Return the response
        logger.info(f"Data generation successful, output saved to: {output_path}")
        return {
            "status": "success",
            "output_path": output_path,
            "count": request.count,
            "template_name": request.template_name,
            "output_format": request.output_format or "json"  # Default if None
        }
        
    except ValueError as e:
        logger.error(f"Value error during generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error during data generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating data: {str(e)}")

@app.post("/generate-batch", response_model=GenerateBatchDataResponse, tags=["Data Generation"])
async def generate_batch_data(request: GenerateBatchDataRequest):
    """
    Generate synthetic data, with an option for batch processing, respecting rate limits.

    - **template_name**: The template to use (emails or products)
    - **count**: Base number of items to generate (default: 10)
    - **output_format**: Output format (json or csv)
    - **batch**: If true, generate count * 10 items (default: False), processed in batches of 15 per minute.
    """
    logger.info(f"Batch data generation endpoint called with: {request.model_dump()}")

    # Validate template name
    valid_templates = ["emails", "products"]
    if request.template_name not in valid_templates:
        logger.error(f"Invalid template name: {request.template_name}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template name. Must be one of: {valid_templates}"
        )

    # Validate output format if provided
    valid_formats = ["json", "csv"]
    if request.output_format is not None and request.output_format not in valid_formats:
        logger.error(f"Invalid output format: {request.output_format}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output format. Must be one of: {valid_formats}"
        )

    # Configure the path for the configuration file
    config_path = "config/system_config.yaml"
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise HTTPException(
            status_code=500,
            detail="System configuration file not found"
        )

    requested_count = request.count
    final_count = request.count * 10 if request.batch else request.count
    logger.info(f"Batch mode: {request.batch}. Requested count: {requested_count}, Final count: {final_count}")

    # --- Rate Limiting Logic ---
    batch_size = 15
    sleep_time = 60  # seconds
    num_batches = math.ceil(final_count / batch_size)
    generated_count_total = 0
    output_paths = []

    try:
        logger.info(f"Starting batch generation for {final_count} items in {num_batches} batches of size {batch_size}.")

        for i in range(num_batches):
            current_batch_count = min(batch_size, final_count - generated_count_total)
            if current_batch_count <= 0:
                break  # Should not happen with ceil, but good practice

            logger.info(f"Generating batch {i+1}/{num_batches} with {current_batch_count} items.")

            # Generate the data for the current batch
            output_path = generate_synthetic_data(
                config_path=config_path,
                template_name=request.template_name,
                count=current_batch_count,
                output_format=request.output_format
            )
            output_paths.append(output_path)
            generated_count_total += current_batch_count
            logger.info(f"Batch {i+1} successful. Output: {output_path}. Total generated: {generated_count_total}/{final_count}")

            # Sleep if there are more batches to process
            if i < num_batches - 1:
                logger.info(f"Sleeping for {sleep_time} seconds before next batch...")
                await asyncio.sleep(sleep_time)

        # Determine the final output path representation
        # If only one batch was run, return the single path string.
        # If multiple batches, return the list of paths.
        final_output_path = output_paths[0] if len(output_paths) == 1 else output_paths

        logger.info(f"Batch data generation completed. Total items generated: {generated_count_total}")
        return {
            "status": "success",
            "output_path": final_output_path,  # Return single path or list
            "requested_count": requested_count,
            "generated_count": generated_count_total,  # Use the actual count generated
            "template_name": request.template_name,
            "output_format": request.output_format or "json",
            "batch_mode": request.batch
        }

    except ValueError as e:
        logger.error(f"Value error during batch generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error during batch data generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating batch data: {str(e)}")

@app.get("/templates", tags=["Data Generation"])
async def list_templates():
    """
    List all available templates for data generation.
    """
    logger.info("Templates listing endpoint called")
    return {
        "templates": [
            {
                "name": "emails",
                "description": "Generate synthetic email content with various complexity levels"
            },
            {
                "name": "products",
                "description": "Generate synthetic product data with descriptions and features"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)