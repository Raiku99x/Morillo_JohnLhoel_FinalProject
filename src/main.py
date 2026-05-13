"""
main.py
-------
Entry point for the Deadline Countdown CLI application.
Run with: python src/main.py
"""

import sys
import os
from datetime import date, datetime
from typing import Optional

import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

sys.path.insert(0, os.path.dirname(__file__))
from tracker import DeadlineTracker
from deadline import Deadline

console = Console()

BANNER = """[bold cyan]
  ____                 _ _ _            _____               _
 |  _ \\  ___  __ _  __| | (_)_ __   __|_   _| __ __ _  ___| | _____ _ __
 | | | |/ _ \\/ _` |/ _` | | | '_ \\ / _ \\| || '__/ _` |/ __| |/ / _ \\ '__|
 | |_| |  __/ (_| | (_| | | | | | |  __/| || | | (_| | (__|   <  __/ |
 |____/ \\___|\\__,_|\\__,_|_|_|_| |_|\\___||_||_|  \\__,_|\\___|_|\\_\\___|_|
[/bold cyan]
[dim]  CLI-Based Academic Deadline Tracker  |  CSPC BSCS[/dim]
"""

MENU_CHOICES = [
    "1. Add deadline",
    "2. View all deadlines",
    "3. Mark as done",
    "4. Delete deadline",
    "5. View stats",
    "6. Exit",
]

STATUS_STYLES = {
    "OVERDUE":  ("💀 OVERDUE",  "bold red"),
    "DUE SOON": ("🔴 DUE SOON", "red"),
    "URGENT":   ("⚠️  URGENT",  "yellow"),
    "UPCOMING": ("📌 UPCOMING", "cyan"),
    "DONE":     ("✅ DONE",     "green"),
}


# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

def get_date(label: str) -> date:
    """
    Keeps prompting until a valid MM-DD-YYYY date is entered.

    Args:
        label (str): Prompt label text.

    Returns:
        date: Validated date object.
    """
    while True:
        raw: str = questionary.text(label).ask()
        if raw is None:
            continue
        raw = raw.strip()
        if not raw:
            console.print("  [red]❌  Date cannot be empty. Format: MM-DD-YYYY (e.g. 05-09-2026)[/red]\n")
            continue
        try:
            return datetime.strptime(raw, "%m-%d-%Y").date()
        except ValueError:
            console.print("  [red]❌  Wrong format. Use MM-DD-YYYY (e.g. 05-09-2026)[/red]\n")


def get_text(label: str) -> Optional[str]:
    """
    Prompts for non-empty text input.

    Args:
        label (str): Prompt label text.

    Returns:
        Optional[str]: Stripped input or None if empty.
    """
    val = questionary.text(label).ask()
    if val is None:
        return None
    return val.strip() or None


# ------------------------------------------------------------------ #
#  Display
# ------------------------------------------------------------------ #

def display_table(
    tracker: DeadlineTracker,
    title: str = "[bold cyan]📋 Your Deadlines[/bold cyan]",
    border_style: str = "bright_blue",
) -> None:
    """
    Renders all deadlines as a rich colored table sorted by urgency.

    Args:
        tracker (DeadlineTracker): Active tracker instance.
        title (str): Table title markup.
        border_style (str): Border color.
    """
    if not tracker.deadlines:
        console.print(Panel("[yellow]No deadlines found. Add one![/yellow]", title="Deadlines"))
        return

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white on dark_blue",
        border_style=border_style,
        title=title,
        title_justify="left",
    )

    table.add_column("#",           style="dim", width=6,  justify="center")
    table.add_column("STATUS",      width=13)
    table.add_column("SUBJECT",     style="bold white", width=22)
    table.add_column("DESCRIPTION", style="white",      width=30)
    table.add_column("DEADLINE",    style="white",      width=12, justify="center")
    table.add_column("DAYS LEFT",   width=10,           justify="center")

    for i, d in enumerate(tracker.sorted_deadlines(), 1):
        status_key = d.get_status()
        label, style = STATUS_STYLES.get(status_key, (status_key, "white"))

        deadline_str = d.due_date.strftime("%m-%d-%Y")

        if d.is_done:
            days_str = Text("Done ✓", style="green")
        else:
            days = d.days_left()
            if days < 0:
                days_str = Text(f"{abs(days)}d ago", style="bold red")
            elif days == 0:
                days_str = Text("TODAY", style="bold red blink")
            elif days == 1:
                days_str = Text("1 day", style="red")
            elif days <= 7:
                days_str = Text(f"{days} days", style="yellow")
            else:
                days_str = Text(f"{days} days", style="cyan")

        table.add_row(
            f"[{i}]",
            Text(label, style=style),
            d.subject[:21],
            d.description[:29],
            deadline_str,
            days_str,
        )

    console.print()
    console.print(table)
    console.print()


# ------------------------------------------------------------------ #
#  Menu Actions
# ------------------------------------------------------------------ #

