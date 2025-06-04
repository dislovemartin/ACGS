# ACGS-PGP Credential Management Guide

## Overview

This document outlines secure credential management practices for the ACGS-PGP framework to prevent exposure of sensitive information like API keys, tokens, and other credentials.

## Security Incident Response

### GitHub Push Protection Violation

On [Date], a GitHub push protection error was triggered due to exposed credentials in commit `1b6ec435ab9f1324703b073e0ac653701def0369`. The following credentials were exposed:

- **GitHub Personal Access Token**: `github_pat_11BKYGVCA0bCYKp6ENCHf7_*` (redacted)
- **Brave API Key**: `BSAwSpsV7sjHJ3M8cGQqBNAkKTE0A4U`
- **Power API Key**: `6b917f9b-582a-4cf8-931e-397ffe6d14b9`

### Remediation Actions Taken

1. **Immediate Response**:
   - Removed `.kilocode/mcp.json` file from working directory
   - Updated `.gitignore` to prevent future credential exposure
   - Created secure template files with environment variable references

2. **Security Infrastructure**:
   - Enhanced `.env.example` with MCP server credential templates
   - Added comprehensive `.gitignore` patterns for credential files
   - Created secure MCP configuration template

3. **Required Actions**:
   - **CRITICAL**: Revoke and regenerate all exposed credentials immediately
   - Update local environment files with new credentials
   - Verify no other credential exposure in git history

## Secure Credential Management Practices

### Environment Variables

All sensitive credentials should be stored in environment variables and referenced in configuration files:

```bash
# .env (never commit this file)
GITHUB_PERSONAL_ACCESS_TOKEN="your_actual_token_here"
BRAVE_API_KEY="your_actual_api_key_here"
POWER_API_KEY="your_actual_power_key_here"
```

### Configuration Files

Use environment variable substitution in configuration files:

```json
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
  }
}
```

### Docker and Kubernetes

For containerized deployments:

```yaml
# docker-compose.yml
environment:
  - GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PERSONAL_ACCESS_TOKEN}

# kubernetes secret
apiVersion: v1
kind: Secret
metadata:
  name: acgs-credentials
type: Opaque
data:
  github-token: <base64-encoded-token>
```

## File Patterns to Avoid

Never commit files containing:
- API keys, tokens, passwords
- Private keys (.key, .pem, .p12, .pfx)
- Configuration files with embedded credentials
- Database connection strings with passwords
- OAuth client secrets

## Git Security Best Practices

1. **Pre-commit Hooks**: Use tools like `git-secrets` or `detect-secrets`
2. **Regular Audits**: Scan repository history for exposed credentials
3. **Branch Protection**: Enable push protection on GitHub
4. **Access Control**: Limit repository access to authorized personnel

## Emergency Response Procedure

If credentials are accidentally committed:

1. **Immediate Actions**:
   - Stop all pushes to remote repository
   - Revoke/regenerate exposed credentials immediately
   - Remove credentials from git history (if possible)

2. **Assessment**:
   - Identify scope of exposure
   - Check for unauthorized access using exposed credentials
   - Document incident for security review

3. **Remediation**:
   - Update all systems with new credentials
   - Review and enhance security practices
   - Implement additional safeguards

## Tools and Resources

- **GitHub Secret Scanning**: Automatically detects exposed secrets
- **git-secrets**: Pre-commit hook for credential detection
- **detect-secrets**: Baseline and audit tool for secrets
- **HashiCorp Vault**: Enterprise secret management
- **AWS Secrets Manager**: Cloud-based secret storage

## Compliance Requirements

For ACGS-PGP production deployments:
- All credentials must be stored in secure secret management systems
- Regular credential rotation (minimum quarterly)
- Audit logging for all credential access
- Encryption at rest and in transit for all sensitive data

## Contact Information

For security incidents or questions:
- Security Team: [security@acgs-pgp.org]
- Emergency Response: [emergency@acgs-pgp.org]
- Documentation Updates: [docs@acgs-pgp.org]
