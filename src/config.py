import os
import json
import logging

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def load_config() -> dict:
    """Загружает конфиг из JSON файла"""
    global CONFIG

    try:
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(f"Config file {CONFIG_PATH} not found")

        with open(CONFIG_PATH, "r") as f:
            CONFIG = json.load(f)

        # logging.info("Configuration successfully loaded")
        return CONFIG
    except Exception as e:
        # logging.critical(f"Configuration loading failed: {str(e)}")
        exit(1)


def _validate_config(config: dict):
    required_fields = [
        "anki_connect_url",
        "deck_name",
        "target_fields",
        "source_lang",
        "target_lang",
        "request_delay",
        "max_retries",
        "translation_service",
    ]

    for field in required_fields:
        if field not in CONFIG:
            raise ValueError(f"Missing required field in config: {field}")

    service_config = config["translation_service"]
    service_type = service_config.get("service", "google")

    if service_type != "google" and not service_config.get("api_key"):
        raise ValueError(f"API key required for {service_type} service")
