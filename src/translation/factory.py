from .base import BaseTranslator
from .google import GoogleTranslatorService


def create_translator(config: dict) -> BaseTranslator:
    service_config = config["translation_service"]
    service_type = service_config.get("service", "google")

    common_params = {
        "source_lang": config["source_lang"],
        "target_lang": config["target_lang"],
    }

    if service_type == "google":
        return GoogleTranslatorService(**common_params)

    # if service_type == "openai":
    #     return OpenAITranslatorService(
    #         api_key=service_config["api_key"],
    #         model=service_config.get("model", "gpt-4"),
    #         **common_params
    #     )

    raise ValueError(f"Unknown translation service: {service_type}")
