"""
AI Orchestrator CLI - Command line interface.
Usage: python -m cli [command] [options]
"""

import asyncio
import sys
from typing import Optional
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


if HAS_RICH:
    app = typer.Typer(
        name="ai-orchestrator",
        help="AI Orchestrator - Multi-service AI router",
        add_completion=False,
    )
    console = Console()
else:
    # Fallback without rich
    class FakeApp:
        def command(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    app = FakeApp()
    console = None


def print_output(text: str, style: str = None):
    """Print with optional rich formatting."""
    if console:
        console.print(text, style=style)
    else:
        print(text)


@app.command()
def text(
    prompt: str = typer.Argument(..., help="Text prompt"),
    model: str = typer.Option("openai/gpt-oss-120b", help="Model name"),
    max_tokens: int = typer.Option(1024, help="Max tokens"),
    temperature: float = typer.Option(0.7, help="Temperature"),
):
    """Generate text using Groq."""
    from services import GroqService

    async def run():
        service = GroqService()
        with Progress() as progress:
            task = progress.add_task("Generating...", total=None)
            result = await service.generate(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        print_output("\n[bold green]Generated Text:[/bold green]")
        print_output(result.get("text", result.get("error", "No output")))
        print_output(f"\n[dim]Model: {result.get('model')} | Tokens: {result.get('tokens_used')}[/dim]")

    asyncio.run(run())


@app.command()
def image(
    prompt: str = typer.Argument(..., help="Image prompt"),
    negative: Optional[str] = typer.Option(None, help="Negative prompt"),
    size: str = typer.Option("1024x1024", help="Image size"),
):
    """Generate image using Stable Diffusion."""
    from services import StableDiffusionService

    async def run():
        service = StableDiffusionService()
        w, h = size.split("x")
        result = await service.generate(
            prompt=prompt,
            negative_prompt=negative,
            width=int(w),
            height=int(h),
        )

        if "image_url" in result:
            print_output(f"\n[bold green]Image generated![/bold green]")
            print_output(f"URL: {result['image_url']}")
        else:
            print_output(f"\n[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")

    asyncio.run(run())


@app.command()
def services():
    """List all services and their status."""
    from services import GroqService, StableDiffusionService, RunwayService, LumaService

    async def run():
        service_list = [
            ("Groq", "Text generation", GroqService()),
            ("Stable Diffusion", "Image generation", StableDiffusionService()),
            ("Runway", "Video generation", RunwayService()),
            ("Luma", "3D generation", LumaService()),
        ]

        table = Table(title="AI Services")
        table.add_column("Service", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="green")

        for name, stype, service in service_list:
            status = await service.health_check()
            status_text = "✅ Ready" if status else "⚠️ Not configured"
            table.add_row(name, stype, status_text)

        console.print(table) if console else print(table)

    asyncio.run(run())


@app.command()
def stats():
    """Show usage statistics."""
    from database import db

    async def run():
        await db.connect()
        dashboard = await db.get_dashboard_stats()
        await db.close()

        print_output("\n[bold]📊 Dashboard Statistics[/bold]")
        print_output(f"Total Generations: {dashboard.get('total_generations', 0)}")
        print_output(f"Total Cost: ${dashboard.get('total_cost_usd', 0):.2f}")
        print_output(f"Avg Latency: {dashboard.get('avg_latency_ms', 0):.0f}ms")

        if dashboard.get("by_service"):
            print_output("\n[bold]By Service:[/bold]")
            for svc in dashboard["by_service"]:
                print_output(f"  {svc['service']}: {svc['count']} (${svc.get('cost', 0):.2f})")

    asyncio.run(run())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host"),
    port: int = typer.Option(8000, help="Port"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
):
    """Start the API server."""
    import uvicorn
    print_output(f"\n🚀 Starting AI Orchestrator on http://{host}:{port}")
    print_output(f"📖 Docs: http://{host}:{port}/docs\n")
    uvicorn.run("orchestrator:app", host=host, port=port, reload=reload)


@app.command()
def backup(
    name: Optional[str] = typer.Option(None, help="Backup name"),
    restore: Optional[str] = typer.Option(None, help="Restore from backup"),
    list_backups: bool = typer.Option(False, "--list", help="List backups"),
):
    """Manage backups."""
    from backup import backup_manager

    async def run():
        if list_backups:
            backups = backup_manager.list_backups()
            print_output("\n[bold]📦 Backups:[/bold]")
            for b in backups:
                print_output(f"  {b['name']} ({b['timestamp']}) - {b['files']} files")
        elif restore:
            result = await backup_manager.restore_backup(restore)
            if result["success"]:
                print_output(f"\n[green]✅ Restored from {restore}[/green]")
            else:
                print_output(f"\n[red]❌ {result['error']}[/red]")
        else:
            result = await backup_manager.create_backup(name)
            print_output(f"\n[green]✅ Backup created: {result['name']}[/green]")
            print_output(f"   Files: {len(result['files'])} | Size: {result['size_bytes']} bytes")

    asyncio.run(run())


@app.command()
def plugins():
    """List installed plugins."""
    from plugins import plugin_registry

    plugin_list = plugin_registry.list_plugins()

    if not plugin_list:
        print_output("\n[dim]No plugins installed[/dim]")
        return

    table = Table(title="Installed Plugins")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Version")
    table.add_column("Status")

    for p in plugin_list:
        status = "✅" if p["initialized"] else "⚠️"
        table.add_row(
            p["id"], p["name"], p["service_type"],
            p["version"], status
        )

    console.print(table) if console else print(table)


@app.command()
def config(
    show: bool = typer.Option(False, help="Show current config"),
    set_key: Optional[str] = typer.Option(None, help="Set API key"),
):
    """View and manage configuration."""
    if show:
        from dotenv import dotenv_values
        config = dotenv_values(".env")

        print_output("\n[bold]⚙️ Configuration[/bold]")
        for key, value in config.items():
            # Mask API keys
            if "key" in key.lower() and value:
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print_output(f"  {key}: {masked}")
            else:
                print_output(f"  {key}: {value}")


def cli():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    cli()
