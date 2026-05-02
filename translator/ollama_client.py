"""OpenRouter API client with Gemini for batch translation."""
import json
import re
import time
from typing import Optional, List, Dict, Tuple

from openai import OpenAI

from .config import (
    OPENROUTER_API_KEYS, OPENROUTER_MODEL, OPENROUTER_BASE_URL,
    USE_OPENROUTER, OLLAMA_HOST, OLLAMA_MODEL, DELAY_BETWEEN_REQUESTS
)
from .logger import TranslationLogger


class OllamaClient:
    """Client for translation API (OpenRouter Gemini or local Ollama fallback)."""
    
    def __init__(self, logger: TranslationLogger, api_key: str = None):
        self.logger = logger
        self.use_openrouter = USE_OPENROUTER
        
        if self.use_openrouter:
            # Use provided key or fall back to first key
            key = api_key or (OPENROUTER_API_KEYS[0] if OPENROUTER_API_KEYS else None)
            self.client = OpenAI(
                base_url=OPENROUTER_BASE_URL,
                api_key=key,
                default_headers={
                    "HTTP-Referer": "https://localhost",
                    "X-Title": "Limbus Thai Translator"
                }
            )
            self.model = OPENROUTER_MODEL
            self.logger.log_info(f"Using OpenRouter with model: {self.model}")
        else:
            import requests
            self.session = requests.Session()
            self.host = OLLAMA_HOST
            self.model = OLLAMA_MODEL
            self.logger.log_info(f"Using Ollama with model: {self.model}")
        
    def check_connection(self) -> bool:
        """Check if translation API is accessible."""
        if self.use_openrouter:
            try:
                # Quick test with a minimal request
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )
                self.logger.log_info(f"Connected to OpenRouter. Model '{self.model}' is available.")
                return True
            except Exception as e:
                self.logger.log_error(f"OpenRouter connection failed: {e}")
                return False
        else:
            import requests
            try:
                response = self.session.get(f"{self.host}/api/tags", timeout=10)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    
                    if self.model in model_names or any(self.model in name for name in model_names):
                        self.logger.log_info(f"Connected to Ollama. Model '{self.model}' is available.")
                        return True
                    else:
                        self.logger.log_warning(f"Model '{self.model}' not found. Available: {model_names}")
                        return False
                else:
                    self.logger.log_error(f"Ollama returned status {response.status_code}")
                    return False
            except requests.exceptions.ConnectionError:
                self.logger.log_error(f"Cannot connect to Ollama at {self.host}. Is it running?")
                return False
            except Exception as e:
                self.logger.log_error(f"Error checking Ollama connection", e)
                return False
    
    def translate_batch(self, items: List[Tuple[str, str, str]], 
                       context: str = "", file_type: str = "general",
                       entry_contexts: Dict[str, str] = None) -> Dict[str, str]:
        """
        Translate a batch of related text items together.
        
        Args:
            items: List of (path, field, text) tuples
            context: Base context string (worldbuilding, scene info)
            file_type: Type of file for few-shot examples
            entry_contexts: Optional dict mapping path -> character voice guide string
                           for per-entry character context injection
        """
        if not items:
            return {}
        
        if self.use_openrouter:
            return self._translate_batch_openrouter(items, context, file_type, entry_contexts)
        else:
            return self._translate_batch_ollama(items, context, file_type, entry_contexts)
    
    def _translate_batch_openrouter(self, items: List[Tuple[str, str, str]], 
                                     context: str, file_type: str,
                                     entry_contexts: Dict[str, str] = None) -> Dict[str, str]:
        """Translate using OpenRouter Gemini."""
        
        few_shots = self._get_few_shot_examples(file_type)
        
        # Build numbered list of items to translate, with per-entry character context
        items_text = []
        for i, (path, field, text) in enumerate(items):
            # Add character context annotation if available
            char_ctx = ""
            if entry_contexts and path in entry_contexts:
                char_ctx = f" [{entry_contexts[path]}]"
            items_text.append(f"[{i}]{char_ctx} {text}")
        
        items_str = "\n".join(items_text)
        
        system_prompt = f"""You are a professional game translator for Limbus Company, translating from English to Thai.

Your role:
- Translate text into natural, gamer-friendly Thai
- Preserve character tone, emotion, and personality
- Use terminology popular in the Thai gaming community

CRITICAL RULES:
1. Characters inside §§§...§§§ are placeholders - NEVER translate or modify them
2. Game terms keep English: Sinner, Sinners, Abnormality, E.G.O, Golden Bough, The City, The Head, Fixer, Wing, District, Nest, Backstreets, Mirror Dungeon, Railway Dungeon, WARP, Limbus Company, Feather
3. Bracketed status/effect names like [Breath], [Charge], [Agility] must stay in English
4. HTML/Unity tags like <color=#...>, <sprite...>, <b>, </b>, <ruby=...> must not be translated
5. Variables like [{{0}}], [{{1}}], %s must not be translated
6. Preserve formatting (newlines, spacing, quotes)
7. Translate naturally, NOT word-for-word
8. WORD ORDER RULE: When translating titles with English nouns + Thai numbers, put the English noun FIRST. Examples: "Fixer grade 8" -> "Fixer ระดับ 8". "Manager high-level" -> "Manager ระดับสูง". English noun always comes before Thai classifier/number.
9. For stuttering/repetition like "T-to" or "N-no", preserve the pattern in Thai: "ก-ก็", "ม-ไม่"
10. CHARACTER VOICE: When a line is annotated with [กำลังพูด: ...], translate that line using that character's voice and personality. Match their tone, pronouns, speech register, and mannerisms.
11. PLACE NAMES: Keep proper nouns in English (Wuthering Heights, La Manchaland, Mephistopheles, Daguanyuan). Translate location descriptors to Thai: Hall -> ห้องโถง, Hallway/Corridor -> ทางเดิน, Interior -> ภายใน, Entrance -> ทางเข้า, Room -> ห้อง. Word order: [Thai descriptor] + [proper noun]. Examples: "Wuthering Heights Hall" -> "ห้องโถง Wuthering Heights", "K Corp. Laboratory" -> "ห้องปฏิบัติการ K Corp."
12. TELLER NAMES: Character names in teller/title fields are already translated by the system. Do NOT retranslate them. If you see Thai text in a teller/title field, keep it as-is.
13. TITLES: Keep organization names in English (The Middle, The Index, The Thumb, etc.). Translate role descriptors into Thai. Examples: "Class 2 Collection Staff" -> "เจ้าหน้าที่เก็บกู้ ระดับ 2", "Öufi Assoc. Director" -> "ผู้อำนวยการ Öufi Assoc."

{few_shots}

Additional context:
{context}"""

        user_prompt = f"""--- TEXTS TO TRANSLATE ---
{items_str}

--- OUTPUT ---
Return results in this format (each line must start with [N]):
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4096,
                extra_headers={
                    "HTTP-Referer": "https://localhost",
                    "X-Title": "Limbus Thai Translator"
                }
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Parse the batch response
            translations = self._parse_batch_response(translated_text, items)
            
            # Delay between requests
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
            return translations
            
        except Exception as e:
            self.logger.log_error(f"OpenRouter API error: {e}")
            return {}
    
    def _translate_batch_ollama(self, items: List[Tuple[str, str, str]], 
                                 context: str, file_type: str,
                                 entry_contexts: Dict[str, str] = None) -> Dict[str, str]:
        """Translate using local Ollama (fallback)."""
        import requests
        
        few_shots = self._get_few_shot_examples(file_type)
        
        items_text = []
        for i, (path, field, text) in enumerate(items):
            char_ctx = ""
            if entry_contexts and path in entry_contexts:
                char_ctx = f" [{entry_contexts[path]}]"
            items_text.append(f"[{i}]{char_ctx} {text}")
        
        items_str = "\n".join(items_text)
        
        prompt = f"""You are a professional game translator for Limbus Company, translating from English to Thai.

