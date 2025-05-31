# ACGS-PGP Security Configuration Guide

## Overview

This guide covers the security configuration for the ACGS-PGP production deployment, including authentication, authorization, CSRF protection, rate limiting, and cryptographic integrity measures.

## Authentication Security

### JWT Configuration

#### Environment Variables
```bash
# Strong JWT secret key (minimum 32 characters)
AUTH_SERVICE_SECRET_KEY=your_strong_jwt_secret_key_minimum_32_chars_long

# JWT algorithm (recommended: HS256 or RS256)
AUTH_SERVICE_ALGORITHM=HS256

# Token expiration times
AUTH_SERVICE_ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTH_SERVICE_REFRESH_TOKEN_EXPIRE_DAYS=7
```

#### Security Best Practices
- Use cryptographically secure random keys
- Rotate JWT secrets regularly (every 90 days)
- Use short-lived access tokens (15-30 minutes)
- Implement refresh token rotation
- Store refresh tokens securely (httpOnly cookies)

### CSRF Protection

#### Configuration
```bash
# Strong CSRF secret key
AUTH_SERVICE_CSRF_SECRET_KEY=your_strong_csrf_secret_key_minimum_32_chars

# Cookie settings
CSRF_COOKIE_SAMESITE=lax
CSRF_COOKIE_SECURE=true  # HTTPS only in production
CSRF_COOKIE_HTTPONLY=true
```

#### Implementation
- All state-changing operations require CSRF tokens
- CSRF tokens are tied to user sessions
- Tokens expire with the session
- SameSite cookie attribute prevents CSRF attacks

### Password Security

#### Requirements
- Minimum 8 characters
- Must contain uppercase, lowercase, numbers
- Special characters recommended
- Password history (prevent reuse of last 5 passwords)
- Account lockout after 5 failed attempts

#### Hashing
```python
# Using bcrypt with salt rounds = 12
import bcrypt

password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
```

## Authorization and Access Control

### Role-Based Access Control (RBAC)

#### Roles
1. **Admin**: Full system access
2. **Policy Manager**: Policy creation and management
3. **Auditor**: Read-only access to audit logs
4. **User**: Basic authenticated access

#### Permissions Matrix
| Resource | Admin | Policy Manager | Auditor | User |
|----------|-------|----------------|---------|------|
| Principles | CRUD | CRUD | R | R |
| Policies | CRUD | CRUD | R | R |
| Audit Logs | CRUD | R | R | - |
| User Management | CRUD | - | - | R (self) |
| System Config | CRUD | - | - | - |

### API Endpoint Security

#### Protected Endpoints
```python
# Require authentication
@require_auth
@app.get("/api/v1/principles/")

# Require specific role
@require_role("policy_manager")
@app.post("/api/v1/principles/")

# Require permission
@require_permission("audit:read")
@app.get("/api/v1/audit/logs")
```

## Rate Limiting

### Configuration
```python
# Default rate limits
DEFAULT_RATE_LIMIT = "100/minute"

# Endpoint-specific limits
RATE_LIMITS = {
    "/auth/login": "10/minute",
    "/auth/register": "5/minute",
    "/auth/refresh": "20/minute",
    "/api/v1/synthesize/policy": "10/minute",  # LLM endpoints
    "/api/v1/verify/policy": "20/minute",      # Z3 verification
}
```

### Implementation
- IP-based rate limiting
- User-based rate limiting for authenticated endpoints
- Sliding window algorithm
- Rate limit headers in responses
- Graceful degradation under load

## Network Security

### CORS Configuration
```python
CORS_SETTINGS = {
    "allow_origins": [
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["*", "X-CSRF-Token"],
    "expose_headers": ["X-RateLimit-Remaining", "X-RateLimit-Reset"]
}
```

### Security Headers
```nginx
# Nginx security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

## Database Security

### Connection Security
```bash
# Use SSL connections
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require

# Connection pooling limits
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
```

### Query Security
- Use parameterized queries (SQLAlchemy ORM)
- Input validation and sanitization
- Principle of least privilege for database users
- Regular security updates

### Backup Security
- Encrypted backups
- Secure backup storage
- Regular backup testing
- Point-in-time recovery capability

## Cryptographic Security

### PGP Assurance (Phase 3)
```python
# Key management
PGP_KEY_SIZE = 4096  # RSA key size
PGP_CIPHER_ALGO = "AES256"
PGP_DIGEST_ALGO = "SHA256"

