HERMES — Autonomous Email Marketing Agent
Complete Build Specification (v1.0)
To the coding agent (Cursor): This document is the single source of truth for building Hermes, an autonomous email-marketing agent powered by open-weight Hermes LLMs (Nous Research). Read this entire document before writing any code. Then execute the milestones in Section 16 strictly in order, one phase at a time. At the end of each phase, run the acceptance checks for that phase and report results before continuing. Do not skip guardrail requirements (Section 14) — they are hard constraints, not suggestions. When a decision is not specified here, choose the simplest option consistent with the stated principles and note the decision in DECISIONS.md.
1. Product overview
Hermes is a self-hosted system that plans, writes, schedules, sends, tracks, and optimizes email marketing campaigns, and maintains its own lightweight CRM — end to end. A human operator supervises through a web dashboard and approves anything that touches a real inbox.
What the agent does autonomously:
Maintains a contact database (import, dedupe, enrich attributes, lifecycle stages).
Builds audience segments from natural-language goals.
Plans campaigns (one-shot blasts, multi-step drip sequences, event-triggered sends).
Writes subject lines, preheaders, and email bodies, including A/B variants and per-contact personalization.
Schedules sends respecting timezones, quiet hours, and volume caps.
Ingests delivery events (delivered / open / click / bounce / complaint / unsubscribe).
Reads and classifies replies, drafts responses, updates the CRM accordingly.
Reviews weekly metrics and files improvement proposals (new tests, segment changes, send-time changes).
What only deterministic code does (never the LLM):
Actually dispatching email through the provider.
Enforcing the suppression list, unsubscribes, bounces, and complaints.
Enforcing volume caps, frequency caps, and quiet hours.
The approval gate.
What only the human does:
Approves campaigns, send batches, outbound reply drafts, and optimizer proposals.
Owns DNS / deliverability setup (Section 16, Phase 0 checklist).
2. Core principles (apply to every file you write)
LLM decides, code executes. Every agent tool is a thin, validated wrapper. The model can request a send; only the dispatcher, after passing all guardrails and an approval record, can perform one.
Suppression is sacred. No code path may create or send a message to a suppressed or unsubscribed address. This is enforced at three layers: DB constraint checks in the dispatcher query, a final pre-send assertion, and webhook handlers that suppress synchronously.
Everything is auditable. Every agent run, tool call, approval, and send is persisted. No fire-and-forget.
Runs offline by default. With the mock email provider and no API keys, the entire system must work end-to-end in dev (sends are written to the DB and a local .eml folder instead of the network).
Boring technology. Plain Python, Postgres, Redis. No microservices. One repo, one deployable backend, one worker.
Small, typed, tested. Pydantic models at every boundary. Type hints everywhere. Tests for every guardrail.
3. Tech stack (pinned — do not substitute without noting in DECISIONS.md)
Concern	Choice
Language	Python 3.12
Web framework	FastAPI + Uvicorn
ORM / migrations	SQLAlchemy 2.x (declarative, async) + Alembic
Validation	Pydantic v2
Database	PostgreSQL 16 with citext and pgvector extensions
Queue / scheduler	Celery 5 + Redis 7 (celery beat for cron)
LLM access	openai Python SDK pointed at an OpenAI-compatible endpoint (OpenRouter, Nous API, or local vLLM). No LangChain.
Models	Planner: Hermes 4 (70B or 405B, hosted). Worker: Hermes 4.3 36B or Hermes 4 14B (hosted or local). Configured by env; never hardcode model names outside config.py.
Email provider	Pluggable EmailProvider interface. Drivers: resend (default real driver) and mock (dev/test). Design so an ses driver can be added later without touching callers.
Inbound replies	IMAP polling via imap-tools (provider-agnostic).
Dashboard	Server-rendered: FastAPI + Jinja2 + HTMX + Tailwind (CDN build, no Node toolchain).
Templating (email)	Jinja2 for merge fields; markdown-it-py to render agent-written Markdown bodies to HTML inside a fixed base layout.
Auth (dashboard)	Single operator: HTTP session with password from env (OPERATOR_PASSWORD). CSRF on mutating forms.
Tests	pytest + pytest-asyncio + httpx test client; factory fixtures.
Lint/format	ruff (lint + format).
Dev orchestration	Makefile. Direct connection to cloud services (Supabase, Upstash). App runs locally with Python.
4. Repository layout
Create exactly this structure (files may be added within these packages, not outside them):
hermes/
├── README.md
├── DECISIONS.md
├── PROJECT_SPEC.md            # this document
├── Makefile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .cursor/rules/hermes.mdc   # Section 18
├── alembic/                   # migrations
├── app/
│   ├── main.py                # FastAPI app factory, routers, startup
│   ├── config.py              # pydantic-settings; ALL env access lives here
│   ├── db.py                  # engine, session, base
│   ├── models/                # SQLAlchemy models (one module per aggregate)
│   │   ├── contact.py  segment.py  campaign.py  template.py
│   │   ├── message.py  event.py  suppression.py  reply.py
│   │   └── agent.py           # agent_runs, approvals, proposals
│   ├── schemas/               # Pydantic I/O schemas mirroring models
│   ├── services/
│   │   ├── contacts.py        # CRM operations, import, dedupe
│   │   ├── segments.py        # rule-tree evaluation → SQL
│   │   ├── campaigns.py       # lifecycle state machine
│   │   ├── templates.py       # render, merge fields, html build
│   │   ├── suppression.py     # THE suppression engine
│   │   ├── dispatcher.py      # the ONLY module that calls provider.send
│   │   ├── analytics.py       # rollups, health metrics
│   │   └── approvals.py
│   ├── providers/
│   │   ├── base.py            # EmailProvider protocol + dataclasses
│   │   ├── resend.py
│   │   ├── mock.py
│   │   └── inbound_imap.py
│   ├── llm/
│   │   ├── client.py          # OpenAI-compatible client, retry, usage log
│   │   ├── router.py          # planner vs worker model selection
│   │   └── prompts/           # system prompts as .md files, loaded at runtime
│   ├── agent/
│   │   ├── loop.py            # generic tool-calling loop
│   │   ├── registry.py        # tool registration + JSON schema export
│   │   ├── tools/             # one module per tool group (Section 8)
│   │   └── runs.py            # persistence of agent_runs
│   ├── workers/
│   │   ├── celery_app.py
│   │   ├── tasks_dispatch.py  # send queue processing
│   │   ├── tasks_sequences.py # drip step advancement
│   │   ├── tasks_inbound.py   # IMAP poll + reply pipeline
│   │   └── tasks_optimizer.py # weekly analyst run
│   ├── web/
│   │   ├── routes/            # dashboard + JSON API + webhooks
│   │   └── templates/         # Jinja2 (base, dashboard, campaigns, approvals, contacts, replies, settings)
│   └── cli.py                 # `hermes` Typer CLI: chat, seed, run-agent, etc.
├── tests/
└── scripts/seed_demo.py
5. Configuration (app/config.py + .env.example)
All settings via pydantic-settings. Generate .env.example with every key below, safe defaults, and a comment per key.
# --- Core ---
APP_ENV=dev                        # dev | prod
DATABASE_URL=postgresql+asyncpg://hermes:hermes@localhost:5432/hermes
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me
OPERATOR_PASSWORD=change-me
BASE_URL=http://localhost:8000     # used to build unsubscribe/click links

