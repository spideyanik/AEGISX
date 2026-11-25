"""Terminal-safe AEGISX branding."""

from __future__ import annotations

from rich.console import Console
from rich.text import Text

LOGO = r"""
 █████╗ ███████╗ ██████╗ ██╗███████╗██╗  ██╗
██╔══██╗██╔════╝██╔════╝ ██║██╔════╝╚██╗██╔╝
███████║█████╗  ██║  ███╗██║███████╗ ╚███╔╝
██╔══██║██╔══╝  ██║   ██║██║╚════██║ ██╔██╗
██║  ██║███████╗╚██████╔╝██║███████║██╔╝ ██╗
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝╚═╝  ╚═╝
""".strip("\n")

MOTTO = "From Isolated Vulnerability Detection to Unified Cybersecurity Intelligence."


def show_logo(console: Console) -> None:
    """Render the logo and motto using colors supported by Rich terminals."""
    console.print(Text(LOGO, style="bold cyan"))
    console.print(Text("AEGISX", style="bold magenta"), justify="center")
    console.print(Text(MOTTO, style="dim"), justify="center")
    console.print()
