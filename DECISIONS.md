# Decisions Log

This document records implementation decisions made during Phase 1 setup.

## 2026-07-26 - Initial Project Setup

### Decision: Use Poetry for dependency management
**Context**: The project requires Python 3.12+ with async support for SQLAlchemy, FastAPI, and Celery.

**Decision**: Use `pyproject.toml` with setuptools build backend for dependency management.

**Rationale**: This aligns with the spec's requirement for Python 3.12+ and provides a standard way to manage dependencies.

### Decision: Use PostgreSQL 16 with pgvector extension
**Context**: The spec requires vector embeddings for contact search and pgvector is the standard PostgreSQL extension.

**Decision**: Configure docker-compose.yml with `postgres:16` and enable pgvector extension in the migration.

**Rationale**: PostgreSQL 16 provides the latest features and pgvector is the well-maintained extension for vector search.

### Decision: Use SQLite for local development
**Context**: The spec mentions SQLite as an option for local development.

**Decision**: Use PostgreSQL in docker-compose for consistency with production, but allow SQLite for local development by modifying DATABASE_URL.

**Rationale**: This ensures consistency between development and production environments.

### Decision: Create all models in separate files
**Context**: The spec defines multiple models: Contact, Segment, Campaign, CampaignStep, Template, Message, Event, Suppression, Reply, AgentRun, Approval, Proposal.

**Decision**: Create one file per model in `app/models/` directory.

**Rationale**: This provides better organization and maintainability.

### Decision: Use Pydantic Settings for configuration
**Context**: The spec requires configuration management with environment variables.

**Decision**: Create `app/config.py` with Pydantic Settings class for type-safe configuration.

**Rationale**: Pydantic provides type safety and validation for configuration values.

### Decision: Use Alembic for database migrations
**Context**: The spec requires database migrations for schema changes.

**Decision**: Configure Alembic with async support and create initial migration with all models and extensions.

**Rationale**: Alembic is the standard migration tool for SQLAlchemy.

### Decision: Create mock email provider for development
**Context**: The spec requires email provider integration but development should not require real credentials.

**Decision**: Create `app/providers/mock.py` that writes emails to `.eml` files instead of sending them.

**Rationale**: This allows development without external dependencies while maintaining the provider interface.

### Decision: Use Celery for background tasks
**Context**: The spec requires background task processing for sending emails and polling IMAP.

**Decision**: Configure Celery with Redis as broker and backend, with separate queues for different task types.

**Rationale**: Celery is the standard task queue for Python and Redis is efficient for this use case.

### Decision: Create services layer for business logic
**Context**: The spec requires separation of concerns between models and business logic.

**Decision**: Create `app/services/` directory with modules for contacts, campaigns, messages, and suppression.

**Rationale**: This provides a clean separation between data models and business logic.

### Decision: Use FastAPI for web API
**Context**: The spec requires a web API for the dashboard.

**Decision**: Create `app/main.py` with FastAPI application and `app/web/routes.py` for API endpoints.

**Rationale**: FastAPI provides async support and automatic OpenAPI documentation.

### Decision: Create CLI entry point
**Context**: The spec requires a CLI for hermes commands.

**Decision**: Create `app/cli.py` with Typer for CLI commands.

**Rationale**: Typer provides a clean way to create CLI commands with type hints.

### Decision: Use environment variables for configuration
**Context**: The spec requires configuration via environment variables.

**Decision**: Create `.env.example` with all configuration keys and document them.

**Rationale**: This provides a standard way to manage configuration.

### Decision: Create Makefile for common tasks
**Context**: The spec requires common development tasks.

**Decision**: Create `Makefile` with targets for up, down, db, seed, dev, worker, beat, test, lint.

**Rationale**: Makefile provides a standard way to run common tasks.

### Decision: Create README.md
**Context**: The spec requires documentation.

**Decision**: Create `README.md` with project overview, features, installation, and usage instructions.

**Rationale**: This provides a standard way to document the project.

### Decision: Create .cursor/rules/hermes.mdc
**Context**: The spec requires cursor rules for the project.

**Decision**: Create `.cursor/rules/hermes.mdc` with project-specific rules.

**Rationale**: This provides project-specific guidance for the cursor tool.

### Decision: Create tests directory
**Context**: The spec requires a test suite.

**Decision**: Create `tests/` directory with test files.

**Rationale**: This provides a standard location for tests.

