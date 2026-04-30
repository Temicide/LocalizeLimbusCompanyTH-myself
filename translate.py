#!/usr/bin/env python3
"""
Limbus Company Thai Localization Translator

This script translates Limbus Company game files from English to Thai
using a local Ollama instance with the scb10x/typhoon-translate1.5-4b model.

Usage:
    python translate.py                    # Translate all files
    python translate.py --test <filename>  # Test translate single file
    python translate.py --analyze-only     # Only analyze characters
"""

import sys
import argparse
from pathlib import Path

# Add translator to path
sys.path.insert(0, str(Path(__file__).parent))

from translator.engine import TranslationEngine
from translator.context_builder import ContextBuilder
from translator.logger import TranslationLogger


def main():
    parser = argparse.ArgumentParser(
        description="Translate Limbus Company files from English to Thai"
    )
    parser.add_argument(
        "--test",
        metavar="FILENAME",
        help="Test translate a single file (e.g., AbDlg_DonQuixote.json)"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze character profiles, don't translate"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last saved state (default behavior)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset state and start from beginning"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        from translator.config import save_state, STATE_FILE
        save_state({"completed_files": [], "current_batch": 0})
        print("State reset. Starting from beginning.")
    
    if args.analyze_only:
        print("Analyzing character profiles only...")
        logger = TranslationLogger()
        context = ContextBuilder(logger)
        context.build_all_context()
        print(f"Character profiles saved to character_profiles.json")
        return
    
    if args.test:
        print(f"Testing translation of: {args.test}")
        engine = TranslationEngine()
        success = engine.translate_single_file(args.test)
        sys.exit(0 if success else 1)
    
    # Full translation run
    print("Starting full translation...")
    engine = TranslationEngine()
    success = engine.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
