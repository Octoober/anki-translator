import logging
from src.translation.factory import create_translator
from src.translation.handler import TranslationHandler
from src.anki.processor import process_notes
from src.config import load_config
from src.utils.logger import setup_logger


def main():
    setup_logger()
    logger = logging.getLogger(__name__)

    try:
        config = load_config()
        logger.info("Start translation process")

        translator = create_translator(config)
        handler = TranslationHandler(translator, config)

        process_notes(config, handler)

        logger.info("Completed!")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
