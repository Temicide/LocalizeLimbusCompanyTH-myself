"""Character profile extractor — parses MD files from data/characters/clean/ into compact Thai voice guides."""
import json
import re
from pathlib import Path
from typing import Dict, Optional

CHARACTERS_DIR = Path(__file__).parent.parent / "data" / "characters" / "clean"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "character_voice_guides.json"


def parse_md_character(filepath: Path) -> dict:
    """Parse a character MD file into structured profile data."""
    text = filepath.read_text(encoding="utf-8")

    name = filepath.stem.replace("_", " ")
    if name.startswith("A Certain "):
        name = name.replace("A Certain ", "")

    sections = {}
    current_section = None
    current_lines = []

    for line in text.split("\n"):
        header_match = re.match(r"^###?\s+(.+)", line)
        if header_match:
            if current_section and current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = header_match.group(1).strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_section and current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    personality = sections.get("personality", "")
    appearance = sections.get("appearance", "")
    story = sections.get("story", "")
    trivia = sections.get("trivia", "")

    speech_patterns = _extract_speech_patterns(personality, name)
    tone = _determine_tone(personality, name)
    register = _determine_register(personality, name)
    pronouns = _determine_pronouns(personality, name)
    key_quirks = _extract_key_quirks(personality, trivia, name)

    return {
        "name_en": name,
        "personality": personality[:800] if personality else "",
        "speech_patterns": speech_patterns,
        "tone": tone,
        "register": register,
        "pronouns": pronouns,
        "key_quirks": key_quirks,
    }


def _extract_speech_patterns(personality: str, name: str) -> list:
    patterns = []
    text_lower = personality.lower()

    if any(w in text_lower for w in ["archaic", "chivalric", "shall", "thee", "thy", "honor", "noble"]):
        patterns.append("archaic_chivalric")
    if any(w in text_lower for w in ["casual", "laid-back", "laid back", "relaxed", "cheeky", "playful", "slang"]):
        patterns.append("casual_playful")
    if any(w in text_lower for w in ["terse", "laconic", "brief", "few words", "quiet"]):
        patterns.append("terse_laconic")
    if any(w in text_lower for w in ["analytical", "rational", "logical", "data", "probability", "precise"]):
        patterns.append("analytical_formal")
    if any(w in text_lower for w in ["sadistic", "cruel", "mocking", "manipulative", "belittling"]):
        patterns.append("cruel_mocking")
    if any(w in text_lower for w in ["formal", "polite", "respectful", "courteous", "dignified"]):
        patterns.append("formal_polite")
    if any(w in text_lower for w in ["timid", "nervous", "hesitant", "stutter", "anxious", "shy"]):
        patterns.append("timid_hesitant")
    if any(w in text_lower for w in ["enthusiastic", "excited", "hyper", "cheerful"]):
        patterns.append("enthusiastic")
    if any(w in text_lower for w in ["sarcastic", "snide", "sardonic", "dry humor", "scoffs"]):
        patterns.append("sarcastic_sardonic")
    if any(w in text_lower for w in ["third person", "refers to herself", "refers to himself"]):
        patterns.append("third_person")
    if any(w in text_lower for w in ["abbreviation", "abbreviations", "abbreviation of"]):
        patterns.append("uses_abbreviations")

    if not patterns:
        patterns.append("neutral")

    return patterns


def _determine_tone(personality: str, name: str) -> str:
    name_lower = name.lower()

    tone_map = {
        "don quixote": "chivalric_enthusiastic",
        "faust": "intellectual_confident",
        "gregor": "world_weary_casual",
        "heathcliff": "hot_tempered_brusque",
        "ishmael": "level_headed_sardonic",
        "ryoshu": "terse_artistic",
        "yi sang": "melancholic_contemplative",
        "hong lu": "cheerful_noble",
        "meursault": "logical_detached",
        "rodion": "warm_brazen",
        "sinclair": "timid_anxious",
        "outis": "formal_disciplined",
        "vergilius": "cold_authoritative",
        "charon": "childish_brief",
        "dante": "awkward_determined",
    }

    for key, tone in tone_map.items():
        if key in name_lower:
            return tone

    text_lower = personality.lower()
    if any(w in text_lower for w in ["sadistic", "cruel", "manipulative"]):
        return "cruel_mocking"
    if any(w in text_lower for w in ["authoritative", "commanding", "leader"]):
        return "authoritative_strict"
    if any(w in text_lower for w in ["quiet", "meek", "timid", "nervous"]):
        return "timid_hesitant"
    if any(w in text_lower for w in ["cheerful", "warm", "friendly", "amiable"]):
        return "warm_friendly"
    if any(w in text_lower for w in ["cold", "detached", "aloof"]):
        return "cold_detached"

    return "neutral"


