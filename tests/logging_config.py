#!/usr/bin/env python3
"""
ACGS-PGP Test Logging Configuration

Provides comprehensive logging configuration for test execution with detailed
failure reporting, performance metrics, and coverage analysis.
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Test logging directory
TEST_LOG_DIR = Path("test_logs")
TEST_LOG_DIR.mkdir(exist_ok=True)

# Generate timestamped log file names
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILES = {
    'main': TEST_LOG_DIR / f"test_execution_{timestamp}.log",
    'failures': TEST_LOG_DIR / f"test_failures_{timestamp}.log",
    'performance': TEST_LOG_DIR / f"test_performance_{timestamp}.log",
    'coverage': TEST_LOG_DIR / f"test_coverage_{timestamp}.log",
    'debug': TEST_LOG_DIR / f"test_debug_{timestamp}.log"
}

# Comprehensive logging configuration
LOGGING_CONFIG: Dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s:%(lineno)-4d | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)-8s | %(name)-20s | %(message)s'
        },
        'test_result': {
            'format': '%(asctime)s | %(test_name)-40s | %(status)-8s | %(duration)-8s | %(message)s',
            'datefmt': '%H:%M:%S'
        },
        'performance': {
            'format': '%(asctime)s | PERF | %(test_name)-40s | %(metric)-15s | %(value)-10s | %(message)s',
            'datefmt': '%H:%M:%S'
        },
        'coverage': {
            'format': '%(asctime)s | COV  | %(module)-30s | %(coverage)-8s | %(missing_lines)-20s | %(message)s',
            'datefmt': '%H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': sys.stdout
        },
        'main_file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(LOG_FILES['main']),
            'mode': 'w',
            'encoding': 'utf-8'
        },
        'failure_file': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': str(LOG_FILES['failures']),
            'mode': 'w',
            'encoding': 'utf-8'
        },
        'performance_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'performance',
            'filename': str(LOG_FILES['performance']),
            'mode': 'w',
            'encoding': 'utf-8'
        },
        'coverage_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'coverage',
            'filename': str(LOG_FILES['coverage']),
            'mode': 'w',
            'encoding': 'utf-8'
        },
        'debug_file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(LOG_FILES['debug']),
            'mode': 'w',
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'test_execution': {
            'level': 'DEBUG',
            'handlers': ['console', 'main_file'],
            'propagate': False
        },
        'test_failures': {
            'level': 'ERROR',
            'handlers': ['console', 'failure_file', 'main_file'],
            'propagate': False
        },
        'test_performance': {
            'level': 'INFO',
            'handlers': ['performance_file', 'main_file'],
            'propagate': False
        },
        'test_coverage': {
            'level': 'INFO',
            'handlers': ['coverage_file', 'main_file'],
            'propagate': False
        },
        'test_debug': {
            'level': 'DEBUG',
            'handlers': ['debug_file'],
            'propagate': False
        },
        # Service-specific loggers
        'acgs.auth': {
            'level': 'DEBUG',
            'handlers': ['main_file', 'debug_file'],
            'propagate': True
        },
        'acgs.ac': {
            'level': 'DEBUG',
            'handlers': ['main_file', 'debug_file'],
            'propagate': True
        },
        'acgs.gs': {
            'level': 'DEBUG',
            'handlers': ['main_file', 'debug_file'],
            'propagate': True
        },
        'acgs.fv': {
            'level': 'DEBUG',
            'handlers': ['main_file', 'debug_file'],
            'propagate': True
        },
        'acgs.integrity': {
            'level': 'DEBUG',
            'handlers': ['main_file', 'debug_file'],
            'propagate': True
        },
        'acgs.pgc': {
            'level': 'DEBUG',
            'handlers': ['main_file', 'debug_file'],
            'propagate': True
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'main_file']
    }
}


def setup_test_logging():
    """Setup comprehensive test logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Create specialized loggers
    execution_logger = logging.getLogger('test_execution')
    failure_logger = logging.getLogger('test_failures')
    performance_logger = logging.getLogger('test_performance')
    coverage_logger = logging.getLogger('test_coverage')
    debug_logger = logging.getLogger('test_debug')
    
    # Log setup completion
    execution_logger.info("=" * 80)
    execution_logger.info("ACGS-PGP Test Execution Started")
    execution_logger.info(f"Timestamp: {datetime.now().isoformat()}")
    execution_logger.info(f"Log Directory: {TEST_LOG_DIR.absolute()}")
    execution_logger.info("=" * 80)
    
    return {
        'execution': execution_logger,
        'failures': failure_logger,
        'performance': performance_logger,
        'coverage': coverage_logger,
        'debug': debug_logger
    }


def log_test_start(test_name: str, logger: logging.Logger = None):
    """Log test start with detailed information."""
    if logger is None:
        logger = logging.getLogger('test_execution')
    
    logger.info(f"🚀 Starting test: {test_name}")
    logger.debug(f"Test environment: {os.environ.get('TESTING', 'unknown')}")
    logger.debug(f"Python version: {sys.version}")


def log_test_result(test_name: str, status: str, duration: float, 
                   details: str = "", logger: logging.Logger = None):
    """Log test result with performance metrics."""
    if logger is None:
        logger = logging.getLogger('test_execution')
    
    status_emoji = {
        'PASSED': '✅',
        'FAILED': '❌', 
        'SKIPPED': '⏭️',
        'ERROR': '💥'
    }.get(status, '❓')
    
    logger.info(f"{status_emoji} {test_name}: {status} ({duration:.3f}s)")
    
    if details:
        logger.debug(f"Details: {details}")
    
    # Log to performance logger
    perf_logger = logging.getLogger('test_performance')
    perf_logger.info(f"", extra={
        'test_name': test_name,
        'metric': 'duration',
        'value': f"{duration:.3f}s"
    })


def log_test_failure(test_name: str, error: Exception, traceback_str: str,
                    logger: logging.Logger = None):
    """Log detailed test failure information."""
    if logger is None:
        logger = logging.getLogger('test_failures')
    
    logger.error(f"❌ FAILED: {test_name}")
    logger.error(f"Error Type: {type(error).__name__}")
    logger.error(f"Error Message: {str(error)}")
    logger.error(f"Traceback:\n{traceback_str}")
    logger.error("-" * 80)


def log_coverage_info(module: str, coverage_pct: float, missing_lines: str = "",
                     logger: logging.Logger = None):
    """Log coverage information for a module."""
    if logger is None:
        logger = logging.getLogger('test_coverage')
    
    coverage_status = "✅" if coverage_pct >= 95 else "⚠️" if coverage_pct >= 80 else "❌"
    
    logger.info(f"", extra={
        'module': module,
        'coverage': f"{coverage_pct:.1f}%",
        'missing_lines': missing_lines or "none"
    })
    
    logger.info(f"{coverage_status} {module}: {coverage_pct:.1f}% coverage")


def cleanup_old_logs(days_to_keep: int = 7):
    """Clean up old log files."""
    import time
    
    current_time = time.time()
    cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
    
    for log_file in TEST_LOG_DIR.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                print(f"Removed old log file: {log_file}")
            except Exception as e:
                print(f"Failed to remove log file {log_file}: {e}")


if __name__ == "__main__":
    # Setup logging and run cleanup
    loggers = setup_test_logging()
    cleanup_old_logs()
    
    # Test the logging setup
    loggers['execution'].info("Test logging configuration validated")
    loggers['performance'].info("Performance logging ready")
    loggers['coverage'].info("Coverage logging ready")
    loggers['debug'].debug("Debug logging ready")
    
    print(f"Test logging configured. Log files in: {TEST_LOG_DIR.absolute()}")
