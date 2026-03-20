"""K8sGPT terminal chat client.

Connects to a running K8sGPT API server and provides an interactive
chat interface in the terminal — ask questions about your Kubernetes
cluster in plain English.

Usage:
    k8sgpt                          # uses default http://localhost:8000
    k8sgpt --url http://host:8000
    k8sgpt --namespace kube-system
"""

import argparse
import sys
import uuid

import httpx
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

BANNER = """[bold cyan]
 ██╗  ██╗ █████╗ ███████╗ ██████╗ ██████╗ ████████╗
 ██║ ██╔╝██╔══██╗██╔════╝██╔════╝ ██╔══██╗╚══██╔══╝
 █████╔╝ ╚█████╔╝███████╗██║  ███╗██████╔╝   ██║
 ██╔═██╗ ██╔══██╗╚════██║██║   ██║██╔═══╝    ██║
 ██║  ██╗╚█████╔╝███████║╚██████╔╝██║        ██║
 ╚═╝  ╚═╝ ╚════╝ ╚══════╝ ╚═════╝ ╚═╝        ╚═╝
[/bold cyan]"""

HELP_TEXT = """[dim]
Commands:
  [bold]/health[/bold]          Check API and cluster connectivity
  [bold]/clear[/bold]           Clear conversation history (start fresh)
  [bold]/namespace <ns>[/bold]  Switch namespace  (e.g. /namespace kube-system)
  [bold]/quit[/bold]  or  [bold]/exit[/bold]    Exit
  [bold]/help[/bold]            Show this message

Example questions:
  • How many pods are running?
  • Are all my deployments healthy?
  • Show me logs for pod nginx-abc123
  • What warnings have been raised recently?
  • How is my cluster doing overall?
[/dim]"""


def _check_server(base_url: str) -> bool:
    """Return True if the API server is reachable."""
    try:
        r = httpx.get(f"{base_url}/health", timeout=4)
        data = r.json()
        k8s = data.get("kubernetes", "unknown")
        version = data.get("version", "?")
        colour = "green" if k8s == "connected" else "yellow"
        console.print(
            f"  API [green]online[/green]  •  "
            f"Kubernetes [{colour}]{k8s}[/{colour}]  •  v{version}"
        )
        return True
    except (httpx.RequestError, ValueError):
        return False


def _ask(base_url: str, query: str, session_id: str, namespace: str) -> str:
    """Send a query to the API and return the answer text."""
    try:
        r = httpx.post(
            f"{base_url}/query",
            json={"query": query, "session_id": session_id, "namespace": namespace},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["answer"]
    except httpx.TimeoutException:
        return (
            "Request timed out. The cluster query took too long "
            "— try a simpler question."
        )
    except httpx.HTTPStatusError as e:
        return f"API error {e.response.status_code}: {e.response.text}"
    except httpx.RequestError as e:
        return f"Connection error: {e}"


def _clear_session(base_url: str, session_id: str) -> None:
    """Delete conversation history for session_id on the server."""
    try:
        httpx.delete(f"{base_url}/sessions/{session_id}", timeout=5)
    except httpx.RequestError:
        pass


def run(base_url: str = "http://localhost:8000", namespace: str = "default") -> None:
    console.print(BANNER)

    console.print(
        Panel(
            f"[bold]Namespace:[/bold] [cyan]{namespace}[/cyan]   "
            f"[bold]API:[/bold] [cyan]{base_url}[/cyan]\n"
            f"Type [bold]/help[/bold] for commands, [bold]/quit[/bold] to exit.",
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 2),
        )
    )

    # Connectivity check
    console.print()
    if not _check_server(base_url):
        console.print(
            f"\n[bold red]Cannot reach the API at {base_url}[/bold red]\n"
            "Make sure the server is running:\n"
            "  [dim]uvicorn main:app --port 8000[/dim]\n"
            "or the Minikube tunnel is open:\n"
            "  [dim]minikube service k8sgpt-service[/dim]\n"
        )
        sys.exit(1)

    session_id = str(uuid.uuid4())
    console.print()

    while True:
        try:
            query = Prompt.ask("[bold cyan] You [/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not query:
            continue

        # --- built-in commands ---
        if query.lower() in ("/quit", "/exit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if query.lower() == "/help":
            console.print(HELP_TEXT)
            continue

        if query.lower() == "/clear":
            _clear_session(base_url, session_id)
            session_id = str(uuid.uuid4())
            console.print("[dim]  Conversation cleared.[/dim]\n")
            continue

        if query.lower() == "/health":
            console.print()
            _check_server(base_url)
            console.print()
            continue

        if query.lower().startswith("/namespace "):
            namespace = query.split(maxsplit=1)[1].strip()
            console.print(f"[dim]  Switched to namespace [cyan]{namespace}[/cyan][/dim]\n")
            continue

        if query.startswith("/"):
            console.print("[red]Unknown command.[/red] Type [bold]/help[/bold] for options.\n")
            continue

        # --- send to agent ---
        with console.status("[dim cyan]Thinking...[/dim cyan]", spinner="dots"):
            answer = _ask(base_url, query, session_id, namespace)

        console.print()
        console.print(
            Panel(
                Markdown(answer),
                title="[bold green] K8sGPT [/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )
        console.print()


def main() -> None:
    """Entry point for the `k8sgpt` CLI command."""
    parser = argparse.ArgumentParser(
        description="K8sGPT — AI Kubernetes assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="K8sGPT API URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace to query (default: default)",
    )
    args = parser.parse_args()
    run(base_url=args.url, namespace=args.namespace)


if __name__ == "__main__":
    main()