Your role:
- Translate text into natural, gamer-friendly Thai
- Preserve character tone, emotion, and personality
- Use terminology popular in the Thai gaming community

CRITICAL RULES:
1. Characters inside §§§...§§§ are placeholders - NEVER translate or modify them
2. Game terms keep English: Sinner, Sinners, Abnormality, E.G.O, Golden Bough, The City, The Head, Fixer, Wing, District, Nest, Backstreets, Mirror Dungeon, Railway Dungeon, WARP, Limbus Company, Feather
3. Bracketed status/effect names like [Breath], [Charge], [Agility] must stay in English
4. HTML/Unity tags like <color=#...>, <sprite...>, <b>, </b>, <ruby=...> must not be translated
5. Variables like [{{0}}], [{{1}}], %s must not be translated
6. Preserve formatting (newlines, spacing, quotes)
7. Translate naturally, NOT word-for-word
8. WORD ORDER RULE: When translating titles with English nouns + Thai numbers, put the English noun FIRST. Examples: "Fixer grade 8" -> "Fixer ระดับ 8". "Manager high-level" -> "Manager ระดับสูง". English noun always comes before Thai classifier/number.
9. For stuttering/repetition like "T-to" or "N-no", preserve the pattern in Thai: "ก-ก็", "ม-ไม่"
10. CHARACTER VOICE: When a line is annotated with [กำลังพูด: ...], translate that line using that character's voice and personality. Match their tone, pronouns, speech register, and mannerisms.
11. PLACE NAMES: Keep proper nouns in English (Wuthering Heights, La Manchaland, Mephistopheles, Daguanyuan). Translate location descriptors to Thai: Hall -> ห้องโถง, Hallway/Corridor -> ทางเดิน, Interior -> ภายใน, Entrance -> ทางเข้า, Room -> ห้อง. Word order: [Thai descriptor] + [proper noun]. Examples: "Wuthering Heights Hall" -> "ห้องโถง Wuthering Heights", "K Corp. Laboratory" -> "ห้องปฏิบัติการ K Corp."
12. TELLER NAMES: Character names in teller/title fields are already translated by the system. Do NOT retranslate them. If you see Thai text in a teller/title field, keep it as-is.
13. TITLES: Keep organization names in English (The Middle, The Index, The Thumb, etc.). Translate role descriptors into Thai. Examples: "Class 2 Collection Staff" -> "เจ้าหน้าที่เก็บกู้ ระดับ 2", "Öufi Assoc. Director" -> "ผู้อำนวยการ Öufi Assoc."

