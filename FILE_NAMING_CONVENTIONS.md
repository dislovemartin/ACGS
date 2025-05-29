# File Naming Conventions for ACGS-PGP

## Overview
This document establishes cross-platform compatible file naming conventions for the ACGS-PGP project to ensure compatibility across Windows, macOS, and Linux systems, particularly for CI/CD pipelines.

## Cross-Platform Compatibility Rules

### Prohibited Characters
The following characters are **NEVER** allowed in file or directory names:
- `:` (colon) - Invalid on Windows
- `<` `>` (angle brackets) - Invalid on Windows
- `"` (double quotes) - Invalid on Windows
- `|` (pipe) - Invalid on Windows
- `?` (question mark) - Invalid on Windows
- `*` (asterisk) - Invalid on Windows
- `/` (forward slash) - Path separator
- `\` (backslash) - Path separator on Windows

### Recommended Characters
Use only the following characters:
- Letters: `a-z`, `A-Z`
- Numbers: `0-9`
- Hyphens: `-`
- Underscores: `_`
- Periods: `.` (for file extensions only)

### Directory Naming Convention
- Use `PascalCase` or `snake_case` for directory names
- Replace spaces with underscores `_` or hyphens `-`
- Keep names concise but descriptive
- Maximum length: 50 characters

### Examples of Correct Naming

#### Before (Problematic)
```
AlphaEvolve-ACGS Integration System: A Framework for Constitutionally Governed Evolutionary Computation/
Artificial Constitutionalism: A Self-Synthesizing Prompt Governance Compiler (ACGS-PGP) Framework for Advanced AI Systems/
```

#### After (Correct)
```
AlphaEvolve-ACGS_Integration_System/
ACGS-PGP_Framework/
```

## File Naming Guidelines

### Research Papers and Documents
- Format: `{project}_{document_type}_{version}.{ext}`
- Example: `acgs_pgp_manuscript_v1.tex`
- Example: `alphaevolve_reproducibility_guide.md`

### Code Files
- Use `snake_case` for Python files
- Use `camelCase` for JavaScript files
- Use `PascalCase` for class files

### Configuration Files
- Use lowercase with hyphens: `docker-compose.yml`
- Use underscores for environment-specific configs: `config_production.yaml`

## CI/CD Considerations

### GitHub Actions
- All paths in workflow files must use the new naming convention
- Test workflows on Windows runners to ensure compatibility
- Use relative paths where possible

### Docker
- Container names should follow the same conventions
- Volume mounts must use compatible path names

## Migration Checklist

When renaming files or directories:

1. **Update References**
   - [ ] GitHub Actions workflows (`.github/workflows/`)
   - [ ] Documentation files (`docs/`, `README.md`)
   - [ ] Docker configurations
   - [ ] Import statements in code
   - [ ] Configuration files

2. **Test Compatibility**
   - [ ] Run CI/CD pipeline on all platforms
   - [ ] Test local development setup
   - [ ] Verify Docker builds

3. **Update Documentation**
   - [ ] Update this file
   - [ ] Update project README
   - [ ] Update developer guide

## Validation Tools

### Pre-commit Hook (Recommended)
Create a pre-commit hook to validate file names:

```bash
#!/bin/bash
# Check for invalid characters in file names
if git diff --cached --name-only | grep -E '[:<>"|?*]'; then
    echo "Error: File names contain invalid characters for cross-platform compatibility"
    echo "See FILE_NAMING_CONVENTIONS.md for guidelines"
    exit 1
fi
```

### Manual Validation
```bash
# Find files with problematic names
find . -name "*:*" -o -name "*<*" -o -name "*>*" -o -name '*"*' -o -name "*|*" -o -name "*?*" -o -name "***"
```

## Historical Changes

### 2025-01-XX - Initial Cleanup
- Renamed `AlphaEvolve-ACGS Integration System: A Framework for Constitutionally Governed Evolutionary Computation/` to `AlphaEvolve-ACGS_Integration_System/`
- Renamed `Artificial Constitutionalism: A Self-Synthesizing Prompt Governance Compiler (ACGS-PGP) Framework for Advanced AI Systems/` to `ACGS-PGP_Framework/`
- Updated GitHub Actions workflow references
- Updated documentation links

## Enforcement

This convention is **mandatory** for all new files and directories. Existing files should be migrated during regular maintenance cycles or when they cause compatibility issues.

For questions or exceptions, please create an issue in the project repository.
