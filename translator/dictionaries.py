"""Static dictionaries and post-processors for Thai localization."""
import re
from typing import Dict, Tuple

# Korean model name -> Thai teller name (from stlinx reference)
KOREAN_TO_THAI_TELLER = {
    # Main Sinners
    "단테": "ดันเต้",
    "파우스트": "เฟาสท์",
    "돈키호테": "ดอนกิโฮเต้",
    "료슈": "เรียวชู",
    "뫼르소": "เมอร์โซ",
    "홍루": "หงลู่",
    "히스클리프": "ฮีธคลิฟฟ์",
    "이스마엘": "อิชมาเอล",
    "로쟈": "โรเดียน",
    "싱클리어": "ซินแคลร์",
    "싱클 레어": "ซินแคลร์",
    "오티스": "อูทิส",
    "그레고르": "เกรกอร์",
    "이상": "อีซัง",
    "베르길리우스": "เวอร์จิลิอุส",
    
    # NPCs / Side characters (from stlinx reference)
    "유리": "ยูริ",
    "홉킨스": "ฮอปกินส์",
    "동랑": "ทงรัง",
    "가치우": "ขงชิว",
    "가시춘": "จื่อชุน",
    "웨이": "เหวย",
    "자공": "จื่อกง",
    "임대옥다침2": "อิมแดอ๊ก",
    "다친뇌횡": "เหลยเหิง",
    "다친가시춘2": "ซีชุน",
    "습인": "ซีเหริน",
    
    # Distorted / Alternate
    "단테3": "ดันเต้",
    "히스클리프2": "ฮีธคลิฟฟ์",
    "료슈F": "เรียวชู",
    "료슈2": "เรียวชู",
    "그레고르F": "เกรกอร์",
    "이스마엘F": "อิชมาเอล",
    "오티스F": "อูทิส",
    "싱클리어F": "ซินแคลร์",
    "홍루F": "หงลู่",
    "이상F": "อีซัง",
    "메르소F": "เมอร์โซ",
    "메르소": "เมอร์โซ",
    
    # Generic / keep English
    "연구원": "Researcher",
    "납치범": "Kidnapper",
    "조수": "Assistant",
    "라디오": "Radio",
    "파일럿": "Pilot",
    "면접관": "Interviewer",
    "스위퍼": "Sweeper",
    "거울세계": "Mirror World",
}

