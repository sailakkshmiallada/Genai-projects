"""Core generator module for synthetic data generation.

This module contains the main Generator class that orchestrates the synthetic data
generation process, including template selection, LLM interaction, and output formatting.
"""

from typing import  Optional
from .assistant import Assistant
from .utils.config_loader import load_config
from .utils.output_formatter import OutputFormatter
from .templates.email_template import EmailTemplate
from .templates.product_template import ProductTemplate
from .utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class Generator:
    """Main generator class for synthetic data generation.
    
    This class orchestrates the entire generation process, including loading templates,
    interacting with the LLM, and formatting output.
    """
    
    def __init__(self, config_path: str):
        """Initialize the generator with configuration.
        
        Args:
            config_path: Path to the configuration file.
        """
        logger.info(f"Initializing Generator with config: {config_path}")
        self.config_path = config_path
        try:
            self.config = load_config(config_path)
            self.temperature = self.config.get('llm', {}).get('temperature', 0.7)
            self.max_tokens = self.config.get('llm', {}).get('max_tokens', 1000000)
            self.model = self.config.get('llm', {}).get('model', 'gpt-3.5-turbo')
            logger.debug(f"Config loaded successfully: {self.config.keys()}")
        except Exception as e:
            logger.exception(f"Failed to load config: {e}")
            raise
            
        try:
            self.llm_client = Assistant()
            logger.debug("LLM client initialized")
        except Exception as e:
            logger.exception(f"Failed to initialize LLM client: {e}")
            raise
            
        try:
            self.output_formatter = OutputFormatter(self.config)
            logger.debug("Output formatter initialized")
        except Exception as e:
            logger.exception(f"Failed to initialize output formatter: {e}")
            raise
        
        # Initialize template handlers
        self.template_handlers = {
            "emails": EmailTemplate,
            "products": ProductTemplate
        }
        logger.debug(f"Available templates: {list(self.template_handlers.keys())}")
    
    def generate(self, 
                template_name: str, 
                count: int = 10,
                output_format: Optional[str] = None) -> str:
        """Generate synthetic data using the specified template.
        
        Args:
            template_name: Name of the template to use (e.g., 'email', 'product')
            count: Number of items to generate
            output_format: Override the default output format
            
        Returns:
            Path to the saved output file
        """
        logger.info(f"Generating {count} synthetic data items using {template_name} template")
        
        try:
            if template_name not in self.template_handlers:
                logger.error(f"Unsupported template type: {template_name}")
                raise ValueError(f"Unsupported template type: {template_name}. "
                              f"Available templates: {list(self.template_handlers.keys())}")
            
            # Override output format if specified
            if output_format:
                logger.info(f"Overriding default output format to: {output_format}")
                self.config['output']['default_format'] = output_format
            
            # Initialize the appropriate template handler
            logger.debug(f"Initializing template handler for: {template_name}")
            template_handler = self.template_handlers[template_name](self.config)
            
            # Build the prompt and get the output model
            logger.debug(f"Building prompt for {count} samples")
            prompt, output_model = template_handler.build_prompt(num_samples=count)
            logger.debug(f"Prompt built successfully, output model: {output_model.__name__}")
            
            # Generate response from LLM
            logger.info("Generating response from LLM")
            response = self.llm_client.generate_response(prompt=prompt, 
                                                         output_pydantic=output_model, 
                                                         temperature=self.temperature, 
                                                         max_tokens=self.max_tokens, 
                                                         model=self.model)
            logger.debug(f"LLM response generated: {len(response.content)} characters")
            
            # Format and save the output
            output_path = self.output_formatter.format_and_save(response, template_name)
            
            return output_path
            
        except Exception as e:
            logger.exception(f"Error in generate method: {e}")
            raise

def generate_synthetic_data(config_path: str, 
                           template_name: str, 
                           count: int = 10,
                           output_format: Optional[str] = None) -> str:
    """Convenience function to generate synthetic data.
    
    Args:
        config_path: Path to the configuration file
        template_name: Name of the template to use
        count: Number of items to generate
        output_format: Override the default output format
        
    Returns:
        Path to the saved output file
    """
    logger.info(f"Starting synthetic data generation: template={template_name}, count={count}")
    try:
        generator = Generator(config_path)
        result = generator.generate(template_name, count, output_format)
        return result
    except Exception as e:
        logger.exception(f"Synthetic data generation failed: {e}")
        raise