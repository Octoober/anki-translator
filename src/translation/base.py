from abc import ABC, abstractmethod


class BaseTranslator(ABC):
    def __init__(self, source_lang: str, target_lang: str):
        self.source_lang = source_lang
        self.target_lang = target_lang

    @abstractmethod
    def translate(self, text: str) -> str:
        pass