# English teller -> Thai teller (for cases where teller is already in English)
ENGLISH_TO_THAI_TELLER = {
    # 12 Sinners
    "Dante": "ดันเต้",
    "Faust": "เฟาสท์",
    "Don Quixote": "ดอนกิโฮเต้",
    "Ryoshu": "เรียวชู",
    "Ryōshū": "เรียวชู",
    "Meursault": "เมอร์โซ",
    "Hong Lu": "หงลู่",
    "Heathcliff": "ฮีธคลิฟฟ์",
    "Ishmael": "อิชมาเอล",
    "Rodion": "โรเดียน",
    "Sinclair": "ซินแคลร์",
    "Outis": "อูทิส",
    "Gregor": "เกรกอร์",
    "Yi Sang": "อีซัง",
    # Main NPCs
    "Vergilius": "เวอร์จิลิอุส",
    "Charon": "แครอน",
    "Yuri": "ยูริ",
    "Hopkins": "ฮอปกินส์",
    "Kromer": "โครเมอร์",
    "Dongrang": "ทงรัง",
    "Dongbaek": "ทงแบ็ก",
    "Aseah": "อาเซีย",
    "Demian": "เดเมียน",
    "Effie": "เอฟฟี",
    "Samjo": "ซัมโจ",
    "Moses": "โมเสส",
    "Ezra": "เอสรา",
    "Hermann": "แฮร์มันน์",
    "Catherine": "แคทเธอรีน",
    "Hindley": "ฮินด์ลีย์",
    "Linton": "ลินตัน",
    "Nelly": "เนลลี",
    "Ahab": "อาแฮบ",
    "Queequeg": "ควีควีก",
    "Starbuck": "สตาร์บัก",
    "Stubb": "สตับบ์",
    "Bari": "บารี",
    "Sansón": "ซองซง",
    "Dulcinea": "ดุลซิเนีย",
    "Hohenheim": "โฮเอนไฮม์",
    "Guido": "กวีโด",
    "Ricardo": "ริการ์โด",
    "Alfonso": "อัลฟองโซ",
    "Vespa": "เวสปา",
    "Josephine": "โจเซฟีน",
    "Paula": "เพาลา",
    "Siegfried": "ซิกฟรีด",
    "Cassetti": "คาสเซตตี",
    "Caiman": "ไคแมน",
    "Bumble": "บัมเบิล",
    "Alan": "อลัน",
    "Aida": "ไอดา",
    "Camille": "คามิลล์",
    "Shrenne": "ชเรนเนอ",
    "Araya": "อารายา",
    "Han-ul": "ฮันอึล",
    "Wei": "เหวย",
    "Gubo": "กูโป",
    "Zilu": "จือหลู",
    "Zigong": "จื่อกง",
    "Xiren": "ซีเหริน",
    "Lin Daiyu": "หลินได้อวี่",
    "Xue Baochai": "เซวะเป่าฉาย",
    "Xue Pan": "เซวะพาน",
    "Jia Huan": "เจี่ยฮวน",
    "Jia Mu": "เจี่ยมู่",
    "Jia Yuanchun": "เจี่ยหยวนชุน",
    "Jia Qiu": "เจี่ยชิว",
    "Jia Zheng": "เจี่ยเจิ้ง",
    "Lady Wang": "หวางไท่ไท่",
    "Wang Ren": "หวันเหริน",
    "Wang Dawei": "หวันต้าเวย",
    "Wang Qingshan": "หวันชิงชาน",
    "Wang Zhao": "หวันเจ้า",
    "Lei Heng": "เหลยเหิง",
    "Kong Youjin": "ขงหยูจิน",
    "Kong Sihui": "ขงซีฮุย",
    "Shi Huazhen": "ซีหัวเจิ้น",
    "Shi Sijing": "ซีซี่จิ้ง",
    "Shi Yihua": "ซีอี้หัว",
    "Lion": "ไลออน",
    "Panther": "แพนเทอร์",
    "Wolf": "วูลฟ์",
    "Rain": "เรน",
    "Ran": "รัน",
    "Ravi": "ราวี",
    "Ren": "เรน",
    "Rien": "เรียน",
    "Rim": "ริม",
    "Niko": "นีโก",
    "Marile": "มาริเลอ",
    "Cesara": "เชซารา",
    "Tomah": "โทมาห์",
    "Callisto": "แคลลิสโต",
    "Alex": "อเล็กซ์",
    "Alessio": "อาเลสซีโอ",
    "Night Drifter": "ผู้พเนจรแห่งราตรี",
    "The Barber": "ช่างตัดผม",
    "The Priest": "บาทหลวง",
    "The Indigo Elder": "ผู้เฒ่าคราบน้ำเงิน",
    "The Time Ripper": "ผู้ฉีกเวลา",
    "Erlking Heathcliff": "เอิร์ลคิง ฮีธคลิฟฟ์",
    "Every Catherine": "แคทเธอรีนทุกคน",
    "Bamboo-hatted Kim": "คิมหมวกไม้ไผ่",
    "Fiddler": "ฟิดเลอร์",
    # Identity variants
    "W. Faust": "เฟาสท์",
    "Liu Gregor": "หลิว เกรกอร์",
    "Seven Ryoshu": "เรียวชู",
    "Seven Ryōshū": "เรียวชู",
    "Seven Yi Sang": "อีซัง",
    "Blade Lineage Outis": "อูทิส",
    "Blade Lineage Sinclair": "ซินแคลร์",
    "Kurokumo Rodion": "โรเดียน",
    "Kurokumo Hong Lu": "หงลู่",
    "Shi Heathcliff": "ฮีธคลิฟฟ์",
    "Liu Meursault": "หลิว เมอร์โซ",
    "R Corp. Ishmael": "อิชมาเอล",
    "Don Quixote & T Corp. Staff": "ดอนกิโฮเต้",
    "Heathcliff, The Heartbroken": "ฮีธคลิฟฟ์",
    "Magical Girl": "ดอนกิโฮเต้",
    "A Prosthetic Head": "ดันเต้",
    "Dongrang, Who Denies All": "ทงรัง",
    "Narrator": "ผู้บรรยาย",
    "Researcher": "นักวิจัย",
}

