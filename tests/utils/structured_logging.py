"""
Structured JSON logging utilities for ACGS-PGP integration tests.

This module provides structured logging capabilities for test execution,
performance monitoring, and debugging integration test failures.
"""

import json
import logging
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
import traceback
import sys


class StructuredTestLogger:
    """Enhanced structured logger for integration tests with JSON output."""
    
    def __init__(self, log_file: str = "tests/logs/integration_test_log.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure JSON logger
        self.logger = logging.getLogger("acgs_integration_tests")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Add JSON file handler
        file_handler = logging.FileHandler(self.log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        
        # Add console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Set formatters
        json_formatter = JSONFormatter()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(json_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Test execution tracking
        self.test_session_id = f"session_{int(time.time())}"
        self.test_results = []
        self.current_test = None
        self.test_start_time = None
    
    def start_test_session(self, session_info: Dict[str, Any]):
        """Start a new test session with metadata."""
        session_data = {
            "event_type": "test_session_start",
            "session_id": self.test_session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_info": session_info,
            "python_version": sys.version,
            "platform": sys.platform
        }
        self.logger.info("Test session started", extra={"structured_data": session_data})
    
    def start_test(self, test_name: str, test_metadata: Optional[Dict[str, Any]] = None):
        """Start logging for a specific test."""
        self.current_test = test_name
        self.test_start_time = time.time()
        
        test_data = {
            "event_type": "test_start",
            "session_id": self.test_session_id,
            "test_name": test_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": test_metadata or {}
        }
        self.logger.info(f"Starting test: {test_name}", extra={"structured_data": test_data})
    
    def end_test(self, test_name: str, status: str, error_info: Optional[Dict[str, Any]] = None):
        """End logging for a specific test."""
        end_time = time.time()
        duration = end_time - self.test_start_time if self.test_start_time else 0
        
        test_result = {
            "event_type": "test_end",
            "session_id": self.test_session_id,
            "test_name": test_name,
            "status": status,  # "passed", "failed", "skipped"
            "duration_seconds": duration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_info": error_info
        }
        
        self.test_results.append(test_result)
        
        if status == "failed":
            self.logger.error(f"Test failed: {test_name}", extra={"structured_data": test_result})
        elif status == "passed":
            self.logger.info(f"Test passed: {test_name}", extra={"structured_data": test_result})
        else:
            self.logger.warning(f"Test skipped: {test_name}", extra={"structured_data": test_result})
        
        self.current_test = None
        self.test_start_time = None
    
    def log_test_step(self, step_name: str, step_data: Dict[str, Any], level: str = "info"):
        """Log a specific test step with structured data."""
        step_log = {
            "event_type": "test_step",
            "session_id": self.test_session_id,
            "test_name": self.current_test,
            "step_name": step_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step_data": step_data
        }
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"Test step: {step_name}", extra={"structured_data": step_log})
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str, context: Dict[str, Any] = None):
        """Log performance metrics with structured data."""
        metric_data = {
            "event_type": "performance_metric",
            "session_id": self.test_session_id,
            "test_name": self.current_test,
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context or {}
        }
        self.logger.info(f"Performance metric: {metric_name}={value}{unit}", 
                        extra={"structured_data": metric_data})
    
    def log_service_interaction(self, service_name: str, operation: str, 
                              request_data: Dict[str, Any], response_data: Dict[str, Any],
                              duration_ms: float, success: bool):
        """Log service interaction details."""
        interaction_data = {
            "event_type": "service_interaction",
            "session_id": self.test_session_id,
            "test_name": self.current_test,
            "service_name": service_name,
            "operation": operation,
            "request_data": request_data,
            "response_data": response_data,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if success:
            self.logger.info(f"Service interaction: {service_name}.{operation}", 
                           extra={"structured_data": interaction_data})
        else:
            self.logger.error(f"Service interaction failed: {service_name}.{operation}", 
                            extra={"structured_data": interaction_data})
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with full traceback and context."""
        error_data = {
            "event_type": "error",
            "session_id": self.test_session_id,
            "test_name": self.current_test,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.logger.error(f"Error occurred: {type(error).__name__}: {error}", 
                         extra={"structured_data": error_data})
    
    def end_test_session(self):
        """End the test session and generate summary."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "passed"])
        failed_tests = len([r for r in self.test_results if r["status"] == "failed"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "skipped"])
        
        total_duration = sum(r["duration_seconds"] for r in self.test_results)
        
        summary_data = {
            "event_type": "test_session_end",
            "session_id": self.test_session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration_seconds": total_duration,
                "average_test_duration": total_duration / total_tests if total_tests > 0 else 0
            },
            "test_results": self.test_results
        }
        
        self.logger.info("Test session completed", extra={"structured_data": summary_data})
        return summary_data


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add structured data if present
        if hasattr(record, 'structured_data'):
            log_entry.update(record.structured_data)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


# Global logger instance
test_logger = StructuredTestLogger()


def log_test_execution(test_name: str):
    """Decorator for automatic test execution logging."""
    def decorator(func):
        import functools

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            test_logger.start_test(test_name, {"function": func.__name__, "args": len(args), "kwargs": list(kwargs.keys())})

            try:
                result = await func(*args, **kwargs)
                test_logger.end_test(test_name, "passed")
                return result
            except Exception as e:
                error_info = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc()
                }
                test_logger.end_test(test_name, "failed", error_info)
                test_logger.log_error(e, {"function": func.__name__})
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            test_logger.start_test(test_name, {"function": func.__name__, "args": len(args), "kwargs": list(kwargs.keys())})

            try:
                result = func(*args, **kwargs)
                test_logger.end_test(test_name, "passed")
                return result
            except Exception as e:
                error_info = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc()
                }
                test_logger.end_test(test_name, "failed", error_info)
                test_logger.log_error(e, {"function": func.__name__})
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator
