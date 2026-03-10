import re
import html
from typing import Optional
from functools import lru_cache
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_client_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip)

RATE_LIMITS = {
    "default": "100/minute",
    "auth": "10/minute",
    "create": "30/minute",
    "ai": "5/minute",
    "read": "200/minute",
}


class InputSanitizer:
    PATTERNS = {
        "alphanumeric": re.compile(r'^[a-zA-Z0-9\s\-_]+$'),
        "email": re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        "sku": re.compile(r'^[A-Z0-9\-_]+$', re.IGNORECASE),
        "phone": re.compile(r'^[\d\s\+\-\(\)]+$'),
        "reference": re.compile(r'^[A-Z]{2,3}\-\d{4}\-\d{4}$'),
    }
    DANGEROUS_CHARS = ['<', '>', '"', "'", '\\', '\x00', '\n', '\r', '\t']
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP))",
    ]
    
    @staticmethod
    def sanitize_string(value: Optional[str], max_length: int = 1000) -> Optional[str]:
        if value is None:
            return None
        value = str(value)
        value = value[:max_length]
        value = html.escape(value, quote=True)
        value = value.replace('\x00', '')
        value = ' '.join(value.split())
        return value.strip()
    
    @staticmethod
    def sanitize_html(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        clean = re.sub(r'<[^>]+>', '', str(value))
        return html.escape(clean, quote=True)
    
    @staticmethod
    def sanitize_filename(filename: Optional[str]) -> Optional[str]:
        if filename is None:
            return None
        filename = filename.replace('/', '').replace('\\', '')
        filename = filename.replace('\x00', '')
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        return filename[:255]
    
    @staticmethod
    def sanitize_sku(sku: Optional[str]) -> Optional[str]:
        if sku is None:
            return None
        sku = re.sub(r'[^A-Z0-9\-_]', '', str(sku).upper())
        return sku[:100]
    
    @staticmethod
    def sanitize_numeric(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        try:
            clean = re.sub(r'[^\d.\-]', '', str(value))
            return float(clean)
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        if not value:
            return False
        value_upper = value.upper()
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_xss(cls, value: str) -> bool:
        if not value:
            return False
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed',
            r'<svg[^>]*onload',
            r'expression\s*\(',
            r'url\s*\(\s*["\']?\s*data:',
        ]
        value_lower = value.lower()
        for pattern in xss_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def validate_and_sanitize(cls, value: Optional[str], field_type: str = "text", 
                              max_length: int = 1000) -> tuple[Optional[str], list[str]]:
        warnings = []
        if value is None:
            return None, warnings
        value = str(value)
        if cls.detect_sql_injection(value):
            warnings.append("Potential SQL injection detected and blocked")
        if cls.detect_xss(value):
            warnings.append("Potential XSS detected and blocked")
        if field_type == "sku":
            sanitized = cls.sanitize_sku(value)
        elif field_type == "filename":
            sanitized = cls.sanitize_filename(value)
        elif field_type == "html":
            sanitized = cls.sanitize_html(value)
        else:
            sanitized = cls.sanitize_string(value, max_length)
        return sanitized, warnings


def sanitize(value: Optional[str], max_length: int = 1000) -> Optional[str]:
    return InputSanitizer.sanitize_string(value, max_length)


def sanitize_sku(value: Optional[str]) -> Optional[str]:
    return InputSanitizer.sanitize_sku(value)


def is_safe_input(value: str) -> bool:
    return not (InputSanitizer.detect_sql_injection(value) or 
                InputSanitizer.detect_xss(value))