def _determine_register(personality: str, name: str) -> str:
    name_lower = name.lower()
    formal_chars = ["faust", "meursault", "outis", "vergilius", "dongrang", "hermann", "aseah"]
    casual_chars = ["rodyon", "rodion", "gregor", "ishmael", "heathcliff", "hong lu", "bumble"]
    terse_chars = ["ryoshu", "ryōshū", "charon", "mephistopheles"]

    for c in formal_chars:
        if c in name_lower:
            return "formal"
    for c in casual_chars:
        if c in name_lower:
            return "casual"
    for c in terse_chars:
        if c in name_lower:
            return "terse"

    text_lower = personality.lower()
    if any(w in text_lower for w in ["formal", "polite", "respectful", "proper"]):
        return "formal"
    if any(w in text_lower for w in ["casual", "slang", "relaxed", "laid-back"]):
        return "casual"

    return "neutral"


def _determine_pronouns(personality: str, name: str) -> dict:
    name_lower = name.lower()
    pronoun_map = {
        "don quixote": {"thai": "ข้า/ข้าพเจ้า", "note": "อัศวิน ใช้ภาษายกระดับตัวเอง"},
        "faust": {"thai": "ฉัน/ฟาวสท์", "note": "ใช้สรรพนามบุรุษที่ 3 เรียกตัวเองเป็น 'ฟาวสท์'"},
        "heathcliff": {"thai": "กู/มึง (informal), ฉัน/ผม", "note": "หยาบกระด้าง มักใช้ภาษาถิ่น"},
        "ishmael": {"thai": "ฉัน", "note": "ตรงไปตรงมา"},
        "ryoshu": {"thai": "ฉัน", "note": "สั้น กระชับ"},
        "yi sang": {"thai": "ผม/ฉัน", "note": "เงียบ มีนัยยะ"},
        "hong lu": {"thai": "หนู/ฉัน", "note": "สุภาพ มีมารยาท"},
        "meursault": {"thai": "ฉัน", "note": "เป็นกลาง ไม่แสดงอารมณ์"},
        "rodion": {"thai": "ฉัน/โรเดีย", "note": "เป็นกันเอง ใช้ชื่อเล่น"},
        "sinclair": {"thai": "ผม", "note": "สุภาพ ไม่มั่นใจ"},
        "outis": {"thai": "ฉัน/ท่านผู้จัดการ", "note": "ทางการ เคารพผู้บังคับบัญชา"},
        "gregor": {"thai": "ฉัน/พวกเธอ", "note": "สบายๆ ทหารผ่านศึก"},
        "vergilius": {"thai": "ฉัน/ข้า", "note": "เย็นชา มีอำนาจ"},
        "charon": {"thai": "แครอน (ชื่อตัวเอง)", "note": "พูดถึงตัวเองด้วยชื่อตัวเอง"},
        "dante": {"thai": "- (เสียงนาฬิกา)", "note": "สื่อสารด้วยเสียงนาฬิกา ผู้อื่นแปลให้"},
        "kromer": {"thai": "ฉัน", "note": "เยาะเย้ย ดูถูก"},
        "dongrang": {"thai": "ฉัน", "note": "สุภาพภายนอก แฝงความเย็นชา"},
        "ahab": {"thai": "ข้า/ฉัน", "note": "ผู้นำที่หลงใหล"},
        "catherine": {"thai": "ฉัน", "note": "มั่นใจ แต่ซ่อนความรู้สึก"},
        "hindley": {"thai": "กู/มึง", "note": "หยาบคาย เห็นแก่ตัว"},
    }

    for key, val in pronoun_map.items():
        if key in name_lower:
            return val

    return {"thai": "ฉัน", "note": ""}


