"""
MAS CLI — single entry point for all runtime commands.

Each command lazily imports only its own dependencies so that
``mas api`` works without temporalio and ``mas worker`` works
without Flask.  The composition root (AppContainer) is created
here and passed into the adapters — adapters never assemble the
world themselves.

After ``pip install -e .`` (or ``pip install mas[all]``) run::

    mas --help
    mas api --dev
    mas worker --threads 20
"""
from __future__ import annotations

import typer

app = typer.Typer(
    name="mas",
    help="MAS — Multi-Agent System orchestration engine.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


def _build_container():
    """Shared bootstrap: config → container."""
    from mas.config.app_config import AppConfig
    from bootstrap.container import AppContainer

    cfg = AppConfig.get_instance()
    return AppContainer(cfg), cfg


# ── API server ────────────────────────────────────────────────────

@app.command()
def api(
    host: str = typer.Option(None, help="Bind address (default: from config)"),
    port: int = typer.Option(None, help="Bind port (default: from config)"),
    dev: bool = typer.Option(False, "--dev", help="Run Flask dev server with auto-reload"),
    workers: int = typer.Option(4, help="Gunicorn worker count (production)"),
):
    """Start the MAS HTTP API server."""
    container, cfg = _build_container()

    from inbound.flask.flask_app import create_app

    flask_app = create_app(container, config=cfg)

    bind_host = host or cfg.hostname
    bind_port = port or int(cfg.port)

    if dev:
        flask_app.run(host=bind_host, port=bind_port, debug=True)
    else:
        import sys
        sys.argv = [
            "gunicorn",
            "--bind", f"{bind_host}:{bind_port}",
            "--workers", str(workers),
            "--access-logfile", "-",
            "run.wsgi:application",
        ]
        from gunicorn.app.wsgiapp import run as gunicorn_run
        gunicorn_run()


# ── Temporal worker ───────────────────────────────────────────────

@app.command()
def worker(
    threads: int = typer.Option(10, help="Activity thread pool size"),
):
    """Start a Temporal worker process."""
    import asyncio
    from inbound.temporal.worker import run_worker

    container, _ = _build_container()
    asyncio.run(run_worker(container, threads))
