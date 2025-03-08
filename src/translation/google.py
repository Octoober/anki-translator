import logging
from deep_translator import GoogleTranslator
from .base import BaseTranslator


logger = logging.getLogger(__name__)


class GoogleTranslatorService(BaseTranslator):
    def translate(self, text: str) -> str:
        try:
            return GoogleTranslator(
                source=self.source_lang, target=self.target_lang
            ).translate(text)
        except Exception as e:
            logger.error(f"Google Translate API error: {str(e)}")
            raise
