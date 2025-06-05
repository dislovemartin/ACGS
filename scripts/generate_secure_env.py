#!/usr/bin/env python3
"""
ACGS-PGP Secure Environment Configuration Generator

Generates secure environment configuration with strong cryptographic keys
and production-ready security settings for Phase 2.1 Security Hardening.

Usage:
    python scripts/generate_secure_env.py [--output .env.production] [--environment production]
"""

import argparse
import secrets
import os
import sys
from datetime import datetime
from typing import Dict, List

def generate_secure_key(length: int = 64) -> str:
    """Generate a cryptographically secure random key."""
    return secrets.token_urlsafe(length)

def generate_strong_password(length: int = 32) -> str:
    """Generate a strong password with mixed characters."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_security_config(environment: str) -> Dict[str, str]:
    """Get security configuration based on environment."""
    
    # Generate secure keys
    jwt_secret = generate_secure_key(64)
    csrf_secret = generate_secure_key(32)
    postgres_password = generate_strong_password(32)
    
    # Base configuration
    config = {
        # Environment
        "ENVIRONMENT": environment,
        "DEBUG": "false" if environment == "production" else "true",
        "TEST_MODE": "false",
        
        # Database Security
        "POSTGRES_PASSWORD": postgres_password,
        
        # JWT Security
        "JWT_SECRET_KEY": jwt_secret,
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30" if environment == "production" else "60",
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "7" if environment == "production" else "30",
        
        # CSRF Protection
        "CSRF_SECRET_KEY": csrf_secret,
        
        # HTTPS/TLS Configuration
        "ENABLE_HTTPS": "true" if environment == "production" else "false",
        "FORCE_HTTPS_REDIRECT": "true" if environment == "production" else "false",
        "TLS_CERT_PATH": "/etc/ssl/certs/acgs.crt",
        "TLS_KEY_PATH": "/etc/ssl/private/acgs.key",
        
        # Security Headers
        "ENABLE_SECURITY_HEADERS": "true",
        "ENABLE_HSTS": "true" if environment == "production" else "false",
        "HSTS_MAX_AGE": "31536000",  # 1 year
        "ENABLE_CSP": "true",
        "CSP_REPORT_URI": "/api/v1/security/csp-report",
        
        # Rate Limiting
        "ENABLE_RATE_LIMITING": "true",
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "60" if environment == "production" else "100",
        "RATE_LIMIT_BURST_SIZE": "10" if environment == "production" else "20",
        "RATE_LIMIT_BLOCK_DURATION_MINUTES": "30" if environment == "production" else "15",
        "ENABLE_IP_BLOCKING": "true",
        "MAX_FAILED_ATTEMPTS": "3" if environment == "production" else "5",
        
        # Input Validation
        "MAX_REQUEST_SIZE_MB": "5" if environment == "production" else "10",
        "ENABLE_REQUEST_VALIDATION": "true",
        "ENABLE_SQL_INJECTION_PROTECTION": "true",
        "ENABLE_XSS_PROTECTION": "true",
        
        # Security Monitoring
        "ENABLE_SECURITY_LOGGING": "true",
        "SECURITY_LOG_LEVEL": "WARNING" if environment == "production" else "INFO",
        "ENABLE_INTRUSION_DETECTION": "true",
        
        # Password Policy
        "PASSWORD_MIN_LENGTH": "12" if environment == "production" else "8",
        "PASSWORD_REQUIRE_UPPERCASE": "true",
        "PASSWORD_REQUIRE_LOWERCASE": "true",
        "PASSWORD_REQUIRE_NUMBERS": "true",
        "PASSWORD_REQUIRE_SPECIAL": "true",
        
        # Session Security
        "SESSION_TIMEOUT_MINUTES": "30" if environment == "production" else "60",
        "ENABLE_SESSION_ROTATION": "true",
        "SECURE_COOKIES": "true" if environment == "production" else "false",
    }
    
    # Environment-specific CORS origins
    if environment == "production":
        config["BACKEND_CORS_ORIGINS"] = "https://acgs-pgp.com,https://api.acgs-pgp.com"
    elif environment == "staging":
        config["BACKEND_CORS_ORIGINS"] = "https://staging.acgs-pgp.com,http://localhost:3000"
    else:
        config["BACKEND_CORS_ORIGINS"] = "http://localhost:3000,http://localhost:3001"
    
    return config

def generate_env_file(config: Dict[str, str], output_file: str, environment: str):
    """Generate the .env file with security configuration."""
    
    header = f"""# =============================================================================
# ACGS-PGP Secure Environment Configuration
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Environment: {environment.upper()}
# Security Level: {'CRITICAL' if environment == 'production' else 'HIGH'}
# =============================================================================

# ⚠️  SECURITY WARNING ⚠️
# This file contains sensitive security credentials.
# - Never commit this file to version control
# - Restrict file permissions (chmod 600)
# - Use secure secret management in production
# - Rotate keys regularly