# Title word-order fixes: Pattern -> Replacement
# Converts "Grade X Fixer" -> "Fixer ระดับ X"
TITLE_PATTERNS = [
    # "Grade N Fixer" -> "Fixer ระดับ N"
    (re.compile(r'Grade\s+(\d+)\s+Fixer', re.IGNORECASE), r'Fixer ระดับ \1'),
    # "Class N Fixer" -> "Fixer ระดับ N"  
    (re.compile(r'Class\s+(\d+)\s+Fixer', re.IGNORECASE), r'Fixer ระดับ \1'),
    # "Level N Fixer" -> "Fixer ระดับ N"
    (re.compile(r'Level\s+(\d+)\s+Fixer', re.IGNORECASE), r'Fixer ระดับ \1'),
    # "G Corp. Remnant" -> "เศษซาก G Corp."
    (re.compile(r'G\s+Corp\.?\s+Remnant', re.IGNORECASE), r'เศษซาก G Corp.'),
    (re.compile(r'Remnant\s+of\s+G\s+Corp', re.IGNORECASE), r'เศษซาก G Corp.'),
    # "Head Manager" -> "หัวหน้าผู้จัดการ"
    (re.compile(r'Head\s+Manager', re.IGNORECASE), r'หัวหน้าผู้จัดการ'),
    # "Executive Manager" -> "ผู้จัดการ"
    (re.compile(r'Executive\s+Manager', re.IGNORECASE), r'ผู้จัดการ'),
    # "District N" in titles
    (re.compile(r'District\s+(\d+)', re.IGNORECASE), r'เขต \1'),
]

# Location vocabulary: English -> Thai
LOCATION_TERMS = {
    "entryway": "ทางเข้า",
    "interior": "ภายในศูนย์",
    "exterior": "ภายนอก",
    "lobby": "ล็อบบี้",
    "hallway": "ทางเดิน",
    "corridor": "ทางเดิน",
    "office": "สำนักงาน",
    "branch": "สาขา",
    "center": "ศูนย์",
    "station": "สถานี",
    "entrance": "ทางเข้า",
    "exit": "ทางออก",
    "room": "ห้อง",
    "chamber": "ห้อง",
    "floor": "ชั้น",
    "level": "ระดับ",
    "sector": "ภาคส่วน",
    "zone": "เขต",
    "area": "พื้นที่",
    "site": "สถานที่",
    "facility": "สถานที่",
    "headquarters": "สำนักงานใหญ่",
    "main office": "สำนักงานใหญ่",
    "branch office": "สำนักงานสาขา",
}

# Place name patterns: English -> Thai
PLACE_PATTERNS = [
    # "District N" -> "เขต N"
    (re.compile(r'District\s+(\d+)', re.IGNORECASE), r'เขต \1'),
    # "L Corp" -> "L Corp."
    (re.compile(r'LC\s+Branch', re.IGNORECASE), r'สาขา L Corp.'),
    (re.compile(r'L\s+Corp\.?', re.IGNORECASE), r'L Corp.'),
]

# Post-translation fixes for common AI mistakes
POST_TRANSLATION_FIXES = [
    # Fix word order: "ระดับ X Fixer" -> "Fixer ระดับ X"
    (re.compile(r'ระดับ\s+(\d+)\s+Fixer'), r'Fixer ระดับ \1'),
    (re.compile(r'เกรด\s+(\d+)\s+Fixer'), r'Fixer เกรด \1'),
    # Fix "Fixer grade/class/level N" -> "Fixer ระดับ N"
    (re.compile(r'Fixer\s+grade\s+(\d+)', re.IGNORECASE), r'Fixer ระดับ \1'),
    (re.compile(r'Fixer\s+class\s+(\d+)', re.IGNORECASE), r'Fixer ระดับ \1'),
    (re.compile(r'Fixer\s+level\s+(\d+)', re.IGNORECASE), r'Fixer ระดับ \1'),
    # Fix "Remnant แห่ง G Corp" -> "เศษซาก G Corp."
    (re.compile(r'Remnant\s+แห่ง\s+G\s+Corp', re.IGNORECASE), r'เศษซาก G Corp.'),
    # Fix "G Corp" spacing
    (re.compile(r'G\s+Corp(?!\.)'), r'G Corp.'),
    # Fix "L Corp" spacing  
    (re.compile(r'L\s+Corp(?!\.)'), r'L Corp.'),
    # Fix double spaces
    (re.compile(r'  +'), r' '),
]

