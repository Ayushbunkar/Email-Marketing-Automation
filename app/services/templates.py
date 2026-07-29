"""Template service for email template rendering."""

import re
from typing import Any, Dict, List, Optional

from jinja2 import Template as JinjaTemplate
from markdown_it import MarkdownIt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.template import Template, TemplateStatus


def render_template(template: Template, contact_data: Dict[str, Any]) -> Dict[str, str]:
    """Render a template with contact data.

    Args:
        template: The template to render
        contact_data: Dictionary of contact data for merge fields

    Returns:
        Dictionary with rendered subject, preheader, html, and text
    """
    # Extract merge fields from template variables
    merge_fields = template.variables or []

    # Create context with contact data
    context = contact_data.copy()

    # Render subject
    subject_template = JinjaTemplate(template.subject)
    subject = subject_template.render(**context)

    # Render preheader
    preheader = ""
    if template.preheader:
        preheader_template = JinjaTemplate(template.preheader)
        preheader = preheader_template.render(**context)

    # Render HTML from markdown
    html = render_markdown_to_html(template.body_markdown, context)

    # Render plain text version
    text = render_markdown_to_text(template.body_markdown, context)

    return {
        "subject": subject,
        "preheader": preheader,
        "html": html,
        "text": text,
    }


def render_markdown_to_html(markdown_text: str, context: Dict[str, Any]) -> str:
    """Convert markdown to HTML with Jinja2 template rendering.

    Args:
        markdown_text: Markdown text to render
        context: Context dictionary for template variables

    Returns:
        Rendered HTML string
    """
    # First render Jinja2 template
    jinja_template = JinjaTemplate(markdown_text)
    rendered_markdown = jinja_template.render(**context)

    # Convert markdown to HTML
    md = MarkdownIt()
    html = md.render(rendered_markdown)

    # Wrap in base email layout
    return wrap_email_html(html)


def render_markdown_to_text(markdown_text: str, context: Dict[str, Any]) -> str:
    """Convert markdown to plain text with Jinja2 template rendering.

    Args:
        markdown_text: Markdown text to render
        context: Context dictionary for template variables

    Returns:
        Plain text string
    """
    # First render Jinja2 template
    jinja_template = JinjaTemplate(markdown_text)
    rendered_markdown = jinja_template.render(**context)

    # Convert markdown to plain text (simple approach)
    # Remove markdown formatting
    text = rendered_markdown

    # Remove headers
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

    # Remove bold/italic markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Remove links but keep text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)

    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Clean up extra whitespace
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = text.strip()

    return text


def wrap_email_html(content: str) -> str:
    """Wrap content in base email HTML layout.

    Args:
        content: Main email content HTML

    Returns:
        Complete HTML email with layout
    """
    # Escape braces for f-string ({{ becomes {, }} becomes })
    unsubscribe_url = f"{settings.BASE_URL}/unsubscribe/{{contact_id}}"
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
        }}
        .footer a {{
            color: #666;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    {content}
    <div class="footer">
        <p>{settings.COMPANY_POSTAL_ADDRESS}</p>
        <p>
            <a href="{unsubscribe_url}">Unsubscribe</a>
        </p>
    </div>
</body>
</html>"""


def validate_template_variables(
    template: Template, contact_data: Dict[str, Any]
) -> List[str]:
    """Validate that all template variables have values.

    Args:
        template: The template to validate
        contact_data: Context data to validate against

    Returns:
        List of missing variable names
    """
    missing = []

    # Extract variable names from template (simple {{variable}} pattern)
    pattern = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}"
    matches = re.findall(pattern, template.subject)
    matches.extend(re.findall(pattern, template.preheader or ""))
    matches.extend(re.findall(pattern, template.body_markdown))

    # Check each variable
    for var in matches:
        if var not in contact_data:
            missing.append(var)

    return missing


def get_preview(
    template: Template, sample_data: Dict[str, Any] = None
) -> Dict[str, str]:
    """Get a preview of the rendered template.

    Args:
        template: The template to preview
        sample_data: Optional sample data, defaults to empty values

    Returns:
        Dictionary with preview content
    """
    if sample_data is None:
        sample_data = {}

    # Add default values for common fields
    defaults = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "company": "Example Corp",
    }
    defaults.update(sample_data)

    return render_template(template, defaults)


async def list_templates(
    session: AsyncSession,
    campaign_id: Optional[str] = None,
    status: Optional[TemplateStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Template]:
    """List templates with optional filters.
    
    Args:
        session: Database session
        campaign_id: Optional campaign ID filter
        status: Optional status filter
        limit: Maximum results
        offset: Offset for pagination
        
    Returns:
        List of templates
    """
    query = select(Template)

    if campaign_id:
        query = query.where(Template.campaign_id == campaign_id)

    query = query.order_by(Template.created_at.desc()).limit(limit).offset(offset)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_template(session: AsyncSession, template_id: str) -> Optional[Template]:
    """Get a specific template.
    
    Args:
        session: Database session
        template_id: Template ID
        
    Returns:
        Template or None
    """
    result = await session.execute(select(Template).where(Template.id == template_id))
    return result.scalar_one_or_none()


async def create_template(
    session: AsyncSession,
    campaign_id: Optional[str] = None,
    step_index: Optional[int] = None,
    name: Optional[str] = None,
    subject: str = "",
    preheader: Optional[str] = None,
    body_markdown: str = "",
    variant_label: str = "A",
    variables: Optional[List[str]] = None,
    status: TemplateStatus = TemplateStatus.DRAFT,
) -> Template:
    """Create a new template.
    
    Args:
        session: Database session
        campaign_id: Campaign ID
        step_index: Campaign step index
        name: Optional template name
        subject: Email subject
        preheader: Optional email preheader
        body_markdown: Email body in markdown
        variant_label: Template variant label
        variables: Optional template variables
        status: Template status
        
    Returns:
        Created template
    """
    template = Template(
        campaign_id=campaign_id,
        step_index=step_index,
        name=name,
        subject=subject,
        preheader=preheader,
        body_markdown=body_markdown,
        variant_label=variant_label,
        variables=variables or [],
    )
    session.add(template)
    await session.commit()
    return template


async def update_template(
    session: AsyncSession,
    template_id: str,
    template_data: Dict[str, Any],
) -> Optional[Template]:
    """Update a template.
    
    Args:
        session: Database session
        template_id: Template ID
        template_data: Update data
        
    Returns:
        Updated template or None
    """
    result = await session.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    
    if template:
        for key, value in template_data.items():
            if hasattr(template, key):
                if hasattr(value, "value"):
                    value = value.value
                setattr(template, key, value)
        await session.commit()
    return template


async def delete_template(
    session: AsyncSession,
    template_id: str,
) -> Optional[Template]:
    """Delete a template.
    
    Args:
        session: Database session
        template_id: Template ID
        
    Returns:
        Deleted template or None
    """
    result = await session.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    
    if template:
        await session.delete(template)
        await session.commit()
    return template
