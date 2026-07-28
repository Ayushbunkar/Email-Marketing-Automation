# IMAP to Brevo Inbound Webhook Migration Plan

## Current IMAP Architecture Analysis

### Files with IMAP References:
1. **Configuration**: `.env.example`, `app/config.py`
2. **Provider**: `app/providers/inbound_imap.py`
3. **Models**: `app/models/reply.py` (imap_uid field), `app/models/inbox.py`
4. **Services**: `app/services/inbox.py`
5. **Workers**: `app/workers/tasks.py`, `app/workers/config.py`
6. **Dependencies**: `pyproject.toml` (imap-tools)
7. **Documentation**: `README.md`, `PROJECT_SPEC.md`, `DECISIONS.md`
8. **Tests**: `tests/test_basic.py`
9. **Migrations**: `alembic/versions/001_initial_migration.py`, `alembic_local/versions/001_initial_migration.py`

### Current Flow:
1. Celery beat task `poll_inbound_emails` runs every 120 seconds
2. Uses `InboundIMAPProvider` to poll IMAP server
3. Processes emails through `process_inbound_email`
4. Stores replies with `imap_uid` for deduplication
5. Creates inbox messages and threads

## Migration Steps

### Step 1: Remove IMAP Components
- [ ] Delete `app/providers/inbound_imap.py`
- [ ] Remove IMAP configuration from `app/config.py`
- [ ] Remove IMAP environment variables from `.env.example`
- [ ] Remove IMAP dependencies from `pyproject.toml`
- [ ] Remove IMAP polling from `app/workers/tasks.py` and `app/workers/config.py`
- [ ] Remove IMAP references from services and models

### Step 2: Update Brevo Provider for Inbound Webhooks
- [ ] Enhance `app/providers/brevo.py` with inbound webhook support
- [ ] Add webhook verification and payload parsing for inbound emails
- [ ] Implement deduplication using Brevo's message ID

### Step 3: Create Brevo Inbound Webhook Endpoint
- [ ] Add `POST /webhooks/brevo/inbound` endpoint in `app/web/routes.py`
- [ ] Implement webhook verification, validation, and error handling
- [ ] Add structured logging and idempotent processing

### Step 4: Update Database Models
- [ ] Remove `imap_uid` field from `Reply` model
- [ ] Add Brevo-specific fields (brevo_message_id, etc.)
- [ ] Create Alembic migration for schema changes

### Step 5: Update Inbound Processing Services
- [ ] Modify `app/services/inbox.py` to handle Brevo webhook payloads
- [ ] Update reply processing to work with webhook data
- [ ] Remove IMAP-specific logic

### Step 6: Update Reply Classification and Draft Generation
- [ ] Ensure AI classification works with webhook-processed replies
- [ ] Verify approval workflow remains unchanged

### Step 7: Update Tests
- [ ] Replace IMAP tests with Brevo webhook tests
- [ ] Add tests for webhook verification, payload parsing, and reply processing

### Step 8: Update Documentation
- [ ] Remove IMAP references from README.md
- [ ] Update PROJECT_SPEC.md to reflect Brevo webhook architecture
- [ ] Update environment variable documentation

### Step 9: Environment Cleanup
- [ ] Remove all IMAP-related environment variables
- [ ] Ensure only Brevo configuration remains

## Breaking Changes
- IMAP polling completely removed
- Inbound email processing now webhook-based only
- Reply deduplication now uses Brevo message IDs instead of IMAP UIDs
- Celery beat schedule no longer includes IMAP polling

## Production Readiness Checklist
- [ ] All IMAP code removed
- [ ] Brevo webhook endpoint implemented and tested
- [ ] Inbound email processing verified end-to-end
- [ ] Reply classification and approval workflow working
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Migration guide created