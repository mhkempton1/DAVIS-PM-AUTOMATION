import logging

logger = logging.getLogger(__name__)

class Crm:
    def __init__(self, db_m_instance):
        self.db_manager = db_m_instance
        logger.info("CRM module initialized with provided db_manager.")
