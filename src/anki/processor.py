import time
import bisect
import logging
from typing import List
from ..utils.progress import ProgressManager
from ..translation.base import BaseTranslator
from ..anki.client import AnkiClient

logger = logging.getLogger(__name__)


def process_notes(config: dict, translator: BaseTranslator):
    progress_manager = ProgressManager()
    completed = False

    try:
        anki_client = AnkiClient(config["anki_connect_url"])
        note_ids = _get_note_ids(anki_client, config)

        if not note_ids:
            logger.warning("No cards found for processing!")
            return

        start_idx = _calculate_start_index(note_ids, progress_manager)

        for idx, note_id in enumerate(note_ids[start_idx:], start=start_idx + 1):
            _process_single_note(anki_client, note_id, config, translator)
            progress_manager.update(note_id)
            logger.info(f"Progress: {idx}/{len(note_ids)}")
            time.sleep(config["request_delay"])

        completed = True
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        raise
    finally:
        if completed:
            progress_manager.cleanup()
        else:
            logger.info("Process saved for next session")


def _get_note_ids(anki_client: AnkiClient, config) -> List[int]:
    """Возвращает отсортированный список всех ID карточек в колоде"""
    fields_query = " OR ".join([f"{field}:*" for field in config["target_fields"]])
    query = f'deck:"{config['deck_name']}", ({fields_query})'

    try:
        note_ids = anki_client.invoke("findNotes", query=query)
        return sorted(map(int, note_ids))
    except Exception as e:
        logger.error(f"Failed to get note IDs: {str(e)}")
        raise


def _calculate_start_index(note_ids: List[int], progress_manager) -> str:
    last_id = progress_manager.load()

    if last_id is None:
        return 0

    start_idx = bisect.bisect_right(note_ids, last_id)

    if start_idx < len(note_ids) and note_ids[start_idx] == last_id:
        start_idx += 1
    logger.info(f"Resuming from position {start_idx}/{len(note_ids)}")

    return start_idx


def _process_single_note(anki_client: AnkiClient, note_id: int, config: dict, handler):
    logger.debug(f"Processing note {note_id}")

    try:
        note_info = anki_client.invoke("notesInfo", notes=[note_id])[0]
        fields = note_info["fields"]

        updates = {}

        texts_to_translate = []
        field_order = []

        for field in config["target_fields"]:
            original = fields.get(field, {}).get("value", "")
            if original.strip():
                texts_to_translate.append(original)
                field_order.append(field)
        if not texts_to_translate:
            return

        # пакетный перевод
        translated_texts = handler.translate(texts_to_translate)

        for field, translated in zip(field_order, translated_texts):
            updates[field] = translated

        if updates:
            anki_client.invoke(
                "updateNoteFields", note={"id": note_id, "fields": updates}
            )
            logger.debug(f"Updated note {note_id}")
    except Exception as e:
        logger.error(f"Failed to process note {note_id}: {str(e)}")
        raise
