# Progress Log

## Session 1 — 2026-05-02 — Research & Design
- Audited entire project structure
- Identified 5 key problems: unused character MDs, only 12 voice guides, Korean model→name gap, per-file context vs per-entry, no translation memory

## Session 2 — 2026-05-02 — Implementation

### Created Files:
1. **`translator/character_profiles.py`** (NEW) — Parses 131 MD files in `data/characters/clean/` into structured Thai voice guides
   - Extracts: personality, speech patterns, tone, register, pronouns, key quirks
   - Generates compact Thai voice guides (3-5 lines) per character
   - Caches to `data/character_voice_guides.json`
   - Includes fuzzy name matching (Ryoshu/Ryōshū, etc.)

2. **`data/character_voice_guides.json`** (NEW) — Cached voice guides for 131 characters
   - All 12 main Sinners with rich voice guides
   - All major NPCs (Vergilius, Charon, Kromer, Dongrang, Ahab, etc.)
   - Minor NPCs get basic guides based on personality text analysis

3. **`data/reference/character_name_mapping.json`** (NEW) — 229 Korean→English mappings + 34 alter/identity mappings
   - Maps Korean `model` field in JSON→English character names→MD file keys→Thai names
   - Covers damaged variants, past/flashback versions, EGO forms
   - Continues to use `dictionaries.py`'s `ENGLISH_TO_THAI_TELLER` as fallback

### Modified Files:
4. **`translator/context_builder.py`** (MAJOR REWRITE)
   - New `resolve_character()` method: Korean model→English name→Thai name→voice key in one call
   - New `get_voice_guide_for_model()`: primary method for per-entry character voice context
   - New `get_characters_in_scene()`: extracts ALL characters from StoryData dataList
   - New `get_scene_context_string()`: builds scene-level character list for batch prompt
   - New `_load_name_mapping()`: loads Korean→English mapping from JSON
   - Kept backward-compatible legacy methods (`get_context_for_file`, `get_character_notes`)

5. **`translator/engine.py`** (MODIFIED)
   - Added `_build_entry_character_map()`: maps entry indices to voice guides
   - Enhanced `translate_file()`: adds scene-level character context + per-entry character annotations
   - Passes `entry_contexts` dict to `translate_batch()` for per-item voice injection

6. **`translator/ollama_client.py`** (MODIFIED)
   - `translate_batch()` now accepts `entry_contexts` parameter
   - Each item in batch can be annotated with `[กำลังพูด: character_name]` prefix
   - Both OpenRouter and Ollama backends updated
   - System prompt updated with rule #10 for character voice consistency

7. **`translator/dictionaries.py`** (EXPANDED)
   - `ENGLISH_TO_THAI_TELLER` expanded from 20→70+ entries
   - Added Thai names for major NPCs: Kromer, Dongrang, Ahab, Catherine, etc.
   - Added identity variants: Kurokumo, Seven, Liu, Shi, etc.

### Tests & Verification:
- ✅ Korean names → English → Thai → voice guide all resolve correctly
- ✅ Scene context built with 6+ characters for S004A.json
- ✅ Entry character map built for 24 entries in S004A.json
- ✅ All 131 voice guides generated and saved
- ✅ 229 Korean name mappings loaded
- ✅ Full integration test passed (context_builder + engine initialization)

### Remaining Work (Phase 5):
- End-to-end test with actual translation API call
- Quality comparison of before/after translations
- Consider re-translating key files to evaluate improvement

## Session 3 — 2026-05-02 — Translation Memory System

### Created Files:
8. **`translator/translation_memory.py`** (NEW) — Translation memory for character-consistent translations
   - Scans 893 paired EN/TH StoryData files, indexes translations by character
   - 3,888 entries across 104 characters (50 per character, randomly sampled)
   - `build_from_translations()`: builds index from existing translations using ContextBuilder for name resolution
   - `get_examples_for_character()`: returns N (en, th) pairs for a character
   - `get_examples_for_scene()`: builds multi-character few-shot context string for prompts
   - `get_vocabulary_string()`: extracts consistent pronoun/marker patterns (e.g., Don Quixote→ข้า, Heathcliff→ฉัน)
   - `add_entry()`: live update during translation
   - `save()`/`load()`: persistent cache to `data/translation_memory.json` (1.2MB)

9. **`data/translation_memory.json`** (NEW) — Cached translation memory (1.2MB)
   - 104 characters, 3,888 translation pairs
   - 57 characters with extracted vocabulary patterns

### Modified Files:
10. **`translator/engine.py`** (MODIFIED)
    - Added `import re` at module level (was inline)
    - Added `self.translation_memory = TranslationMemory(self.logger)` in `__init__`
    - `initialize()`: loads translation memory from cache or builds from existing TH files
    - `translate_file()`: injects translation memory examples + vocabulary into context
    - Scene-level: adds few-shot examples from characters in the scene
    - Per-character: adds vocabulary consistency notes (pronouns, speech markers)

