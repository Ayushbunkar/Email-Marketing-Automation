"""Business logic services package."""

from app.services.analytics import (
    get_account_metrics,
    get_campaign_metrics,
    get_contact_metrics,
    get_daily_rollups,
    get_variant_metrics,
)
from app.services.campaigns import create_campaign, get_campaign, list_campaigns
from app.services.contacts import get_contact_by_email, search_contacts, upsert_contact
from app.services.dispatcher import (
    calculate_send_time,
    check_daily_cap,
    check_global_circuit_breaker,
    check_hourly_cap,
    check_weekly_contact_cap,
    create_send_request,
    generate_unsubscribe_token,
    get_due_messages,
    get_provider,
    materialize_campaign,
    pause_campaign,
    process_scheduled_messages,
    render_message_with_template,
    resume_campaign,
    verify_unsubscribe_token,
)
from app.services.dispatcher import (
    send_message as dispatcher_send_message,
)
from app.services.inbox import (
    classify_reply_with_ai,
    find_or_create_contact,
    generate_draft_response_if_needed,
    get_inbox_messages,
    get_inbox_threads,
    get_unread_count,
    mark_as_read,
    mark_thread_as_read,
    process_brevo_inbound_email,
)
from app.services.messages import (
    create_message,
    get_messages_to_send,
    record_event,
    send_message,
)
from app.services.optimizer import (
    apply_proposal,
    generate_optimization_proposals,
    get_optimization_recommendations,
    run_weekly_optimizer,
)
from app.services.segments import (
    create_segment,
    delete_segment,
    evaluate_rule,
    evaluate_rule_tree,
    evaluate_segment,
    get_segment_contacts_paginated,
    get_segment_count,
    update_segment,
    validate_segment_definition,
)
from app.services.sequences import (
    calculate_delay,
    complete_sequence,
    create_sequence,
    enroll_contact,
    get_next_sequence_step,
    get_sequence_progress,
    should_skip_step,
    trigger_sequence,
    update_sequence_status,
)
from app.services.suppression import (
    add_suppression,
    is_suppressed,
    remove_suppression,
    suppress_contact_from_event,
    update_contact_status,
)
from app.services.templates import (
    get_preview,
    render_markdown_to_html,
    render_markdown_to_text,
    render_template,
    validate_template_variables,
    wrap_email_html,
)

__all__ = [
    # Suppression
    "is_suppressed",
    "add_suppression",
    "remove_suppression",
    "suppress_contact_from_event",
    "update_contact_status",
    # Contacts
    "search_contacts",
    "get_contact_by_email",
    "upsert_contact",
    # Campaigns
    "create_campaign",
    "get_campaign",
    "list_campaigns",
    # Messages
    "create_message",
    "get_messages_to_send",
    "send_message",
    "record_event",
    # Templates
    "render_template",
    "render_markdown_to_html",
    "render_markdown_to_text",
    "wrap_email_html",
    "validate_template_variables",
    "get_preview",
    # Dispatcher
    "get_provider",
    "check_global_circuit_breaker",
    "check_hourly_cap",
    "check_daily_cap",
    "check_weekly_contact_cap",
    "get_due_messages",
    "render_message_with_template",
    "create_send_request",
    "generate_unsubscribe_token",
    "verify_unsubscribe_token",
    "dispatcher_send_message",
    "process_scheduled_messages",
    "materialize_campaign",
    "calculate_send_time",
    "pause_campaign",
    "resume_campaign",
    # Segments
    "evaluate_rule",
    "evaluate_rule_tree",
    "evaluate_segment",
    "get_segment_count",
    "get_segment_contacts_paginated",
    "validate_segment_definition",
    "create_segment",
    "update_segment",
    "delete_segment",
    # Sequences
    "get_next_sequence_step",
    "should_skip_step",
    "calculate_delay",
    "enroll_contact",
    "complete_sequence",
    "get_sequence_progress",
    "create_sequence",
    "update_sequence_status",
    "trigger_sequence",
    # Inbox
    "classify_reply_with_ai",
    "find_or_create_contact",
    "generate_draft_response_if_needed",
    "get_inbox_messages",
    "get_inbox_threads",
    "get_unread_count",
    "mark_as_read",
    "mark_thread_as_read",
    "process_brevo_inbound_email",
    # Analytics
    "get_campaign_metrics",
    "get_account_metrics",
    "get_daily_rollups",
    "get_variant_metrics",
    "get_contact_metrics",
    # Optimizer
    "generate_optimization_proposals",
    "get_optimization_recommendations",
    "run_weekly_optimizer",
    "apply_proposal",
]
