import logging

logger = logging.getLogger(__name__)

class Estimate:
    def __init__(self, db_m_instance):
        self.db_manager = db_m_instance
        logger.info("Estimate module initialized with provided db_manager.")