{few_shots}

Additional context:
{context}

--- TEXTS TO TRANSLATE ---
{items_str}

--- OUTPUT ---
Return results in this format (each line must start with [N]):
"""
        
        try:
            response = self.session.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_ctx": 8192,
                    }
                },
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get("response", "").strip()
                
                translations = self._parse_batch_response(translated_text, items)
                
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
                return translations
            else:
                self.logger.log_error(f"Ollama API error: {response.status_code} - {response.text}")
                return {}
                
        except requests.exceptions.Timeout:
            self.logger.log_error("Ollama request timed out")
            return {}
        except Exception as e:
            self.logger.log_error(f"Error during batch translation", e)
            return {}
    
    def _get_few_shot_examples(self, file_type: str) -> str:
        """Get few-shot examples from stlinx reference translations."""
        
        story_examples = """--- Translation examples from professional translator (Story/Narrative) ---
[Source - PLACE]
District 4 - LC Branch Entryway
[Translation - PLACE]
ทางเข้า L Corp. สาขาเขต 4

[Source - PLACE]
Wuthering Heights Hall
[Translation - PLACE]
ห้องโถง Wuthering Heights

[Source - PLACE]
K Corp. Laboratory Hallway
[Translation - PLACE]
ทางเดินห้องปฏิบัติการ K Corp.

[Source - PLACE]
Aboard Mephistopheles
[Translation - PLACE]
บนรถเมฆิสโตเฟเลส

[Source - PLACE]
Daguanyuan - Special Lecture Hall
[Translation - PLACE]
ต้ากวนอวน - ห้องบรรยายพิเศษ

[Source - PLACE]
Catherine's Room
[Translation - PLACE]
ห้องของแคทเธอรีน

[Source]
Gregor lights his cigarette and takes a drag before sighing a long plume of smoke.
[Translation]
เกรกอร์หยิบบุหรี่ขึ้นมาจุด สูดลมหายใจลึกก่อนจะพ่นควันออกมาเป็นสาย

[Source]
They'd have fared better than this if they got a job at a security company or something...
[Translation]
พวกเขาคงมีชีวิตที่ดีกว่านี้ ถ้าไปสมัครงานกับบริษัทรักษาความปลอดภัยหรืออะไรแบบนั้น...

[Source]
Being a soldier is all they've ever known. The changes required for them to start a new life must have been overwhelming.
[Translation]
พวกเขาใช้ชีวิตทั้งชีวิตเป็นทหาร การเปลี่ยนตัวเองเพื่อเริ่มต้นชีวิตใหม่คงเป็นเรื่องยากเกินไป