# Master encryption key
ACGS_MASTER_KEY = "your_256_bit_master_encryption_key"
```

### Hashing and Integrity
```python
# SHA3-256 for integrity verification
import hashlib

def calculate_hash(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()

# Merkle tree for policy versioning
class MerkleTree:
    def __init__(self, policies: List[Policy]):
        self.root = self._build_tree(policies)
```

### Timestamping
- RFC 3161 compliant timestamping
- Trusted timestamp authorities
- Cryptographic proof of existence

## Input Validation

### Pydantic Models
```python
from pydantic import BaseModel, validator, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain number')
        return v
```

### SQL Injection Prevention
- Use SQLAlchemy ORM exclusively
- Parameterized queries for raw SQL
- Input sanitization
- Query result validation

### XSS Prevention
- Output encoding
- Content Security Policy headers
- Input validation
- Secure cookie settings

## Monitoring and Alerting

### Security Metrics Collection
```python
# Track security events with detailed context
security_events = Counter(
    'acgs_security_events_total',
    'Security events by type',
    ['event_type', 'severity', 'source', 'service', 'user_id']
)

# Monitor authentication failures with geolocation
auth_failures = Counter(
    'acgs_auth_failures_total',
    'Authentication failures',
    ['failure_type', 'source_ip', 'user_agent', 'country']
)

# Track rate limiting violations
rate_limit_violations = Counter(
    'acgs_rate_limit_violations_total',
    'Rate limit violations',
    ['endpoint', 'source_ip', 'user_id']
)

# Monitor CSRF protection events
csrf_events = Counter(
    'acgs_csrf_events_total',
    'CSRF protection events',
    ['event_type', 'source_ip', 'user_agent']
)

# Track privilege escalation attempts
privilege_escalation = Counter(
    'acgs_privilege_escalation_total',
    'Privilege escalation attempts',
    ['user_id', 'attempted_role', 'source_ip']
)
```

### Real-time Threat Detection
```python
# Anomaly detection for authentication patterns
def detect_auth_anomalies(user_id: str, source_ip: str, user_agent: str):
    """Detect unusual authentication patterns"""
    # Check for multiple IPs for same user
    recent_ips = get_recent_user_ips(user_id, hours=24)
    if len(recent_ips) > 5:
        log_security_event("multiple_ip_login", {
            "user_id": user_id,
            "ip_count": len(recent_ips),
            "ips": recent_ips
        }, "warning")

    # Check for unusual user agent
    if is_suspicious_user_agent(user_agent):
        log_security_event("suspicious_user_agent", {
            "user_id": user_id,
            "user_agent": user_agent,
            "source_ip": source_ip
        }, "warning")

# Brute force detection
def detect_brute_force(source_ip: str):
    """Detect brute force attacks"""
    failure_count = get_auth_failures(source_ip, minutes=15)
    if failure_count > 10:
        # Automatically block IP
        add_ip_to_blocklist(source_ip, duration_hours=24)
        log_security_event("brute_force_detected", {
            "source_ip": source_ip,
            "failure_count": failure_count,
            "action": "ip_blocked"
        }, "high")
```

### Advanced Alert Rules
```yaml
# Prometheus alerting rules for security monitoring
groups:
- name: acgs_security_alerts
  rules:
  # High authentication failure rate
  - alert: HighAuthFailureRate
    expr: rate(acgs_auth_failures_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
      category: authentication
    annotations:
      summary: "High authentication failure rate detected"
      description: "Authentication failure rate is {{ $value }} failures/second"
      runbook_url: "https://docs.acgs-pgp.example.com/runbooks/auth-failures"

  # Brute force attack detection
  - alert: BruteForceAttack
    expr: increase(acgs_auth_failures_total[15m]) > 10
    for: 1m
    labels:
      severity: critical
      category: attack
    annotations:
      summary: "Potential brute force attack detected"
      description: "{{ $labels.source_ip }} has {{ $value }} failed login attempts"

  # Unusual privilege escalation
  - alert: PrivilegeEscalationAttempt
    expr: acgs_privilege_escalation_total > 0
    for: 0s
    labels:
      severity: critical
      category: authorization
    annotations:
      summary: "Privilege escalation attempt detected"
      description: "User {{ $labels.user_id }} attempted to access {{ $labels.attempted_role }}"

  # High rate limit violations
  - alert: HighRateLimitViolations
    expr: rate(acgs_rate_limit_violations_total[5m]) > 1
    for: 5m
    labels:
      severity: warning
      category: abuse
    annotations:
      summary: "High rate of rate limit violations"
      description: "Rate limit violations: {{ $value }}/second on {{ $labels.endpoint }}"

  # CSRF attack detection
  - alert: CSRFAttackDetected
    expr: acgs_csrf_events_total{event_type="csrf_failure"} > 0
    for: 0s
    labels:
      severity: high
      category: attack
    annotations:
      summary: "Potential CSRF attack detected"
      description: "CSRF protection triggered for {{ $labels.source_ip }}"

  # Service security degradation
  - alert: SecurityServiceDown
    expr: up{job=~"acgs-.*"} == 0
    for: 1m
    labels:
      severity: critical
      category: availability
    annotations:
      summary: "Security-critical service is down"
      description: "Service {{ $labels.job }} is not responding"

  # Database security events
  - alert: DatabaseSecurityEvent
    expr: acgs_security_events_total{event_type=~"sql_injection|unauthorized_query"} > 0
    for: 0s
    labels:
      severity: critical
      category: database
    annotations:
      summary: "Database security event detected"
      description: "{{ $labels.event_type }} detected from {{ $labels.source }}"
```

### Grafana Security Dashboards
```json
{
  "dashboard": {
    "title": "ACGS-PGP Security Monitoring",
    "panels": [
      {
        "title": "Authentication Metrics",
        "targets": [
          {
            "expr": "rate(acgs_auth_failures_total[5m])",
            "legendFormat": "Auth Failures/sec"
          },
          {
            "expr": "rate(acgs_auth_success_total[5m])",
            "legendFormat": "Auth Success/sec"
          }
        ]
      },
      {
        "title": "Security Events by Severity",
        "targets": [
          {
            "expr": "acgs_security_events_total",
            "legendFormat": "{{ severity }} - {{ event_type }}"
          }
        ]
      },
      {
        "title": "Rate Limiting Violations",
        "targets": [
          {
            "expr": "topk(10, acgs_rate_limit_violations_total)",
            "legendFormat": "{{ endpoint }} - {{ source_ip }}"
          }
        ]
      },
      {
        "title": "Geographic Distribution of Threats",
        "targets": [
          {
            "expr": "sum by (country) (acgs_auth_failures_total)",
            "legendFormat": "{{ country }}"
          }
        ]
      }
    ]
  }
}
```

## Incident Response

### Security Event Logging
```python
import logging

security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Log security events
def log_security_event(event_type: str, details: dict, severity: str = "info"):
    security_logger.log(
        getattr(logging, severity.upper()),
        f"Security Event: {event_type}",
        extra={
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity
        }
    )
```

### Automated Response
- Account lockout after failed attempts
- IP blocking for suspicious activity
- Automatic token revocation
- Alert notifications to security team

## Compliance and Auditing

### Audit Trail
- All API calls logged with user context
- Database changes tracked
- Authentication events recorded
- Policy modifications audited

### Data Protection
- GDPR compliance for EU users
- Data encryption at rest and in transit
- Right to be forgotten implementation
- Data retention policies

### Regular Security Tasks
- [ ] Weekly security log review
- [ ] Monthly vulnerability scans
- [ ] Quarterly penetration testing
- [ ] Annual security audit
- [ ] Key rotation schedule
- [ ] Backup testing
- [ ] Incident response drills

## Production Checklist

### Pre-deployment Security
- [ ] All secrets properly configured
- [ ] SSL certificates installed
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Database security hardened
- [ ] Monitoring alerts configured

### Post-deployment Verification
- [ ] Authentication flow tested
- [ ] CSRF protection verified
- [ ] Rate limiting functional
- [ ] Security headers present
- [ ] Audit logging working
- [ ] Monitoring alerts triggered
- [ ] Backup procedures tested

### Ongoing Security Maintenance
- [ ] Regular security updates
- [ ] Log monitoring and analysis
- [ ] Performance impact assessment
- [ ] Security training for team
- [ ] Incident response procedures
- [ ] Compliance documentation
- [ ] Third-party security assessments
