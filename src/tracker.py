"""
tracker.py
----------
Defines the DeadlineTracker class that manages all Deadline objects.
Handles add, view, mark done, delete, stats, save, and load.
"""

import json
import os
import statistics
from datetime import date
from typing import List, Optional

from deadline import Deadline


DATA_FILE: str = os.path.join(os.path.dirname(__file__), "../data/deadlines.json")


class DeadlineTracker:
    """
    Manages a list of Deadline objects with full CRUD and persistence.

    Attributes:
        deadlines (List[Deadline]): All stored deadlines.
    """

    def __init__(self) -> None:
        """Initializes the tracker and loads saved deadlines from disk."""
        self.deadlines: List[Deadline] = []
        self.load()

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def sorted_deadlines(self) -> List[Deadline]:
        """
        Returns deadlines sorted by urgency (overdue first, done last).

        Returns:
            List[Deadline]: Sorted list.
        """
        def sort_key(d: Deadline):
            if d.is_done:
                return (2, 0)
            days = d.days_left()
            return (0 if days < 0 else 1, days)
        return sorted(self.deadlines, key=sort_key)

    def get_by_index(self, index: int) -> Optional[Deadline]:
        """
        Returns a Deadline by its 1-based display index.

        Args:
            index (int): 1-based row number from the table.

        Returns:
            Optional[Deadline]: Matching deadline or None.
        """
        lst = self.sorted_deadlines()
        if 1 <= index <= len(lst):
            return lst[index - 1]
        return None

    # ------------------------------------------------------------------ #
    #  CRUD
    # ------------------------------------------------------------------ #

    def add(self, subject: str, description: str, due_date: date) -> None:
        """
        Adds a new deadline and saves to disk.

        Args:
            subject (str): Subject name.
            description (str): Task description.
            due_date (date): Due date.
        """
        self.deadlines.append(Deadline(subject, description, due_date))
        self.save()

    def mark_done_by_index(self, index: int) -> Optional[str]:
        """
        Marks a deadline as done by its table row number.

        Args:
            index (int): 1-based row number.

        Returns:
            Optional[str]: Subject name if successful, None otherwise.
        """
        d = self.get_by_index(index)
        if d is None or d.is_done:
            return None
        d.mark_done()
        self.save()
        return d.subject

    def delete_by_index(self, index: int) -> Optional[str]:
        """
        Deletes a deadline by its table row number.

        Args:
            index (int): 1-based row number.

        Returns:
            Optional[str]: Subject name if deleted, None if not found.
        """
        d = self.get_by_index(index)
        if d is None:
            return None
        subject: str = d.subject
        self.deadlines.remove(d)
        self.save()
        return subject

    # ------------------------------------------------------------------ #
    #  Display
    # ------------------------------------------------------------------ #

    def display_table(self) -> None:
        """
        Prints all deadlines as a numbered table sorted by urgency.
        Format: # | STATUS | SUBJECT | DESCRIPTION | DEADLINE | DAYS LEFT
        """
        if not self.deadlines:
            print("\n  No deadlines found. Add one!\n")
            return

        lst = self.sorted_deadlines()

        W_NUM  = 5
        W_EMO  = 3
        W_STA  = 10
        W_SUB  = 22
        W_DES  = 30
        W_DEA  = 12
        W_DAY  = 10

        total_width = W_NUM + W_EMO + W_STA + W_SUB + W_DES + W_DEA + W_DAY + 14

        print()
        print(
            f"  {'#':<{W_NUM}} {'':>{W_EMO}} {'STATUS':<{W_STA}} "
            f"{'SUBJECT':<{W_SUB}} {'DESCRIPTION':<{W_DES}} "
            f"{'DEADLINE':<{W_DEA}} {'DAYS LEFT':<{W_DAY}}"
        )
        print("  " + "-" * total_width)

        for i, d in enumerate(lst, 1):
            num      = f"[{i}]"
            emoji    = d.get_status_emoji()
            status   = d.get_status()
            subject  = d.subject[:W_SUB - 1]
            desc     = d.description[:W_DES - 1]
            deadline = d.due_date.strftime("%m-%d-%Y")

            if d.is_done:
                days_str = "Done ✓"
            else:
                days = d.days_left()
                if days < 0:
                    days_str = f"{abs(days)}d ago"
                elif days == 0:
                    days_str = "TODAY"
                elif days == 1:
                    days_str = "1 day"
                else:
                    days_str = f"{days} days"

            print(
                f"  {num:<{W_NUM}} {emoji:<{W_EMO}} {status:<{W_STA}} "
                f"{subject:<{W_SUB}} {desc:<{W_DES}} "
                f"{deadline:<{W_DEA}} {days_str:<{W_DAY}}"
            )

        print()

    # ------------------------------------------------------------------ #
    #  Stats
    # ------------------------------------------------------------------ #

    def show_stats(self) -> None:
        """
        Displays statistics using rich: totals, averages, most urgent.
        Uses the statistics module for mean calculation.
        """
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box

        console = Console()
        pending: List[Deadline] = [d for d in self.deadlines if not d.is_done]
        done_count: int = len(self.deadlines) - len(pending)

        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Key",   style="dim",        width=20)
        table.add_column("Value", style="bold white",  width=30)

        table.add_row("Total deadlines",  str(len(self.deadlines)))
        table.add_row("Completed",        f"[green]{done_count}[/green]")
        table.add_row("Pending",          f"[yellow]{len(pending)}[/yellow]")

        if pending:
            days_list: List[int] = [d.days_left() for d in pending]
            avg: float = statistics.mean(days_list)
            nearest: Deadline = min(pending, key=lambda d: d.days_left())
            overdue: int = sum(1 for x in days_list if x < 0)
            table.add_row("Avg days left",    f"[cyan]{avg:.1f} days[/cyan]")
            table.add_row("Most urgent",      f"[red]{nearest.subject}[/red] ({nearest.days_left()}d left)")
            table.add_row("Overdue tasks",    f"[bold red]{overdue}[/bold red]")

        console.print(Panel(table, title="[bold cyan]📊 Stats[/bold cyan]", box=box.ROUNDED))
        console.print()

    # ------------------------------------------------------------------ #
    #  Persistence
    # ------------------------------------------------------------------ #

    def save(self) -> None:
        """Saves all deadlines to a JSON file on disk."""
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump([d.to_dict() for d in self.deadlines], f, indent=2)

    def load(self) -> None:
        """Loads deadlines from JSON file if it exists."""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                raw = json.load(f)
                self.deadlines = [Deadline.from_dict(item) for item in raw]
