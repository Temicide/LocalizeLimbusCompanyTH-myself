"""Configuration module for the Limbus Company Thai Localization Translator."""
import json
import os
from pathlib import Path

# Base paths - relative to project root
BASE_DIR = Path(__file__).parent.parent
EN_DIR = BASE_DIR / "EN"
TH_DIR = BASE_DIR / "TH"
RESOURCES_DIR = BASE_DIR / "data" / "reference"
LOGS_DIR = BASE_DIR / "logs"

# Translation API Configuration
# Use OpenRouter instead of local Ollama
USE_OPENROUTER = True
OPENROUTER_API_KEYS = [
    "Your API Key"
]
OPENROUTER_MODEL = "google/gemma-4-31b-it"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Ollama Configuration (fallback)
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "scb10x/typhoon-translate1.5-4b"

# Processing Configuration
BATCH_SIZE = 5
DELAY_BETWEEN_REQUESTS = 2  # seconds
DELAY_BETWEEN_BATCHES = 5   # seconds

# Game terms that should NEVER be translated
PRESERVED_TERMS = {
    # Core Game Mechanics
    "E.G.O",
    "EGO",
    "Abnormality",
    "Abnormalities",
    "Sinners",
    "Sinner",
    "Golden Boughs",
    "Golden Bough",
    "Distortion",
    "Distortions",
    "Peccatula",
    
    # Organizations
    "Limbus Company",
    "LCB",
    "LCA",
    "LCC",
    "LCCA",
    "LCCB",
    "LCD",
    "LCE",
    "The City",
    "The Head",
    "The Eye",
    "The Claw",
    "Arbiters",
    "Beholders",
    "Claws",
    
    # Wings (Corporations)
    "A Corp",
    "B Corp", 
    "C Corp",
    "D Corp",
    "E Corp",
    "F Corp",
    "G Corp",
    "H Corp",
    "I Corp",
    "J Corp",
    "K Corp",
    "L Corp",
    "M Corp",
    "N Corp",
    "O Corp",
    "P Corp",
    "Q Corp",
    "R Corp",
    "S Corp",
    "T Corp",
    "U Corp",
    "V Corp",
    "W Corp",
    "X Corp",
    "Y Corp",
    "Z Corp",
    
    # Districts
    "District 1", "District 2", "District 3", "District 4", "District 5",
    "District 6", "District 7", "District 8", "District 9", "District 10",
    "District 11", "District 12", "District 13", "District 14", "District 15",
    "District 16", "District 17", "District 18", "District 19", "District 20",
    "District 21", "District 22", "District 23", "District 24", "District 25", "District 26",
    "Nest",
    "Backstreets",
    "Outskirts",
    "Great Lake",
    "Ruins",
    
    # Game Systems
    "Singularity",
    "Singularities",
    "Taboo",
    "Taboos",
    "Fixers",
    "Fixer",
    "Syndicates",
    "Syndicate",
    "Offices",
    "Office",
    "Associations",
    "Association",
    "Fingers",
    "Finger",
    "Bloodfiends",
    "Bloodfiend",
    "Sweepers",
    "Sweeper",
    
    # Combat Mechanics
    "Tremor",
    "Rupture",
    "Sinking",
    "Burn",
    "Bleed",
    "Poise",
    "Charge",
    "Ammo",
    "Bullet",
    "Coin",
    "Coin Power",
    "Clash",
    "Attack",
    "Defense",
    "Evade",
    "HP",
    "SP",
    "Sanity",
    "Feather",
    "Feathers",
    
    # Status Effects
    "Bind",
    "Fragile",
    "Paralyze",
    "Protection",
    "Shield",
    "Regen",
    "Attack Up",
    "Attack Down",
    "Defense Up",
    "Defense Down",
    "Haste",
    "Slash",
    "Pierce",
    "Blunt",
    
    # E.G.O Types
    "ZAYIN",
    "TETH",
    "HE",
    "WAW",
    "ALEPH",
    
    # Locations/Areas
    "Mirror Dungeon",
    "Railway Dungeon",
    "Refraction Railway",
    "Thread",
    "Lunacy",
    "Enkephalin",
    
    # UI Terms (keep English for consistency)
    "VERY_HIGH",
    "HIGH", 
    "NORMAL",
    "LOW",
    "VERY_LOW",
    "SUCCESS",
    "FAILURE",
}

# Character names that appear in teller fields - keep these consistent
CHARACTER_NAMES = {
    "Dante",
    "Vergilius",
    "Charon",
    "Faust",
    "W. Faust",
    "Don Quixote",
    "Ryōshū",
    "Ryoshu",
    "Seven Ryōshū",
    "Seven Ryoshu",
    "Meursault",
    "Hong Lu",
    "Ishmael",
    "Rodion",
    "Sinclair", 
    "Outis",
    "Gregor",
    "Liu Gregor",
    "Heathcliff",
}

# Fields in JSON that should be translated
TRANSLATABLE_FIELDS = {
    # Dialogue & Story
    "dialog",
    "dlg",            # Battle speech bubbles
    "content",        # Story text
    
    # Descriptions
    "desc",
    "description", 
    "summary",        # Skill/buff summaries
    "flavor",         # Flavor text
    
    # Names & Titles
    "name",
    "title",
    "nickName",       # Character nicknames
    "nameWithTitle",  # Character names with titles
    "abnormalityName", # Abnormality names
    "longName",       # Long names (e.g., Line 4, Line 5)
    "specialName",    # Special event names
    
    # Event Text
    "eventDesc",
    "prevDesc",
    "behaveDesc",
    "successDesc",
    "failureDesc",
    
    # Locations & Places
    # "place" is handled statically by dictionaries.py - DO NOT add here
    "company",        # Company/organization names
    "area",           # Area descriptions
    
    # Character Info
    "teller",
    
    # Chapter & Stage
    "chaptertitle",   # Chapter titles
    "chapter",        # Chapter names (Canto I, Prologue, etc.)
    "parttitle",      # Part titles
    "openCondition",  # Unlock conditions
    
    # Abnormality & Combat
    "clue",           # Abnormality clues
    "panicName",      # Panic state names
    "panicDescription", # Panic descriptions
    "lowMoraleDescription", # Low morale descriptions
    "rawDesc",        # Raw descriptions
    "subDesc",        # Sub descriptions
    "variation",      # Variation descriptions
    "variation2",     # Variation 2 descriptions
    "askLevelUp",     # Level up questions
}

# State file for resume support
STATE_FILE = BASE_DIR / "translation_state.json"
CHARACTER_PROFILES_FILE = BASE_DIR / "character_profiles.json"

# Worldbuilding guide file
WORLDBUILDING_GUIDE = RESOURCES_DIR / "limbus_company_worldbuilding_guide.md"

def load_state():
    """Load translation state for resume support."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed_files": [], "current_batch": 0}

def save_state(state):
    """Save translation state."""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def load_character_profiles():
    """Load character profiles if they exist."""
    if CHARACTER_PROFILES_FILE.exists():
        with open(CHARACTER_PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_character_profiles(profiles):
    """Save character profiles."""
    with open(CHARACTER_PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