# Character name replacements in content text
# Maps English names -> Thai names (when AI keeps them in English)
CONTENT_NAME_REPLACEMENTS = [
    # Character names
    (re.compile(r'Vergilius'), r'เวอร์จิลิอุส'),
    (re.compile(r'Hopkins'), r'ฮอปกินส์'),
    (re.compile(r'Yuri'), r'ยูริ'),
    (re.compile(r'Gregor(?!\w)'), r'เกรกอร์'),
    (re.compile(r'Faust(?!\w)'), r'เฟาสท์'),
    (re.compile(r'Don Quixote'), r'ดอนกิโฮเต้'),
    (re.compile(r'Ryoshu'), r'เรียวชู'),
    (re.compile(r'Ryōshū'), r'เรียวชู'),
    (re.compile(r'Meursault'), r'เมอร์โซ'),
    (re.compile(r'Hong Lu'), r'หงลู่'),
    (re.compile(r'Ishmael'), r'อิชมาเอล'),
    (re.compile(r'Rodion'), r'โรเดียน'),
    (re.compile(r'Sinclair'), r'ซินแคลร์'),
    (re.compile(r'Outis'), r'อูทิส'),
    (re.compile(r'Yi Sang'), r'อีซัง'),
    (re.compile(r'Heathcliff'), r'ฮีธคลิฟฟ์'),
    (re.compile(r'Dante(?!\w)'), r'ดันเต้'),
    (re.compile(r'Charon'), r'แครอน'),
    (re.compile(r'Red Gaze'), r'เรดเกซ'),
    # Job titles that should be translated
    (re.compile(r'Executive Manager'), r'ผู้จัดการ'),
    (re.compile(r'Head Manager'), r'หัวหน้าผู้จัดการ'),
    # Title patterns in content
    (re.compile(r'G Corp\.?\s+Remnant'), r'เศษซาก G Corp.'),
]


def get_thai_teller(model: str, teller: str) -> str:
    """Get Thai teller name from model or teller field."""
    # Priority: Korean model mapping first
    if model in KOREAN_TO_THAI_TELLER:
        return KOREAN_TO_THAI_TELLER[model]
    
    # Then English teller mapping
    if teller in ENGLISH_TO_THAI_TELLER:
        return ENGLISH_TO_THAI_TELLER[teller]
    
    # Return original if no mapping found
    return teller


def fix_title_word_order(text: str) -> str:
    """Fix word order in title fields."""
    if not text:
        return text
    
    for pattern, replacement in TITLE_PATTERNS:
        text = pattern.sub(replacement, text)
    
    return text


def translate_place_name(text: str) -> str:
    """Translate place names while keeping proper nouns and reordering to Thai syntax.
    
    This is now a FALLBACK function - the glossary is checked first in engine.py.
    Only called when the glossary doesn't have a match.
    """
    if not text:
        return text
    
    # Handle non-place values
    if text == "-1" or text == -1:
        return "-1"
    if text == "???" or text == "???":
        return text
    
    original = text
    text_lower = text.lower()
    
    # Extract components
    district_match = re.search(r'District\s+(\d+)', text, re.IGNORECASE)
    district_part = f"เขต {district_match.group(1)}" if district_match else ""
    
    corp_match = re.search(r'L\s*C\s*(?:orp\.?|Branch)?', text, re.IGNORECASE)
    corp_part = "L Corp."
    branch_part = "สาขา"
    
    # Find location descriptor (last word usually)
    location_word = None
    location_thai = ""
    for eng, thai in LOCATION_TERMS.items():
        if eng.lower() in text_lower:
            location_word = eng
            location_thai = thai
            break
    
    # Reconstruct in Thai order: [Location] [Corp] [Branch] [District]
    parts = []
    if location_thai:
        parts.append(location_thai)
    if corp_part:
        parts.append(corp_part)
    if branch_part and district_part:
        parts.append(branch_part + district_part)
    elif district_part:
        parts.append(district_part)
    
    if parts:
        return " ".join(parts)
    
    # Fallback: apply regex patterns
    for pattern, replacement in PLACE_PATTERNS:
        text = pattern.sub(replacement, text)
    
    # Clean up extra spaces around hyphens
    text = re.sub(r'\s+-\s+', ' - ', text)
    text = re.sub(r'  +', ' ', text)
    
    return text.strip()