# --- LLM ---
LLM_BASE_URL=https://openrouter.ai/api/v1   # or http://localhost:8001/v1 for vLLM
LLM_API_KEY=
PLANNER_MODEL=nousresearch/hermes-4-405b    # verify exact slug on the chosen host
WORKER_MODEL=nousresearch/hermes-4-70b      # or a local hermes-4.3-36b served by vLLM
LLM_MAX_TOOL_ITERATIONS=12
LLM_TIMEOUT_SECONDS=120

# --- Email provider ---
EMAIL_PROVIDER=mock                # mock | resend
RESEND_API_KEY=
RESEND_WEBHOOK_SECRET=             # svix signature verification
FROM_NAME=Hermes
FROM_EMAIL=hello@mail.example.com  # must be on the authenticated sending subdomain
REPLY_TO_EMAIL=replies@mail.example.com
COMPANY_POSTAL_ADDRESS="Acme Pvt Ltd, 1 Example Road, Lucknow, UP 226001, India"

# --- Inbound (IMAP) ---
IMAP_HOST=  IMAP_PORT=993  IMAP_USER=  IMAP_PASSWORD=  IMAP_FOLDER=INBOX
INBOUND_POLL_SECONDS=120

# --- Guardrails (hard caps; dispatcher reads these) ---
MAX_SENDS_PER_DAY=500
MAX_SENDS_PER_HOUR=100
MAX_EMAILS_PER_CONTACT_PER_WEEK=3
QUIET_HOURS_START=21               # contact-local time, 24h
QUIET_HOURS_END=8
AUTO_PAUSE_BOUNCE_RATE=0.02        # pause all sending above 2% hard bounces (rolling 24h)
AUTO_PAUSE_COMPLAINT_RATE=0.001    # pause above 0.1% complaints
REQUIRE_APPROVAL_FOR_SENDS=true    # never default to false
config.py must expose a single settings object; no other module reads os.environ directly.
6. Database schema
Implement as SQLAlchemy models + one initial Alembic migration. Enable extensions citext and vector in the migration. All tables get id UUID PK default gen_random_uuid(), created_at, updated_at. Reference SQL (authoritative for names, enums, and constraints):
CREATE TYPE lifecycle_stage AS ENUM ('lead','subscriber','engaged','customer','churned');
CREATE TYPE contact_status  AS ENUM ('active','unsubscribed','bounced','complained','suppressed');
CREATE TYPE campaign_status AS ENUM ('draft','pending_approval','approved','scheduled','running','paused','completed','archived');
CREATE TYPE campaign_type   AS ENUM ('one_shot','sequence','trigger');
CREATE TYPE message_status  AS ENUM ('queued','pending_approval','approved','sending','sent','delivered','bounced','failed','suppressed','canceled');
CREATE TYPE event_type      AS ENUM ('delivered','open','click','bounce_hard','bounce_soft','complaint','unsubscribe','reply');
CREATE TYPE suppression_reason AS ENUM ('unsubscribe','hard_bounce','complaint','manual','legal_request');
CREATE TYPE reply_class     AS ENUM ('interested','question','not_interested','unsubscribe_request','out_of_office','auto_reply','other');
CREATE TYPE agent_run_kind  AS ENUM ('campaign_planner','copywriter','inbox','optimizer','adhoc_chat');
CREATE TYPE approval_status AS ENUM ('pending','approved','rejected');
CREATE TYPE approval_subject AS ENUM ('campaign','reply_draft','proposal');

