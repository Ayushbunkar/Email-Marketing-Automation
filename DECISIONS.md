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

## Phase 2 - IMAP to Brevo Migration (IN PROGRESS)

### 1. IMAP Architecture Removal
**Date**: 2026-07-28
**Context**: The original architecture used IMAP polling for inbound email processing, which required periodic polling of mailboxes and had reliability issues.
**Decision**: Completely remove IMAP architecture and replace with Brevo inbound webhooks.
**Rationale**: Brevo webhooks provide real-time, event-driven processing that is more reliable, scalable, and reduces infrastructure complexity. This aligns with the production requirement to use Brevo as the single source of truth for all email communication.

### 2. Brevo Provider Enhancement
**Date**: 2026-07-28
**Context**: The Brevo provider only supported outbound email sending.
**Decision**: Enhanced Brevo provider with inbound webhook verification and payload parsing capabilities.
**Rationale**: Centralizes all Brevo-related functionality in a single provider class, making it easier to maintain and extend.

### 3. Webhook Endpoint Implementation
**Date**: 2026-07-28
**Context**: Need to handle Brevo inbound email webhooks securely and reliably.
**Decision**: Implemented `/webhooks/brevo/inbound` endpoint with signature verification, payload validation, error handling, and idempotent processing.
**Rationale**: Production-ready webhook handling that prevents unauthorized access and ensures reliable processing.

### 4. Database Schema Changes
**Date**: 2026-07-28
**Context**: The Reply model had an `imap_uid` field for deduplication.
**Decision**: Replaced `imap_uid` with `brevo_message_id` field.
**Rationale**: Maintains deduplication capability while using Brevo's message IDs instead of IMAP UIDs.

### 5. Configuration Updates
**Date**: 2026-07-28
**Context**: Environment variables and configuration needed to support Brevo inbound webhooks.
**Decision**: Added `BREVO_INBOUND_WEBHOOK_SECRET` configuration and removed all IMAP-related environment variables.
**Rationale**: Provides secure webhook verification while eliminating unused IMAP configuration.

### 6. Worker Task Updates
**Date**: 2026-07-28
**Context**: Celery beat schedule included IMAP polling tasks.
**Decision**: Removed `poll_inbound_emails` task from beat schedule and worker configuration.
**Rationale**: Inbound email processing is now event-driven via webhooks, eliminating the need for periodic polling.

### 7. Dependency Management
**Date**: 2026-07-28
**Context**: The project had `imap-tools` dependency that is no longer needed.
**Decision**: Removed `imap-tools` from pyproject.toml dependencies.
**Rationale**: Reduces project dependencies and eliminates unused code.

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