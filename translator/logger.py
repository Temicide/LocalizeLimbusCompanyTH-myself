"""Logger module for translation activities."""
import logging
import sys
from datetime import datetime
from pathlib import Path

from .config import LOGS_DIR


def setup_logger(name: str = "translator") -> logging.Logger:
    """Setup and return a logger with both file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler - detailed logs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = LOGS_DIR / f"translation_{timestamp}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler - info and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Error handler - separate error log
    error_file = LOGS_DIR / f"errors_{timestamp}.log"
    error_handler = logging.FileHandler(error_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    logger.info(f"Logging started. Log file: {log_file}")
    
    return logger


class TranslationLogger:
    """Detailed logger for translation decisions."""
    
    def __init__(self):
        self.logger = setup_logger("translator")
        self.translation_log = []
    
    def log_translation(self, source_file: str, field: str, original: str, 
                       translated: str, context: dict = None):
        """Log a single translation decision."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "file": source_file,
            "field": field,
            "original": original,
            "translated": translated,
            "context": context or {}
        }
        self.translation_log.append(entry)
        
        self.logger.debug(f"Translated [{field}] in {source_file}")
        self.logger.debug(f"  Original: {original[:100]}..." if len(original) > 100 else f"  Original: {original}")
        self.logger.debug(f"  Result: {translated[:100]}..." if len(translated) > 100 else f"  Result: {translated}")
    
    def log_file_start(self, filename: str):
        """Log start of file processing."""
        self.logger.info(f"Starting translation: {filename}")
    
    def log_file_complete(self, filename: str, success: bool = True):
        """Log completion of file processing."""
        status = "completed" if success else "failed"
        self.logger.info(f"Translation {status}: {filename}")
    
    def log_batch_start(self, batch_num: int, files: list):
        """Log start of batch processing."""
        self.logger.info(f"Starting batch {batch_num} with {len(files)} files")
    
    def log_batch_complete(self, batch_num: int, success_count: int, fail_count: int):
        """Log completion of batch processing."""
        self.logger.info(f"Batch {batch_num} complete: {success_count} success, {fail_count} failed")
    
    def log_error(self, message: str, exception: Exception = None):
        """Log an error."""
        if exception:
            self.logger.error(f"{message}: {str(exception)}", exc_info=True)
        else:
            self.logger.error(message)
    
    def log_warning(self, message: str):
        """Log a warning."""
        self.logger.warning(message)
    
    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def save_translation_log(self):
        """Save detailed translation log to JSON."""
        import json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = LOGS_DIR / f"translations_{timestamp}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.translation_log, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Translation log saved: {log_file}")
