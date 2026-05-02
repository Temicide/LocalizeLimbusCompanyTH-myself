"""Translation memory system for character-consistent translations.

Indexes existing EN→TH translation pairs from completed StoryData files,
organized by character, to provide few-shot examples for consistent
character voice in new translations.
"""
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import EN_DIR, TH_DIR
from .logger import TranslationLogger


class TranslationMemory:
    """Stores and retrieves previous translations indexed by character.
    
    Scans paired EN/TH files to build a per-character index of
    (source_english, target_thai) pairs. When translating new content,
    provides relevant examples for each character to ensure consistent
    voice, pronouns, and vocabulary.
    """

    MEMORY_FILE = Path(__file__).parent.parent / "data" / "translation_memory.json"
    MAX_EXAMPLES_PER_CHARACTER = 8
    MAX_SOURCE_LENGTH = 200
    MIN_SOURCE_LENGTH = 5

    def __init__(self, logger: TranslationLogger, korean_to_english: Dict[str, str] = None):
        self.logger = logger
        self.korean_to_english = korean_to_english or {}
        self.memory: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.vocabulary: Dict[str, Dict[str, str]] = {}
        self._loaded = False

    def build_from_translations(self, context_builder=None):
        """Scan all paired EN/TH StoryData files and index translations by character.
        
        Args:
            context_builder: Optional ContextBuilder instance for Korean→English resolution.
                           If not provided, only korean_to_english mapping is used.
        """
        if self._loaded:
            return

        self.logger.log_info("Building translation memory from existing translations...")

        en_dir = EN_DIR / "StoryData"
        th_dir = TH_DIR / "StoryData"

        if not en_dir.exists() or not th_dir.exists():
            self.logger.log_warning("EN/TH StoryData directories not found, skipping memory build")
            return

        en_files = {f.name for f in en_dir.glob("*.json")}
        th_files = {f.name for f in th_dir.glob("*.json")}
        paired = en_files & th_files

        total_pairs = 0
        total_entries = 0
        characters_found = set()

        for fname in sorted(paired):
            en_path = en_dir / fname
            th_path = th_dir / fname

            try:
                with open(en_path, 'r', encoding='utf-8') as f:
                    en_data = json.load(f)
                with open(th_path, 'r', encoding='utf-8') as f:
                    th_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            if "dataList" not in en_data or "dataList" not in th_data:
                continue

            en_list = en_data["dataList"]
            th_list = th_data["dataList"]

            if len(en_list) != len(th_list):
                continue

            for en_entry, th_entry in zip(en_list, th_list):
                if not isinstance(en_entry, dict) or not isinstance(th_entry, dict):
                    continue

                model = en_entry.get("model", "")
                if not model:
                    continue

                en_content = en_entry.get("content", "") or en_entry.get("dialog", "") or en_entry.get("dlg", "")
                th_content = th_entry.get("content", "") or th_entry.get("dialog", "") or th_entry.get("dlg", "")

                if not en_content or not th_content:
                    continue

                en_stripped = en_content.strip()
                th_stripped = th_content.strip()

                if (len(en_stripped) < self.MIN_SOURCE_LENGTH or
                    len(en_stripped) > self.MAX_SOURCE_LENGTH):
                    continue

                english_name = self._resolve_model_to_english(model, context_builder)
                if not english_name:
                    continue

                self.memory[english_name].append((en_stripped, th_stripped))
                total_entries += 1
                characters_found.add(english_name)

            total_pairs += 1

        for char_name in self.memory:
            if len(self.memory[char_name]) > 50:
                import random
                random.seed(42)
                self.memory[char_name] = random.sample(self.memory[char_name], 50)

        self._extract_vocabulary()

        self._loaded = True
        self.logger.log_info(
            f"Translation memory built: {total_pairs} files, "
            f"{total_entries} entries, {len(characters_found)} characters"
        )

    def _resolve_model_to_english(self, model: str, context_builder=None) -> str:
        """Resolve a Korean model name to an English character name."""
        if model in self.korean_to_english:
            return self.korean_to_english[model]

        if context_builder:
            english_name, _, _ = context_builder.resolve_character(model, "")
            if english_name:
                return english_name

        return ""

    def _extract_vocabulary(self):
        """Extract character-specific vocabulary patterns from translation memory.
        
        Analyzes each character's translations to find consistent patterns:
        - First-person pronouns (ข้า, ฉัน, ผม, กู, etc.)
        - Speech register markers (ครับ/ค่ะ/นะ/น่ะ/หรอก etc.)
        - Character catchphrases
        """
        thai_pronouns = [
            "ข้า", "ข้าพเจ้า", "ฉัน", "ผม", "กู", "อาขอ", "อั๊ขอ", "เรา",
            "หมอ", "วะ", "ขิง", "กระหม่อม",
        ]

        thai_speech_markers = [
            "ครับ", "ค่ะ", "นะ", "น่ะ", "หรอก", "สิ", "ดิ",
            "เจ้า", "ท่าน", "เอ้ย", "โว้ย",
        ]

        for char_name, entries in self.memory.items():
            if len(entries) < 3:
                continue

            vocab = {
                "pronouns": [],
                "markers": [],
                "sample_count": len(entries),
            }

            pronoun_counts = defaultdict(int)
            marker_counts = defaultdict(int)

            for en_text, th_text in entries:
                for pronoun in thai_pronouns:
                    if pronoun in th_text:
                        pronoun_counts[pronoun] += 1

                for marker in thai_speech_markers:
                    if marker in th_text:
                        marker_counts[marker] += 1

            for pronoun, count in sorted(pronoun_counts.items(), key=lambda x: -x[1]):
                if count >= len(entries) * 0.3:
                    vocab["pronouns"].append(pronoun)

            for marker, count in sorted(marker_counts.items(), key=lambda x: -x[1]):
                if count >= len(entries) * 0.3:
                    vocab["markers"].append(marker)

            if vocab["pronouns"] or vocab["markers"]:
                self.vocabulary[char_name] = vocab

    def get_examples_for_character(self, english_name: str, n: int = None) -> List[Tuple[str, str]]:
        """Get translation examples for a specific character.
        
        Args:
            english_name: English character name (e.g., "Don Quixote")
            n: Number of examples to return (default: MAX_EXAMPLES_PER_CHARACTER)
            
        Returns:
            List of (english_text, thai_text) tuples
        """
        if n is None:
            n = self.MAX_EXAMPLES_PER_CHARACTER

        entries = self.memory.get(english_name, [])
        if not entries:
            return []

        import random
        random.seed(hash(english_name))
        sampled = random.sample(entries, min(n, len(entries)))
        return sampled

    def get_examples_for_scene(self, character_names: List[str], n_per_char: int = 3) -> str:
        """Build a few-shot context string with examples from multiple characters.
        
        Args:
            character_names: List of English character names in the scene
            n_per_char: Number of examples per character
            
        Returns:
            Formatted string for injection into translation prompt
        """
        if not self.memory:
            return ""

        examples_by_char = []
        for char_name in character_names:
            entries = self.get_examples_for_character(char_name, n_per_char)
            if entries:
                examples_by_char.append((char_name, entries))

        if not examples_by_char:
            return ""

        lines = ["ตัวอย่างการแปลก่อนหน้า (ใช้เป็นแนวทางสำหรับรูปแบบภาษา):"]

        for char_name, entries in examples_by_char:
            for en_text, th_text in entries:
                en_short = en_text[:120] + ("..." if len(en_text) > 120 else "")
                th_short = th_text[:120] + ("..." if len(th_text) > 120 else "")
                lines.append(f"  [{char_name}] อังกฤษ: \"{en_short}\"")
                lines.append(f"  [{char_name}] ไทย: \"{th_short}\"")

        return "\n".join(lines)

    def get_vocabulary_string(self, english_name: str) -> str:
        """Get vocabulary consistency notes for a character.
        
        Returns a Thai string describing the character's consistent
        pronoun/speech marker usage, for injection into prompts.
        """
        vocab = self.vocabulary.get(english_name, {})
        if not vocab:
            return ""

        parts = []
        if vocab.get("pronouns"):
            pronouns = " / ".join(vocab["pronouns"])
            parts.append(f"สรรพนามบุคคลที่ 1: {pronouns}")
        if vocab.get("markers"):
            markers = " / ".join(vocab["markers"])
            parts.append(f"คำลงท้าย/ลักษณะพิเศษ: {markers}")

        if not parts:
            return ""

        return f"รูปแบบที่ใช้สม่ำเสมอ: {', '.join(parts)}"

    def add_entry(self, english_name: str, en_text: str, th_text: str):
        """Add a new translation entry to memory (for live updates during translation)."""
        if len(en_text) < self.MIN_SOURCE_LENGTH or len(en_text) > self.MAX_SOURCE_LENGTH:
            return

        self.memory[english_name].append((en_text.strip(), th_text.strip()))

    def save(self):
        """Persist translation memory to disk."""
        memory_data = {}
        for char_name, entries in self.memory.items():
            memory_data[char_name] = [
                {"en": en, "th": th} for en, th in entries
            ]

        vocab_data = {}
        for char_name, vocab in self.vocabulary.items():
            vocab_data[char_name] = vocab

        data = {
            "version": 1,
            "memory": memory_data,
            "vocabulary": vocab_data,
        }

        self.MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.log_info(f"Translation memory saved: {len(self.memory)} characters, "
                           f"{sum(len(v) for v in self.memory.values())} entries")

    def load(self) -> bool:
        """Load translation memory from disk cache.
        
        Returns:
            True if loaded successfully, False if no cache exists
        """
        if not self.MEMORY_FILE.exists():
            return False

        try:
            with open(self.MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            memory_data = data.get("memory", {})
            for char_name, entries in memory_data.items():
                self.memory[char_name] = [
                    (e["en"], e["th"]) for e in entries
                ]

            vocab_data = data.get("vocabulary", {})
            self.vocabulary = vocab_data

            self._loaded = True
            self.logger.log_info(
                f"Translation memory loaded from cache: {len(self.memory)} characters, "
                f"{sum(len(v) for v in self.memory.values())} entries"
            )
            return True

        except Exception as e:
            self.logger.log_error("Error loading translation memory", e)
            return False

    def get_stats(self) -> dict:
        """Return statistics about the translation memory."""
        char_counts = {}
        for char_name, entries in self.memory.items():
            char_counts[char_name] = len(entries)

        return {
            "total_characters": len(self.memory),
            "total_entries": sum(len(v) for v in self.memory.values()),
            "characters_with_vocabulary": len(self.vocabulary),
            "top_characters": sorted(char_counts.items(), key=lambda x: -x[1])[:10],
        }