"""
    
    sections = {
        "Environment Configuration": [
            "ENVIRONMENT", "DEBUG", "TEST_MODE"
        ],
        "Database Security": [
            "POSTGRES_PASSWORD"
        ],
        "JWT Security Configuration": [
            "JWT_SECRET_KEY", "JWT_ALGORITHM", "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 
            "JWT_REFRESH_TOKEN_EXPIRE_DAYS"
        ],
        "CSRF Protection": [
            "CSRF_SECRET_KEY"
        ],
        "HTTPS/TLS Configuration": [
            "ENABLE_HTTPS", "FORCE_HTTPS_REDIRECT", "TLS_CERT_PATH", "TLS_KEY_PATH"
        ],
        "Security Headers Configuration": [
            "ENABLE_SECURITY_HEADERS", "ENABLE_HSTS", "HSTS_MAX_AGE", 
            "ENABLE_CSP", "CSP_REPORT_URI"
        ],
        "Rate Limiting Configuration": [
            "ENABLE_RATE_LIMITING", "RATE_LIMIT_REQUESTS_PER_MINUTE", 
            "RATE_LIMIT_BURST_SIZE", "RATE_LIMIT_BLOCK_DURATION_MINUTES",
            "ENABLE_IP_BLOCKING", "MAX_FAILED_ATTEMPTS"
        ],
        "Input Validation Configuration": [
            "MAX_REQUEST_SIZE_MB", "ENABLE_REQUEST_VALIDATION", 
            "ENABLE_SQL_INJECTION_PROTECTION", "ENABLE_XSS_PROTECTION"
        ],
        "Security Monitoring": [
            "ENABLE_SECURITY_LOGGING", "SECURITY_LOG_LEVEL", "ENABLE_INTRUSION_DETECTION"
        ],
        "Password Policy": [
            "PASSWORD_MIN_LENGTH", "PASSWORD_REQUIRE_UPPERCASE", 
            "PASSWORD_REQUIRE_LOWERCASE", "PASSWORD_REQUIRE_NUMBERS", 
            "PASSWORD_REQUIRE_SPECIAL"
        ],
        "Session Security": [
            "SESSION_TIMEOUT_MINUTES", "ENABLE_SESSION_ROTATION", "SECURE_COOKIES"
        ],
        "CORS Configuration": [
            "BACKEND_CORS_ORIGINS"
        ]
    }
    
    content = header
    
    for section_name, keys in sections.items():
        content += f"\n# {section_name}\n"
        for key in keys:
            if key in config:
                value = config[key]
                # Add security comment for sensitive keys
                if "SECRET" in key or "PASSWORD" in key:
                    content += f"# SENSITIVE: Keep this value secure and rotate regularly\n"
                content += f"{key}={value}\n"
        content += "\n"
    
    # Add security recommendations
    content += """# =============================================================================
# Security Recommendations for Production
# =============================================================================

# 1. Key Management:
#    - Store secrets in a secure key management system (AWS KMS, HashiCorp Vault)
#    - Rotate JWT and CSRF keys every 90 days
#    - Use different keys for each environment

# 2. Database Security:
#    - Use strong, unique passwords for each environment
#    - Enable database encryption at rest
#    - Configure database firewall rules

# 3. Network Security:
#    - Use HTTPS/TLS 1.3 for all communications
#    - Configure proper firewall rules
#    - Use VPN for administrative access

# 4. Monitoring:
#    - Enable comprehensive security logging
#    - Set up real-time security alerts
#    - Regular security audits and penetration testing

# 5. Backup and Recovery:
#    - Regular encrypted backups
#    - Test disaster recovery procedures
#    - Document incident response procedures

# =============================================================================
"""
    
    # Write the file
    with open(output_file, 'w') as f:
        f.write(content)
    
    # Set secure file permissions (Unix/Linux only)
    try:
        os.chmod(output_file, 0o600)
        print(f"✅ Set secure file permissions (600) for {output_file}")
    except:
        print(f"⚠️  Could not set file permissions for {output_file} (Windows or permission issue)")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate secure ACGS-PGP environment configuration")
    parser.add_argument("--output", default=".env.secure", help="Output file path")
    parser.add_argument("--environment", default="production", 
                       choices=["development", "staging", "production"],
                       help="Target environment")
    parser.add_argument("--force", action="store_true", help="Overwrite existing file")
    
    args = parser.parse_args()
    
    # Check if file exists
    if os.path.exists(args.output) and not args.force:
        print(f"❌ File {args.output} already exists. Use --force to overwrite.")
        sys.exit(1)
    
    print("🔐 Generating ACGS-PGP Secure Environment Configuration")
    print(f"Environment: {args.environment.upper()}")
    print(f"Output: {args.output}")
    print()
    
    # Generate configuration
    config = get_security_config(args.environment)
    
    # Generate the file
    generate_env_file(config, args.output, args.environment)
    
    print(f"✅ Secure environment configuration generated: {args.output}")
    print()
    print("🔒 Security Checklist:")
    print("  ✅ Strong cryptographic keys generated")
    print("  ✅ Production-ready security settings configured")
    print("  ✅ Rate limiting and input validation enabled")
    print("  ✅ Security headers and CORS properly configured")
    print("  ✅ Comprehensive security monitoring enabled")
    print()
    print("⚠️  Next Steps:")
    print(f"  1. Review the generated configuration in {args.output}")
    print("  2. Copy to your deployment environment")
    print("  3. Configure TLS certificates if using HTTPS")
    print("  4. Set up security monitoring and alerting")
    print("  5. Test the configuration with security validation script")
    print()
    print("🚨 Security Reminders:")
    print("  - Never commit this file to version control")
    print("  - Use secure secret management in production")
    print("  - Rotate keys regularly (every 90 days)")
    print("  - Monitor security logs and alerts")

if __name__ == "__main__":
    main()