contacts(
  email CITEXT UNIQUE NOT NULL,
  first_name TEXT, last_name TEXT, company TEXT,
  attributes JSONB NOT NULL DEFAULT '{}',
  lifecycle_stage lifecycle_stage NOT NULL DEFAULT 'lead',
  status contact_status NOT NULL DEFAULT 'active',
  consent_source TEXT,            -- e.g. 'signup_form', 'import:2026-07-csv'
  consent_at TIMESTAMPTZ,
  timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
  last_emailed_at TIMESTAMPTZ,
  embedding VECTOR(768)           -- optional; for similarity segments later
)

segments(name TEXT NOT NULL, description TEXT,
  definition JSONB NOT NULL,      -- rule tree, see services/segments.py below
  is_dynamic BOOL NOT NULL DEFAULT true,
  created_by TEXT NOT NULL)       -- 'human' | 'agent'

campaigns(name TEXT NOT NULL, goal TEXT NOT NULL,
  type campaign_type NOT NULL, status campaign_status NOT NULL DEFAULT 'draft',
  segment_id UUID REFERENCES segments,
  settings JSONB NOT NULL DEFAULT '{}',   -- overrides: caps, send window, ab_split
  scheduled_at TIMESTAMPTZ, started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ,
  created_by TEXT NOT NULL, approved_by TEXT, approved_at TIMESTAMPTZ)

campaign_steps(campaign_id UUID NOT NULL REFERENCES campaigns ON DELETE CASCADE,
  step_index INT NOT NULL, delay_hours INT NOT NULL DEFAULT 0,
  send_condition JSONB NOT NULL DEFAULT '{}',  -- e.g. {"skip_if":"replied"}
  UNIQUE(campaign_id, step_index))

templates(campaign_id UUID REFERENCES campaigns ON DELETE CASCADE,
  step_id UUID REFERENCES campaign_steps ON DELETE CASCADE,
  name TEXT, subject TEXT NOT NULL, preheader TEXT,
  body_markdown TEXT NOT NULL,    -- agent writes markdown; renderer builds HTML+text
  variant_label TEXT NOT NULL DEFAULT 'A',
  variables JSONB NOT NULL DEFAULT '[]')  -- merge fields used, for validation

