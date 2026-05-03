#!/usr/bin/env python3
"""
Re-translate Canto 1 files with the improved translation system.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from translator.engine import TranslationEngine

CANTO1_FILES = [
    "StoryData/1D101A.json",
    "StoryData/1D102A.json",
    "StoryData/1D103A.json",
    "StoryData/1D104B.json",
    "StoryData/1D105A.json",
    "StoryData/1D105B.json",
    "StoryData/1D201B.json",
    "StoryData/1D202A.json",
    "StoryData/1D202B.json",
    "StoryData/1D203B.json",
    "StoryData/1D204B.json",
    "StoryData/1D301B.json",
    "StoryData/1D302B.json",
    "StoryData/1D303B.json",
    "StoryData/1D304B.json",
    "StoryData/1D305B.json",
    "StoryData/1D306A.json",
    "StoryData/1D306B.json",
    "StoryData/1D306I.json",
    "StoryData/1D306I2.json",
]


def main():
    engine = TranslationEngine()
    if not engine.initialize():
        print("Failed to initialize engine")
        sys.exit(1)

    total = len(CANTO1_FILES)
    success = 0
    fail = 0

    for i, filename in enumerate(CANTO1_FILES, 1):
        filepath = PROJECT_ROOT / "EN" / filename
        if not filepath.exists():
            print(f"[{i}/{total}] SKIP (not found): {filename}")
            fail += 1
            continue

        print(f"[{i}/{total}] Translating: {filename}")
        if engine.translate_file(filepath):
            print(f"[{i}/{total}] SUCCESS: {filename}")
            success += 1
        else:
            print(f"[{i}/{total}] FAILED: {filename}")
            fail += 1

    print(f"\n{'='*60}")
    print(f"CANTO 1 RE-TRANSLATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total: {total}")
    print(f"Success: {success}")
    print(f"Failed: {fail}")


if __name__ == "__main__":
    main()
