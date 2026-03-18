import logging
import json
import time
from flask import request, has_request_context

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": "ai-support-desk",
            "message": record.getMessage(),
            "request_id": getattr(request, 'request_id', 'static-internal') if has_request_context() else "none"
        }
        return json.dumps(log_record)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)