messages(campaign_id UUID REFERENCES campaigns, step_id UUID REFERENCES campaign_steps,
  contact_id UUID NOT NULL REFERENCES contacts,
  template_id UUID REFERENCES templates,
  status message_status NOT NULL DEFAULT 'queued',
  provider_message_id TEXT UNIQUE,
  scheduled_for TIMESTAMPTZ NOT NULL,
  sent_at TIMESTAMPTZ, error TEXT,
  UNIQUE(campaign_id, step_id, contact_id))   -- idempotency: one send per contact per step

events(message_id UUID REFERENCES messages, contact_id UUID REFERENCES contacts,
  type event_type NOT NULL, payload JSONB NOT NULL DEFAULT '{}',
  provider_event_id TEXT UNIQUE,              -- webhook dedupe
  occurred_at TIMESTAMPTZ NOT NULL)

suppressions(email CITEXT UNIQUE NOT NULL,
  reason suppression_reason NOT NULL, source TEXT NOT NULL)

replies(contact_id UUID REFERENCES contacts, message_id UUID REFERENCES messages,
  from_email CITEXT NOT NULL, subject TEXT, body_text TEXT NOT NULL,
  classification reply_class, confidence REAL,
  draft_response TEXT, handled BOOL NOT NULL DEFAULT false,
  received_at TIMESTAMPTZ NOT NULL, imap_uid TEXT UNIQUE)

agent_runs(kind agent_run_kind NOT NULL, status TEXT NOT NULL,
  model TEXT NOT NULL, input JSONB NOT NULL, output JSONB,
  transcript JSONB NOT NULL DEFAULT '[]',     -- full message list incl. tool calls
  tokens_in INT DEFAULT 0, tokens_out INT DEFAULT 0,
  started_at TIMESTAMPTZ NOT NULL, finished_at TIMESTAMPTZ, error TEXT)

approvals(subject_type approval_subject NOT NULL, subject_id UUID NOT NULL,
  status approval_status NOT NULL DEFAULT 'pending',
  summary TEXT NOT NULL,                      -- human-readable "what am I approving"
  decided_by TEXT, decided_at TIMESTAMPTZ, notes TEXT,
  UNIQUE(subject_type, subject_id) WHERE status = 'pending')  -- partial unique index

proposals(title TEXT NOT NULL, rationale TEXT NOT NULL,
  changes JSONB NOT NULL,                     -- structured suggested actions
  status approval_status NOT NULL DEFAULT 'pending',
  source_run_id UUID REFERENCES agent_runs)
Indexes: contacts(status), contacts(lifecycle_stage), messages(status, scheduled_for), events(contact_id, type, occurred_at), replies(handled).
Segment definition format (segments.definition): a JSON rule tree the service compiles to SQL. Support: {"all":[...]}, {"any":[...]}, and leaf conditions {"field":"lifecycle_stage","op":"eq","value":"lead"}, ops eq, neq, in, contains, gt, lt, exists, days_since_gt/lt over columns and attributes.* JSONB paths, plus behavioral leaves {"event":"open","within_days":30,"min_count":1}. Reject unknown ops. Always implicitly AND: status = 'active' AND email NOT IN suppressions — segments can never surface suppressed contacts, even if the rule tree asks.
7. Provider layer (app/providers/)
base.py defines the contract:
class SendRequest(BaseModel):
    to_email: str; to_name: str | None
    from_email: str; from_name: str; reply_to: str
    subject: str; html: str; text: str
    headers: dict[str, str]        # must include List-Unsubscribe + List-Unsubscribe-Post
    idempotency_key: str           # = message.id

class SendResult(BaseModel):
    provider_message_id: str; accepted: bool; error: str | None

class EmailProvider(Protocol):
    async def send(self, req: SendRequest) -> SendResult: ...
    def verify_webhook(self, headers, body) -> bool: ...
    def parse_webhook(self, body) -> list[NormalizedEvent]: ...