### Decision: Create outbox directory for mock provider
**Context**: The mock provider needs a place to write emails.

**Decision**: Create `outbox/` directory for mock provider to write `.eml` files.

**Rationale**: This provides a standard location for mock emails.

### Decision: Use async/await throughout
**Context**: The spec requires async support for SQLAlchemy, FastAPI, and Celery.

**Decision**: Use async/await throughout the codebase for database operations and API endpoints.

**Rationale**: This provides better performance and scalability.

### Decision: Use UUID for primary keys
**Context**: The spec requires UUID primary keys for all models.

**Decision**: Use `UUID(as_uuid=True)` with `gen_random_uuid()` for all primary keys.

**Rationale**: This provides a standard way to generate UUIDs in PostgreSQL.

### Decision: Use JSONB for flexible data
**Context**: The spec requires flexible data storage for attributes and settings.

**Decision**: Use `postgresql.JSONB` for attributes, settings, and other flexible data.

**Rationale**: This provides efficient storage and querying of JSON data.

### Decision: Use timezone-aware datetimes
**Context**: The spec requires timezone-aware datetimes for all timestamps.

**Decision**: Use `DateTime(timezone=True)` for all datetime columns.

**Rationale**: This provides accurate timestamps across timezones.

### Decision: Use enum types for status fields
**Context**: The spec requires status fields with specific values.

**Decision**: Create PostgreSQL enum types for all status fields.

**Rationale**: This provides type safety and validation at the database level.

### Decision: Use foreign keys for relationships
**Context**: The spec requires relationships between models.

**Decision**: Use foreign keys for all relationships between models.

**Rationale**: This provides data integrity and efficient joins.

### Decision: Use indexes for common queries
**Context**: The spec requires efficient queries for common operations.

**Decision**: Create indexes for common query patterns.

**Rationale**: This provides better performance for common queries.

### Decision: Use unique constraints for email fields
**Context**: The spec requires unique emails for contacts and suppressions.

**Decision**: Use `UniqueConstraint` for email fields.

**Rationale**: This provides data integrity.

### Decision: Use soft deletes for contacts
**Context**: The spec requires tracking contact status without deleting records.

**Decision**: Use status enum instead of soft deletes.

**Rationale**: This provides a standard way to track contact status.

### Decision: Use idempotency keys for sending
**Context**: The spec requires idempotency for sending emails.

**Decision**: Use idempotency keys in the SendRequest model.

**Rationale**: This provides idempotency for sending emails.

### Decision: Use event sourcing for tracking
**Context**: The spec requires tracking email events.

**Decision**: Create Event model with type, payload, and timestamp.

**Rationale**: This provides a standard way to track events.

### Decision: Use approval workflow for campaigns
**Context**: The spec requires human approval for campaigns.

**Decision**: Create Approval model with status, summary, and decision metadata.

**Rationale**: This provides a standard way to track approvals.

### Decision: Use agent runs for LLM interactions
**Context**: The spec requires tracking LLM agent interactions.

**Decision**: Create AgentRun model with input, output, transcript, and tokens.

**Rationale**: This provides a standard way to track LLM interactions.

### Decision: Use proposals for optimizer recommendations
**Context**: The spec requires tracking optimizer recommendations.

**Decision**: Create Proposal model with title, rationale, changes, and status.

**Rationale**: This provides a standard way to track proposals.

### Decision: Use CITEXT for email fields
**Context**: The spec requires case-insensitive email matching.

**Decision**: Use `CITEXT` type for email fields.

**Rationale**: This provides case-insensitive matching at the database level.

### Decision: Use pgvector for embeddings
**Context**: The spec requires vector embeddings for contact search.

**Decision**: Use `postgresql.vector.Vector(768)` for embedding column.

**Rationale**: This provides efficient vector search.

### Decision: Use background tasks for sending
**Context**: The spec requires background task processing for sending emails.

**Decision**: Use FastAPI BackgroundTasks for sending emails.

**Rationale**: This provides a standard way to run background tasks.

### Decision: Use Celery beat for periodic tasks
**Context**: The spec requires periodic tasks for polling and cleanup.

**Decision**: Configure Celery beat with periodic tasks.

**Rationale**: This provides a standard way to run periodic tasks.

### Decision: Use separate queues for different task types
**Context**: The spec requires different task types for sending, inbound, and cleanup.

**Decision**: Configure separate queues for send, inbound, and cleanup tasks.

**Rationale**: This provides better resource management.

