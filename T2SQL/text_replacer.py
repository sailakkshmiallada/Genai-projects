import re
import json
from typing import Dict, List
import inflect

class TextReplacer:
    def __init__(self, replacements_file):
        """
        Initialize the TextReplacer with a dictionary of replacements.
        :param replacements: A dictionary where keys are standard phrases and values are lists of variations.
        """
        with open(replacements_file, 'r') as f:
            self.replacements = json.load(f)
        self.p = inflect.engine()
        self.replacements = self._expand_replacements(self.replacements)
        self.sorted_replacements = sorted(
            [(standard, variation) for standard, variations in self.replacements.items() for variation in variations],
            key=lambda x: len(x[1]), reverse=True
        )

    def _expand_replacements(self, replacements: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Expand the replacements dictionary to include both singular and plural forms.
        """
        expanded = {}
        for standard, variations in replacements.items():
            singular_standard = self.p.singular_noun(standard) or standard
            plural_standard = self.p.plural(standard)
            
            expanded_variations = set()
            for variation in variations:
                expanded_variations.add(variation.lower())
                expanded_variations.add(self.p.singular_noun(variation) or variation.lower())
                expanded_variations.add(self.p.plural(variation))
            
            expanded[singular_standard] = list(expanded_variations)
            if plural_standard != singular_standard:
                expanded[plural_standard] = list(expanded_variations)
        
        return expanded

    def replace_text(self, text: str) -> str:
        """
        Replace variations in the input text with their corresponding standard phrases.
        This version allows for matching variations even with multiple spaces between words.

        :param text: The input text to be processed.
        :return: The processed text with all variations replaced by their standard phrases.
        """
        placeholder_dict = {}
        placeholder_counter = 0

        for standard, variation in self.sorted_replacements:
            variation_words = variation.split()
            variation_pattern = r'\s+'.join(map(re.escape, variation_words))
            pattern = re.compile(r'\b(' + variation_pattern + r')\b', re.IGNORECASE)

            def replacement(match):
                nonlocal placeholder_counter
                placeholder = f"__PLACEHOLDER_{placeholder_counter}__"
                placeholder_dict[placeholder] = standard
                placeholder_counter += 1
                return placeholder

            text = pattern.sub(replacement, text)

        for placeholder, standard in placeholder_dict.items():
            text = text.replace(placeholder, standard)

        return text



def format_criteria(text):
    replacer = TextReplacer("replacements.json")
    processed_text = replacer.replace_text(text)
    return processed_text