def action_add(tracker: DeadlineTracker) -> None:
    """
    Handles adding a new deadline with validated inputs.

    Args:
        tracker (DeadlineTracker): Active tracker instance.
    """
    console.print(Panel("[bold cyan]ADD DEADLINE[/bold cyan]", box=box.ROUNDED))

    subject = get_text("Subject (e.g. Intermediate Prog)")
    if not subject:
        console.print("[red]❌  Subject cannot be empty.[/red]\n")
        return

    description = get_text("Description (e.g. Final Project submission)")
    if not description:
        console.print("[red]❌  Description cannot be empty.[/red]\n")
        return

    due_date = get_date("Due date (MM-DD-YYYY, e.g. 05-09-2026)")

    action = questionary.select(
        f"{subject} — {description} | {due_date.strftime('%m-%d-%Y')}",
        choices=[
            questionary.Choice(title="  ✔  Add", value="add"),
            questionary.Choice(title="  ✖  Cancel", value="cancel"),
        ],
        instruction=" ",
    ).ask()

    if action != "add":
        console.print("[dim]Cancelled. Nothing was added.[/dim]\n")
        return

    tracker.add(subject, description, due_date)
    console.print(f"\n  [green]✅  Added:[/green] [bold]{subject}[/bold] — due [cyan]{due_date.strftime('%m-%d-%Y')}[/cyan]\n")


def action_mark_done(tracker: DeadlineTracker) -> None:
    """
    Marks a deadline as done via numbered selection.

    Args:
        tracker (DeadlineTracker): Active tracker instance.
    """
    pending = [d for d in tracker.sorted_deadlines() if not d.is_done]
    if not pending:
        console.print("[yellow]⚠️   No pending deadlines.[/yellow]\n")
        return

    display_table(tracker, title="[bold cyan]📋 Your Deadlines[/bold cyan]", border_style="bright_blue")

    total = len(tracker.deadlines)

    action = questionary.select(
        "What do you want to do?",
        choices=[
            questionary.Choice(title="  ✅  Type deadline number to mark as done", value="type"),
            questionary.Choice(title="  ✖  Cancel", value="cancel"),
        ],
    ).ask()

    if action != "type":
        console.print("[dim]Cancelled.[/dim]\n")
        return

    raw = questionary.text(f"  Enter deadline # (1–{total}):").ask()
    if raw is None or not raw.strip():
        console.print("[dim]Cancelled.[/dim]\n")
        return

    try:
        index = int(raw.strip())
    except ValueError:
        console.print("[red]❌  Invalid number.[/red]\n")
        return

    if not (1 <= index <= total):
        console.print(f"[red]❌  Please enter a number between 1 and {total}.[/red]\n")
        return

    subject = tracker.mark_done_by_index(index)

    if subject:
        console.print(f"\n  [green]✅  [{subject}] marked as done![/green]\n")
    else:
        console.print("[red]❌  Already done or not found.[/red]\n")


def action_delete(tracker: DeadlineTracker) -> None:
    """
    Deletes a deadline via numbered selection with confirmation.

    Args:
        tracker (DeadlineTracker): Active tracker instance.
    """
    if not tracker.deadlines:
        console.print("[yellow]⚠️   No deadlines to delete.[/yellow]\n")
        return

    display_table(tracker, title="[bold cyan]📋 Your Deadlines[/bold cyan]", border_style="bright_blue")

    total = len(tracker.deadlines)

    action = questionary.select(
        "What do you want to do?",
        choices=[
            questionary.Choice(title="  🗑️  Type deadline number to delete", value="type"),
            questionary.Choice(title="  ✖  Cancel", value="cancel"),
        ],
    ).ask()

    if action != "type":
        console.print("[dim]Cancelled.[/dim]\n")
        return

    raw = questionary.text(f"  Enter deadline # (1–{total}):").ask()
    if raw is None or not raw.strip():
        console.print("[dim]Cancelled.[/dim]\n")
        return

    try:
        index = int(raw.strip())
    except ValueError:
        console.print("[red]❌  Invalid number.[/red]\n")
        return

    if not (1 <= index <= total):
        console.print(f"[red]❌  Please enter a number between 1 and {total}.[/red]\n")
        return

    target = tracker.get_by_index(index)
    if target is None:
        console.print("[red]❌  Not found.[/red]\n")
        return

    confirm = questionary.confirm(
        f"Delete [{target.subject}] — {target.description}?"
    ).ask()

    if confirm:
        tracker.delete_by_index(index)
        console.print(f"\n  [red]🗑️   [{target.subject}] deleted.[/red]\n")
    else:
        console.print("[dim]Cancelled. Nothing was deleted.[/dim]\n")


def action_stats(tracker: DeadlineTracker) -> None:
    """
    Displays deadline statistics in a styled panel.

    Args:
        tracker (DeadlineTracker): Active tracker instance.
    """
    if not tracker.deadlines:
        console.print("[yellow]⚠️   No deadlines yet.[/yellow]\n")
        return
    tracker.show_stats()


# ------------------------------------------------------------------ #
#  Main
# ------------------------------------------------------------------ #

def main() -> None:
    """
    Main loop: renders menu via questionary and routes to actions.
    """
    tracker = DeadlineTracker()

    console.print(BANNER)
    console.print(f"  [dim]Today is {date.today().strftime('%A, %B %d, %Y')}[/dim]\n")

    action_map = {
        "1. Add deadline":       action_add,
        "2. View all deadlines": lambda t: display_table(t),
        "3. Mark as done":       action_mark_done,
        "4. Delete deadline":    action_delete,
        "5. View stats":         action_stats,
    }

    while True:
        choice = questionary.select(
            "What do you want to do?",
            choices=MENU_CHOICES,
        ).ask()

        if choice is None or choice == "6. Exit":
            console.print("\n  [cyan]👋  Goodbye! Stay on top of your deadlines![/cyan]\n")
            break

        if choice in action_map:
            try:
                action_map[choice](tracker)
            except Exception as exc:
                console.print(f"\n  [bold red]❌ Unexpected error:[/bold red] {exc}\n")


if __name__ == "__main__":
    main()
