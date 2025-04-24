# templates/product_template.py
import os
import json
import random
from typing import Dict, Any, List, Tuple, Type 
from pydantic import BaseModel, Field
from src.utils.logger import get_logger
from src.utils.pydantic_generator import create_pydantic_models
# Initialize logger
logger = get_logger(__name__)

# # --- Pydantic model for ProductOutput definition ---
# class ProductOutput(BaseModel):
#     """Pydantic model for product description output"""
#     product_name: str = Field(..., description="Specific, marketable name/title of the product")
#     tagline: str = Field(..., description="Short, catchy tagline or headline summarizing the main benefit")
#     description: str = Field(..., description="Main product description adhering to complexity guidelines")
#     features: List[str] = Field(..., description="Key features as a list of strings (bullet points)")
#     # specifications: Optional[Any] = Field(default_factory=dict, description="Technical specifications as key-value pairs (e.g., {'Material': 'Cotton', 'Size': 'Large'})")
#     price: float = Field(..., description="Specific price within the suggested range for the product")
#     category: str = Field(..., description="Product category assigned during generation")
#     complexity_level: str = Field(..., description="Complexity level used for generation (e.g., 'simple', 'medium')")

# # Pydantic model for a list of product outputs
# class ProductOutputList(BaseModel):
#     """Pydantic model for a list of product outputs"""
#     products: List[ProductOutput] = Field(..., description="A list containing the generated product description objects")