### Test Results:
- ✅ Translation memory builds: 104 characters, 3,888 entries from 893 paired files
- ✅ Don Quixote correctly identified as using "ข้า"
- ✅ Heathcliff correctly identified as using "ฉัน"
- ✅ Scene examples formatted properly for prompt injection
- ✅ Save/load cycle works correctly (1.2MB JSON cache)
- ✅ Engine integration imports and initializes correctly

## Session 4 — 2026-05-02 — Validation

### Integration Test Results:
- ✅ ContextBuilder: 131 voice guides, 229 Korean mappings loaded
- ✅ Character profiles: 131 voice guides loaded from cache
- ✅ Translation memory: 3,888 entries across 104 characters loaded from cache
- ✅ Dictionaries: 124 English→Thai tellers, 46 Korean→Thai tellers
- ✅ Korean→English→Thai→voice_key resolution: all 5 test cases pass
- ✅ Translation memory vocabulary: Don Quixote→ข้า, Heathcliff→ฉัน correctly detected

### Full Pipeline Context Injection (S004B.json test):
- World setting: loaded and truncated to 800 chars
- Scene characters: 7 characters with Thai voice guides (Ishmael, Faust, Vergilius, Rodion, Yi Sang, Outis, Gregor)
- Translation memory: few-shot EN→TH examples for each character
- Vocabulary notes: pronoun/speech marker consistency per character
- Per-entry map: 22 entries annotated with speaker identity + voice

### All systems operational. Character voice consistency system complete.

## Session 5 — 2026-05-02 — Real Translation Quality Test

### Methodology:
- Re-translated S003A.json (22 entries, 6 characters: Ishmael, Faust, Don Quixote, Charon, Yi Sang, Dante)
- Compared against existing translation (produced by the old system without character context)
- Focused on character voice differentiation, pronoun usage, and register consistency

### Key Improvements Found:

**1. Don Quixote — Archiac/Chivalric Thai (was generic casual)**
- OLD: "มันไม่ได้ไร้ความหมายเสียหน่อย!" (casual)
- NEW: "มิใช่ว่าไร้ความหมายนะ!" (archaic/formal — matches อัศวิน register)
- NEW uses "เหล่าคนชั่ว" (literary) + "บังอาจ" (audacious) instead of plain "คนชั่ว"

**2. Faust — Formal with 3rd-person self-reference (was casual)**
- OLD: uses "เธอ" (casual you), "ฉัน" (generic I)
- NEW: uses "คุณ" (formal you), "ค่ะ" (polite particle), "ฟาวสท์" (3rd-person self-ref)
- Faust's voice guide says: ใช้สรรพนามบุรุษที่ 3 เรียกตัวเองเป็น 'ฟาวสท์' — correctly applied!

