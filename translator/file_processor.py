"""Enhanced file processor with proper tag preservation."""
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

from .config import TRANSLATABLE_FIELDS, PRESERVED_TERMS, CHARACTER_NAMES
from .logger import TranslationLogger


class FileProcessor:
    """Process JSON files for translation with advanced tag preservation."""
    
    # Patterns to preserve exactly (never translate these)
    PRESERVE_PATTERNS = [
        # Unity rich text tags
        r'<color=[^>]+>',
        r'</color>',
        r'<b>',
        r'</b>',
        r'<i>',
        r'</i>',
        r'<u>',
        r'</u>',
        r'<mark[^>]*>',
        r'</mark>',
        r'<sprite[^>]*>',
        r'<size=[^>]+>',
        r'</size>',
        r'<ruby=[^>]+>',
        r'</ruby>',
        
        # Game mechanic brackets
        r'\[[A-Za-z][A-Za-z0-9_\s]*\]',  # [Breath], [Charge], etc.
        
        # Placeholders
        r'\[\{[^}]+\}\]',  # [{0}], [{1}]
        r'\{\{[^}]+\}\}',  # {{variable}}
        r'%[sd]',
        r'%\d*\.?\d*[df]',
        
        # HTML-like line breaks
        r'<br\s*/?>',
        
        # Special markers
        r'@[^\s]+',
        r'#[0-9a-fA-F]+',
    ]
    
    def __init__(self, logger: TranslationLogger):
        self.logger = logger
        self.preserved_pattern = self._build_preserved_pattern()
        self.compiled_patterns = [re.compile(p) for p in self.PRESERVE_PATTERNS]
        
    def _build_preserved_pattern(self) -> re.Pattern:
        """Build regex pattern to identify preserved game terms."""
        sorted_terms = sorted(PRESERVED_TERMS, key=len, reverse=True)
        escaped_terms = [re.escape(term) for term in sorted_terms]
        pattern = '|'.join(escaped_terms)
        return re.compile(f'({pattern})')
    
    def protect_special_tokens(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Protect all special tokens, HTML tags, brackets, and placeholders.
        
        Returns (protected_text, token_map) where token_map maps
        placeholders back to original tokens.
        """
        token_map = {}
        counter = 0
        
        def make_placeholder():
            nonlocal counter
            ph = f"§§§{counter:04d}§§§"
            counter += 1
            return ph
        
        # First pass: protect Unity/HTML tags and brackets
        for pattern in self.compiled_patterns:
            def replace_match(match):
                original = match.group(0)
                # Don't double-protect
                if original.startswith('§§§') and original.endswith('§§§'):
                    return original
                placeholder = make_placeholder()
                token_map[placeholder] = original
                return placeholder
            
            text = pattern.sub(replace_match, text)
        
        # Second pass: protect game terms (but not if already protected)
        def replace_term(match):
            original = match.group(0)
            if original.startswith('§§§') and original.endswith('§§§'):
                return original
            placeholder = make_placeholder()
            token_map[placeholder] = original
            return placeholder
        
        text = self.preserved_pattern.sub(replace_term, text)
        
        return text, token_map
    
    def restore_special_tokens(self, text: str, token_map: Dict[str, str]) -> str:
        """Restore all protected tokens."""
        # Sort by placeholder number in descending order to avoid partial replacements
        items = sorted(token_map.items(), key=lambda x: int(x[0].replace('§§§', '').replace('§§§', '')), reverse=True)
        for placeholder, original in items:
            text = text.replace(placeholder, original)
        return text
    
    def extract_translatable_texts(self, data: Any, path: str = "") -> List[Tuple[str, str, Any]]:
        """Extract translatable texts from JSON structure."""
        texts = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                if key in TRANSLATABLE_FIELDS and isinstance(value, str):
                    if self._is_translatable(value):
                        texts.append((current_path, key, value))
                elif isinstance(value, (dict, list)):
                    texts.extend(self.extract_translatable_texts(value, current_path))
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                texts.extend(self.extract_translatable_texts(item, current_path))
        
        return texts
    
    def _is_translatable(self, text: str) -> bool:
        """Check if text should be translated."""
        if not text or not text.strip():
            return False
        
        # Skip if only whitespace
        if text.strip() == "":
            return False
        
        # Skip if only placeholders/special chars
        # After removing all protected patterns, if nothing left, skip
        test_text = text
        for pattern in self.compiled_patterns:
            test_text = pattern.sub('', test_text)
        
        # Also remove preserved terms
        test_text = self.preserved_pattern.sub('', test_text)
        
        if not test_text.strip():
            return False
        
        # Skip if only numbers/punctuation
        if re.match(r'^[\s\d\-_\(\)\[\]\{\}\.\,\!\?\:\;\'\"\n\r]*$', test_text.strip()):
            return False
        
        return True
    
    def group_by_scene(self, texts: List[Tuple[str, str, str]], data: Any) -> List[List[Tuple[str, str, str]]]:
        """
        Group related texts into scenes for batch translation.
        
        For StoryData files, group consecutive content entries.
        For other files, return as single group.
        """
        if not texts:
            return []
        
        # For now, group all texts in a file together for context
        # This allows the model to understand character relationships
        return [texts]
    
    def update_json_with_translations(self, data: Any, translations: Dict[str, str], path: str = "") -> Any:
        """Update JSON data with translations."""
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                if key in TRANSLATABLE_FIELDS and isinstance(value, str):
                    if current_path in translations:
                        new_data[key] = translations[current_path]
                    else:
                        new_data[key] = value
                elif isinstance(value, (dict, list)):
                    new_data[key] = self.update_json_with_translations(value, translations, current_path)
                else:
                    new_data[key] = value
            return new_data
                    
        elif isinstance(data, list):
            new_list = []
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                new_list.append(self.update_json_with_translations(item, translations, current_path))
            return new_list
        
        return data
    
    def get_teller_from_data(self, data: Any) -> str:
        """Extract teller/character name from dialogue data."""
        if isinstance(data, dict):
            if "teller" in data and isinstance(data["teller"], str):
                return data["teller"]
            
            if "dataList" in data and isinstance(data["dataList"], list):
                for entry in data["dataList"]:
                    if isinstance(entry, dict) and "teller" in entry:
                        return entry["teller"]
        
        return ""
    
    def validate_json_structure(self, original: Any, translated: Any) -> bool:
        """Validate that translation preserved JSON structure."""
        if type(original) != type(translated):
            return False
        
        if isinstance(original, dict):
            if set(original.keys()) != set(translated.keys()):
                return False
            for key in original:
                if not self.validate_json_structure(original[key], translated[key]):
                    return False
        
        elif isinstance(original, list):
            if len(original) != len(translated):
                return False
            for i in range(len(original)):
                if not self.validate_json_structure(original[i], translated[i]):
                    return False
        
        return True
    
    def load_json(self, filepath: Path) -> Any:
        """Load JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_json(self, data: Any, filepath: Path):
        """Save JSON file with proper formatting."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