class ProductTemplate:
    def __init__(self, config: Dict[str, Any]):
        # Store the raw config if needed, focusing on 'product_templates'
        self.product_config = config.get("product_templates", {})

        # --- Load Categories ---
        self.categories = self.product_config.get("categories", [])
        if not self.categories:
            print("Warning: No 'categories' found in product_templates config.")
            self.categories = ["general merchandise"] # Default fallback

        # --- Load Price Ranges ---
        self.price_ranges = self.product_config.get("price_ranges", {})
        if not self.price_ranges or not isinstance(self.price_ranges, dict):
             print("Warning: 'price_ranges' missing or invalid in config. Using defaults.")
             self.price_ranges = {
                "mid_range": [51, 200]
             }
        self.price_tiers = list(self.price_ranges.keys())

        # --- Load Complexity Definitions FROM CONFIG ---
        self.complexity_templates = self.product_config.get("complexity_templates", {})
        if not self.complexity_templates or not isinstance(self.complexity_templates, dict):
            print("Warning: 'complexity_templates' missing or invalid in config. Using defaults.")
            # Define fallbacks if config is missing/invalid
            self.complexity_templates = {
                "simple": {"description": "Basic info", "word_count_range": [30, 70], "features_count": [2, 3], "specs_count": [0, 1]},
                "medium": {"description": "Detailed info", "word_count_range": [70, 150], "features_count": [4, 5], "specs_count": [2, 3]},
            }
        # Derive available levels from the keys of the loaded templates
        self.complexity_levels = list(self.complexity_templates.keys())

        self.project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

        logger.debug(f"Detected project root: {self.project_root_dir}")

        self.reference_examples = self._load_reference_examples()
        ProductOutput, ProductOutputList = create_pydantic_models(
                                            "ProductOutput",
                                            config['product_templates']['response_fields'],
                                            docstring="Pydantic model for product output",
                                            list_field_name= "products"
                                          )
        self.ProductOutput = ProductOutput
        self.ProductOutputList = ProductOutputList
        


    def _load_reference_examples(self, max_examples: int = 5) -> List[Dict[str, Any]]:
        """
        Loads and samples reference examples from data/input/emails.json.
        Checks for file existence first and returns [] on any error.
        """
        examples_path = os.path.join(self.project_root_dir, 'data', 'input', 'products.json')
        reference_examples = []

        # --- Check if file exists BEFORE trying to open ---
        if not os.path.exists(examples_path):
            logger.info(f"Reference examples file not found at {examples_path}. Proceeding without examples.")
            return [] # Return empty list if file doesn't exist

        # --- File exists, now try to read and parse ---
        try:
            logger.info(f"Attempting to load reference examples from: {examples_path}")
            with open(examples_path, 'r', encoding='utf-8') as f:
                all_examples = json.load(f)

            if isinstance(all_examples, list) and all_examples:
                num_to_sample = min(len(all_examples), max_examples)
                reference_examples = random.sample(all_examples, num_to_sample)
                logger.info(f"Successfully loaded and sampled {len(reference_examples)} reference examples.")
            else:
                logger.warning(f"Reference examples file '{examples_path}' does not contain a reference examples list.")
                reference_examples = [] # Ensure empty list if format is wrong

        except json.JSONDecodeError:
            # Log error but return empty list
            logger.error(f"Error decoding JSON from {examples_path}. Proceeding without examples.")
            reference_examples = []
        except Exception as e:
            # Log error but return empty list
            logger.exception(f"An unexpected error occurred loading reference examples: {e}")
            reference_examples = []

        return reference_examples

    def build_prompt(self, num_samples: int = 10) -> Tuple[str, Type[BaseModel]]:
        """
        Builds a prompt for generating multiple synthetic product descriptions,
        using complexity definitions from the loaded config.

        Args:
            num_samples: The number of distinct product descriptions to generate.

        Returns:
            A tuple containing the prompt string and the ProductOutputList model class.
        """
        # --- Dynamically create complexity guidelines from config ---
        complexity_guidelines = []
        for level, details in self.complexity_templates.items():
            desc = details.get('description', f'{level} level')
            wc = details.get('word_count_range', ['N/A', 'N/A'])
            fc = details.get('features_count', ['N/A', 'N/A'])
            sc = details.get('specs_count', ['N/A', 'N/A'])
            complexity_guidelines.append(
                f"- {level}: {desc} (approx. {wc[0]}-{wc[1]} words, {fc[0]}-{fc[1]} features, {sc[0]}-{sc[1]} specs)"
            )
        complexity_section = "\n".join(complexity_guidelines)

        # (Using the full ProductOutput model definition for clarity)
        single_product_model_def = self.ProductOutput.model_json_schema()


        # Define the structure for the list output
        list_model_def = """
        class ProductOutputList(BaseModel):
            products: List[ProductOutput] # A list containing EXACTLY {num_samples} product objects
        """.format(num_samples=num_samples)

        # --- Format Reference Examples (if available) ---
        reference_section = ""
        if self.reference_examples:
            try:
                examples_str = json.dumps(self.reference_examples, indent=2)
                reference_section = f"""
        <reference_examples>
        Here are {len(self.reference_examples)} examples of customer emails for reference.
        Use these to understand the typical tone, style, structure, and level of detail.
        ***Do NOT copy these examples directly.*** Generate completely new and distinct emails based on the requirements.

        {examples_str}
        </reference_examples>
        """
            except TypeError:
                logger.error("Failed to serialize reference examples. Skipping inclusion.")
                reference_section = "\n\n"

        # --- Construct the main prompt using config data ---
        prompt = f"""Generate EXACTLY {num_samples} distinct and realistic product descriptions for an e-commerce setting.

        Ensure variety across the generated product descriptions using different combinations of:
        - Product Category: Use a variety from {self.categories}. Assign a relevant category to each product.
        - Price Tier: Use different tiers from {self.price_tiers}, generating a specific price within the corresponding range: {self.price_ranges}.
        - Complexity Levels: Generate descriptions representing DIFFERENT complexity levels, adhering strictly to the following guidelines for description length, feature count, and specification count:
        {complexity_section}

        First, understand the required structure for each individual product object:
        ```python
        {single_product_model_def}
        ```

        Now, format your entire response as a single JSON object conforming strictly to the following Pydantic model.
        The JSON object must have ONE key 'products' containing a list of EXACTLY {num_samples} distinct `ProductOutput` objects, each matching the structure defined above.

        ```python{list_model_def}
        ```
        {reference_section}

        Return ONLY the valid JSON object conforming to the `ProductOutputList` structure. Do not include any other text or explanation before or after the JSON.
        """

        # Return the prompt and the Pydantic model class for the list
        return prompt, self.ProductOutputList