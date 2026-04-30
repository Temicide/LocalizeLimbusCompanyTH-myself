"""Main translation engine with batch processing."""
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import (
    EN_DIR, TH_DIR, BATCH_SIZE, DELAY_BETWEEN_BATCHES,
    load_state, save_state, PRESERVED_TERMS, OPENROUTER_API_KEYS
)
from .logger import TranslationLogger
from .ollama_client import OllamaClient
from .context_builder import ContextBuilder
from .file_processor import FileProcessor
from .dictionaries import (
    get_thai_teller, fix_title_word_order, translate_place_name,
    post_process_translation, fix_character_names_in_content, get_character_voice_guide,
    KOREAN_TO_THAI_TELLER, ENGLISH_TO_THAI_TELLER
)


class TranslationEngine:
    """Main engine for translating Limbus Company localization files."""
    
    def __init__(self):
        self.logger = TranslationLogger()
        # Create one client per API key for parallel processing
        num_keys = len(OPENROUTER_API_KEYS) if OPENROUTER_API_KEYS else 1
        self.clients = [OllamaClient(self.logger, key) for key in (OPENROUTER_API_KEYS or [None])]
        self.logger.log_info(f"Created {len(self.clients)} API clients for parallel processing")
        self.context_builder = ContextBuilder(self.logger)
        self.file_processor = FileProcessor(self.logger)
        self.state = load_state()
        
    def initialize(self) -> bool:
        """Initialize the translation engine."""
        self.logger.log_info("=" * 60)
        self.logger.log_info("Limbus Company Thai Localization Translator v2")
        self.logger.log_info("=" * 60)
        
        if not self.clients[0].check_connection():
            self.logger.log_error("Cannot connect to translation API. Please ensure it's available.")
            return False
        
        self.context_builder.build_all_context()
        TH_DIR.mkdir(exist_ok=True)
        
        self.logger.log_info("Initialization complete")
        return True
    
    def get_files_to_process(self) -> List[Path]:
        """Get list of JSON files that need to be processed."""
        # Only process EN/StoryData/ files for now
        story_dir = EN_DIR / "StoryData"
        all_files = list(story_dir.glob("*.json"))
        
        completed = set(self.state.get("completed_files", []))
        pending = [f for f in all_files if f.name not in completed]
        
        pending.sort()
        
        self.logger.log_info(f"Found {len(all_files)} StoryData files, {len(pending)} pending")
        return pending
    
    def detect_file_type(self, filepath: Path) -> str:
        """Detect the type of file for appropriate translation strategy."""
        name = filepath.name.lower()
        
        if "storydata" in str(filepath).lower():
            return "story"
        elif "abd dlg_" in name:
            return "dialogue"
        elif "skills_" in name or "passives_" in name:
            return "skills"
        elif "battlekeywords" in name or "bufs" in name or "abnormalityguides" in name:
            return "keywords"
        elif "abevents" in name or "actionevents" in name:
            return "story"
        elif "uitext" in name or "mainui" in name or "tutorial" in name:
            return "ui"
        else:
            return "general"
    
    def translate_file(self, filepath: Path, client: OllamaClient = None) -> bool:
        """Translate a single file using batch translation with static dictionaries."""
        relative_path = filepath.relative_to(EN_DIR)
        output_path = TH_DIR / relative_path
        
        # Use provided client or fall back to first client
        ollama = client or self.clients[0]
        
        self.logger.log_file_start(filepath.name)
        
        try:
            # Load source file
            data = self.file_processor.load_json(filepath)
            
            # Detect file type
            file_type = self.detect_file_type(filepath)
            
            # Get teller for character context
            teller = self.file_processor.get_teller_from_data(data)
            
            # === STATIC DICTIONARY MAPPINGS (pre-translation) ===
            
            # 1. Map teller fields using static dictionary
            data = self._apply_teller_mapping(data)
            
            # 2. Translate place fields using static patterns
            data = self._apply_place_translation(data)
            
            # 3. Pre-process title fields to fix word order before AI sees them
            data = self._apply_title_preprocessing(data)
            
            # Build context with character voice guide
            context = self.context_builder.get_context_for_file(filepath.name, teller)
            character_notes = self.context_builder.get_character_notes(teller)
            if character_notes:
                context += f"\n\nTRANSLATION NOTES: {character_notes}"
            
            # Add character voice guide
            voice_guide = get_character_voice_guide(teller)
            if voice_guide:
                context += f"\n\nบุคลิกตัวละคร:\n{voice_guide}"
            
            # Extract translatable texts
            texts_to_translate = self.file_processor.extract_translatable_texts(data)
            
            if not texts_to_translate:
                self.logger.log_info(f"No translatable text in {filepath.name}, copying as-is")
                self.file_processor.save_json(data, output_path)
                return True
            
            # === DEDUPLICATION: Group identical texts to save API tokens ===
            # Map unique text -> list of (path, field) that share it
            unique_texts_map: Dict[str, List[Tuple[str, str]]] = {}
            # Keep original order for path->token_map
            path_to_token_map: Dict[str, Dict[str, str]] = {}
            
            dedup_skipped = 0
            for path, field, original_text in texts_to_translate:
                # Skip if already handled by static dictionary (teller/place)
                if field == "teller" and original_text in ENGLISH_TO_THAI_TELLER:
                    dedup_skipped += 1
                    continue
                
                protected_text, token_map = self.file_processor.protect_special_tokens(original_text)
                path_to_token_map[path] = token_map
                
                if protected_text not in unique_texts_map:
                    unique_texts_map[protected_text] = []
                unique_texts_map[protected_text].append((path, field))
            
            # Build deduplicated items for API: each unique text once
            deduped_items = []
            for protected_text, path_field_list in unique_texts_map.items():
                # Use the first path as the representative for this unique text
                rep_path, rep_field = path_field_list[0]
                deduped_items.append((rep_path, rep_field, protected_text))
            
            total_raw = len(texts_to_translate) - dedup_skipped
            deduped_count = len(deduped_items)
            saved = total_raw - deduped_count
            if saved > 0:
                self.logger.log_info(f"  Deduplicated: {total_raw} -> {deduped_count} unique texts (saved {saved} API items)")
            
            # Translate in batches (using deduplicated items)
            all_translations: Dict[str, str] = {}
            batch_size = 15
            
            for i in range(0, len(deduped_items), batch_size):
                batch = deduped_items[i:i+batch_size]
                
                self.logger.log_info(f"  Translating batch {i//batch_size + 1}/{(len(deduped_items)-1)//batch_size + 1} "
                                   f"({len(batch)} items)")
                
                # Translate batch using the assigned client
                batch_translations = ollama.translate_batch(batch, context, file_type)
                
                if batch_translations:
                    all_translations.update(batch_translations)
                else:
                    self.logger.log_warning(f"  Batch translation failed, using originals")
                    for path, field, text in batch:
                        all_translations[path] = text
                
                # Small delay between batches
                if i + batch_size < len(deduped_items):
                    time.sleep(2)
            
            # === Expand deduplicated translations back to all paths ===
            final_translations: Dict[str, str] = {}
            for protected_text, path_field_list in unique_texts_map.items():
                rep_path = path_field_list[0][0]
                if rep_path in all_translations:
                    translated = all_translations[rep_path]
                    # Apply to ALL paths that had this same text
                    for path, field in path_field_list:
                        # Restore tokens for this path
                        if path in path_to_token_map:
                            translated_restored = self.file_processor.restore_special_tokens(translated, path_to_token_map[path])
                        else:
                            translated_restored = translated
                        final_translations[path] = translated_restored
                else:
                    # Fallback: use original protected text for all paths
                    for path, field in path_field_list:
                        final_translations[path] = protected_text
            
            # Apply post-processing per-path to expanded translations
            for path, field, original_text in texts_to_translate:
                if field == "teller" and original_text in ENGLISH_TO_THAI_TELLER:
                    continue  # Already handled by static dictionary
                
                if path in final_translations:
                    translated = final_translations[path]
                    
                    # === POST-TRANSLATION FIXES ===
                    # Fix title word order
                    if field == "title":
                        translated = fix_title_word_order(translated)
                    
                    # Fix character names in content and titles
                    if field in ("content", "dlg", "dialog", "title"):
                        translated = fix_character_names_in_content(translated)
                    
                    # General post-processing
                    translated = post_process_translation(translated)
                    
                    final_translations[path] = translated
                    
                    self.logger.log_translation(
                        filepath.name,
                        field,
                        original_text,
                        translated
                    )
                else:
                    final_translations[path] = original_text
            
            # Update JSON with translations
            translated_data = self.file_processor.update_json_with_translations(data, final_translations)
            
            # Validate structure
            if not self.file_processor.validate_json_structure(data, translated_data):
                self.logger.log_error(f"Structure validation failed for {filepath.name}")
                return False
            
            # Save translated file
            self.file_processor.save_json(translated_data, output_path)
            
            self.logger.log_file_complete(filepath.name, success=True)
            return True
            
        except Exception as e:
            self.logger.log_error(f"Error processing {filepath.name}", e)
            return False
    
    def _apply_teller_mapping(self, data):
        """Apply static teller name mappings to JSON data."""
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                if key == "teller" and isinstance(value, str):
                    # Map teller name
                    new_data[key] = get_thai_teller("", value)
                elif key == "dataList" and isinstance(value, list):
                    new_data[key] = [self._apply_teller_mapping(item) for item in value]
                elif isinstance(value, (dict, list)):
                    new_data[key] = self._apply_teller_mapping(value)
                else:
                    new_data[key] = value
            return new_data
        elif isinstance(data, list):
            return [self._apply_teller_mapping(item) for item in data]
        return data
    
    def _apply_place_translation(self, data):
        """Apply static place name translations to JSON data."""
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                if key == "place" and isinstance(value, str):
                    new_data[key] = translate_place_name(value)
                elif key == "dataList" and isinstance(value, list):
                    new_data[key] = [self._apply_place_translation(item) for item in value]
                elif isinstance(value, (dict, list)):
                    new_data[key] = self._apply_place_translation(value)
                else:
                    new_data[key] = value
            return new_data
        elif isinstance(data, list):
            return [self._apply_place_translation(item) for item in data]
        return data
    
    def _apply_title_preprocessing(self, data):
        """Pre-process title fields to fix English word order before AI translation."""
        import re
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                if key == "title" and isinstance(value, str):
                    # Fix "Grade/Class/Level N Fixer" -> "Fixer grade N" 
                    # so AI sees correct word order and translates grade->ระดับ
                    value = re.sub(r'Grade\s+(\d+)\s+Fixer', r'Fixer grade \1', value, flags=re.IGNORECASE)
                    value = re.sub(r'Class\s+(\d+)\s+Fixer', r'Fixer class \1', value, flags=re.IGNORECASE)
                    value = re.sub(r'Level\s+(\d+)\s+Fixer', r'Fixer level \1', value, flags=re.IGNORECASE)
                    new_data[key] = value
                elif key == "dataList" and isinstance(value, list):
                    new_data[key] = [self._apply_title_preprocessing(item) for item in value]
                elif isinstance(value, (dict, list)):
                    new_data[key] = self._apply_title_preprocessing(value)
                else:
                    new_data[key] = value
            return new_data
        elif isinstance(data, list):
            return [self._apply_title_preprocessing(item) for item in data]
        return data
    
    def process_batch(self, files: List[Path], batch_num: int) -> tuple:
        """Process a batch of files in parallel using multiple API keys."""
        self.logger.log_batch_start(batch_num, files)
        
        success_count = 0
        fail_count = 0
        
        # Process files in parallel using ThreadPoolExecutor
        # Each file gets assigned to a different API client
        max_workers = min(len(self.clients), len(files))
        
        if max_workers > 1:
            self.logger.log_info(f"Processing {len(files)} files in parallel with {max_workers} API keys")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit tasks with round-robin client assignment
                future_to_file = {}
                for idx, filepath in enumerate(files):
                    client = self.clients[idx % len(self.clients)]
                    future = executor.submit(self.translate_file, filepath, client)
                    future_to_file[future] = filepath
                
                # Collect results as they complete
                for future in as_completed(future_to_file):
                    filepath = future_to_file[future]
                    try:
                        result = future.result()
                        if result:
                            success_count += 1
                            self.state["completed_files"].append(filepath.name)
                        else:
                            fail_count += 1
                    except Exception as e:
                        self.logger.log_error(f"Error in parallel processing {filepath.name}", e)
                        fail_count += 1
            
            save_state(self.state)
        else:
            # Sequential fallback
            for filepath in files:
                if self.translate_file(filepath):
                    success_count += 1
                    self.state["completed_files"].append(filepath.name)
                    save_state(self.state)
                else:
                    fail_count += 1
        
        self.logger.log_batch_complete(batch_num, success_count, fail_count)
        
        if success_count > 0:
            time.sleep(DELAY_BETWEEN_BATCHES)
        
        return success_count, fail_count
    
    def run(self):
        """Run the translation process."""
        if not self.initialize():
            return False
        
        files = self.get_files_to_process()
        
        if not files:
            self.logger.log_info("No files to translate. All done!")
            return True
        
        total_files = len(files)
        total_success = 0
        total_fail = 0
        
        self.logger.log_info(f"Starting translation of {total_files} files")
        
        batch_num = self.state.get("current_batch", 0)
        for i in range(0, len(files), BATCH_SIZE):
            batch = files[i:i + BATCH_SIZE]
            batch_num += 1
            
            self.logger.log_info(f"\n{'='*40}")
            self.logger.log_info(f"Progress: {i+1}/{total_files} files")
            self.logger.log_info(f"{'='*40}\n")
            
            success, fail = self.process_batch(batch, batch_num)
            total_success += success
            total_fail += fail
            
            self.state["current_batch"] = batch_num
            save_state(self.state)
        
        # Final summary
        self.logger.log_info(f"\n{'='*60}")
        self.logger.log_info("TRANSLATION COMPLETE")
        self.logger.log_info(f"{'='*60}")
        self.logger.log_info(f"Total files: {total_files}")
        self.logger.log_info(f"Successful: {total_success}")
        self.logger.log_info(f"Failed: {total_fail}")
        self.logger.log_info(f"Output directory: {TH_DIR}")
        
        self.logger.save_translation_log()
        
        return total_fail == 0
    
    def translate_single_file(self, filename: str) -> bool:
        """Translate a single file by name (for testing)."""
        if not self.initialize():
            return False
        
        filepath = EN_DIR / filename
        if not filepath.exists():
            self.logger.log_error(f"File not found: {filepath}")
            return False
        
        return self.translate_file(filepath)
