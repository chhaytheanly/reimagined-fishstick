import logging
from .color import Color

class LoggingConfig:
    @staticmethod
    def logger_config(name: str = "data_engineering") -> logging.Logger:
        """Configure and return a module-level logger.

        Uses a single stream handler to avoid duplicate logs when imported multiple times.
        """
        logger = logging.getLogger(name)
        if logger.handlers:
            return logger       
        
        logging.addLevelName(logging.DEBUG, f"{Color.OKBLUE}DEBUG{Color.ENDC}")
        logging.addLevelName(logging.INFO, f"{Color.OKGREEN}INFO{Color.ENDC}")
        logging.addLevelName(logging.WARNING, f"{Color.WARNING}WARNING{Color.ENDC}")
        logging.addLevelName(logging.ERROR, f"{Color.FAIL}ERROR{Color.ENDC}")
        
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        return logger

logger = LoggingConfig.logger_config()