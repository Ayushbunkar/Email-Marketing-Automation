# Implementation Decisions

This document records key implementation decisions made during the development of the Hermes Email Marketing Agent.

## Phase 1 - Core Infrastructure (COMPLETED)

### 11. Phase 1 Acceptance Checks
**Date**: 2026-07-27
**Context**: Phase 1 acceptance criteria requires: `make up && make db && make seed && make test green; hermes --help works.`
**Decision**: All acceptance checks passed:
- Docker services (PostgreSQL + Redis) were already running and healthy
- Database migrations ran successfully with `alembic upgrade head`
- Seed script created 200 demo contacts and 1 demo segment
- All 19 tests passed
- CLI `hermes --help` works and shows 3 commands (chat, seed, run-agent)
**Rationale**: Phase 1 foundations are complete and verified.

### 5. Alembic Configuration
**Date**: 2026-07-27
**Context**: The project had alembic files in `alembic_local` directory but the spec requires them in `alembic` directory.
**Decision**: Copied all alembic files from `alembic_local` to `alembic` directory and updated `alembic.ini` to point to `script_location = alembic`.
**Rationale**: Complies with PROJECT_SPEC.md Section 4 which specifies `alembic/` directory for migrations.

### 6. Makefile Configuration
**Date**: 2026-07-27
**Context**: Makefile uses hardcoded Python path which may vary by system.
**Decision**: Makefile uses `C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe` which is the system Python path. This is acceptable for the current environment.
**Rationale**: The Makefile targets (up, db, seed, dev, worker, beat, test, lint) are all properly configured and functional.

### 7. Docker Compose Configuration
**Date**: 2026-07-27
**Context**: docker-compose.yml defines PostgreSQL and Redis services.
**Decision**: The configuration uses `pgvector/pgvector:pg16` image with proper health checks and Redis 7 Alpine.
**Rationale**: Complies with PROJECT_SPEC.md Section 3 which specifies PostgreSQL 16 with pgvector and Redis 7.

### 8. Pyproject.toml Dependencies
**Date**: 2026-07-27
**Context**: pyproject.toml defines all project dependencies.
**Decision**: All required dependencies are present: fastapi, uvicorn, sqlalchemy, asyncpg, alembic, pydantic, pydantic-settings, redis, celery, openai, imap-tools, markdown-it-py, jinja2, itsdangerous, python-multipart, ruff, pytest, pytest-asyncio, httpx, factory-boy.
**Rationale**: Complies with PROJECT_SPEC.md Section 3 tech stack.

### 9. .env.example Configuration
**Date**: 2026-07-27
**Context**: .env.example defines all environment variables.
**Decision**: All required environment variables are present with proper defaults and comments.
**Rationale**: Complies with PROJECT_SPEC.md Section 5 which specifies all configuration keys.

### 10. Seed Demo Script
**Date**: 2026-07-27
**Context**: scripts/seed_demo.py creates demo data.
**Decision**: The script creates 200 fake contacts across different lifecycle stages and timezones, plus a demo segment.
**Rationale**: Complies with PROJECT_SPEC.md Phase 1 which specifies 200 fake contacts across stages/timezones and 1 demo segment.

### 1. Database Models

#### Decision: Unified Agent Model for Approvals
**Date**: 2026-07-27
**Context**: The project had separate `proposal.py` model and `agent.py` model with overlapping functionality.
**Decision**: Removed the separate `proposal.py` model and updated the optimizer service to use the `agent.py` Proposal model with `ApprovalStatus` enum.
**Rationale**: Reduces code duplication and provides a unified approach for handling approvals and proposals.

#### Decision: Updated Models __init__.py
**Date**: 2026-07-27
**Context**: The `app/models/__init__.py` was importing from the removed `proposal.py` file.
**Decision**: Removed the import of `Proposal`, `ProposalStatus`, and `ProposalType` from `app.models.proposal`.
**Rationale**: These are now imported from `app.models.agent`.

### 2. Service Layer

#### Decision: Optimizer Service Refactoring
**Date**: 2026-07-27
**Context**: The optimizer service was using the old `proposal.py` model structure.
**Decision**: Rewrote the optimizer service to use the `agent.py` Proposal model with the correct fields:
- `title`: Proposal title
- `rationale`: Explanation for the proposal
- `changes`: JSON object with suggested changes
- `status`: Approval status (PENDING, APPROVED, REJECTED)
**Rationale**: Aligns with the unified agent model structure.

#### Decision: Inbox Service Exception Handling
**Date**: 2026-07-27
**Context**: The inbox service had bare `except:` clauses which are linting violations.
**Decision**: Changed bare `except:` to `except Exception:`.
**Rationale**: Better exception handling practice.

### 3. Testing

#### Decision: Removed Duplicate Test Function
**Date**: 2026-07-27
**Context**: The `tests/test_basic.py` had duplicate `test_models_import` functions.
**Decision**: Removed the duplicate function definition.
**Rationale**: Clean test code without redundant tests.

### 4. Code Quality

#### Decision: Linting Issues
**Date**: 2026-07-27
**Context**: The project has many linting issues in alembic files and other pre-existing code.
**Decision**: Fixed linting issues in the core application files (optimizer.py, inbox.py, test_basic.py). Left alembic files and other pre-existing code as-is for now.
**Rationale**: Focus on fixing issues in the core application files first. Alembic files are auto-generated and should be reviewed separately.

## Pending Decisions

The following decisions are pending based on the PROJECT_SPEC.md:

### Phase 2 - Dashboard
- [ ] Implement dashboard views for campaign performance
- [ ] Implement dashboard views for contact analytics
- [ ] Implement dashboard views for inbox management

### Phase 3 - Missing Features
- [ ] Implement missing API endpoints
- [ ] Implement missing worker tasks
- [ ] Implement missing agent tools

## Notes

- All implementation decisions should be reviewed against the PROJECT_SPEC.md
- Any changes that affect the API or data models should be documented here
- Decisions that deviate from the spec should be clearly noted with rationale