def post_process_translation(text: str) -> str:
    """Apply post-translation fixes."""
    if not text:
        return text
    
    for pattern, replacement in POST_TRANSLATION_FIXES:
        text = pattern.sub(replacement, text)
    
    return text.strip()


def fix_character_names_in_content(text: str) -> str:
    """Replace English character names with Thai names in translated content."""
    if not text:
        return text
    
    for pattern, replacement in CONTENT_NAME_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    
    return text


# Character voice guidance for prompt injection
CHARACTER_VOICE_GUIDE = {
    "Gregor": """
เกรกอร์เป็นทหารผ่านศึกที่เคยรับใช้บริษัทเก่า มีท่าทีสบายๆ แต่แฝงความ bettered
- ใช้สรรพนาม: พวกเธอ (ไม่ใช่ คุณ) เมื่อพูดกับคนทั่วไป
- ใช้คำพูดสบายๆ: อ่า..., เอ๊ะ..., ฮึ...
- ไม่พูดสุภาพมาก แต่ไม่หยาบคาย
- มีประสบการณ์ชีวิตมาก มักใช้คำเปรียบเทียบจากชีวิตจริง
- มีความเห็นใจผู้อื่นแต่แสดงออกแบบกลั้นๆ""",
    
    "Faust": """
เฟาสท์เป็นผู้เชี่ยวชาญที่มั่นใจในตัวเองสูง ใช้เหตุผลนำทางทุกอย่าง
- ใช้ภาษาที่เป็นทางการและแม่นยำ
- มักอ้างอิง "การวิเคราะห์" "ข้อมูล" "ความน่าจะเป็น"
- มีความมั่นใจสูง แต่ไม่ถือตัว
- ใช้คำพูดตรงไปตรงมา""",
    
    "Don Quixote": """
ดอนกิโฮเต้มีบุคลิกแบบอัศวินในตำนาน มุ่งมั่นและมีความยุติธรรมสูง
- ใช้ภาษาที่ยกระดับตนเอง: ข้า, ข้าพเจ้า
- ใช้คำเก่าแก่หรือยกระดับ: อุทิศ, ศึก, ศักดิ์ศรี
- มีพลังงานสูง มักตะโกนหรือพูดด้วยความตื่นเต้น
- มองตัวเองเป็นวีรบุรุษ""",
    
    "Ishmael": """
อิชมาเอลเป็นผู้ที่เคยผ่านความสูญเสียมาอย่างหนัก มีท่าทีเย็นชาแต่มีเหตุผล
- ใช้ภาษาที่กระชับและตรงประเด็น
- มักแสดงความไม่พอใจหรือความเหนื่อยหน่าย
- มีประสบการณ์ทะเลมาก
- ใช้คำพูดที่แสดงความเป็นผู้นำแบบเงียบๆ""",
    
    "Heathcliff": """
ฮีธคลิฟฟ์มีท่าทีดุดันและโมโหง่าย แต่ภายในมีความอ่อนไหว
- ใช้ภาษาหยาบๆ ฉุนเฉียว: เฮ้ย!, บ้าเอ้ย!, ไอ้...
- มักตะโกนหรือพูดเสียงดัง
- ใช้สำนวนถิ่นหรือภาษาปาก
- แสดงความโกรธง่ายแต่ก็หายเร็ว""",
    
    "Ryoshu": """
เรียวชูเป็นศิลปินที่มีมุมมองเฉพาะตัว พูดน้อยแต่มีความหมาย
- ใช้ภาษากระชับ สั้นๆ ตรงประเด็น
- มักใช้คำเปรียบเทียบทางศิลปะ: งดงาม, สมบูรณ์แบบ, สิ่งประดิษฐ์
- มีความภาคภูมิใจในฝีมือตนเองสูง
- ดูเย็นชาแต่มีแรงบันดาลใจลึกๆ""",
    
    "Yi Sang": """
อีซังเป็นคนฉลาดและมีความคิดสร้างสรรค์ แต่มักกังวลใจ
- ใช้ภาษาที่กระชับและมีนัยยะ
- มักใช้คำถามหรือคำกล่าวที่มีความหมายลึกซึ้ง
- มีความสงสัยในตัวเอง
- ใช้ภาษาที่เป็นนามธรรม""",
    
    "Hong Lu": """
หงลู่มาจากตระกูลที่ร่ำรวย มีท่าทีสุขุมและมีมารยาท
- ใช้ภาษาสุภาพ มารยาทดี
- มักพูดถึงความสะดวกสบายหรือของกิน
- มีความรู้สึกดีต่อเพื่อนร่วมทีม
- ใช้คำพูดที่แสดงความเป็นขุนนางหรือคนชั้นสูง""",
    
    "Meursault": """
เมอร์โซเป็นคนที่มีเหตุผลและไม่แสดงอารมณ์มาก
- ใช้ภาษาตรงไปตรงมา ไม่มีน้ำจิ้มน้ำใจ
- มักวิเคราะห์สถานการณ์อย่างเป็นกลาง
- ไม่แสดงความรู้สึกส่วนตัว
- ใช้คำพูดที่เป็นระบบและมีโครงสร้าง""",
    
    "Rodion": """
โรเดียนเป็นคนที่ร่าเริงและชอบพูดคุย
- ใช้ภาษาที่เป็นกันเองและอบอุ่น
- มักใช้คำลงท้ายแบบผู้หญิง: ~นะ, ~สิ
- ชอบช่วยเหลือผู้อื่น
- มีความมั่นใจในตัวเอง""",
    
    "Sinclair": """
ซินแคลร์เป็นคนที่อายุน้อยที่สุดในทีม มักกลัวและกังวล
- ใช้ภาษาที่แสดงความไม่มั่นใจ: ผมคิดว่า..., อาจจะ...
- มักขอโทษหรือแสดงความกังวล
- ใช้สรรพนามสุภาพ: ผม, ครับ/ค่ะ
- มีความกตัญญูสูง""",
    
    "Outis": """
อูทิสเป็นทหารที่มีระเบียบวินัยสูง
- ใช้ภาษาทางการ มารยาทดี
- มักเรียก "ท่านผู้จัดการ" หรือใช้คำสุภาพ
- มีความภักดีสูง
- ใช้ภาษาที่แสดงความเคารพ""",
    
    "Vergilius": """
เวอร์จิลิอุสเป็นผู้นำที่ลึกลับและมีอำนาจ
- ใช้ภาษาที่แสดงความเป็นผู้นำ
- มักพูดน้อยแต่มีน้ำหนัก
- มีท่าทีเย็นชาและไม่อาจคาดเดาได้
- ใช้คำพูดที่มีความหมายลึกซึ้ง""",
}


