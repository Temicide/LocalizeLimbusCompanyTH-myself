# Research Findings: Translation Consistency (Names, Titles, Places, Tone)

## 1. PLACE TRANSLATIONS — CRITICAL

### Severity: 91% of place fields incorrectly translated

The `translate_place_name()` function in `dictionaries.py:325-373` is fundamentally broken. It only handles two patterns:
- `District N` → `เขต N`
- `LC Branch` / `L Corp` → `L Corp.` + `สาขา`

Every other place string is passed to `PLACE_PATTERNS` which also only matches these same two patterns. When neither matches, the original English is sent to the AI, which overwhelmingly translates it to just "L Corp." regardless of actual content.

### Examples of Place Translation Failures

| EN Place | TH Result | Problem |
|---|---|---|
| `"U Corp.'s Marlin Portship"` | `"L Corp."` | Total loss |
| `"The Pallid Whale's Right Ventricle"` | `"L Corp."` | Total loss |
| `"Wuthering Heights"` | `"L Corp."` | Total loss |
| `"Aboard Mephistopheles"` | `"L Corp."` | Total loss |
| `"La Manchaland"` | `"L Corp."` | Total loss |
| `"N Corp. Cubic Room"` | `"ห้อง L Corp."` | Wrong corp, lost "Cubic" |
| `"K Corp. Laboratory Hallway"` | `"ทางเดิน L Corp."` | Wrong corp |
| `"Casino Entrance"` | `"ทางเข้า L Corp."` | Added spurious "L Corp." |
| `"District 4 - LC Branch Entryway"` | `"ทางเข้า L Corp. สาขาเขต 4"` | **Only correct one** |

### Root Cause
1. `translate_place_name()` tries to decompose places into `[Location] [Corp] [Branch] [District]` — but almost no places in Limbus Company follow this pattern
2. When decomposition fails, falls through to regex patterns that only match `District N` and `L Corp`
3. System prompt contains NO instructions about place translation, so AI defaults to "L Corp."

### Fix Strategy
- Build exhaustive `data/place_glossary.json` mapping ALL unique EN place strings → TH translations
- Replace `translate_place_name()` with dictionary-first lookup
- For novel places not in dictionary, use AI with explicit place-translation instructions in prompt
- ~200 unique place strings need mapping

---

## 2. CHARACTER NAME / TELLER CONSISTENCY — HIGH

### Bug: Teller Mapping Bypass

In `engine.py:195`:
```python
if field == "teller" and original_text in ENGLISH_TO_THAI_TELLER:
    dedup_skipped += 1
    continue
```

At this point `original_text` is already Thai (mapped by `_apply_teller_mapping()` at line 120). Since "ยูริ" is not a key in `ENGLISH_TO_THAI_TELLER` (which has "Yuri" → "ยูริ"), the check ALWAYS fails for mapped tellers. Result: Thai tellers get sent to AI and retranslated inconsistently.

### Dictionary Gaps

**ENGLISH_TO_THAI_TELLER**: 191 entries, but 494 unique tellers exist → **303 (61%) unmapped**

Key missing mappings (high-frequency):
| Teller | Frequency | Status |
|---|---|---|
| `Saude` | 83 entries | UNMAPPED |
| `Irene` | 118 entries | UNMAPPED |
| `Sonya` | 110 entries | UNMAPPED |
| `Mika` | 45 entries | UNMAPPED |
| `Sang Yi` | 45 entries | UNMAPPED |
| `Olga` | 33 entries | UNMAPPED |
| `Ahab` | 30 entries | UNMAPPED |
| `Smee` | 29 entries | UNMAPPED |
| `Domino` | 22 entries | UNMAPPED |
| `Shi Huazhen` | 19 entries | UNMAPPED |
| `Poludnitsa` | 18 entries | UNMAPPED |
| `Vera` | 13 entries | UNMAPPED |
| `Tingtang Boss` | 8+ entries | UNMAPPED |

### Korean Path Inconsistency

`가시춘` → `ขงชิว` (KOREAN_TO_THAI) but `Shi Huazhen` → `ซีหัวเจิ้น` (ENGLISH_TO_THAI). Same character, different Thai transliterations depending on which code path resolves the name.

