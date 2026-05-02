"""Context builder for character profiles and worldbuilding.

Loads character voice guides from MD-derived profiles and Korean name mappings
to provide per-entry character context for translation prompts.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .config import (
    EN_DIR, WORLDBUILDING_GUIDE,
    load_character_profiles, save_character_profiles
)
from .logger import TranslationLogger
from .character_profiles import (
    build_all_profiles, load_voice_guides, save_voice_guides,
    get_voice_guide_for_character
)
from .dictionaries import ENGLISH_TO_THAI_TELLER, get_character_voice_guide


class ContextBuilder:
    """Builds context for translation from character profiles and worldbuilding."""
    
    VOICE_GUIDES_FILE = Path(__file__).parent.parent / "data" / "character_voice_guides.json"
    NAME_MAPPING_FILE = Path(__file__).parent.parent / "data" / "reference" / "character_name_mapping.json"
    
    def __init__(self, logger: TranslationLogger):
        self.logger = logger
        self.character_profiles = {}
        self.worldbuilding_context = ""
        self.preserved_terms = set()
        self.voice_guides: Dict[str, str] = {}
        self.korean_to_english: Dict[str, str] = {}
        self.english_to_voice_key: Dict[str, str] = {}
    
    def build_all_context(self):
        """Build all context - character profiles, voice guides, and worldbuilding."""
        self.logger.log_info("Building context from character files and worldbuilding guide...")
        
        # Load or build character profiles from dialogue analysis
        existing_profiles = load_character_profiles()
        if existing_profiles:
            self.logger.log_info("Loading existing character profiles")
            self.character_profiles = existing_profiles
        else:
            self.logger.log_info("Analyzing character dialogue files...")
            self._build_character_profiles()
            save_character_profiles(self.character_profiles)
        
        # Load or build voice guides from MD character files
        self.voice_guides = load_voice_guides()
        if not self.voice_guides:
            self.logger.log_info("Building voice guides from character MD files...")
            self.voice_guides = build_all_profiles()
            save_voice_guides(self.voice_guides)
        self.logger.log_info(f"Loaded voice guides for {len(self.voice_guides)} characters")
        
        # Load Korean→English name mapping
        self._load_name_mapping()
        
        # Build worldbuilding context
        self._build_worldbuilding_context()
        
        self.logger.log_info(f"Context built: {len(self.character_profiles)} dialogue profiles, "
                           f"{len(self.voice_guides)} voice guides, "
                           f"{len(self.korean_to_english)} Korean name mappings, "
                           f"worldbuilding guide loaded")
    
    def _load_name_mapping(self):
        """Load the Korean→English character name mapping."""
        if self.NAME_MAPPING_FILE.exists():
            try:
                with open(self.NAME_MAPPING_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.korean_to_english = data.get("korean_to_english", {})
                self.logger.log_info(f"Loaded {len(self.korean_to_english)} Korean name mappings")
            except Exception as e:
                self.logger.log_error("Error loading name mapping", e)
                self.korean_to_english = {}
        else:
            self.logger.log_warning("Name mapping file not found, using fallback")
            self.korean_to_english = {}
    
    def resolve_character(self, model: str, teller: str = "") -> tuple:
        """Resolve a Korean model or English teller name to (english_name, thai_name, voice_key).
        
        Args:
            model: Korean model field from the JSON data
            teller: English teller field from the JSON data
            
        Returns:
            (english_name, thai_name, voice_guide_key) tuple
        """
        english_name = ""
        thai_name = ""
        voice_key = ""
        
        # 1. Try Korean model → English name
        if model and model in self.korean_to_english:
            english_name = self.korean_to_english[model]
        
        # 2. Try English teller → English name (direct)
        if teller and not english_name:
            english_name = teller
            # Strip identity prefixes like "Liu", "Seven", "Kurokumo", etc.
            for prefix in ["Liu ", "Seven ", "Kurokumo ", "Shi ", "Blade Lineage ",
                          "W. ", "R Corp. "]:
                if teller.startswith(prefix):
                    english_name = teller[len(prefix):].strip()
                    break
        
        # 3. Get Thai name
        if teller and teller in ENGLISH_TO_THAI_TELLER:
            thai_name = ENGLISH_TO_THAI_TELLER[teller]
        elif english_name and english_name in ENGLISH_TO_THAI_TELLER:
            thai_name = ENGLISH_TO_THAI_TELLER[english_name]
        
        # 4. Get voice guide key (MD file stem)
        if english_name:
            voice_key = self._english_to_voice_key(english_name)
        
        return (english_name, thai_name, voice_key)
    
    def _english_to_voice_key(self, english_name: str) -> str:
        """Map an English character name to the voice guide key (MD file stem)."""
        # Normalize macron characters for matching
        normalized = english_name.replace("ō", "o").replace("ū", "u").replace("ē", "e")
        
        # Direct lookup in voice guides - try both original and normalized
        key_variants = [
            english_name.replace(" ", "_"),
            normalized.replace(" ", "_"),
            english_name.replace(" ", "_").replace("-", "_"),
            normalized.replace(" ", "_").replace("-", "_"),
            english_name,
            normalized,
        ]
        
        for key in key_variants:
            if key in self.voice_guides:
                return key
        
        # Also try matching against keys in the voice guides with macron normalization
        for key in self.voice_guides:
            normalized_key = key.replace("ō", "o").replace("ū", "u").replace("ē", "e")
            if normalized_key.lower() == normalized.replace(" ", "_").lower():
                return key
        
        # Known name-to-file-stem mapping for common characters
        name_to_stem = {
            "Dante": "Dante",
            "Faust": "Faust",
            "Don Quixote": "Don_Quixote",
            "Ryoshu": "Ryoshu",
            "Ryōshū": "Ryoshu",
            "Meursault": "Meursault",
            "Hong Lu": "Hong_Lu",
            "Heathcliff": "Heathcliff",
            "Ishmael": "Ishmael",
            "Rodion": "Rodion",
            "Sinclair": "Sinclair",
            "Outis": "Outis",
            "Yi Sang": "Yi_Sang",
            "Gregor": "Gregor",
            "Vergilius": "Vergilius",
            "Charon": "Charon",
            "Kromer": "Kromer",
            "Dongrang": "Dongrang",
            "Ahab": "Ahab",
            "Catherine": "Catherine",
            "Hindley": "Hindley",
            "Linton": "Linton",
            "Bari": "Bari",
            "Dongbaek": "Dongbaek",
            "Demian": "Demian",
            "Aseah": "Aseah",
            "Hermann": "Hermann",
            "Effie": "Effie",
            "Samjo": "Samjo",
            "Sonya": "Sonya",
            "Yuri": "Yuri",
            "Hopkins": "Hopkins",
            "Gubo": "Gubo",
            "Sansón": "Sansón",
            "Dulcinea": "Dulcinea",
            "Nelly": "Nelly",
            "Queequeg": "Queequeg",
            "Starbuck": "Starbuck",
            "Stubb": "Stubb",
            "Erlking Heathcliff": "Erlking_Heathcliff",
            "Every Catherine": "Every_Catherine",
            "Hohenheim": "Hohenheim",
            "Guido": "Guido",
            "Ricardo": "Ricardo",
            "Alfonso": "Alfonso",
            "Vespa": "Vespa",
            "Josephine": "Josephine",
            "Paula": "Paula",
            "Moses": "Moses",
            "Ezra": "Ezra",
            "Shrenne": "Shrenne",
            "Siegfried": "Siegfried",
            "Bamboo-hatted Kim": "Bamboo-hatted_Kim",
            "Tomah": "Tomah",
            "Sancho": "Don_Quixote",
            "Rocinante": "Don_Quixote",
            "The Barber": "The_Barber",
            "The Priest": "The_Priest",
            "The Indigo Elder": "The_Indigo_Elder",
            "The Time Ripper": "The_Time_Ripper",
            "Eunbong's Bar & Fryers Owner": "Eunbongs_Bar__Fryers_Owner",
            "Old G Corp. Head Manager": "Old_G_Corp_Head_Manager",
            "Night Drifter": "Night_Drifter",
            "Carmen": "Carmen",
            "Mephistopheles": "Mephistopheles",
            "Dantes_Notes": "Dantes_Notes",
            "A Certain Sinclair": "A_Certain_Sinclair",
            "Wei": "Wei",
            "Zilu": "Zilu",
            "Zigong": "Zigong",
            "Xiren": "Xiren",
            "Han-ul": "Han-ul",
            "Jun": "Jun",
            "Kira": "Kira",
            "Camille": "Camille",
            "Bumble": "Bumble",
            "Callisto": "Callisto",
            "Alex": "Alex",
            "Alan": "Alan",
            "Aida": "Aida",
            "Araya": "Araya",
            "Rain": "Rain",
            "Ran": "Ran",
            "Ravi": "Ravi",
            "Ren": "Ren",
            "Rien": "Rien",
            "Rim": "Rim",
            "Niko": "Niko",
            "Marile": "Marile",
            "Lion": "Lion",
            "Panther": "Panther",
            "Wolf": "Wolf",
            "Cesara": "Cesara",
            "Sang Yi": "Sang_Yi",
        }
        
        stem = name_to_stem.get(english_name, "")
        if stem and stem in self.voice_guides:
            return stem
        
        # Fuzzy: try matching lowercased
        en_lower = english_name.lower().replace(" ", "_")
        for key in self.voice_guides:
            if key.lower().replace(" ", "_") == en_lower:
                return key
        
        return ""
    
    def get_voice_guide_for_model(self, model: str, teller: str = "") -> str:
        """Get the Thai voice guide for a character identified by model/teller.
        
        This is the primary method for injecting character voice context
        into translation prompts.
        """
        english_name, thai_name, voice_key = self.resolve_character(model, teller)
        
        voice_text = ""
        
        # 1. Try voice guide from MD profiles (most detailed)
        if voice_key and voice_key in self.voice_guides:
            voice_text = self.voice_guides[voice_key]
        
        # 2. Fallback to static voice guides in dictionaries.py
        if not voice_text and teller:
            voice_text = get_character_voice_guide(teller)
        
        # Build the result with character identification
        if english_name and thai_name and voice_text:
            return f"กำลังพูด: {thai_name} ({english_name})\n{voice_text}"
        elif english_name and voice_text:
            return f"กำลังพูด: {english_name}\n{voice_text}"
        elif voice_text:
            return voice_text
        
        return ""
    
    def get_characters_in_scene(self, data: dict) -> Dict[str, str]:
        """Extract all characters from a scene and return their voice guides.
        
        Returns a dict of {character_identifier: voice_guide_string}
        """
        characters = {}
        
        if isinstance(data, dict) and "dataList" in data:
            for entry in data["dataList"]:
                if not isinstance(entry, dict):
                    continue
                model = entry.get("model", "")
                teller = entry.get("teller", "")
                
                if not model and not teller:
                    continue
                
                english_name, thai_name, voice_key = self.resolve_character(model, teller)
                
                # Use english name as key to deduplicate
                char_key = english_name or teller or model
                if char_key and char_key not in characters and voice_key:
                    voice = self.get_voice_guide_for_model(model, teller)
                    if voice:
                        characters[char_key] = voice
        
        return characters
    
    def get_scene_context_string(self, data: dict) -> str:
        """Build a scene context string listing all characters and their voice guides.
        
        This is used when translating multi-character dialogue (StoryData files)
        to give the model context about who is in the scene.
        """
        characters = self.get_characters_in_scene(data)
        
        if not characters:
            return ""
        
        lines = ["ตัวละครในฉากนี้:"]
        for char_name, voice in characters.items():
            # Truncate each voice guide to keep context manageable
            voice_brief = voice[:200] if len(voice) > 200 else voice
            lines.append(f"- {voice_brief}")
        
        return "\n".join(lines)
    
    def get_context_for_file(self, filename: str, teller: str = "") -> str:
        """Get appropriate context for a specific file (legacy method, enhanced)."""
        contexts = []
        
        # Add worldbuilding context (truncated for API efficiency)
        if self.worldbuilding_context:
            contexts.append("WORLD SETTING:\n" + self.worldbuilding_context[:800])
        
        # Add character context if applicable
        if teller and "AbDlg_" in filename:
            # For AbDlg files, the teller is the character
            voice_guide = get_character_voice_guide(teller)
            if voice_guide:
                contexts.append(f"บุคลิกตัวละคร:\n{voice_guide}")
            
            # Also try MD-based voice guide
            model = ""  # AbDlg files use teller field, not model
            md_guide = self.get_voice_guide_for_model(model, teller)
            if md_guide and md_guide != voice_guide:
                contexts.append(md_guide)
        
        return "\n\n".join(contexts)
    
    def get_character_notes(self, teller: str) -> str:
        """Get translation notes for a specific character (legacy compatibility)."""
        voice = get_character_voice_guide(teller)
        if voice:
            return voice
        
        # Try MD-based voice guide
        english_name, thai_name, voice_key = self.resolve_character("", teller)
        if voice_key and voice_key in self.voice_guides:
            return self.voice_guides[voice_key]
        
        return ""
    
    # === Legacy methods (kept for backward compatibility) ===
    
    def _build_character_profiles(self):
        """Analyze AbDlg_*.json files to build character profiles."""
        character_files = list(EN_DIR.glob("AbDlg_*.json"))
        
        for char_file in character_files:
            character_name = char_file.stem.replace("AbDlg_", "")
            self.logger.log_info(f"Analyzing {character_name}...")
            
            try:
                with open(char_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                profile = self._analyze_character_dialogue(data, character_name)
                self.character_profiles[character_name] = profile
                
            except Exception as e:
                self.logger.log_error(f"Error analyzing {char_file.name}", e)
        
        self.logger.log_info(f"Built profiles for {len(self.character_profiles)} characters")
    
    def _analyze_character_dialogue(self, data: dict, character_name: str) -> dict:
        """Analyze dialogue to extract character traits."""
        dialogs = []
        tellers = set()
        
        for entry in data.get("dataList", []):
            dialog = entry.get("dialog", "").strip()
            teller = entry.get("teller", "")
            
            if dialog:
                dialogs.append(dialog)
            if teller:
                tellers.add(teller)
        
        speech_patterns = self._analyze_speech_patterns(dialogs)
        tone = self._determine_tone(dialogs, character_name)
        key_phrases = self._extract_key_phrases(dialogs)
        
        return {
            "name": character_name,
            "tellers": list(tellers),
            "sample_dialogs": dialogs[:5],
            "speech_patterns": speech_patterns,
            "tone": tone,
            "key_phrases": key_phrases,
            "dialog_count": len(dialogs),
        }
    
    def _analyze_speech_patterns(self, dialogs: List[str]) -> List[str]:
        patterns = []
        all_text = " ".join(dialogs).lower()
        
        archaic_words = ["shall", "thou", "thee", "thy", "shan't", "ought", "must needs"]
        if any(word in all_text for word in archaic_words):
            patterns.append("archaic_formal")
        
        casual_words = ["welp", "eh", "huh", "yeah", "gonna", "wanna"]
        if any(word in all_text for word in casual_words):
            patterns.append("casual")
        
        avg_length = sum(len(d) for d in dialogs) / max(len(dialogs), 1)
        if avg_length < 50:
            patterns.append("terse")
        
        analytical_words = ["analysis", "rational", "logic", "data", "probability"]
        if any(word in all_text for word in analytical_words):
            patterns.append("analytical")
        
        heroic_words = ["hero", "justice", "glory", "shall", "victory", "charge"]
        if any(word in all_text for word in heroic_words):
            patterns.append("heroic")
        
        if not patterns:
            patterns.append("standard")
        
        return patterns
    
    def _determine_tone(self, dialogs: List[str], character_name: str) -> str:
        all_text = " ".join(dialogs).lower()
        
        if "hero" in all_text or "justice" in all_text or character_name == "DonQuixote":
            return "enthusiastic_chivalric"
        elif "analysis" in all_text or "rational" in all_text or character_name == "Faust":
            return "intellectual_confident"
        elif "dumm gelaufen" in all_text or character_name == "Gregor":
            return "world_weary_casual"
        elif len(dialogs) > 0 and sum(len(d) for d in dialogs) / max(len(dialogs), 1) < 40:
            return "terse_artistic"
        else:
            return "neutral"
    
    def _extract_key_phrases(self, dialogs: List[str]) -> List[str]:
        phrase_counts = {}
        for dialog in dialogs:
            phrases = re.findall(r'["\']([^"\']{10,50})["\']', dialog)
            for phrase in phrases:
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        sorted_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
        return [p[0] for p in sorted_phrases[:3]]
    
    def _build_worldbuilding_context(self):
        """Extract key worldbuilding information from the guide."""
        if not WORLDBUILDING_GUIDE.exists():
            self.logger.log_warning("Worldbuilding guide not found, skipping")
            return
        
        try:
            with open(WORLDBUILDING_GUIDE, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sections = []
            key_headers = [
                "Limbus Company",
                "The World Scenario",
                "The Wings",
                "The Head",
                "E.G.O and Distortion",
                "Fixers and Syndicates",
            ]
            
            for header in key_headers:
                pattern = rf"## {re.escape(header)}.*?\n\n(.*?)(?=\n## |$)"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    section_text = match.group(1).strip()
                    if len(section_text) > 500:
                        section_text = section_text[:500] + "..."
                    sections.append(f"{header}: {section_text}")
            
            self.worldbuilding_context = "\n\n".join(sections)
            
        except Exception as e:
            self.logger.log_error("Error reading worldbuilding guide", e)