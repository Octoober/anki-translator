import logging
import time
from typing import List
from .base import BaseTranslator


logger = logging.getLogger(__name__)


class TranslationHandler:
    def __init__(self, translator: BaseTranslator, config: dict):
        self.translator = translator
        self.max_retries = config["max_retries"]
        self.request_delay = config["request_delay"]
        self.separator = "|||"

    def translate(self, texts: List[str]) -> List[str]:
        combined_text = self.separator.join(texts)

        for attempt in range(self.max_retries):
            try:
                translated_combined_text = self.translator.translate(combined_text)
                translated_texts = translated_combined_text.split(self.separator)

                if len(translated_texts) != len(texts):
                    raise ValueError(
                        "Number of translated texts does not match the original"
                    )

                return translated_texts
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(
                        f"Translation failed after {self.max_retries} attempts: {str(e)}"
                    )
                    return texts
                wait_time = 2**attempt
                logger.warning(f"Retry #{attempt + 1}. Waiting for {wait_time} seconds")
                time.sleep(wait_time)
        return texts