mock.py: writes an .eml file to ./outbox/, returns a fake id, and exposes a test helper to synthesize webhook events (used heavily in tests and demo mode).
resend.py: real HTTP calls; verify webhooks with the svix signature; map Resend event names → event_type enum (email.delivered→delivered, email.opened→open, email.clicked→click, email.bounced→bounce_hard/soft by bounce subtype, email.complained→complaint).
inbound_imap.py: poll IMAP, fetch unseen, parse (from, subject, text body, In-Reply-To header to link message_id), store as replies with imap_uid dedupe, mark seen. Strip quoted history with a simple heuristic (On ... wrote: split).
Webhook endpoint (POST /webhooks/email): verify signature → dedupe on provider_event_id → insert event → synchronously apply consequences in the same transaction: bounce_hard → suppress(email, hard_bounce) + contact.status=bounced; complaint → suppress + status=complained; unsubscribe → suppress + status=unsubscribed. Also handle first-party unsubscribe: GET/POST /u/{token} (signed token embedding contact_id) → same suppression path + a plain confirmation page. Every outgoing email body gets the unsubscribe link and COMPANY_POSTAL_ADDRESS injected by the base layout — templates cannot omit them.
8. LLM layer + agent core
8.1 Client (llm/client.py)
Use the openai SDK with base_url=settings.LLM_BASE_URL. Expose async def complete(messages, tools=None, model=..., temperature=...) -> ChatResponse. Retries (3, exponential) on 429/5xx. Log usage tokens into the active agent_run. Both OpenRouter and vLLM speak the OpenAI schema; when self-hosting, run vLLM with --enable-auto-tool-choice --tool-call-parser hermes so Hermes's native <tool_call> output arrives as standard tool_calls. Do not hand-parse XML; if a provider returns raw <tool_call> text, fix the serving config instead.
8.2 Model routing (llm/router.py)
PLANNER_MODEL for: campaign planning, copywriting, optimizer runs, operator chat. WORKER_MODEL for: reply classification, per-contact personalization, segment-rule drafting. Single function pick_model(run_kind) -> str.
8.3 Agent loop (agent/loop.py)
Generic, model-agnostic loop:
run = create_agent_run(kind, input)
messages = [system_prompt(kind), *context_messages]
for i in range(settings.LLM_MAX_TOOL_ITERATIONS):
    resp = complete(messages, tools=registry.schemas(kind))
    persist assistant message to run.transcript
    if resp.tool_calls:
        for call in resp.tool_calls:
            result = registry.execute(call, actor="agent", run=run)   # validated, try/except
            append tool result message
    else:
        finalize(run, output=resp.content); break
