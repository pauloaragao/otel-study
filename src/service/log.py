import logging


class LogConsole:
    def __init__(self, name: str = "LogConsole"):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)