def _extract_key_quirks(personality: str, trivia: str, name: str) -> list:
    quirks = []
    text = (personality + " " + trivia).lower()
    name_lower = name.lower()

    specific_quirks = {
        "ryoshu": ["ใช้คำย่อ SANGRIA เสมอ", "เรียกศิลปะความรุนแรงว่า 'งาม'"],
        "don quixote": ["เรียกตัวเองว่า 'ข้า'", "พูดด้วยพลังงานสูง", "ใช้ภาษาอัศวิน"],
        "heathcliff": ["มักพูดเสียงดัน", "ใช้คำหยาบเมื่อโกรธ", "มีสำนวนถิ่น"],
        "ishmael": ["มักพูดถึงทะเล", "มีประสบการณ์เรือ"],
        "sinclair": ["มักลังเล", "พูดไม่เต็มเสียง", "ขอโทษบ่อย"],
        "rodion": ["ใช้ชื่อเล่นเรียกคนอื่น", "ชอบพูดคุย", "มักพูดถึงเงิน/อาหาร"],
        "outis": ["เรียก Dante ว่า 'ท่านผู้จัดการ'", "ทำความเคารพ"],
        "faust": ["อ้างอิงตัวเองเป็นบุรุษที่ 3 (ฟาวสท์)", "พูดด้วยความมั่นใจ"],
        "charon": ["พูดถึงตัวเองด้วยชื่อตัวเอง", "พูดสั้นๆ", "ใช้คำเด็ก"],
        "meursault": ["ไม่แสดงอารมณ์", "พูดตรงไปตรงมา", "มีโครงสร้าง"],
        "hong lu": ["สุภาพ", "มักพูดถึงอาหารหรือความสะดวกสบาย"],
        "kromer": ["เรียกคนด้วยน้ำเสียงเยาะเย้ย", "เรียก Sinclair ว่าของตัวเอง"],
        "dongrang": ["เยาะเย้ยความสำเร็จของคนอื่น", "แฝงความหลงตัวเอง"],
        "vergilius": ["พูดน้อยแต่มีน้ำหนัก", "ภาษามีอำนาจ"],
        "yi sang": ["มักใช้คำเปรียบเทียบเชิงนามธรรม", "พูดเงียบๆ"],
    }

    for key, qs in specific_quirks.items():
        if key in name_lower:
            quirks.extend(qs)
            return quirks

    if "stutter" in text or "stammers" in text:
        quirks.append("มักพูดตะกุกตะกก")
    if "third person" in text:
        quirks.append("พูดถึงตัวเองด้วยชื่อตัวเอง")
    if "sarcastic" in text or "sardonic" in text:
        quirks.append("มักพูดเย้ยหยัน")
    if "abbreviation" in text:
        quirks.append("ใช้คำย่อ")

    return quirks if quirks else []


def generate_thai_voice_guide(profile: dict) -> str:
    """Generate a compact Thai voice guide string from a character profile."""
    name = profile["name_en"]
    tone = profile["tone"]
    register = profile["register"]
    pronouns = profile["pronouns"]
    quirks = profile["key_quirks"]
    patterns = profile["speech_patterns"]
    personality = profile["personality"]

    tone_descriptions = {
        "chivalric_enthusiastic": "มุ่งมั่น มีความยุติธรรมสูง ใช้ภาษาอัศวิน",
        "intellectual_confident": "มั่นใจ ใช้เหตุผลนำ พูดตรงไปตรงมา",
        "world_weary_casual": "สบายๆ ทหารผ่านศึก แฝงความเหนื่อยหน่าย",
        "hot_tempered_brusque": "ดุดัน โมโหง่าย แต่มีความอ่อนไหวภายใน",
        "level_headed_sardonic": "มีเหตุผล เย็นชา มักเย้ยหยัน",
        "terse_artistic": "สั้น กระชับ มีมุมมองเฉพาะตัว",
        "melancholic_contemplative": "เงียบขรึม มีนัยยะลึกซึ้ง มักใช้คำเปรียบเทียบ",
        "cheerful_noble": "ร่าเริง สุภาพ มีมารยาทชั้นสูง",
        "logical_detached": "มีเหตุผล ไม่แสดงอารมณ์ พูดตรงไปตรงมา",
        "warm_brazen": "อบอุ่น เป็นกันเอง ชอบเรียกคนอื่นด้วยชื่อเล่น",
        "timid_anxious": "ไม่มั่นใจ มักขอโทษ ลังเล",
        "formal_disciplined": "ทางการ มีระเบียบวินัย เคารพผู้บังคับบัญชา",
        "cold_authoritative": "เย็นชา มีอำนาจ พูดน้อยแต่มีน้ำหนัก",
        "childish_brief": "พูดสั้นๆ ใช้คำเด็ก พูดถึงตัวเองด้วยชื่อตัวเอง",
        "awkward_determined": "อึดอัด พยายามจริง มักถามคำถาม",
        "cruel_mocking": "เยาะเย้ย ดูถูก ใช้น้ำเสียงเป็นมิตรเทียม",
        "authoritative_strict": "เข้มงวด มีอำนาจ พูดสั่งการ",
        "warm_friendly": "อบอุ่น เป็นมิตร",
        "cold_detached": "เย็นชา ไม่สนใจ",
        "neutral": "",
    }

    register_descriptions = {
        "formal": "ภาษาทางการ เคารพ",
        "casual": "ภาษาปาก เป็นกันเอง",
        "terse": "พูดน้อย สั้นกระชับ",
        "neutral": "",
    }

    parts = []
    tone_desc = tone_descriptions.get(tone, "")
    if tone_desc:
        parts.append(f"บุคลิก: {tone_desc}")

    register_desc = register_descriptions.get(register, "")
    if register_desc:
        parts.append(f"ระดับภาษา: {register_desc}")

    if pronouns.get("thai"):
        pronoun_str = pronouns["thai"]
        if pronouns.get("note"):
            pronoun_str += f" ({pronouns['note']})"
        parts.append(f"สรรพนาม: {pronoun_str}")

    if quirks:
        parts.append("ลักษณะพิเศษ: " + ", ".join(quirks))

    # Add brief personality excerpt for context
    if personality:
        excerpt = personality[:200].strip()
        if excerpt and excerpt[-1] not in ".!?。":
            excerpt = excerpt.rsplit(".", 1)[-1] if "." in excerpt else excerpt
        # Keep very short for prompt efficiency
        pass

    return "\n".join(parts)


