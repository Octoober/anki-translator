import os
import json
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class ProgressManager:
    def __init__(self):
        self.PROGRESS_PATH = os.path.join(
            os.path.dirname(__file__), "..", "..", "translation_progress.json"
        )

    def load(self) -> Optional[int]:
        if not os.path.exists(self.PROGRESS_PATH):
            return None

        try:
            with open(self.PROGRESS_PATH, "r") as f:
                data = json.load(f)
                logger.info(f"Loaded progress: {data.get('last_id')}")
                return data.get("last_id")
        except Exception as e:
            logger.error(f"Progress loading failed: {str(e)}")
            return None

    def update(self, note_id: int):
        try:
            with open(self.PROGRESS_PATH, "w") as f:
                json.dump({"last_id": note_id}, f)
            logger.debug(f"Progress saved for note {note_id}")
        except Exception as e:
            logger.error(f"Failed to save progress: {str(e)}")

    def cleanup(self):
        if os.path.exists(self.PROGRESS_PATH):
            try:
                os.remove(self.PROGRESS_PATH)
                logger.info("Progress file cleaned up")
            except Exception as e:
                logger.error(f"Progress cleanup failed: {str(e)}")