### Generic/Descriptive Teller Inconsistency

| Teller | TH Variants Found |
|---|---|
| `Interviewer` | `Interviewer`, `ผู้สัมภาษณ์` |
| `Assistant` | `Assistant`, `ผู้ช่วย` |
| `Radio` | `วิทยุ`, `วิทยุสื่อสาร` |
| `Kidnapper` | `โจรลักพาตัว`, `โจรกิดนับ` (typo!) |
| `Bodhisattva Chicken's Manager` | 7 different translations |
| `Class 2 Collection Staff` | 7 different translations |

---

## 3. TITLE FIELD TRANSLATION — MODERATE-HIGH

### 91 titles have multiple inconsistent Thai translations

| EN Title | TH Variants |
|---|---|
| `G Corp. Remnant` | `G Corp. ผู้หลงเหลือ`, `Remnant แห่ง G Corp.`, `เศษซาก G Corp.` |
| `Grade 8 Fixer` | `Fixer Fixer ระดับ 8`, `Fixer ระดับ 8` |
| `Central Command Sephirah` | `Central Command Sephirah`, `Sephirah แผนกควบคุมส่วนกลาง`, `Sephirah แผนกบัญชาการส่วนกลาง` |
| `Dieci Section 4` | `Dieci ส่วนที่ 4`, `Dieci เซกชัน 4` |
| `Daguanyuan` | `Daguanyuan`, `ต้ากวนหยวน`, `ต้ากวานหยวน` |
| `Distorted Thing` | 5 variants |
| `Eleventh Note` | `จดหมายฉบับที่ 11`, `บันทึกฉบับที่ 11`, `โน้ตฉบับที่ 11` |

### "Double Fixer" Bug
`Grade 8 Fixer` → preprocessed to `Fixer grade 8` → AI sometimes outputs both → `Fixer Fixer ระดับ 8`

### TITLE_PATTERNS Coverage
Only 7 patterns exist. Missing patterns for:
- Association sections (Cinq Section N, Dieci Section N, Liu Section N, etc.)
- Organization names (The Middle, The Index, The Thumb, The Ring)
- Corp department titles (K/T/W/H/N Corp. variants)
- Numbered Notes (First through Twelfth)
- Chinese-inspired titles (Jia Family, Hongyuan, Daguanyuan)
- Role titles (Inquisitor, Collector, Distorted Thing)

---

## 4. SYSTEM PROMPT GAPS

### Missing Instructions
- **Place translation**: No rules → AI defaults to "L Corp." for everything
- **Teller/title handling**: No instructions on translating these fields deterministically
- **Proper noun handling**: No guidance on transliterating names consistently

