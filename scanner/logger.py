import logging
class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colored boxes based on log level/content."""
    GREEN_SQUARE = "\033[92m[🟩]\033[0m"
    RED_SQUARE = "\033[91m[🟥]\033[0m"
    INFO_BLUE = "\033[94m[ℹ️]\033[0m"
    RESET = "\033[0m"
    def format(self, record):
        message = record.getMessage()
        if "[ALIVE]" in message:
            record.msg = f"{self.GREEN_SQUARE} {message.replace('[ALIVE] ', '')}"
        elif "[DEAD]" in message:
            record.msg = f"{self.RED_SQUARE} {message.replace('[DEAD] ', '')}"
        elif "Open port" in message:
            record.msg = f"\033[92m{message}\033[0m" 
        return super().format(record)
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    handler = logging.StreamHandler()
    formatter = ColoredFormatter("%(asctime)s %(message)s", datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
