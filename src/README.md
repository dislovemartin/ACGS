# ACGS-PGP Source Code

This directory contains all source code for the AI Compliance Governance System - Policy Generation Platform (ACGS-PGP).

## Directory Structure

### `backend/`
Contains all backend microservices and shared modules:

- **`ac_service/`** - Audit & Compliance Service
  - Manages AI governance principles and guidelines
  - Handles Constitutional Council operations
  - Provides principle management APIs

- **`auth_service/`** - Authentication Service
  - User registration, login, and session management
  - JWT token issuance and validation
  - RBAC (Role-Based Access Control) implementation

- **`fv_service/`** - Formal Verification Service
  - Z3 SMT solver integration
  - Policy verification against principles
  - Safety property checking

- **`gs_service/`** - Governance Synthesis Service
  - LLM-driven policy synthesis
  - Constitutional prompting
  - Policy generation from principles

- **`integrity_service/`** - Integrity & Verifiability Service
  - Policy storage and versioning
  - Audit log management
  - Cryptographic integrity (PGP Assurance)

- **`pgc_service/`** - Protective Governance Controls Service
  - Runtime policy enforcement
  - OPA (Open Policy Agent) integration
  - Real-time constraint checking

- **`shared/`** - Shared Backend Modules
  - Database models and schemas
  - Common utilities and middleware
  - Security components

### `frontend/`
React-based web application providing:
- User interface for policy management
- Constitutional Council dashboard
- Governance workflow visualization
- Administrative tools

### `alphaevolve_gs_engine/`
AlphaEvolve integration engine for:
- Evolutionary computation governance
- Adaptive policy evolution
- Constitutional constraint enforcement
- Bias detection and mitigation

## Development Guidelines

1. **Service Independence**: Each microservice should be independently deployable
2. **Shared Dependencies**: Use `shared/` modules for common functionality
3. **API Consistency**: Follow RESTful API conventions across all services
4. **Testing**: Write comprehensive tests for all components
5. **Documentation**: Maintain up-to-date API documentation

## Getting Started

1. Set up the development environment (see main README.md)
2. Install dependencies for each service
3. Configure environment variables
4. Run database migrations
5. Start services using Docker Compose

For detailed setup instructions, refer to the main project documentation.