def build_all_profiles() -> dict:
    """Parse all character MD files and build voice guides."""
    profiles = {}
    guides = {}

    if not CHARACTERS_DIR.exists():
        return {}

    for md_file in sorted(CHARACTERS_DIR.glob("*.md")):
        if md_file.name == "characters_clean.md":
            continue

        profile = parse_md_character(md_file)
        voice_guide = generate_thai_voice_guide(profile)
        name_key = md_file.stem

        profiles[name_key] = profile
        guides[name_key] = voice_guide

    return guides


def save_voice_guides(guides: dict, output_path: Path = OUTPUT_FILE):
    """Save voice guides to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(guides, f, ensure_ascii=False, indent=2)


def load_voice_guides(path: Path = OUTPUT_FILE) -> dict:
    """Load voice guides from JSON cache."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_voice_guide_for_character(character_name: str, guides: dict) -> str:
    """Look up voice guide by character name (English), with fuzzy matching."""
    if not character_name:
        return ""

    name_lower = character_name.lower().replace(" ", "_")

    # Direct match
    if name_lower in guides:
        return guides[name_lower]

    # Try without underscores
    name_no_underscore = character_name.lower().replace(" ", "_")
    if name_no_underscore in guides:
        return guides[name_no_underscore]

    # Try with underscores as spaces
    name_with_underscore = character_name.lower().replace(" ", "_")
    for key in guides:
        if key.lower() == name_with_underscore:
            return guides[key]

    # Partial match
    for key in guides:
        key_lower = key.lower().replace("_", " ")
        if name_lower.replace("_", " ") in key_lower or key_lower in name_lower.replace("_", " "):
            return guides[key]

    # Check common name variations
    variations = _get_name_variations(character_name)
    for var in variations:
        var_key = var.lower().replace(" ", "_")
        if var_key in guides:
            return guides[var_key]

    return ""


def _get_name_variations(name: str) -> list:
    """Get common name variations for fuzzy matching."""
    variations = [name]
    name_lower = name.lower().replace("ō", "o").replace("ū", "u")

    # Known variations (normalized)
    variation_map = {
        "ryoshu": ["Ryoshu", "Ryōshū"],
        "ryōshū": ["Ryoshu", "Ryōshū"],
        "don quixote": ["Don Quixote", "Don_Quixote"],
        "yi sang": ["Yi Sang", "Yi_Sang"],
        "hong lu": ["Hong Lu", "Hong_Lu"],
        "a certain sinclair": ["Sinclair", "A_Certain_Sinclair"],
        "erlking heathcliff": ["Erlking_Heathcliff"],
        "every catherine": ["Every_Catherine"],
        "eunbongs bar  fryers owner": ["Eunbongs_Bar__Fryers_Owner"],
        "the barber": ["The_Barber"],
        "the priest": ["The_Priest"],
        "the time ripper": ["The_Time_Ripper"],
        "the indigo elder": ["The_Indigo_Elder"],
        "old g corp head manager": ["Old_G_Corp_Head_Manager"],
        "bamboo-hatted kim": ["Bamboo-hatted_Kim"],
    }

    for key, vars_list in variation_map.items():
        if name_lower == key or name_lower in [v.lower() for v in vars_list]:
            variations.extend(vars_list)
            break

    return variations


if __name__ == "__main__":
    guides = build_all_profiles()
    save_voice_guides(guides)
    print(f"Built voice guides for {len(guides)} characters")
    for name, guide in sorted(guides.items()):
        print(f"\n--- {name} ---")
        print(guide)