#!/usr/bin/env python3
"""
Re-translate ALL StoryData files from EN to TH.
Bypasses the completion state — every file gets retranslated.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from translator.engine import TranslationEngine


def main():
    engine = TranslationEngine()
    if not engine.initialize():
        print("Failed to initialize engine")
        sys.exit(1)

    story_dir = PROJECT_ROOT / "EN" / "StoryData"
    all_files = sorted(story_dir.glob("*.json"), key=lambda p: p.name)

    total = len(all_files)
    success = 0
    fail = 0

    print(f"Retranslating ALL {total} StoryData files...")
    print("=" * 60)

    for i, filepath in enumerate(all_files, 1):
        print(f"[{i}/{total}] Translating: {filepath.name}")
        if engine.translate_file(filepath):
            print(f"[{i}/{total}] SUCCESS: {filepath.name}")
            success += 1
        else:
            print(f"[{i}/{total}] FAILED: {filepath.name}")
            fail += 1

    print(f"\n{'='*60}")
    print(f"STORYDATA RE-TRANSLATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total: {total}")
    print(f"Success: {success}")
    print(f"Failed: {fail}")


if __name__ == "__main__":
    main()
