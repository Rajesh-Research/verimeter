import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Sets up the central logger for verimeter.
    """
    logger = logging.getLogger("verimeter")
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    logger.propagate = False
    return logger
