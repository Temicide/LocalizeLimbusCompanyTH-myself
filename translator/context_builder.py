"""Context builder for character profiles and worldbuilding."""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .config import (
    EN_DIR, WORLDBUILDING_GUIDE, 
    load_character_profiles, save_character_profiles
)
from .logger import TranslationLogger


class ContextBuilder:
    """Builds context for translation from character profiles and worldbuilding."""
    
    def __init__(self, logger: TranslationLogger):
        self.logger = logger
        self.character_profiles = {}
        self.worldbuilding_context = ""
        self.preserved_terms = set()
        
    def build_all_context(self):
        """Build all context - character profiles and worldbuilding."""
        self.logger.log_info("Building context from character files and worldbuilding guide...")
        
        # Load or build character profiles
        existing_profiles = load_character_profiles()
        if existing_profiles:
            self.logger.log_info("Loading existing character profiles")
            self.character_profiles = existing_profiles
        else:
            self.logger.log_info("Analyzing character dialogue files...")
            self._build_character_profiles()
            save_character_profiles(self.character_profiles)
        
        # Build worldbuilding context
        self._build_worldbuilding_context()
        
        self.logger.log_info(f"Context built: {len(self.character_profiles)} characters, "
                           f"worldbuilding guide loaded")
    
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
        
        # Analyze speech patterns
        speech_patterns = self._analyze_speech_patterns(dialogs)
        
        # Determine tone
        tone = self._determine_tone(dialogs, character_name)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(dialogs)
        
        return {
            "name": character_name,
            "tellers": list(tellers),
            "sample_dialogs": dialogs[:5],  # Store first 5 as samples
            "speech_patterns": speech_patterns,
            "tone": tone,
            "key_phrases": key_phrases,
            "dialog_count": len(dialogs),
        }
    
    def _analyze_speech_patterns(self, dialogs: List[str]) -> List[str]:
        """Analyze speech patterns from dialogues."""
        patterns = []
        
        all_text = " ".join(dialogs).lower()
        
        # Check for archaic/formal speech
        archaic_words = ["shall", "thou", "thee", "thy", "shan't", "shan't", "ought", "must needs"]
        if any(word in all_text for word in archaic_words):
            patterns.append("archaic_formal")
        
        # Check for casual speech
        casual_words = ["welp", "eh", "huh", "yeah", "gonna", "wanna"]
        if any(word in all_text for word in casual_words):
            patterns.append("casual")
        
        # Check for terse/short responses
        avg_length = sum(len(d) for d in dialogs) / max(len(dialogs), 1)
        if avg_length < 50:
            patterns.append("terse")
        
        # Check for analytical speech
        analytical_words = ["analysis", "rational", "logic", "data", "probability"]
        if any(word in all_text for word in analytical_words):
            patterns.append("analytical")
        
        # Check for enthusiastic/heroic
        heroic_words = ["hero", "justice", "glory", "shall", "victory", "charge"]
        if any(word in all_text for word in heroic_words):
            patterns.append("heroic")
        
        if not patterns:
            patterns.append("standard")
        
        return patterns
    
    def _determine_tone(self, dialogs: List[str], character_name: str) -> str:
        """Determine character's general tone."""
        all_text = " ".join(dialogs).lower()
        
        # Check personality markers
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
        """Extract distinctive phrases the character uses."""
        # Simple extraction of phrases that appear multiple times
        phrase_counts = {}
        
        for dialog in dialogs:
            # Look for phrases in quotes or with special punctuation
            phrases = re.findall(r'["\']([^"\']{10,50})["\']', dialog)
            for phrase in phrases:
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        # Return most common phrases
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
            
            # Extract key sections
            sections = []
            
            # Look for key headers and their content
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
                    # Limit section length
                    if len(section_text) > 500:
                        section_text = section_text[:500] + "..."
                    sections.append(f"{header}: {section_text}")
            
            self.worldbuilding_context = "\n\n".join(sections)
            
        except Exception as e:
            self.logger.log_error("Error reading worldbuilding guide", e)
    
    def get_context_for_file(self, filename: str, teller: str = "") -> str:
        """Get appropriate context for a specific file."""
        contexts = []
        
        # Add worldbuilding context (truncated for API efficiency)
        if self.worldbuilding_context:
            contexts.append("WORLD SETTING:\n" + self.worldbuilding_context[:1000])
        
        # Add character context if applicable
        if teller and "AbDlg_" in filename:
            # Extract character name from filename
            char_name = filename.replace("AbDlg_", "").replace(".json", "")
            if char_name in self.character_profiles:
                profile = self.character_profiles[char_name]
                char_context = f"""CHARACTER PROFILE - {char_name}:
Tone: {profile.get('tone', 'neutral')}
Speech patterns: {', '.join(profile.get('speech_patterns', ['standard']))}
Key phrases: {', '.join(profile.get('key_phrases', []))}
Sample dialog style: {' | '.join(profile.get('sample_dialogs', [])[:2])}
"""
                contexts.append(char_context)
        
        return "\n\n".join(contexts)
    
    def get_character_notes(self, teller: str) -> str:
        """Get translation notes for a specific character."""
        # Map teller names to character profile keys
        char_map = {
            "Don Quixote": "DonQuixote",
            "Faust": "Faust",
            "W. Faust": "Faust",
            "Gregor": "Gregor",
            "Liu Gregor": "Gregor",
            "Ryōshū": "Ryoshu",
            "Ryoshu": "Ryoshu",
            "Seven Ryōshū": "Ryoshu",
            "Seven Ryoshu": "Ryoshu",
        }
        
        char_key = char_map.get(teller, "")
        if char_key and char_key in self.character_profiles:
            profile = self.character_profiles[char_key]
            tone = profile.get('tone', '')
            
            notes = {
                "enthusiastic_chivalric": "Use elevated, heroic Thai. Character speaks like a chivalric knight.",
                "intellectual_confident": "Use formal, precise Thai. Character is analytical and confident.",
                "world_weary_casual": "Use relaxed, casual Thai. Character is laid-back and world-weary.",
                "terse_artistic": "Use concise but artistic Thai. Character values brevity and aesthetics.",
            }
            
            return notes.get(tone, "Use natural Thai appropriate for the context.")
        
        return ""
