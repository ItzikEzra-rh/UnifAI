import logging

class Logger:
    _instance = None

    def __new__(cls, logger_name="custom_logger"):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger(logger_name)
        return cls._instance

    def _initialize_logger(self, logger_name):
        """Set up the logger configuration."""
        self.logger = logging.getLogger(logger_name)
        if not self.logger.handlers:  # Ensure handlers are not duplicated
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

            # Suppress propagation to the root logger to avoid duplication
            self.logger.propagate = False

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
