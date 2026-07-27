"""Segment service for evaluating contact segments."""

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact, ContactStatus
from app.models.segment import Segment
from app.models.suppression import Suppression


def evaluate_rule(rule: Dict[str, Any], contact: Contact) -> bool:
    """Evaluate a single rule against a contact.

    Args:
        rule: Rule dictionary with field, op, and value
        contact: Contact to evaluate

    Returns:
        True if contact matches rule
    """
    field = rule.get("field")
    op = rule.get("op")
    value = rule.get("value")

    # Get contact field value
    if field == "status":
        contact_value = contact.status
    elif field == "lifecycle_stage":
        contact_value = contact.lifecycle_stage
    elif field == "email":
        contact_value = contact.email
    elif field == "first_name":
        contact_value = contact.first_name
    elif field == "last_name":
        contact_value = contact.last_name
    elif field == "company":
        contact_value = contact.company
    elif field.startswith("attributes."):
        # Get attribute from JSONB
        attr_path = field.split(".", 1)[1]
        contact_value = contact.attributes.get(attr_path)
    else:
        # Unknown field
        return False

    # Evaluate operation
    if op == "eq":
        return contact_value == value
    elif op == "neq":
        return contact_value != value
    elif op == "in":
        return contact_value in value
    elif op == "contains":
        if contact_value is None:
            return False
        return value.lower() in str(contact_value).lower()
    elif op == "exists":
        return contact_value is not None
    else:
        # Unknown operation
        return False


def evaluate_rule_tree(
    rule_tree: Dict[str, Any],
    contact: Contact,
) -> bool:
    """Evaluate a rule tree against a contact.

    Args:
        rule_tree: Rule tree dictionary
        contact: Contact to evaluate

    Returns:
        True if contact matches rule tree
    """
    if "all" in rule_tree:
        # AND condition
        return all(evaluate_rule_tree(rule, contact) for rule in rule_tree["all"])
    elif "any" in rule_tree:
        # OR condition
        return any(evaluate_rule_tree(rule, contact) for rule in rule_tree["any"])
    else:
        # Single rule
        return evaluate_rule(rule_tree, contact)


async def evaluate_segment(
    session: AsyncSession,
    segment_id: str,
) -> List[Contact]:
    """Evaluate a segment and return matching contacts.

    Args:
        session: Database session
        segment_id: Segment ID to evaluate

    Returns:
        List of contacts matching the segment
    """
    # Get segment
    result = await session.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()

    if not segment:
        return []

    # Get all active, non-suppressed contacts
    result = await session.execute(
        select(Contact)
        .where(Contact.status == ContactStatus.ACTIVE)
        .where(~Contact.email.in_(select(Suppression.email)))
    )
    contacts = list(result.scalars().all())

    # Filter by segment rules
    matching = []
    for contact in contacts:
        if evaluate_rule_tree(segment.definition, contact):
            matching.append(contact)

    return matching


async def get_segment_count(
    session: AsyncSession,
    segment_id: str,
) -> int:
    """Get the count of contacts in a segment."""
    contacts = await evaluate_segment(session, segment_id)
    return len(contacts)


async def get_segment_contacts_paginated(
    session: AsyncSession,
    segment_id: str,
    page: int = 1,
    page_size: int = 50,
) -> List[Contact]:
    """Get contacts in a segment with pagination."""
    contacts = await evaluate_segment(session, segment_id)

    start = (page - 1) * page_size
    end = start + page_size

    return contacts[start:end]


async def validate_segment_definition(
    definition: Dict[str, Any],
) -> List[str]:
    """Validate a segment definition.

    Args:
        definition: Segment definition dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    def validate_rule(rule: Dict[str, Any]) -> None:
        if "field" not in rule:
            errors.append("Rule missing 'field'")
        if "op" not in rule:
            errors.append("Rule missing 'op'")
        if "value" not in rule:
            errors.append("Rule missing 'value'")

        # Check valid operations
        valid_ops = ["eq", "neq", "in", "contains", "exists"]
        if rule.get("op") not in valid_ops:
            errors.append(f"Invalid operation: {rule.get('op')}")

    def validate_tree(tree: Dict[str, Any]) -> None:
        if "all" in tree:
            for rule in tree["all"]:
                if isinstance(rule, dict):
                    validate_tree(rule)
        elif "any" in tree:
            for rule in tree["any"]:
                if isinstance(rule, dict):
                    validate_tree(rule)
        else:
            validate_rule(tree)

    validate_tree(definition)
    return errors


async def create_segment(
    session: AsyncSession,
    name: str,
    description: str,
    definition: Dict[str, Any],
    is_dynamic: bool = True,
    created_by: str = "system",
) -> Segment:
    """Create a new segment."""
    # Validate definition
    errors = await validate_segment_definition(definition)
    if errors:
        raise ValueError(f"Invalid segment definition: {errors}")

    segment = Segment(
        name=name,
        description=description,
        definition=definition,
        is_dynamic=is_dynamic,
        created_by=created_by,
    )
    session.add(segment)
    await session.commit()
    return segment


async def update_segment(
    session: AsyncSession,
    segment_id: str,
    **kwargs,
) -> Optional[Segment]:
    """Update a segment."""
    result = await session.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()

    if not segment:
        return None

    for key, value in kwargs.items():
        if hasattr(segment, key):
            setattr(segment, key, value)

    await session.commit()
    return segment


async def delete_segment(
    session: AsyncSession,
    segment_id: str,
) -> bool:
    """Delete a segment."""
    result = await session.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()

    if not segment:
        return False

    await session.delete(segment)
    await session.commit()
    return True
