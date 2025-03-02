import os
import time
import json
import requests
import logging
import bisect
from typing import List, Optional
from deep_translator import GoogleTranslator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("translation.log"), logging.StreamHandler()],
)

PROGRESS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "translation_progress.json"
)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
CONFIG = None


def load_config() -> dict:
    """Загружает конфиг из JSON файла"""
    global CONFIG

    try:
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(f"Config file {CONFIG_PATH} not found")

        with open(CONFIG_PATH, "r") as f:
            CONFIG = json.load(f)

        required_fields = [
            "anki_connect_url",
            "deck_name",
            "target_fields",
            "source_lang",
            "target_lang",
            "request_delay",
            "max_retries",
        ]
        for field in required_fields:
            if field not in CONFIG:
                raise ValueError(f"Missing required field in config: {field}")

        logging.info("Configuration successfully loaded")
        return CONFIG
    except Exception as e:
        logging.critical(f"Configuration loading failed: {str(e)}")
        exit(1)


load_config()


def invoke_anki(action: str, **params) -> Optional[dict]:
    """Отправляет запрос к Anki Connect API"""
    try:
        payload = {
            "action": action,
            "params": params,
            "version": 6,  # Версия Anki Connect. Я не уверен, нужно ли ее прописывать, но пусть будет.
        }
        response = requests.post(CONFIG["anki_connect_url"], json=payload, timeout=10)

        response.raise_for_status()

        json_data = response.json()

        if json_data.get("error"):
            raise Exception(f"Anki Error: {json_data['error']}")

        return json_data.get("result")
    except Exception as e:
        raise


def get_all_note_ids() -> List[int]:
    """Возвращает отсортированный список всех ID карточек в колоде"""
    fields_query = " OR ".join([f"{field}:*" for field in CONFIG["target_fields"]])
    query = f'deck:"{CONFIG['deck_name']}", ({fields_query})'
    notes_ids = invoke_anki("findNotes", query=query)

    return sorted(map(int, notes_ids))


def load_progress() -> Optional[int]:
    """Загружает последний обработанный ID из файла"""
    if not os.path.exists(PROGRESS_PATH):
        return None

    try:
        with open(PROGRESS_PATH, "r") as f:
            return json.load(f).get("last_id")
    except Exception as e:
        logging.error(f"Failed to load progress: {str(e)}")
        return None


def save_progress(note_id: int) -> None:
    """Сохраняет текущий прогресс в файл"""
    try:
        with open(PROGRESS_PATH, "w") as f:
            json.dump({"last_id": note_id}, f)
    except Exception as e:
        logging.error(f"Failed to save progress: {str(e)}")


def translate_text(text: str) -> str:
    """Перевод текста"""
    # В случае ошибки повторяет попытку перевода
    for attempt in range(CONFIG["max_retries"]):
        try:
            return GoogleTranslator(
                source=CONFIG["source_lang"], target=CONFIG["target_lang"]
            ).translate(text)
        except Exception as e:
            # Если привышен лимит попыток перевода - оставляет текст в оригинальном виде.
            if attempt == CONFIG["max_retries"] - 1:
                print(f"Translation failed: {str(e)}. Keeping original text.")
                return text
            time.sleep(2**attempt)
    return text


def process_note(note_id: int) -> bool:
    """Обрабатывает одну карточку"""
    try:
        note_info = invoke_anki("notesInfo", notes=[note_id])[0]
        fields = note_info["fields"]
        # original = note_info["fields"].get(CONFIG["target_field"], {}).get("value", "")
        updates = {}

        for field in CONFIG["target_fields"]:
            original = fields.get(field, {}).get("value", "")
            if original.strip():
                translated = translate_text(original)
                updates[field] = translated
        if updates:
            invoke_anki("updateNoteFields", note={"id": note_id, "fields": updates})
        # if not original.strip():
        #     logging.debug(f"Skipping empty field in note {note_id}")
        #     return True

        # translated = translate_text(original)
        # query = {"id": note_id, "fields": {CONFIG["target_field"]: translated}}
        # invoke_anki("updateNoteFields", note=query)

        return True
    except Exception as e:
        logging.error(f"Failed progress note {note_id}: {str(e)}")
        return False


def main():
    try:
        all_note_ids = get_all_note_ids()
        if not all_note_ids:
            logging.warning("No cards found!")
            return

        # Стартовая позиция
        last_id = load_progress()
        start_idx = 0

        if last_id is not None:
            start_idx = bisect.bisect_right(all_note_ids, last_id)
            if start_idx < len(all_note_ids) and all_note_ids[start_idx] == last_id:
                start_idx += 1
            logging.info(f"Resuming from position {start_idx + 1}/{len(all_note_ids)}")

        for idx, note_id in enumerate(all_note_ids[start_idx:], start=start_idx + 1):
            success = process_note(note_id)

            if success:
                save_progress(note_id)
                time.sleep(CONFIG["request_delay"])

            logging.info(f"Progress: {idx}/{len(all_note_ids)}")

    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}")
    finally:
        logging.info("Completed")


if __name__ == "__main__":
    main()
