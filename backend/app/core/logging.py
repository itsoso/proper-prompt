"""Logging configuration with structlog"""
import logging
import sys
import os
from datetime import datetime
from typing import Any, Dict
from pathlib import Path
import structlog
from structlog.types import Processor

from app.core.config import settings


def ensure_log_directory():
    """Ensure log directory exists"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir


def add_timestamp(
    logger: logging.Logger, 
    method_name: str, 
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add timestamp to log entries"""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_service_info(
    logger: logging.Logger, 
    method_name: str, 
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add service information to log entries"""
    event_dict["service"] = settings.APP_NAME
    event_dict["version"] = settings.APP_VERSION
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


def setup_logging():
    """Configure structured logging"""
    ensure_log_directory()
    
    # Define shared processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_timestamp,
        add_service_info,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # JSON or console renderer based on config
    if settings.LOG_FORMAT == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup stdlib logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler for application logs
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(formatter)
    
    # Performance file handler
    perf_handler = logging.FileHandler(settings.PERFORMANCE_LOG_FILE)
    perf_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Configure performance logger
    perf_logger = logging.getLogger("performance")
    perf_logger.handlers.clear()
    perf_logger.addHandler(perf_handler)
    perf_logger.addHandler(console_handler)
    perf_logger.setLevel(logging.INFO)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    

def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


def get_performance_logger() -> structlog.stdlib.BoundLogger:
    """Get performance logger instance"""
    return structlog.get_logger("performance")


class LogContext:
    """Context manager for adding context to logs"""
    
    def __init__(self, **kwargs):
        self.context = kwargs
    
    def __enter__(self):
        structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.unbind_contextvars(*self.context.keys())

