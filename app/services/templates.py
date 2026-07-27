"""Template service for email template rendering."""

import re
from typing import Any, Dict, List

from jinja2 import Template as JinjaTemplate
from markdown_it import MarkdownIt

from app.config import settings
from app.models.template import Template


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
            <a href="{{{{
                settings.BASE_URL
            }}}}/unsubscribe/{{{{ contact_id }}}}">Unsubscribe</a>
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
