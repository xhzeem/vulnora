"""
VulnerableShop Configuration
DELIBERATELY INSECURE - For Educational Purposes Only
"""

import os

class Config:
    # INSECURE: Debug mode enabled in production
    DEBUG = True
    TESTING = False
    
    # INSECURE: Weak, hardcoded secret key
    SECRET_KEY = 'vulnerable-secret-key-12345'
    
    # Database Configuration
    # Default PostgreSQL connection - modify if needed
    DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
    DATABASE_PORT = os.getenv('DB_PORT', '5432')
    DATABASE_NAME = os.getenv('DB_NAME', 'vulnerableshop')
    DATABASE_USER = os.getenv('DB_USER', 'postgres')
    DATABASE_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    
    # Build connection string
    DATABASE_URI = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    
    # Session Configuration
    # INSECURE: Session cookies without security flags
    SESSION_COOKIE_HTTPONLY = False  # Vulnerable to XSS
    SESSION_COOKIE_SECURE = False    # No HTTPS requirement
    SESSION_COOKIE_SAMESITE = None   # No CSRF protection
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # File Upload Configuration
    # INSECURE: No file type restrictions
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = set()  # Empty = allow all files!
    
    # Application Settings
    PRODUCTS_PER_PAGE = 12
    ADMIN_EMAIL = 'admin@vulnerableshop.local'
    
    # INSECURE: Flags for CTF challenges hidden in config
    FLAG_1 = 'FLAG{c0nf1g_f1l3s_4r3_s3ns1t1v3}'
    INTERNAL_API_KEY = 'INTERNAL-SECRET-KEY-XYZ'
    
    # INSECURE: No security headers
    SECURITY_HEADERS = {
        'X-Frame-Options': None,  # Clickjacking possible
        'X-Content-Type-Options': None,
        'X-XSS-Protection': None,
        'Strict-Transport-Security': None,
        'Content-Security-Policy': None
    }