else: finalize(run, error="max_iterations")
Rules: every tool executes inside try/except and returns a JSON-serializable result or {"error": ...} — the loop never crashes on a bad tool call; it feeds the error back to the model. Registry validates arguments against the tool's Pydantic schema before execution.
8.4 Tool registry (agent/registry.py + agent/tools/)
Tools are declared with a decorator that captures name, description, Pydantic input model (auto-exported to JSON Schema), and an allowlist of run kinds. Implement exactly this toolset:
Tool	Args (summary)	Behavior / guardrail notes
search_contacts	filters: stage, status, text query, limit≤50	read-only; never returns suppressed contacts' emails to the model beyond count
upsert_contact	email, names, attributes, stage, consent_source	citext dedupe; cannot change status of suppressed contacts
preview_segment	definition (rule tree)	validates tree, returns count + 5 sample contacts (names only)
create_segment	name, description, definition	persists after validation
draft_campaign	name, goal, type, segment_id, steps[{delay_hours, send_condition}]	creates campaign in draft + steps; no templates yet
write_template	campaign_id, step_index, subject, preheader, body_markdown, variant_label	renders a preview to catch Jinja errors; validates merge fields against contacts columns/attributes; stores
submit_for_approval	campaign_id, proposed_schedule_at	recomputes audience count, builds human summary ("X emails to segment Y starting Z"), sets pending_approval, creates approvals row. Never sends.
pause_campaign	campaign_id	allowed anytime; sets paused, cancels queued messages
get_campaign_metrics	campaign_id or date range	sends, delivery/open/click/bounce/complaint/unsub rates, per-variant split
get_account_health	—	rolling 24h/7d bounce+complaint rates, cap utilization, paused?
list_unhandled_replies	limit	returns reply id, from, subject, body (truncated 2k chars)
submit_reply_handling	reply_id, classification, confidence, draft_response?, stage_update?	for unsubscribe_request: suppression applied by code immediately; drafts for interested/question create reply_draft approvals; never auto-sends
update_contact_stage	contact_id, stage, reason	audited
send_test_email	campaign_id, step_index, variant	sends rendered template only to settings operator email, bypassing approval (still logged)
create_proposal	title, rationale, changes[]	optimizer output; changes are structured {action, target, params}
8.5 System prompts (llm/prompts/*.md)
Write four prompts. Shared preamble for all: identity ("You are Hermes, the email-marketing agent for {company}"), today's date, account health snapshot, the non-negotiables ("You cannot send email. You draft and submit for human approval. Never attempt to contact suppressed or unsubscribed addresses. Never invent metrics — use tools."), and brand voice pulled from a settings/brand.md file the operator edits in the dashboard.
campaign_planner.md: think stepwise — clarify goal → inspect audience with tools → propose structure → create draft → write templates → send_test_email → submit_for_approval with reasoning in the summary.
inbox.md: for each unhandled reply, classify conservatively; when in doubt use other; anything resembling "stop/remove/unsubscribe" in any language → unsubscribe_request; keep drafts short, plain, human.
optimizer.md: read metrics; propose at most 3 changes/week; every proposal must cite the metric that motivates it.
chat.md: operator Q&A over the CRM with read tools.
9. Campaign engine
9.1 Campaign lifecycle (state machine in services/campaigns.py)
draft → pending_approval → approved → scheduled → running → completed, with paused reachable from approved/scheduled/running and rejected returning to draft. Only approvals decisions move pending_approval → approved/draft. Enforce transitions in one function; raise on illegal moves.
9.2 Materialization
On approval + schedule: expand the segment (dynamic segments evaluate at each step's send time, not at approval), create messages rows for step 0 with scheduled_for computed per contact: campaign start, shifted into the contact's timezone send window, respecting quiet hours (if the slot falls inside quiet hours, move to next window start), jittered ±15 min to avoid burst patterns.
9.3 Dispatcher (workers/tasks_dispatch.py + services/dispatcher.py)
Celery beat runs dispatch_due_messages every minute:
Global circuit breaker: if get_account_health() breaches AUTO_PAUSE_* thresholds → pause all running campaigns, create an operator notification, stop.
Select due messages FOR UPDATE SKIP LOCKED where status='approved' AND scheduled_for<=now, joined to contacts with status='active' AND email NOT IN suppressions, honoring MAX_SENDS_PER_HOUR/DAY (count sent in window) and MAX_EMAILS_PER_CONTACT_PER_WEEK (skip+reschedule if exceeded).
Render template (subject/preheader/body) with contact merge fields; wrap in base HTML layout that ALWAYS appends unsubscribe link + postal address; generate text part.
Final assertion immediately before provider.send: contact not suppressed (re-check). Then send with idempotency_key=message.id, set sent/failed, update contacts.last_emailed_at.
Any exception → message failed with error, never retried more than twice, never blocks the batch.
9.4 Sequences & triggers
advance_sequences (beat, every 10 min): for running sequence campaigns, for each contact who completed step N at time T, create the step N+1 message at T + delay_hours unless send_condition skips it (supported: skip_if: replied | clicked | opened, evaluated from events/replies). Trigger campaigns: services/campaigns.enroll(contact, campaign) is called from code hooks (e.g. contact created with stage=subscriber) — the LLM cannot enroll directly.
9.5 A/B variants
If a step has multiple variant_labels, split the audience deterministically (hash(contact_id) mod). get_campaign_metrics reports per-variant. (Auto-winner selection is a v2 proposal the optimizer can file, not automatic.)
10. Inbox pipeline
Brevo inbound webhook endpoint: POST /webhooks/brevo/inbound → verify signature → parse payload → process_brevo_inbound_email() → create reply record → AI classification → draft generation (if needed) → create approval (if response needed). Code post-processing of submit_reply_handling:
unsubscribe_request → suppress + status change in code, instantly, mark handled, no draft needed.
out_of_office / auto_reply → mark handled, optionally reschedule next sequence step +3 days.
interested / question → store draft_response, create reply_draft approval; dashboard shows thread + draft; on operator approval, dispatcher sends the reply (from REPLY_TO mailbox, threading headers In-Reply-To/References set).
not_interested → mark handled, stage→churned, stop sequences for that contact.
11. Analytics & optimizer
services/analytics.py: nightly rollup task computing per-campaign and account-level daily stats into a stats_daily table (sends, delivered, opens, clicks, bounces, complaints, unsubs, replies, rates). get_account_health reads live from events for the rolling windows (fast queries with the indexes above).
Weekly beat (Mon 09:00 IST): optimizer agent run with metrics + proposals tools. Output = proposals rows rendered in the dashboard with approve/reject. Approving a proposal does not auto-execute it in v1; it creates a checklist item for the operator (v2 may wire safe actions).
12. Dashboard (server-rendered, HTMX)
Pages (all behind operator login):
Overview: account health, caps utilization, sends today, pending approvals count, recent agent runs.
Approvals (the heart): queue of pending items. Campaign approvals show goal, audience count, schedule, full rendered preview of every template/variant, and the agent's summary; buttons Approve / Reject-with-note. Reply drafts show the thread and editable draft (operator can edit text before approving).
Campaigns: list + detail (status, steps, variants, live metrics, pause button).
Contacts: search/filter, detail with timeline (messages, events, replies), manual suppress button, CSV import (maps columns, requires choosing a consent_source).
Replies: inbox view, filters by classification/handled.
Chat: operator ↔️ agent (adhoc_chat runs) with visible tool-call trace.
Settings: brand voice editor (brand.md), guardrail values (read-only display of env), provider status.
Keep JS to HTMX attributes + a 20-line app.js. Tailwind via CDN. No build step.
13. HTTP API surface (JSON, same FastAPI app, prefix /api)
POST /api/agent/runs {kind, input} (fires a run async, returns run id) · GET /api/agent/runs/{id} · GET/POST /api/contacts · POST /api/contacts/import · GET /api/campaigns POST /api/campaigns/{id}/pause · GET/POST /api/approvals/{id}/decision · GET /api/metrics/health. Webhooks: POST /webhooks/email. Unsubscribe: GET+POST /u/{token}. All mutating dashboard forms CSRF-protected; API uses the session or a bearer SECRET_KEY (dev).
14. Compliance & guardrails — HARD REQUIREMENTS (test each one)
A suppressed/unsubscribed/bounced/complained address can never receive email: enforced in segment compilation, dispatcher query, and final pre-send assertion. Test all three independently.
Unsubscribe (webhook, reply-intent, or /u/{token}) takes effect in the same transaction it's observed. No queue delay.
Every outbound email contains a working one-click unsubscribe link, List-Unsubscribe + List-Unsubscribe-Post headers, and the postal address.
REQUIRE_APPROVAL_FOR_SENDS cannot be bypassed by any tool; there is no code path from an agent tool to provider.send except send_test_email → operator's own address.
Volume caps, frequency caps, and quiet hours enforced in the dispatcher; breaching the auto-pause thresholds halts all sending until an operator resumes.
Consent tracking: contacts without consent_source are excluded from all segments by default (importable but not mailable until consent recorded).
Full audit: for any sent message you can trace message → approval → campaign → agent_run transcript.
Secrets only via env; .env gitignored; webhook signatures verified; unsubscribe tokens signed (itsdangerous) and non-enumerable.
15. Testing requirements
pytest suite, mock provider, ephemeral Postgres (testcontainers or a hermes_test DB). Minimum coverage:
Suppression: the three-layer tests from 14.1; webhook bounce/complaint/unsub consequences; unsubscribe token flow.
Dispatcher: caps, quiet-hours rescheduling, idempotency (running dispatch twice sends once), circuit breaker.
Segments: rule-tree → SQL for every op; implicit active+non-suppressed filter; rejection of unknown ops.
Agent loop: tool error fed back, max-iterations, transcript persisted; registry validates bad args.
Tools: submit_for_approval never sends; submit_reply_handling unsubscribe path; send_test_email refuses non-operator recipients.
Inbound: IMAP parse fixtures (plain, quoted, HTML-only), dedupe by uid, threading link via In-Reply-To.
Rendering: merge fields, missing-field error, unsubscribe+address always present.
E2E happy path (mock provider): seed → plan campaign via scripted agent run → approve → dispatch → synth webhooks → metrics reflect events. LLM calls in tests are faked with a FakeLLM that returns scripted tool calls; never hit the network in tests.
16. Milestones — execute in order
Phase 0 — human checklist (generate docs/DELIVERABILITY.md, do not code): buy/choose sending subdomain; configure SPF, DKIM, DMARC (start p=none); set up Resend domain + webhook; create replies mailbox with IMAP; plan 4–8 week warm-up ramp (start ≤50/day); pick consent-clean initial list.
Phase 1 — Skeleton & data. Scaffold repo per Section 4; docker-compose (postgres16+pgvector image, redis); config; models; initial migration; scripts/seed_demo.py (200 fake contacts across stages/timezones, 1 demo segment); Makefile targets up, db, seed, dev, worker, beat, test, lint. ✅ Accept: make up && make db && make seed && make test green; hermes --help works.
Phase 2 — Provider + suppression + webhooks. Provider interface, mock + resend drivers, webhook endpoint with consequences, unsubscribe page, suppression service, base email layout renderer. ✅ Accept: tests for Section 14.1–14.3 pass; posting a synthetic bounce webhook suppresses the contact.
Phase 3 — LLM + agent loop + read tools. Client, router, loop, registry, tools: search_contacts, preview_segment, get_campaign_metrics, get_account_health; chat.md prompt; CLI hermes chat; agent_runs persisted. ✅ Accept: with FakeLLM, loop tests pass; with a real key, hermes chat "how many leads do we have?" answers via tool call.
Phase 4 — Campaign drafting + approvals + dashboard core. Remaining write tools; campaign state machine; template rendering with validation; dashboard: login, overview, approvals, campaigns, contacts, chat pages. ✅ Accept: E2E in mock mode: agent run drafts a 3-step sequence with A/B on step 1, test email lands in ./outbox/, approval appears with full previews, approving moves it to scheduled.
Phase 5 — Dispatcher + sequences. Materialization, dispatch task, caps/quiet-hours/circuit-breaker, sequence advancement, A/B split. ✅ Accept: Section 15 dispatcher tests pass; the E2E happy path runs end-to-end.
Phase 6 — Inbound + inbox agent. IMAP poller, reply pipeline, inbox prompt + tools, reply-draft approvals, threading on approved reply sends. ✅ Accept: fixture replies get classified by FakeLLM script; unsubscribe-intent reply suppresses instantly; approved draft dispatches with correct headers.
Phase 7 — Analytics + optimizer. Rollups, stats page numbers, optimizer prompt + weekly beat, proposals UI. ✅ Accept: seeded events produce correct rates; optimizer run (FakeLLM) files proposals visible in dashboard.
Phase 8 — Hardening & docs. Fill README (setup, going-live checklist referencing Phase 0, switching mock→resend, vLLM serving command incl. --tool-call-parser hermes), structured logging, ruff clean, final test sweep. ✅ Accept: fresh-clone bootstrap works from README alone in mock mode.
17. Demo mode
APP_ENV=dev + EMAIL_PROVIDER=mock must showcase everything with zero external accounts: seeded CRM, one pre-approved running campaign, make demo-events synthesizing opens/clicks/bounces/replies so the dashboard and optimizer have data. This is the mode you (Cursor) develop and test in throughout.
18. .cursor/rules/hermes.mdc
---
description: Hermes project rules
alwaysApply: true
---
- PROJECT_SPEC.md is authoritative; if code and spec conflict, follow spec and note it in DECISIONS.md.
- Work one phase at a time; do not start phase N+1 with failing phase-N acceptance checks.
- Never add a code path from agent tools to provider.send (except send_test_email → operator address).
- All suppression/approval/cap guardrails from spec §14 must keep passing tests; treat them as frozen behavior.
- No new dependencies beyond spec §3 without recording rationale in DECISIONS.md.
- Every model/schema change gets an Alembic migration. Every service function gets type hints. Run `make lint test` before declaring a task done.
- Do not read os.environ outside app/config.py. No secrets in code or tests.
Appendix A — Makefile & compose (reference)
docker-compose.yml: postgres (image pgvector/pgvector:pg16, env creds hermes/hermes, volume) + redis:7-alpine. Makefile targets: up (compose up -d), db (alembic upgrade head), seed, dev (uvicorn app.main:app --reload), worker (celery -A app.workers.celery_app worker -l info), beat, test (pytest -q), lint (ruff check + format), demo-events.
Appendix B — Hermes native tool-call format (fallback reference only)
Hermes models are trained on ChatML with tool schemas inside <tools>…</tools> in the system prompt, emitting <tool_call>{"name": …, "arguments": {…}}</tool_call> and expecting results in a tool role wrapped in <tool_response> tags. You should never implement this manually — vLLM's hermes parser or the hosted API surfaces it as OpenAI tool_calls — but if debugging raw serving output, this is what you're seeing.
— End of specification. Begin with Phase 1. —