**3. Yi Sang — Poetic/Philosophical register (was casual)**
- OLD: "การเติบโตของคนเรา" (casual "kohn rao")
- NEW: "การเติบโตของมนุษย์นั้น... ไร้ซึ่งขีดจำกัด" (literary/poetic)
- NEW uses "ผม" (Yi Sang's pronoun) instead of "ฉัน" (generic)

**4. Charon — Childlike/simple (was formal/hydrated)**
- OLD: "Mephi หิวอยู่ตลอดเวลา และมันก็ร้องโหยหาอยู่เสมอ" (formal, mechanical)
- NEW: "เมฟิหิวตลอดเลย ร้องไห้ไม่หยุดเลยด้วย" (short, casual, childlike)

### Assessment:
- Character voices are now clearly differentiated by register, vocabulary, and pronouns
- The system correctly applies: archaic Thai for Don Quixote, formal + 3rd-person for Faust, poetic for Yi Sang, childlike for Charon
- Translation memory few-shot examples are being referenced (Faust's "ฟาวสท์" self-reference)
- Per-entry character annotation (`[กำลังพูด: ...]`) is working as intended

## Session 6 — 2026-05-02 — 5-File Batch Quality Test

### Test Setup:
- Translated 5 files: E701B (22 entries, 9 chars), S529A (27 entries, 11 chars), S722B (29 entries, 9 chars), 1D105A (31 entries, 8 chars), 5D102A (31 entries, 7 chars)
- Characters tested: Don Quixote, Faust, Ryoshu, Heathcliff, Outis, Hong Lu, Yi Sang, Rodion, Dante, Charon, Meursault, Sinclair, Yuri, Vergilius
- Compared against existing translations (old system without character context)

### Key Results by Character:

**1. Don Quixote (Archaic/Chivalric)**
- S003A [4]: "มิใช่ว่าไร้ความหมายนะ!" (archaic) vs old "มันไม่ได้ไร้ความหมายเสียหน่อย!" (generic)
- S722B [1]: "ชัยชนะเป็นของพวกเราแล้ว!" vs old "ชัยชนะเป็นของพวกเราล่ะ!"

**2. Faust (Formal + 3rd-person self-reference ฟาวสท์)**
- 5D102A: "ฟาวสท์เห็นว่าเราต้องคำนึงด้วยว่า..." — correctly self-references as ฟาวสท์!
- 5D102A: "ฟาวสท์เป็นคนโจมตีสิ่งนั้นก่อน" — 3rd-person self-reference
- S003A: "คุณไม่ได้อ่านสัญญาจ้างงานหรือคะ?" — formal คุณ + ค่ะ

**3. Yi Sang (Philosophical + ผม pronoun)**
- S003A [19]: "การเติบโตของมนุษย์นั้น... ไร้ซึ่งขีดจำกัด" — poetic literary language
- E701B: "แต่ผมกังวลว่า..." — correct ผม pronoun (was misusing ข้าน้อย+ขอรับ)

**4. Ryoshu (Terse/Blunt/Artistic)**
- S722B: "ไร้ยางอายสิ้นดี" — blunt idiom vs old "ไร้ซึ่งความละอายแม้แต่นิดเดียว" (overly literary)
- S529A: "ม.จ.ต.ต." — SANGRIA abbreviation style (N.W.C.D. → Thai initials)

**5. Heathcliff (Casual/Aggressive)**
- S529A: "เฮ้ย แกต้องรู้..." — aggressive เฮ้ย + แก (was neutral นี่ นาย)
- S722B: "ไอ้พวก Bloodfiends แถวนี้..." — ไอ้พวก aggressive demonstrative

**6. Outis (Formal/Military)**
- E701B: "พวกเจ้าพวกโง่เง่า!" — เจ้า military superior address (was ไอ้ generic)

**7. Hong Lu (Playful/Cheerful)**
- E701B: "แหม แต่สุดท้าย..." — แหม interjection + playful tone

**8. Rodion (Warm/Casual)**
- S529A: "ตาคนชื่อริมคนนั้น..." — casual intimate register

### Issues Found:
- 1D105A: Batch 1 failed (API timeout), 10 entries left in English. Batches 2-3 translated correctly.
- All restored originals after testing

## Session 8 — 2026-05-03 — Canto 1 Re-translation (Phase 15)

### Goal
Re-translate all 20 Canto 1 story files with the complete improved translation system.

### Setup:
- Backed up current TH/StoryData/1D*.json files to TH_Test/Canto1_pre_retranslate/
- Created scripts/retranslate_canto1.py for targeted re-translation

### Files Re-translated (20/20 success):
1D101A, 1D102A, 1D103A, 1D104B, 1D105A, 1D105B, 1D201B, 1D202A, 1D202B, 1D203B, 1D204B, 1D301B, 1D302B, 1D303B, 1D304B, 1D305B, 1D306A, 1D306B, 1D306I, 1D306I2

### Quality Improvements Verified:

**1. Place Translations Fixed (glossary system working)**
- OLD: 6 files had places = "L Corp." (generic fallback)
- NEW: All places properly translated
  - "L Corp." → "ท่ามกลางสงครามควัน" (1D301B)
  - "L Corp." → "แนวหน้ากลางสงครามควัน" (1D302B-305B)
  - "L Corp." → "บนรถเมฆิสโตเฟเลส" (1D306A)

**2. Teller Mapping Fixed (100% Thai)**
- OLD: English tellers untranslated — "Yuri", "Tomah", "Jia Huan", "Hermann", "Security Guard", "Gubo", "Statuehead"
- NEW: All mapped to Thai — "ยูริ", "โทมาห์", "เจี่ยฮวน", "แฮร์มันน์", "รปภ.", "กูโป", "หัวรูปปั้น"

**3. Title Consistency Fixed**
- OLD: "Fixer Fixer ระดับ 8" bug in 1D306A
- OLD: 3 variants of "ผู้รอดชีวิต?" / 4 variants of "Reminisced Soldier"
- NEW: All titles deterministic — "Fixer ระดับ 8", "ผู้รอดชีวิตงั้นเหรอ?", "ทหารในความทรงจำ"

**4. Character Voice Improvements**
- Yuri: More consistent use of polite particle "ค่ะ"
- Kind Citizen: Better word choice ("ได้โปรด" instead of "ขอร้องล่ะ")
- Security Guard: More natural phrasing

### Assessment:
All 20 Canto 1 files successfully re-translated with zero failures. Glossary, teller mapping, title consistency, and place translation systems all working correctly in production.

---

## Session 9 — 2026-05-03 — Full Remaining Translation Run

### Scope
- 1,015 pending files across all categories
- Major categories: PersonalityVoiceDlg (176), BattleAnnouncerDlg (53), BgmLyrics (15), EGOVoiceDig (14)
- Plus 750+ individual UI, skill, buff, event, and other files
- Engine modified to process ALL EN/*.json files recursively (was StoryData-only)
- Fixed UTF-8 BOM handling in file_processor.load_json() for ProjectGS.json

---

## Session 7 — 2026-05-02 — Translation Consistency Fix (Phases 8-13)

### Problem Summary
- **Place translations**: 91% broken — almost everything became "L Corp."
- **Teller mapping bug**: Mapped Thai tellers sent to AI for re-translation
- **Teller gaps**: Only 191 of 500 tellers had mappings (61% unmapped)
- **Title inconsistency**: 91 titles with multiple Thai variants
- **System prompt gaps**: No place/title rules, Ollama prompt missing rules 9-10

### Created Files:
1. **`translator/glossary.py`** (NEW) — Centralized glossary class
   - `Glossary` class loads JSON data files
   - `lookup_place()`, `lookup_teller()`, `lookup_title()`, `lookup_term()`
   - Handles newline normalization and case-insensitive matching
   - Pattern-based title fallback for dynamic titles (Grade N Fixer, etc.)
   - `get_glossary()` singleton for global access

2. **`data/place_glossary.json`** (NEW) — 441 place translations
   - All unique places from 893 EN/TH file pairs
   - Proper Thai translations replacing "L Corp." generic outputs
   - Examples: "Wuthering Heights Hall" → "ห้องโถง Wuthering Heights", "K Corp. Laboratory" → "ห้องปฏิบัติการ K Corp."

3. **`data/teller_glossary.json`** (NEW) — 527 teller translations
   - All 500 unique teller values with consistent Thai translations
   - Generic tellers: "Interviewer" → "ผู้สัมภาษณ์", "Radio" → "วิทยุ"
   - Character names match ENGLISH_TO_THAI_TELLER conventions

4. **`data/title_glossary.json`** (NEW) — 304 title translations
   - All unique titles with deterministic Thai translations
   - "G Corp. Remnant" → "เศษซาก G Corp." (was 3 different variants)
   - "Grade 8 Fixer" → "Fixer ระดับ 8" (was "Fixer Fixer ระดับ 8" bug)

5. **`data/term_glossary.json`** (NEW) — 75 game term translations
   - Organization names kept in English (The Middle, The Index, etc.)
   - Corp names with Thai descriptors (K Corp. Laboratory → ห้องปฏิบัติการ K Corp.)

6. **`data/glossary_auto_extracted.json`** (NEW) — Raw auto-extraction data
   - 500 tellers, 290 titles, 386 places extracted from existing translations
   - Confidence scores for each translation

### Modified Files:
7. **`translator/engine.py`** (MAJOR CHANGES)
   - Added `from .glossary import get_glossary` import
   - `__init__()`: added `self.glossary = None` and `self._title_glossary_values`
   - `initialize()`: loads glossary and pre-computes title values for dedup
   - `_apply_teller_mapping()`: falls back to glossary when `get_thai_teller()` returns unchanged
   - `_apply_place_translation()`: checks glossary first before `translate_place_name()`
   - `_apply_title_preprocessing()`: checks glossary first before regex patterns
   - Dedup loop: expanded to skip glossary-mapped tellers, places, and titles
   - Post-processing loop: fixed bug where code after `continue` was unreachable; now correctly applies fixes
   - Added term glossary replacement in content post-processing

8. **`translator/dictionaries.py`** (MINOR)
   - Updated `translate_place_name()` with `-1`, `???`, and `-1` edge case handling
   - Added docstring noting it's now a fallback (glossary checked first)

9. **`translator/ollama_client.py`** (MAJOR CHANGES)
   - OpenRouter prompt: added rules #11 (place names), #12 (teller names), #13 (titles)
   - Ollama prompt: fully synced with OpenRouter — added rules #9-13
   - Few-shot examples: added 6 place translation examples to story_examples
   - Both prompts now have consistent rule sets

### Key Fixes:
- **Teller dedup bug**: Fixed check that was using Thai text as English dict key — now checks EN keys, TH values, KR values, AND glossary
- **Place translation**: 441 places now have curated Thai translations (was 91% "L Corp.")
- **Teller coverage**: 527 teller mappings (was 191, 61% gap → 100%)
- **Title consistency**: 304 deterministic title translations (was 7 regex patterns)
- **System prompt**: Both OpenRouter and Ollama now have consistent rules 1-13