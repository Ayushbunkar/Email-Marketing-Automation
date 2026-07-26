"""Command-line interface for Hermes email marketing agent."""

import typer

app = typer.Typer(
    name="hermes",
    help="Hermes Email Marketing Agent CLI",
)


@app.command()
def chat():
    """Start an interactive chat session with the agent."""
    print("Chat feature not yet implemented")


@app.command()
def seed():
    """Seed demo data."""
    print("Seed feature not yet implemented")


@app.command()
def run_agent():
    """Run the agent loop."""
    print("Agent run feature not yet implemented")


if __name__ == "__main__":
    app()