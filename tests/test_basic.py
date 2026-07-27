"""Basic tests for Hermes email marketing agent."""


def test_app_import():
    """Test that the app module can be imported."""
    import app

    assert app is not None


def test_config_import():
    """Test that the config module can be imported."""
    from app.config import settings

    assert settings is not None


def test_db_import():
    """Test that the db module can be imported."""
    from app.db import Base, engine

    assert engine is not None
    assert Base is not None


def test_models_import():
    """Test that models can be imported."""
    from app.models.agent import AgentRun, Approval, Proposal
    from app.models.campaign import Campaign, CampaignStatus, CampaignType
    from app.models.contact import Contact, ContactStatus, LifecycleStage
    from app.models.event import Event, EventType
    from app.models.message import Message, MessageStatus
    from app.models.reply import Reply
    from app.models.segment import Segment
    from app.models.suppression import Suppression, SuppressionReason

    assert Contact is not None
    assert LifecycleStage is not None
    assert ContactStatus is not None
    assert Segment is not None
    assert Campaign is not None
    assert CampaignStatus is not None
    assert CampaignType is not None
    assert Message is not None
    assert MessageStatus is not None
    assert Suppression is not None
    assert SuppressionReason is not None
    assert Event is not None
    assert EventType is not None
    assert Reply is not None
    assert AgentRun is not None
    assert Approval is not None
    assert Proposal is not None


def test_providers_import():
    """Test that providers can be imported."""
    from app.providers.base import EmailProvider, SendRequest, SendResult
    from app.providers.mock import MockProvider

    assert EmailProvider is not None
    assert SendRequest is not None
    assert SendResult is not None
    assert MockProvider is not None


def test_services_functions_import():
    """Test that service functions can be imported."""
    from app.services.campaigns import create_campaign, get_campaign, list_campaigns
    from app.services.contacts import (
        get_contact_by_email,
        search_contacts,
        upsert_contact,
    )
    from app.services.messages import create_message, get_messages_to_send
    from app.services.suppression import (
        add_suppression,
        is_suppressed,
        remove_suppression,
        suppress_contact_from_event,
        update_contact_status,
    )

    assert is_suppressed is not None
    assert add_suppression is not None
    assert remove_suppression is not None
    assert suppress_contact_from_event is not None
    assert update_contact_status is not None
    assert search_contacts is not None
    assert get_contact_by_email is not None
    assert upsert_contact is not None
    assert create_campaign is not None
    assert get_campaign is not None
    assert list_campaigns is not None
    assert create_message is not None
    assert get_messages_to_send is not None


def test_llm_import():
    """Test that LLM module can be imported."""
    from app.llm.client import LLMClient

    assert LLMClient is not None


def test_workers_import():
    """Test that workers module can be imported."""
    from app.workers.celery_app import celery_app

    assert celery_app is not None


def test_cli_import():
    """Test that CLI module can be imported."""
    from app.cli import app

    assert app is not None


def test_routes_import():
    """Test that web routes can be imported."""
    from app.web.routes import router

    assert router is not None


def test_templates_import():
    """Test that templates service can be imported."""
    from app.services.templates import (
        get_preview,
        render_markdown_to_html,
        render_markdown_to_text,
        render_template,
        validate_template_variables,
        wrap_email_html,
    )

    assert render_template is not None
    assert render_markdown_to_html is not None
    assert render_markdown_to_text is not None
    assert wrap_email_html is not None
    assert validate_template_variables is not None
    assert get_preview is not None


def test_dispatcher_import():
    """Test that dispatcher service can be imported."""
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
        send_message,
        verify_unsubscribe_token,
    )

    assert get_provider is not None
    assert check_global_circuit_breaker is not None
    assert check_hourly_cap is not None
    assert check_daily_cap is not None
    assert check_weekly_contact_cap is not None
    assert get_due_messages is not None
    assert render_message_with_template is not None
    assert create_send_request is not None
    assert generate_unsubscribe_token is not None
    assert verify_unsubscribe_token is not None
    assert send_message is not None
    assert process_scheduled_messages is not None
    assert materialize_campaign is not None
    assert calculate_send_time is not None
    assert pause_campaign is not None
    assert resume_campaign is not None


def test_segments_import():
    """Test that segments service can be imported."""
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

    assert evaluate_rule is not None
    assert evaluate_rule_tree is not None
    assert evaluate_segment is not None
    assert get_segment_count is not None
    assert get_segment_contacts_paginated is not None
    assert validate_segment_definition is not None
    assert create_segment is not None
    assert update_segment is not None
    assert delete_segment is not None


def test_sequences_import():
    """Test that sequences service can be imported."""
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

    assert get_next_sequence_step is not None
    assert should_skip_step is not None
    assert calculate_delay is not None
    assert enroll_contact is not None
    assert complete_sequence is not None
    assert get_sequence_progress is not None
    assert create_sequence is not None
    assert update_sequence_status is not None
    assert trigger_sequence is not None


def test_inbox_import():
    """Test that inbox service can be imported."""
    from app.services.inbox import (
        extract_email_address,
        extract_text_from_html,
        find_or_create_contact,
        find_or_create_thread,
        get_inbox_messages,
        get_inbox_threads,
        get_unread_count,
        mark_as_read,
        mark_thread_as_read,
        parse_inbound_email,
        poll_inbox,
        process_inbound_email,
    )

    assert extract_text_from_html is not None
    assert extract_email_address is not None
    assert parse_inbound_email is not None
    assert find_or_create_contact is not None
    assert find_or_create_thread is not None
    assert process_inbound_email is not None
    assert poll_inbox is not None
    assert mark_as_read is not None
    assert mark_thread_as_read is not None
    assert get_unread_count is not None
    assert get_inbox_messages is not None
    assert get_inbox_threads is not None


def test_analytics_import():
    """Test that analytics service can be imported."""
    from app.services.analytics import (
        get_account_metrics,
        get_campaign_metrics,
        get_contact_metrics,
        get_daily_rollups,
        get_variant_metrics,
    )

    assert get_campaign_metrics is not None
    assert get_account_metrics is not None
    assert get_daily_rollups is not None
    assert get_variant_metrics is not None
    assert get_contact_metrics is not None


def test_optimizer_import():
    """Test that optimizer service can be imported."""
    from app.services.optimizer import (
        apply_proposal,
        generate_optimization_proposals,
        get_optimization_recommendations,
        run_weekly_optimizer,
    )

    assert generate_optimization_proposals is not None
    assert get_optimization_recommendations is not None
    assert run_weekly_optimizer is not None
    assert apply_proposal is not None


def test_agent_loop_import():
    """Test that agent loop can be imported."""
    from app.agent.loop import AgentLoop, run_agent

    assert AgentLoop is not None
    assert run_agent is not None


def test_agent_tools_import():
    """Test that agent tools can be imported."""
    from app.agent.tools import AgentTools, ToolResult

    assert AgentTools is not None
    assert ToolResult is not None