[Source]
You have no idea how stubbornly the stigma of being a fallen Wing's remnants will cling to you. If anyone's generous enough to take you in, licking their boots is the least you can do...
[Translation]
พวกเธอไม่มีทางรู้หรอก... ว่าตราบาปของพวกที่รอดจากปีกที่ล่มสลายน่ะ มันติดตัวไปจนวันตาย ถึงขนาดที่แม้จะมีคนใจดีพอจะรับเธอเข้าทำงาน... การเลียรองเท้าพวกเขาคงเป็นต่ำสุดที่พวกเธอต้องทำให้พวกนั้นเลยล่ะ

[Source]
Oh... Sorry 'bout that. Should've chosen my words more carefully.
[Translation]
อ่า... ขอโทษ ฉันน่าจะเลือกคำพูดให้ดีกว่านี้

[Source]
No, it's fine. I'm sure things were rough with G Corp.'s fall, too.
[Translation]
ไม่เป็นไรหรอก ฉันมั่นใจว่าตอนที่ G Corp. พังลง มันก็คงเป็นช่วงเวลาที่โหดร้ายสำหรับคุณเหมือนกัน

[Source]
... The breaking of a Wing is a turbulent affair for many people.
[Translation]
...การที่ Wing ล่มสลาย ไม่ได้เป็นเรื่องเล็กน้อยสำหรับใครเลย"""
        
        dialogue_examples = """--- Translation examples (Character Dialogue) ---
[Source]
Let me lead the charge! I shall raise the banner of victory in the name of justice!
[Translation]
ข้าขอเป็นผู้นำการบุก! ข้าจะชูธงแห่งชัยชนะในนามของความยุติธรรม!

[Source]
The rational choice would be to allow me to handle this.
[Translation]
ทางเลือกที่มีเหตุผลที่สุดคือมอบให้ฉันจัดการเอง"""
        
        keyword_examples = """--- Translation examples (Status/Skill descriptions) ---
[Source]
At 10+ [Charge] Count, Coin Power +1
[Translation]
เมื่อมี [Charge] Count 10+ หน่วย, Coin Power +1

[Source]
Turn End: gain 2 [Vulnerable] and [MentalIncreaseDown] next turn
[Translation]
จบเทิร์น: ได้รับ [Vulnerable] 2 หน่วย และ [MentalIncreaseDown] ในเทิร์นถัดไป"""
        
        examples = {
            "story": story_examples,
            "dialogue": dialogue_examples,
            "skills": keyword_examples,
            "keywords": keyword_examples,
            "ui": """--- Translation examples (UI) ---
[Source]
Mirror Dungeon
[Translation]
Mirror Dungeon""",
        }
        
        return examples.get(file_type, story_examples)
    
    def _parse_batch_response(self, response: str, 
                             items: List[Tuple[str, str, str]]) -> Dict[str, str]:
        """Parse batch translation response."""
        translations = {}
        
        # Split response by lines and look for [N] pattern
        lines = response.split('\n')
        current_idx = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with [N]
            match = re.match(r'^\[(\d+)\]\s*(.*)', line)
            if match:
                # Save previous item
                if current_idx is not None and current_idx < len(items):
                    path, field, original = items[current_idx]
                    translated = ' '.join(current_text).strip()
                    if translated:
                        translations[path] = translated
                
                current_idx = int(match.group(1))
                current_text = [match.group(2)]
            elif current_idx is not None:
                current_text.append(line)
        
        # Save last item
        if current_idx is not None and current_idx < len(items):
            path, field, original = items[current_idx]
            translated = ' '.join(current_text).strip()
            if translated:
                translations[path] = translated
        
        # If parsing failed, fall back to line-by-line
        if not translations and len(lines) >= len(items):
            for i, (path, field, original) in enumerate(items):
                if i < len(lines):
                    translated = lines[i].strip()
                    # Remove [N] prefix if present
                    translated = re.sub(r'^\[\d+\]\s*', '', translated)
                    if translated:
                        translations[path] = translated
        
        return translations
    
    def translate_single(self, text: str, context: str = "") -> Optional[str]:
        """Translate a single text (fallback for small items)."""
        if not text or not text.strip():
            return text
        
        items = [("path", "field", text)]
        result = self.translate_batch(items, context)
        return result.get("path", text)
