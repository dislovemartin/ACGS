# ACGS-PGP: AI Compliance Governance System - Policy Generation Platform

## Overview

The AI Compliance Governance System - Policy Generation Platform (ACGS-PGP) is a comprehensive framework for automated governance and compliance in AI systems. It provides constitutional principles, governance synthesis, formal verification, and real-time policy enforcement.

## Architecture

### Core Services
- **Fv Service**: Advanced fv service capabilities
- **Federated Service**: Advanced federated service capabilities
- **Pgc Service**: Advanced pgc service capabilities
- **Gs Service**: Advanced gs service capabilities
- **Integrity Service**: Advanced integrity service capabilities
- **Workflow Service**: Advanced workflow service capabilities
- **Monitoring**: Advanced monitoring capabilities
- **Auth Service**: Advanced auth service capabilities
- **Ac Service**: Advanced ac service capabilities
- **Ec Service**: Advanced ec service capabilities
- **Shared**: Advanced shared capabilities
- **Research Service**: Advanced research service capabilities

### Key Features
- **Constitutional Governance**: Democratic oversight and principle management
- **Governance Synthesis**: LLM-driven policy generation with MAB optimization
- **Formal Verification**: Mathematical guarantees for safety-critical principles
- **Real-time Enforcement**: Sub-50ms policy decision latency
- **Cryptographic Integrity**: PGP-assured audit trails and policy validation
- **WINA Optimization**: 40-70% GFLOPs reduction with >95% accuracy

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/dislovemartin/ACGS.git
   cd ACGS
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start services:
   ```bash
   docker-compose up -d
   ```

4. Verify installation:
   ```bash
   curl http://localhost:8000/health
   ```

### Policy Corpus Setup

The policy corpus under `data/principle-policy-corpus` includes
profiles from the [NIST OSCAL project](https://github.com/usnistgov/OSCAL).
These files total more than 100 MB. To keep the repository small, you can
store them using [Git LFS](https://git-lfs.github.com/) or host them on an
external storage service such as S3.

If the directory `nist-oscal-profiles` is missing, retrieve the latest
profiles and place them under `data/principle-policy-corpus`:

```bash
git clone https://github.com/usnistgov/oscal-content.git tmp-oscal
mkdir -p data/principle-policy-corpus/nist-oscal-profiles
cp -r tmp-oscal/examples/* data/principle-policy-corpus/nist-oscal-profiles/
rm -rf tmp-oscal
```

## Development

### Project Structure
```
ACGS-PGP/
├── src/
│   ├── backend/          # Microservices
│   ├── frontend/         # React dashboard
│   └── shared/           # Shared utilities
├── config/               # Configuration files
├── docs/                 # Documentation
├── scripts/              # Automation scripts
└── tests/                # Test suites
```

### Running Tests
```bash
# Run all tests
pytest

# Legacy integration scripts (require running services)
ACGS_INTEGRATION=1 pytest tests/integration/legacy

# Run specific service tests
pytest tests/backend/ac_service/

# Run with coverage
pytest --cov=src/backend
```

### API Documentation
- AC Service: http://localhost:8001/docs
- Integrity Service: http://localhost:8002/docs
- FV Service: http://localhost:8003/docs
- GS Service: http://localhost:8004/docs
- PGC Service: http://localhost:8005/docs

## Production Deployment

See [Production Deployment Guide](docs/PHASE3_PRODUCTION_DEPLOYMENT_GUIDE.md) for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Research and Publications

- [AlphaEvolve-ACGS Research Paper](docs/research/AlphaEvolve-ACGS_arXiv_submission/)
- [Technical Specifications](docs/research/technical_specifications.md)
- [Architecture Documentation](docs/architecture_documentation.md)

## Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/dislovemartin/ACGS/issues)
- Discussions: [GitHub Discussions](https://github.com/dislovemartin/ACGS/discussions)

---

**Last Updated:** 2025-06-05
**Version:** 3.0.0
**Status:** Production Ready
