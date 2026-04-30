"""Limbus Company Thai Localization Translator."""

from .config import (
    EN_DIR, TH_DIR, LOGS_DIR,
    PRESERVED_TERMS, TRANSLATABLE_FIELDS,
    load_state, save_state,
    load_character_profiles, save_character_profiles,
)
from .logger import TranslationLogger, setup_logger
from .ollama_client import OllamaClient
from .context_builder import ContextBuilder
from .file_processor import FileProcessor
from .engine import TranslationEngine

__version__ = "1.0.0"
__all__ = [
    "TranslationEngine",
    "ContextBuilder",
    "FileProcessor",
    "OllamaClient",
    "TranslationLogger",
    "EN_DIR",
    "TH_DIR",
    "LOGS_DIR",
]