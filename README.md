# Limbus Company Thai Localization (AI-Assisted)

---

## ข้อสงวนสิทธิ์ (Disclaimer)

คำเตือนการแปลเหล่านี้ใช้ AI + ผมเช็คผ่านๆ ในการ automate การแปลทั้งหมด ดังนั้นหากไม่อยากสนับสนุนการแปล AI สามารถสนับสนุนคนไทยแปลได้ที่ https://github.com/stlinx/LocalizeLimbusTH.git

---

## เกี่ยวกับโปรเจ็คนี้

โปรเจ็คนี้ทำเพื่อความสนุกและความสงสัยของผมเท่านั้น

Localization อันนี้ผมทำการสร้างขึ้นเพื่อใช้สำหรับเล่นเนื้อเรื่อง Limbus Company เอง สามารถนำไปใช้ได้หากคุณอยากใช้

**หมายเหตุ** การแปลนี้จะถูกผมแก้ไขทีละนิดด้วยตัวเอง เพราะผมจะเริ่มเล่นตั้งแต่ต้นเนื้อเรื่องใหม่ การแปลเลยจะเป็นการรวมระหว่าง AI + ตัวผมเอง ขอบคุณครับ

---

## ข้อมูลเทคนิค

- **Translation model** : google/gemma-4-31b-it
- **Vibe code** : Opencode-Kimi-K2.6
- **Manual check** : Temicide

---

## Project Structure

```
LocalizeLimbusCompanyTH-myself/
├── EN/                        # Source English localization files
├── TH/                        # Thai translated output files
│   └── StoryData/
├── Fonts/                     # Game fonts for Thai display
├── data/                      # Supporting data
│   ├── characters/
│   │   ├── raw/               # Raw wiki character data
│   │   └── clean/             # Cleaned character data
│   └── reference/             # Reference materials & guides
├── scripts/                   # Utility scripts
│   ├── translate.py           # Main translation entry point
│   ├── fetch_characters.py    # Fetch character data from wiki
│   ├── clean_characters.py    # Clean/process character data
│   └── retry_failed.py        # Retry failed wiki fetches
├── translator/                 # Python translation package
│   ├── __init__.py
│   ├── config.py              # Local config (gitignored, has API keys)
│   ├── config_sample.py       # Config template
│   ├── engine.py              # Translation engine
│   ├── ollama_client.py       # API client (OpenRouter/Ollama)
│   ├── file_processor.py       # JSON processing
│   ├── context_builder.py     # Character context builder
│   ├── dictionaries.py         # Thai dictionaries & post-processing
│   └── logger.py              # Logging
├── requirements.txt            # Python dependencies
├── character_profiles.json     # Auto-generated character profiles
├── translation_state.json      # Translation progress state
└── LICENSE
```

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `translator/config_sample.py` to `translator/config.py` and fill in your API key.

3. Run translation:
   ```bash
   python scripts/translate.py                    # Translate all files
   python scripts/translate.py --test <filename>  # Test single file
   python scripts/translate.py --analyze-only     # Analyze characters only
   ```

---

<p align="center">
  <img src=".github/ISSUE_TEMPLATE/readme/angela.png" alt="angela" width="600"/>
</p>