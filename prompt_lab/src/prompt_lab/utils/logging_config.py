import logging


class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Set up the logger configuration."""
        self.logger = logging.getLogger("PromptLab")
        if not self.logger.hasHandlers():  # Prevent duplicate handlers
            self.logger.setLevel(logging.INFO)

            # Create a console handler
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)

            # Create a formatter and set it for the handler
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def get_logger(self):
        """Provide access to the singleton logger."""
        return self.logger

    def update_log_level(self, log_level: str) -> None:
        """Update the logger level based on the input."""
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)
        self.logger.info(f"Logger level set to {log_level.upper()}")


# Singleton instance of the logger
Logger_instance = Logger()
logger = Logger_instance.get_logger()
