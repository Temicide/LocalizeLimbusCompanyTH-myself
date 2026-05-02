# Task Plan: Translation Consistency Across All Fields

## Goal
Fix systematic consistency problems in character names, titles, tone, and place translations across the Limbus Company Thai localization pipeline.

## Problem Summary

### CRITICAL — Place Translations (91% broken)
- `translate_place_name()` only handles 2 patterns: `District N` and `LC Branch`
- 91% of all place fields become generic "L Corp." — destroying scene-setting info
- Example: "U Corp.'s Marlin Portship" → "L Corp." / "Wuthering Heights" → "L Corp."
- Only "District 4 - LC Branch Entryway" translates correctly

### HIGH — Teller/Name Mapping Bug + Gaps
- **Bug**: `_apply_teller_mapping()` maps EN→TH, but `engine.py` dedup check `original_text in ENGLISH_TO_THAI_TELLER` fails because `original_text` is already Thai (not a dict key). Mapped tellers get sent to AI anyway.
- **Gap**: Only 191 of 494 unique English teller values have Thai mappings (61% unmapped)
- **Korean path inconsistency**: `가시춘` → `ขงชิว` (KOREAN_TO_THAI) vs `Shi Huazhen` → `ซีหัวเจิ้น` (ENGLISH_TO_THAI) — same character, different transliterations
- **Generic tellers**: "Interviewer", "Researcher", "Radio" etc. translate inconsistently (2+ variants each)
- **Descriptive tellers**: "Bodhisattva Chicken's Manager" has 7 different Thai translations

### HIGH — Title Inconsistency (91 titles with multiple TH variants)
- `G Corp. Remnant` → 3 variants: `G Corp. ผู้หลงเหลือ`, `Remnant แห่ง G Corp.`, `เศษซาก G Corp.`
- Only 7 TITLE_PATTERNS exist; hundreds of unique titles have no deterministic mapping
- "Double Fixer" bug: `Grade 8 Fixer` → `Fixer Fixer ระดับ 8`
- `K Corp.` vs `K Corp` period inconsistency in translations

### MODERATE — System Prompt Gaps
- No instructions for place name translation → AI defaults to "L Corp."
- No instructions for teller/title field handling
- Ollama fallback prompt missing rules #9 (stuttering) and #10 (character voice)

## Phases

### Phase 8: Fix Teller Mapping Bug ✅
- Fixed dedup check in `engine.py` — now checks ENGLISH dict keys AND Thai dict values
- Added `statically_mapped_paths` dict to track all pre-mapped fields (teller/place/title)
- Glossary-mapped tellers/titles also skipped in dedup
- Post-processing loop now correctly applies fixes for non-skipped entries

### Phase 9: Build Comprehensive Glossary System ✅
- Created `translator/glossary.py` — centralized glossary class with lookup methods
- Auto-extracted existing translations from 893 EN/TH file pairs
- Curated and fixed translations (places were 91% broken → all corrected)
- Glossary data files:
  - `data/place_glossary.json`: 441 entries (all unique places)
  - `data/teller_glossary.json`: 527 entries (all unique tellers)
  - `data/title_glossary.json`: 304 entries (all unique titles)
  - `data/term_glossary.json`: 75 entries (game terms/orgs)

### Phase 10: Rewrite `translate_place_name()` ✅
- `translate_place_name()` now handles `-1` and `???` edge cases
- Added glossary-first lookup in `_apply_place_translation()` — checks glossary before pattern matching
- All ~441 places now have proper Thai translations instead of "L Corp."
- Examples: "Wuthering Heights Hall" → "ห้องโถง Wuthering Heights" (was "L Corp.")

### Phase 11: Expand Teller Dictionaries ✅
- 527 teller entries via glossary (was 191 in dictionaries.py, 61% gap → 100% coverage)
- All 500 unique teller values now have deterministic Thai translations
- Fixed KR→TH vs EN→TH inconsistencies by using glossary as single source of truth
- Generic tellers now consistently translated (Interviewer → ผู้สัมภาษณ์, Radio → วิทยุ, etc.)
- `_apply_teller_mapping()` now falls back to glossary when `get_thai_teller()` returns unchanged

### Phase 12: Expand Title Patterns ✅
- 304 title entries via glossary (was 7 regex patterns)
- Pattern-based matching in `Glossary._match_title_pattern()` for dynamic titles
- "Grade/Class/Level N Fixer" → "Fixer ระดับ N" patterns preserved
- Deterministic Thai for org titles: "Class 2 Collection Staff" → "เจ้าหน้าที่เก็บกู้ ระดับ 2"
- `_apply_title_preprocessing()` now checks glossary first, falls back to regex

### Phase 13: Update System Prompt ✅
- Added rule #11: Place name translation rules (keep proper nouns, translate descriptors)
- Added rule #12: Teller names are pre-translated, don't retranslate
- Added rule #13: Title translation rules (keep org names, translate roles)
- Synced Ollama prompt with OpenRouter prompt (rules 9-13 now in both)
- Added place name few-shot examples to story examples (6 place translation pairs)

### Phase 14: Audit & Regression Test — PENDING
- Need to re-translate sample files with all fixes
- Compare before/after for places, names, titles
- Verify teller mapping bug is fixed
- Check for regressions in character voice quality

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Teller dedup check uses Thai text as EN dict key | 1 | Fixed: check EN dict keys, TH dict values, and KR dict values |
| 91% of places translated to "L Corp." | 1 | Fixed: glossary-first lookup with 441 curated place translations |
| Smart quotes in glossary JSON | 1 | Fixed: replaced \u2019 with regular apostrophe |