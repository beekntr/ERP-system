"""
Security utilities for ERP Purchase Order System.
Includes input sanitization and rate limiting configuration.
"""

import re
import html
from typing import Optional
from functools import lru_cache
from slowapi import Limiter
from slowapi.util import get_remote_address


# =====================
# Rate Limiter Configuration
# =====================

def get_client_ip(request) -> str:
    """
    Get client IP address from request.
    Handles proxy headers for accurate IP detection.
    """
    # Check for forwarded headers (when behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return get_remote_address(request)


# Create rate limiter instance
limiter = Limiter(key_func=get_client_ip)

# Rate limit configurations
RATE_LIMITS = {
    "default": "100/minute",           # Default for most endpoints
    "auth": "10/minute",               # Stricter for auth endpoints
    "create": "30/minute",             # Creating resources
    "ai": "5/minute",                  # AI generation (expensive)
    "read": "200/minute",              # Read operations
}


# =====================
# Input Sanitization
# =====================

class InputSanitizer:
    """
    Utility class for sanitizing user inputs to prevent XSS and injection attacks.
    """
    
    # Regex patterns for validation
    PATTERNS = {
        "alphanumeric": re.compile(r'^[a-zA-Z0-9\s\-_]+$'),
        "email": re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        "sku": re.compile(r'^[A-Z0-9\-_]+$', re.IGNORECASE),
        "phone": re.compile(r'^[\d\s\+\-\(\)]+$'),
        "reference": re.compile(r'^[A-Z]{2,3}\-\d{4}\-\d{4}$'),
    }
    
    # Characters to strip from inputs
    DANGEROUS_CHARS = ['<', '>', '"', "'", '\\', '\x00', '\n', '\r', '\t']
    
    # SQL injection patterns to detect
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP))",
    ]
    
    @staticmethod
    def sanitize_string(value: Optional[str], max_length: int = 1000) -> Optional[str]:
        """
        Sanitize a string input by escaping HTML and removing dangerous characters.
        
        Args:
            value: The input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string or None if input is None
        """
        if value is None:
            return None
        
        # Convert to string if not already
        value = str(value)
        
        # Truncate to max length
        value = value[:max_length]
        
        # HTML escape to prevent XSS
        value = html.escape(value, quote=True)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Normalize whitespace
        value = ' '.join(value.split())
        
        return value.strip()
    
    @staticmethod
    def sanitize_html(value: Optional[str]) -> Optional[str]:
        """
        Remove all HTML tags from input.
        """
        if value is None:
            return None
        
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', str(value))
        
        # HTML escape remaining content
        return html.escape(clean, quote=True)
    
    @staticmethod
    def sanitize_filename(filename: Optional[str]) -> Optional[str]:
        """
        Sanitize a filename to prevent path traversal attacks.
        """
        if filename is None:
            return None
        
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Keep only safe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Limit length
        return filename[:255]
    
    @staticmethod
    def sanitize_sku(sku: Optional[str]) -> Optional[str]:
        """
        Sanitize SKU to only allow alphanumeric and hyphens.
        """
        if sku is None:
            return None
        
        # Uppercase and remove invalid characters
        sku = re.sub(r'[^A-Z0-9\-_]', '', str(sku).upper())
        
        return sku[:100]
    
    @staticmethod
    def sanitize_numeric(value: Optional[str]) -> Optional[float]:
        """
        Sanitize numeric input.
        """
        if value is None:
            return None
        
        try:
            # Remove any non-numeric characters except . and -
            clean = re.sub(r'[^\d.\-]', '', str(value))
            return float(clean)
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """
        Detect potential SQL injection attempts.
        
        Returns:
            True if potential SQL injection detected
        """
        if not value:
            return False
        
        value_upper = value.upper()
        
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def detect_xss(cls, value: str) -> bool:
        """
        Detect potential XSS attempts.
        
        Returns:
            True if potential XSS detected
        """
        if not value:
            return False
        
        # Common XSS patterns
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
        """
        Validate and sanitize input, returning sanitized value and any warnings.
        
        Args:
            value: Input value
            field_type: Type of field (text, sku, email, etc.)
            max_length: Maximum allowed length
            
        Returns:
            Tuple of (sanitized_value, list_of_warnings)
        """
        warnings = []
        
        if value is None:
            return None, warnings
        
        # Convert to string
        value = str(value)
        
        # Check for SQL injection attempts
        if cls.detect_sql_injection(value):
            warnings.append("Potential SQL injection detected and blocked")
        
        # Check for XSS attempts
        if cls.detect_xss(value):
            warnings.append("Potential XSS detected and blocked")
        
        # Sanitize based on field type
        if field_type == "sku":
            sanitized = cls.sanitize_sku(value)
        elif field_type == "filename":
            sanitized = cls.sanitize_filename(value)
        elif field_type == "html":
            sanitized = cls.sanitize_html(value)
        else:
            sanitized = cls.sanitize_string(value, max_length)
        
        return sanitized, warnings


# Convenience functions
def sanitize(value: Optional[str], max_length: int = 1000) -> Optional[str]:
    """Quick sanitize a string value."""
    return InputSanitizer.sanitize_string(value, max_length)


def sanitize_sku(value: Optional[str]) -> Optional[str]:
    """Quick sanitize a SKU value."""
    return InputSanitizer.sanitize_sku(value)


def is_safe_input(value: str) -> bool:
    """Check if input is safe (no SQL injection or XSS)."""
    return not (InputSanitizer.detect_sql_injection(value) or 
                InputSanitizer.detect_xss(value))
