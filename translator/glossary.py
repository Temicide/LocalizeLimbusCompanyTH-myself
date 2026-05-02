"""Glossary system for deterministic translation of places, tellers, and titles.

Loads curated glossary data from JSON files and provides lookup methods.
Used by engine.py to pre-translate known strings before sending to AI.
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

DATA_DIR = Path(__file__).parent.parent / "data"


class Glossary:
    """Centralized lookup for deterministic translations of places, tellers, and titles."""
    
    def __init__(self):
        self.places: Dict[str, str] = {}
        self.tellers: Dict[str, str] = {}
        self.titles: Dict[str, str] = {}
        self.terms: Dict[str, str] = {}
        self._loaded = False
    
    def load(self):
        """Load all glossary data from JSON files."""
        self._load_json("place_glossary.json", self.places)
        self._load_json("teller_glossary.json", self.tellers)
        self._load_json("title_glossary.json", self.titles)
        self._load_json("term_glossary.json", self.terms)
        self._loaded = True
    
    def _load_json(self, filename: str, target: dict):
        """Load a glossary JSON file into the target dict."""
        filepath = DATA_DIR / filename
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict) and 'th' in value:
                            target[key] = value['th']
                        elif isinstance(value, str):
                            target[key] = value
            except Exception:
                pass
    
    def lookup_place(self, en_place: str) -> Optional[str]:
        """Look up a place name in the glossary.
        
        Args:
            en_place: English place string (may contain newlines)
        Returns:
            Thai translation if found, None otherwise
        """
        if not self._loaded:
            self.load()
        
        # Normalize: strip newlines and extra spaces
        normalized = ' '.join(en_place.split())
        
        # Exact match on normalized
        if normalized in self.places:
            return self.places[normalized]
        
        # Try original
        if en_place in self.places:
            return self.places[en_place]
        
        # Try lowercase match
        lower = normalized.lower()
        for key, value in self.places.items():
            if key.lower() == lower:
                return value
        
        return None
    
    def lookup_teller(self, en_teller: str) -> Optional[str]:
        """Look up a teller name in the glossary.
        
        Args:
            en_teller: English teller string
        Returns:
            Thai translation if found, None otherwise
        """
        if not self._loaded:
            self.load()
        
        # Exact match
        if en_teller in self.tellers:
            return self.tellers[en_teller]
        
        # Strip trailing question mark for uncertain tellers like "Heathcliff?"
        stripped = en_teller.rstrip('?').strip()
        if stripped in self.tellers:
            return self.tellers[stripped]
        
        return None
    
    def lookup_title(self, en_title: str) -> Optional[str]:
        """Look up a title in the glossary.
        
        Args:
            en_title: English title string
        Returns:
            Thai translation if found, None otherwise
        """
        if not self._loaded:
            self.load()
        
        if en_title in self.titles:
            return self.titles[en_title]
        
        # Try pattern-based title matching
        return self._match_title_pattern(en_title)
    
    def _match_title_pattern(self, title: str) -> Optional[str]:
        """Try to match a title against known patterns and generate Thai."""
        # "Grade/Class/Level N Fixer" -> "Fixer ระดับ N"
        m = re.match(r'Grade\s+(\d+)\s+Fixer', title, re.IGNORECASE)
        if m:
            return f"Fixer ระดับ {m.group(1)}"
        
        m = re.match(r'Class\s+(\d+)\s+Fixer', title, re.IGNORECASE)
        if m:
            return f"Fixer ระดับ {m.group(1)}"
        
        m = re.match(r'Level\s+(\d+)\s+Fixer', title, re.IGNORECASE)
        if m:
            return f"Fixer ระดับ {m.group(1)}"
        
        # "[Corp] [Title]" patterns
        corp_patterns = [
            (r'G\s+Corp\.?\s+Remnant', 'เศษซาก G Corp.'),
            (r'Remnant\s+of\s+G\s+Corp\.?', 'เศษซาก G Corp.'),
        ]
        for pattern, replacement in corp_patterns:
            if re.match(pattern, title, re.IGNORECASE):
                return replacement
        
        # "X Section N" -> "X สาขาที่ N"
        m = re.match(r'(\w+)\s+Section\s+(\d+)', title, re.IGNORECASE)
        if m:
            return f"{m.group(1)} สาขาที่ {m.group(2)}"
        
        # "Class N [Role] Staff" patterns
        m = re.match(r'Class\s+(\d+)\s+Collection\s+Staff', title, re.IGNORECASE)
        if m:
            return f"เจ้าหน้าที่เก็บกู้ ระดับ {m.group(1)}"
        
        m = re.match(r'Class\s+(\d+)\s+Clerical\s+Staff', title, re.IGNORECASE)
        if m:
            return f"เจ้าหน้าที่สารรรพกร ระดับ {m.group(1)}"
        
        m = re.match(r'Class\s+(\d+)\s+Excision\s+Staff', title, re.IGNORECASE)
        if m:
            return f"เจ้าหน้าที่ผ่าตัด ระดับ {m.group(1)}"
        
        m = re.match(r'Class\s+(\d+)\s+Audit\s+Staff', title, re.IGNORECASE)
        if m:
            return f"เจ้าหน้าที่ตรวจสอบ ระดับ {m.group(1)}"
        
        m = re.match(r'Class\s+(\d+)\s+Collector', title, re.IGNORECASE)
        if m:
            return f"นักสะสม ระดับ {m.group(1)}"
        
        return None
    
    def lookup_term(self, en_term: str) -> Optional[str]:
        """Look up a game/adjective term in the glossary."""
        if not self._loaded:
            self.load()
        return self.terms.get(en_term)


# Global glossary instance
_glossary_instance: Optional[Glossary] = None


def get_glossary() -> Glossary:
    """Get the global glossary instance, loading if necessary."""
    global _glossary_instance
    if _glossary_instance is None:
        _glossary_instance = Glossary()
        _glossary_instance.load()
    return _glossary_instance