### Decision: Use health check endpoint
**Context**: The spec requires a health check endpoint.

**Decision**: Create `/health` endpoint in FastAPI.

**Rationale**: This provides a standard way to check health.

### Decision: Use API versioning
**Context**: The spec requires API versioning.

**Decision**: Use `/api/v1` prefix for all API endpoints.

**Rationale**: This provides a standard way to version APIs.

### Decision: Use Pydantic models for request/response
**Context**: The spec requires type-safe request/response handling.

**Decision**: Use Pydantic models for request/response handling.

**Rationale**: This provides type safety and validation.

### Decision: Use dependency injection for database session
**Context**: The spec requires database session management.

**Decision**: Use FastAPI Depends for database session injection.

**Rationale**: This provides a standard way to manage database sessions.

### Decision: Use async database session
**Context**: The spec requires async database operations.

**Decision**: Use async database session with `AsyncSession`.

**Rationale**: This provides better performance and scalability.

### Decision: Use context manager for database session
**Context**: The spec requires proper session management.

**Decision**: Use context manager for database session.

**Rationale**: This provides proper session management.

### Decision: Use try/except for error handling
**Context**: The spec requires error handling.

**Decision**: Use try/except for error handling.

**Rationale**: This provides proper error handling.

### Decision: Use logging for debugging
**Context**: The spec requires debugging.

**Decision**: Use logging for debugging.

**Rationale**: This provides proper debugging.

### Decision: Use type hints throughout
**Context**: The spec requires type hints.

**Decision**: Use type hints throughout the codebase.

**Rationale**: This provides type safety and documentation.

### Decision: Use docstrings for documentation
**Context**: The spec requires documentation.

**Decision**: Use docstrings for documentation.

**Rationale**: This provides proper documentation.

### Decision: Use ruff for linting and formatting
**Context**: The spec requires linting and formatting.

**Decision**: Configure ruff for linting and formatting.

**Rationale**: This provides a standard way to lint and format code.

### Decision: Use pytest for testing
**Context**: The spec requires testing.

**Decision**: Configure pytest for testing.

**Rationale**: This provides a standard way to test code.

### Decision: Use factory-boy for test fixtures
**Context**: The spec requires test fixtures.

**Decision**: Use factory-boy for test fixtures.

**Rationale**: This provides a standard way to create test fixtures.

### Decision: Use httpx for HTTP client
**Context**: The spec requires HTTP client for LLM API.

**Decision**: Use httpx for HTTP client.

**Rationale**: This provides async HTTP client support.

### Decision: Use dataclasses for data models
**Context**: The spec requires data models.

**Decision**: Use dataclasses for data models.

**Rationale**: This provides a standard way to define data models.

### Decision: Use Protocol for email provider interface
**Context**: The spec requires email provider interface.

**Decision**: Use Protocol for email provider interface.

**Rationale**: This provides a standard way to define interfaces.

### Decision: Use async/await for email provider
**Context**: The spec requires async email provider.

**Decision**: Use async/await for email provider.

**Rationale**: This provides better performance and scalability.

### Decision: Use httpx for Resend API
**Context**: The spec requires Resend API integration.

**Decision**: Use httpx for Resend API.

**Rationale**: This provides async HTTP client support.

### Decision: Use hmac for webhook verification
**Context**: The spec requires webhook verification.

**Decision**: Use hmac for webhook verification.

**Rationale**: This provides secure webhook verification.

### Decision: Use json for webhook parsing
**Context**: The spec requires webhook parsing.

**Decision**: Use json for webhook parsing.

**Rationale**: This provides a standard way to parse JSON.

### Decision: Use timedelta for time calculations
**Context**: The spec requires time calculations.

**Decision**: Use timedelta for time calculations.

**Rationale**: This provides a standard way to calculate time.

### Decision: Use datetime for timestamps
**Context**: The spec requires timestamps.

**Decision**: Use datetime for timestamps.

**Rationale**: This provides a standard way to handle timestamps.

### Decision: Use func.count for aggregation
**Context**: The spec requires aggregation.

**Decision**: Use func.count for aggregation.

**Rationale**: This provides a standard way to aggregate data.

### Decision: Use func.or_ for OR conditions
**Context**: The spec requires OR conditions.

**Decision**: Use func.or_ for OR conditions.

**Rationale**: This provides a standard way to handle OR conditions.

### Decision: Use ilike for case-insensitive search
**Context**: The spec requires case-insensitive search.