def get_character_voice_guide(teller: str) -> str:
    """Get voice guidance for a character."""
    # Map teller names to guide keys
    name_map = {
        "Gregor": "Gregor",
        "Liu Gregor": "Gregor",
        "Faust": "Faust",
        "W. Faust": "Faust",
        "Don Quixote": "Don Quixote",
        "Ryoshu": "Ryoshu",
        "Ryōshū": "Ryoshu",
        "Seven Ryoshu": "Ryoshu",
        "Seven Ryōshū": "Ryoshu",
        "Ishmael": "Ishmael",
        "Heathcliff": "Heathcliff",
        "Shi Heathcliff": "Heathcliff",
        "Hong Lu": "Hong Lu",
        "Kurokumo Hong Lu": "Hong Lu",
        "Yi Sang": "Yi Sang",
        "Seven Yi Sang": "Yi Sang",
        "Meursault": "Meursault",
        "Liu Meursault": "Meursault",
        "Rodion": "Rodion",
        "Kurokumo Rodion": "Rodion",
        "Sinclair": "Sinclair",
        "Blade Lineage Sinclair": "Sinclair",
        "Outis": "Outis",
        "Blade Lineage Outis": "Outis",
        "Vergilius": "Vergilius",
    }
    
    key = name_map.get(teller, "")
    return CHARACTER_VOICE_GUIDE.get(key, "")
