"""
deadline.py
-----------
Defines the Deadline class representing one academic deadline entry.
"""

from datetime import date
from typing import Optional


class Deadline:
    """
    Represents a single academic deadline.

    Attributes:
        subject (str): Subject or course name.
        description (str): Short task description.
        due_date (date): The date the task is due.
        is_done (bool): Whether the task is completed.
    """

    def __init__(
        self,
        subject: str,
        description: str,
        due_date: date,
        is_done: bool = False,
    ) -> None:
        """
        Initializes a Deadline instance.

        Args:
            subject (str): Subject or course name.
            description (str): Task description.
            due_date (date): Due date.
            is_done (bool): Completion flag. Defaults to False.
        """
        self.subject: str = subject
        self.description: str = description
        self.due_date: date = due_date
        self.is_done: bool = is_done

    def days_left(self) -> int:
        """
        Calculates days remaining until due date.

        Returns:
            int: Days left. Negative value means overdue.
        """
        return (self.due_date - date.today()).days

    def mark_done(self) -> None:
        """Marks this deadline as completed."""
        self.is_done = True

    def get_status(self) -> str:
        """
        Returns urgency status label based on days remaining.

        Returns:
            str: Status string with emoji.
        """
        if self.is_done:
            return "DONE"
        d: int = self.days_left()
        if d < 0:
            return "OVERDUE"
        elif d <= 2:
            return "DUE SOON"
        elif d <= 7:
            return "URGENT"
        else:
            return "UPCOMING"

    def get_status_emoji(self) -> str:
        """
        Returns the emoji icon for the current status.

        Returns:
            str: Emoji string.
        """
        icons = {
            "DONE":     "✅",
            "OVERDUE":  "💀",
            "DUE SOON": "🔴",
            "URGENT":   "⚠️ ",
            "UPCOMING": "📌",
        }
        return icons.get(self.get_status(), "📌")

    def to_dict(self) -> dict:
        """
        Serializes the Deadline to a dict for JSON storage.

        Returns:
            dict: Dictionary representation.
        """
        return {
            "subject": self.subject,
            "description": self.description,
            "due_date": self.due_date.isoformat(),
            "is_done": self.is_done,
        }

    @staticmethod
    def from_dict(data: dict) -> "Deadline":
        """
        Deserializes a dict into a Deadline object.

        Args:
            data (dict): Dictionary with deadline fields.

        Returns:
            Deadline: Reconstructed instance.
        """
        return Deadline(
            subject=data["subject"],
            description=data["description"],
            due_date=date.fromisoformat(data["due_date"]),
            is_done=data["is_done"],
        )

    def __str__(self) -> str:
        return f"{self.subject} | {self.description} | {self.due_date.strftime('%m-%d-%Y')}"
