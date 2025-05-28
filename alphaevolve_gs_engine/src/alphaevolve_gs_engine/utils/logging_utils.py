"""
logging_utils.py

This module provides logging utilities for the AlphaEvolve Governance System.
It sets up a standardized logger to be used across the application.

Functions:
    setup_logger: Configures and returns a logger instance.
"""

import logging
import sys

DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logger(logger_name: str, 
                 level: int = DEFAULT_LOG_LEVEL, 
                 log_file: str = None,
                 stdout: bool = True) -> logging.Logger:
    """
    Configures and returns a logger instance.

    Args:
        logger_name (str): The name for the logger.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file (str, optional): Path to a file to save logs. Defaults to None.
        stdout (bool): Whether to output logs to stdout. Defaults to True.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Clear existing handlers to avoid duplicate logging
    if logger.hasHandlers():
        logger.handlers.clear()

    # Handler for logging to a file
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a') # Append mode
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Handler for logging to standard output
    if stdout:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    
    # If no handlers are configured (e.g. log_file=None and stdout=False),
    # add a default NullHandler to prevent "No handlers could be found" warnings.
    if not log_file and not stdout:
        logger.addHandler(logging.NullHandler())

    logger.propagate = False # Prevent log propagation to root logger if handlers are set

    return logger

# Example Usage (Illustrative)
if __name__ == '__main__':
    # Setup a general application logger
    app_logger = setup_logger('AlphaEvolveApp', level=logging.DEBUG, log_file='app.log')
    app_logger.debug("This is a debug message for the application.")
    app_logger.info("Application started successfully.")
    app_logger.warning("A minor issue occurred.")
    
    # Setup a specific module logger
    module_logger = setup_logger('AlphaEvolveApp.ModuleX', level=logging.INFO)
    module_logger.info("ModuleX is processing data.")
    try:
        x = 1 / 0
    except ZeroDivisionError:
        module_logger.error("Critical error in ModuleX: Division by zero.", exc_info=True)

    print("Check 'app.log' for file-based logs (if log_file was specified).")
    print("Console output should also show formatted logs.")

    # Example of a logger that only logs to file
    file_only_logger = setup_logger('FileOnlyLogger', log_file='file_only.log', stdout=False)
    file_only_logger.info("This message goes only to file_only.log")
    print("Check 'file_only.log'. This message should not appear on console from file_only_logger.")

    # Example of a logger that only logs to stdout (useful for CLI tools)
    stdout_only_logger = setup_logger('StdoutOnlyLogger', log_file=None, stdout=True)
    stdout_only_logger.info("This message goes only to stdout from stdout_only_logger.")