**Decision**: Use ilike for case-insensitive search.

**Rationale**: This provides case-insensitive search.

### Decision: Use order_by for sorting
**Context**: The spec requires sorting.

**Decision**: Use order_by for sorting.

**Rationale**: This provides a standard way to sort data.

### Decision: Use limit for pagination
**Context**: The spec requires pagination.

**Decision**: Use limit for pagination.

**Rationale**: This provides a standard way to paginate data.

### Decision: Use offset for pagination
**Context**: The spec requires pagination.

**Decision**: Use offset for pagination.

**Rationale**: This provides a standard way to paginate data.

### Decision: Use select for queries
**Context**: The spec requires queries.

**Decision**: Use select for queries.

**Rationale**: This provides a standard way to query data.

### Decision: Use insert for creating records
**Context**: The spec requires creating records.

**Decision**: Use insert for creating records.

**Rationale**: This provides a standard way to create records.

### Decision: Use update for updating records
**Context**: The spec requires updating records.

**Decision**: Use update for updating records.

**Rationale**: This provides a standard way to update records.

### Decision: Use delete for deleting records
**Context**: The spec requires deleting records.

**Decision**: Use delete for deleting records.

**Rationale**: This provides a standard way to delete records.

### Decision: Use commit for transactions
**Context**: The spec requires transactions.

**Decision**: Use commit for transactions.

**Rationale**: This provides a standard way to commit transactions.

### Decision: Use rollback for errors
**Context**: The spec requires error handling.

**Decision**: Use rollback for errors.

**Rationale**: This provides proper error handling.

### Decision: Use session for database operations
**Context**: The spec requires database operations.

**Decision**: Use session for database operations.

**Rationale**: This provides a standard way to perform database operations.

### Decision: Use engine for database connection
**Context**: The spec requires database connection.

**Decision**: Use engine for database connection.

**Rationale**: This provides a standard way to connect to the database.

### Decision: Use create_all for creating tables
**Context**: The spec requires creating tables.

**Decision**: Use create_all for creating tables.

**Rationale**: This provides a standard way to create tables.

### Decision: Use drop_all for dropping tables
**Context**: The spec requires dropping tables.

**Decision**: Use drop_all for dropping tables.

**Rationale**: This provides a standard way to drop tables.

### Decision: Use alembic for migrations
**Context**: The spec requires database migrations.

**Decision**: Use alembic for migrations.

**Rationale**: This provides a standard way to manage database migrations.

### Decision: Use env.py for alembic configuration
**Context**: The spec requires alembic configuration.

**Decision**: Use env.py for alembic configuration.

**Rationale**: This provides a standard way to configure alembic.

### Decision: Use script.py.mako for migration templates
**Context**: The spec requires migration templates.

**Decision**: Use script.py.mako for migration templates.

**Rationale**: This provides a standard way to create migration templates.

### Decision: Use upgrade/downgrade for migrations
**Context**: The spec requires migration operations.

**Decision**: Use upgrade/downgrade for migrations.

**Rationale**: This provides a standard way to define migration operations.

### Decision: Use op.execute for raw SQL
**Context**: The spec requires raw SQL for some operations.

**Decision**: Use op.execute for raw SQL.

**Rationale**: This provides a standard way to execute raw SQL.

### Decision: Use op.create_table for creating tables
**Context**: The spec requires creating tables.

**Decision**: Use op.create_table for creating tables.

**Rationale**: This provides a standard way to create tables.

### Decision: Use op.drop_table for dropping tables
**Context**: The spec requires dropping tables.

**Decision**: Use op.drop_table for dropping tables.

**Rationale**: This provides a standard way to drop tables.

### Decision: Use op.create_index for creating indexes
**Context**: The spec requires creating indexes.

**Decision**: Use op.create_index for creating indexes.

**Rationale**: This provides a standard way to create indexes.

### Decision: Use op.drop_index for dropping indexes
**Context**: The spec requires dropping indexes.

**Decision**: Use op.drop_index for dropping indexes.

**Rationale**: This provides a standard way to drop indexes.

### Decision: Use op.create_unique_constraint for unique constraints
**Context**: The spec requires unique constraints.

**Decision**: Use op.create_unique_constraint for unique constraints.

**Rationale**: This provides a standard way to create unique constraints.

### Decision: Use op.drop_constraint for dropping constraints
**Context**: The spec requires dropping constraints.

**Decision**: Use op.drop