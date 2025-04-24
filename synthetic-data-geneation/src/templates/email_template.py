# templates/email_template.py
import os
import json
import random
from typing import Dict, Any, List, Type, Tuple # Added List and Type
from pydantic import BaseModel
from src.utils.logger import get_logger
from src.utils.pydantic_generator import create_pydantic_models
# Initialize logger
logger = get_logger(__name__)


# # --- Existing EmailOutput definition ---
# class EmailOutput(BaseModel):
#     """Pydantic model for email output"""
#     subject: str
#     greeting: str
#     body: str
#     closing: str
#     customer_name: str
#     complexity_level: str
#     issue_type: str

# # --- NEW: Pydantic model for a list of email outputs ---
# class EmailOutputList(BaseModel):
#     """Pydantic model for a list of email outputs"""
#     emails: List[EmailOutput]

class EmailTemplate:
    def __init__(self, config: Dict[str, Any]):
        # Extract email-specific configuration
        self.email_config = config.get("email_templates", {})

        # Get available product types from config
        self.product_types = self.email_config.get("product_types", [
            "electronics", "furniture", "clothing", "food", "cosmetics"
        ])

        # Get available issue types from config
        self.issue_types = self.email_config.get("issue_types", [
            "delivery_delay", "order_status", "wrong_item", "damaged_product"
        ])

        # --- Load complexity definitions FROM CONFIG ---
        self.complexity_templates = self.email_config.get("complexity_templates", {})
        if not self.complexity_templates or not isinstance(self.complexity_templates, dict):
            print("Warning: 'complexity_templates' missing or invalid in config. Using defaults.")
            # Define fallbacks if config is missing/invalid
            self.complexity_templates = {
                "simple": {"description": "Brief inquiry", "word_count_range": [30, 70]},
                "medium": {"description": "Some details", "word_count_range": [70, 150]},
            }
        # Derive available levels from the keys of the loaded templates
        self.complexity_levels = list(self.complexity_templates.keys())

        self.project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

        logger.debug(f"Detected project root: {self.project_root_dir}")

        self.reference_examples = self._load_reference_examples()
        # --- Dynamically generate Pydantic models ---
        EmailOutput, EmailOutputList = create_pydantic_models(
            "EmailOutput",
            config['email_templates']['response_fields'],
            docstring="Pydantic model for email output",
            list_field_name= "emails"
        )
        self.EmailOutput = EmailOutput
        self.EmailOutputList = EmailOutputList

    def _load_reference_examples(self, max_examples: int = 5) -> List[Dict[str, Any]]:
        """
        Loads and samples reference examples from data/input/emails.json.
        Checks for file existence first and returns [] on any error.
        """
        examples_path = os.path.join(self.project_root_dir, 'data', 'input', 'emails.json')
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

    # --- Method to generate multiple samples ---
    def build_prompt(self, num_samples: int = 10) -> Tuple[str, Type[BaseModel]]:
        """
        Builds a prompt for generating multiple synthetic email samples
        and returns the prompt string and the Pydantic model for the list.
        """
        complexity = random.choice(self.complexity_levels)
        product_type = random.choice(self.product_types)
        issue_type = random.choice(self.issue_types)

        # --- Dynamically create complexity descriptions from config ---
        complexity_guidelines = []
        for level, details in self.complexity_templates.items():
            desc = details.get('description', f'{level} level')
            wc = details.get('word_count_range', ['N/A', 'N/A'])
            complexity_guidelines.append(
                f"- {level}: {desc} (approx. {wc[0]}-{wc[1]} words)"
            )
        complexity_section = "\n".join(complexity_guidelines)

        # (Using the full EmailOutput model definition for clarity)
        single_email_model_def = self.EmailOutput.model_json_schema()

        # Define the structure for the list output
        list_model_def = """
        class EmailOutputList(BaseModel):
            emails: List[EmailOutput] # A list containing {num_samples} email objects
        """.format(num_samples=num_samples)

        # --- Format Reference Examples (if available) ---
        reference_section = ""
        if self.reference_examples:
            try:
                examples_str = json.dumps(self.reference_examples, indent=2)
                # Note: Moved this section to be appended later in the prompt
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

        # Construct the main prompt
        prompt = f"""Generate {num_samples} distinct and realistic customer email samples.

        Each email should simulate a customer contacting a support team. Distribute the emails among the following three categories:

        1. Shipment Inquiry WITH Order Number: 
        - These customers are asking for shipping updates and include a valid order number in their message.
        - Generate order numbers in various formats between 10-25 digits in length. Include a mix of the following styles:
            1. Standard numerical format (10-25 digits):
                - Plain numbers: 1234567890123456789
                - With prefix: #1234567890123456
                - With separator: 12345-67890-12345

            2. Carrier-style formats:
                - USPS style (20-25 digits starting with 9): 91234567890123456789012
                - UPS style (1Z followed by 16 alphanumeric characters): 1Z9876A1B2C3D4E5F6G7
                - FedEx style (12-14 digits): 123456789012, 1234567890123, 12345678901234

        2. Shipment Inquiry WITHOUT Order Number:
        - These customers are asking about their order shipment status but do NOT include an order number.
        - Instead, use hints like customer name, email context, or vague references to the product or order date.

        3. General or Non-Shipment Related Emails:
        - These could be inquiries about promotions, returns, complaints, or general feedback.
        - Should clearly not mention anything about tracking or shipping.

        Across all emails, vary the following parameters:
        - Issue Types: Use a range of issue categories from {self.issue_types}.
        - Product Types: Mention products conceptually related to {self.product_types}.
        - Complexity Levels: Reflect the tone and depth described in {complexity_section}.
            - simple: Brief, direct inquiry with basic language
            - medium: Some details and context with average vocabulary
            - complex: Multiple questions or concerns with more sophisticated language
            - very_complex: Detailed situation description with advanced vocabulary, multiple references to order details, and complex requests
        - Customer details: Use a variety of customer names, tones, greetings, and sign-offs to simulate real-world diversity.

        First, understand the structure of a single email object:
        ```python{single_email_model_def}
        ```

        Now, format your entire response as a single JSON object conforming to the following Pydantic model,
        which contains a list called 'emails' holding exactly {num_samples} distinct `EmailOutput` objects:

        ```python{list_model_def}
        ```
        {reference_section}

        Ensure the final output is a valid JSON object matching the `EmailOutputList` structure.
        """

        # Return the prompt and the Pydantic model class for the list
        return prompt, self.EmailOutputList