### Ollama vs OpenRouter Prompt Divergence
- OpenRouter: rules 1-10 (including stuttering #9, character voice #10)
- Ollama: rules 1-8 only (missing #9 and #10)

### Few-shot Example Gap
- Only one place translation example: `District 4 - LC Branch Entryway` → `ทางเข้า L Corp. สาขาเขต 4`
- No title translation examples
- No teller/name examples

---

## 5. PROPOSED SOLUTION ARCHITECTURE (IMPLEMENTED)

### A. Centralized Glossary System (`translator/glossary.py`) — IMPLEMENTED

```python
class Glossary:
    def __init__(self):
        self.places = {}       # EN string → TH string (441 entries)
        self.tellers = {}      # EN → TH (527 entries)
        self.titles = {}       # EN string → TH string (304 entries)
        self.terms = {}        # EN term → TH term (75 entries)
    
    def lookup_place(self, en_place: str) -> Optional[str]  # Normalizes newlines, case-insensitive fallback
    def lookup_teller(self, en_teller: str) -> Optional[str]  # Strips trailing "?"
    def lookup_title(self, en_title: str) -> Optional[str]  # Pattern fallback for dynamic titles
    def lookup_term(self, en_term: str) -> Optional[str]
```

### B. Glossary Data Files (IMPLEMENTED)

1. **`data/place_glossary.json`** — 441 entries, all unique places → Thai
   - "Wuthering Heights Hall" → "ห้องโถง Wuthering Heights" (was "L Corp.")
   - "K Corp. Laboratory" → "ห้องปฏิบัติการ K Corp." (was "L Corp.")
   - "Aboard Mephistopheles" → "บนรถเมฆิสโตเฟเลส" (was "L Corp.")

2. **`data/teller_glossary.json`** — 527 entries, complete EN→TH teller mapping
   - "Interviewer" → "ผู้สัมภาษณ์" (was inconsistent: "ผู้สัมภาษณ์" or "Interviewer")
   - "Saude" → "Saude" (kept as-is, proper name convention)
   - "Class 2 Collection Staff" → "เจ้าหน้าที่เก็บกู้ ระดับ 2" (was 7 different variants)

3. **`data/title_glossary.json`** — 304 entries, deterministic title translations
   - "G Corp. Remnant" → "เศษซาก G Corp." (was 3 different variants)
   - "Grade 8 Fixer" → "Fixer ระดับ 8" (was "Fixer Fixer ระดับ 8" bug)

4. **`data/term_glossary.json`** — 75 entries, game terms and organizations
   - "Abnormality" → "Abnormality" (kept English)
   - "Cinq Association" → "Cinq Association" (kept English)
   - "Bloodfiend" → "Bloodfiend" (kept English)

### C. Auto-Build from Existing Translations (IMPLEMENTED)

- `data/glossary_auto_extracted.json` — raw extraction from 893 EN/TH pairs
- Used as base for curated glossary files
- Confidence scores identify inconsistencies for manual review
- 500 tellers, 290 titles, 386 places extracted

### D. Pipeline Integration (IMPLEMENTED)

```python
# In engine.py translate_file():
# 1. _apply_teller_mapping() — checks dict first, then glossary
# 2. _apply_place_translation() — checks glossary first, then old pattern fallback
# 3. _apply_title_preprocessing() — checks glossary first, then regex
# 4. Dedup loop — skips all statically-mapped fields (teller/place/title)
# 5. Post-processing — applies term glossary replacement in content
```

### E. Teller Dedup Bug Fix (IMPLEMENTED)

```python
# NEW: Track all statically-mapped paths (not just tellers)
statically_mapped_paths = {}

for path, field, original_text in texts_to_translate:
    if field == "teller":
        # Check dict keys AND values (Thai translations already applied)
        if original_text in ENGLISH_TO_THAI_TELLER:
            statically_mapped_paths[path] = original_text
            continue
        if original_text in ENGLISH_TO_THAI_TELLER.values():
            statically_mapped_paths[path] = original_text
            continue
        if original_text in KOREAN_TO_THAI_TELLER.values():
            statically_mapped_paths[path] = original_text
            continue
        if self.glossary.lookup_teller(original_text):
            statically_mapped_paths[path] = original_text
            continue
    elif field == "place":
        statically_mapped_paths[path] = original_text
        continue
    elif field == "title":
        if self.glossary.lookup_title(original_text):
            statically_mapped_paths[path] = original_text
            continue
```

### F. System Prompt Updates (IMPLEMENTED)

Added rules 11-13 to both OpenRouter and Ollama prompts:
- Rule 11: Place name translation (keep proper nouns, translate descriptors)
- Rule 12: Teller names pre-translated by system, don't retranslate
- Rule 13: Title translation (keep org names, translate role descriptors)

Added 6 place translation few-shot examples to story_examples.

### Test Results

```
PLACE GLOSSARY (previously all -> L Corp.):
  'Aboard Mephistopheles' -> 'บนรถเมฆิสโตเฟเลส'
  'Wuthering Heights Hall' -> 'ห้องโถง Wuthering Heights'
  'K Corp. Laboratory' -> 'ห้องปฏิบัติการ K Corp.'

TELLER GLOSSARY (previously inconsistent):
  'Interviewer' -> 'ผู้สัมภาษณ์' (was: inconsistent)
  'Radio' -> 'วิทยุ' (was: inconsistent)
  'Class 2 Collection Staff' -> 'เจ้าหน้าที่เก็บกู้ ระดับ 2' (was: 7 variants)

TITLE GLOSSARY (previously inconsistent):
  'G Corp. Remnant' -> 'เศษซาก G Corp.' (was: 3 variants)
  'Grade 8 Fixer' -> 'Fixer ระดับ 8' (was: double-Fixer bug)
```