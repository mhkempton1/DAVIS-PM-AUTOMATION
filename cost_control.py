import logging

logger = logging.getLogger(__name__)

class CostControl:
    def __init__(self, db_m_instance):
        self.db_manager = db_m_instance
        logger.info("Cost Control module initialized with provided db_manager.")
