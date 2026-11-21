"""Cooperative resource budget tracking.

Per doc 02 §1 (AP-9) and doc 02 §10:
Cooperative resource budgets (steps, nodes, states, output size) instead of killing threads.
Every loop that can grow with user input checks a budget.
"""

from __future__ import annotations

import time


class BudgetExceededError(Exception):
    """Raised when an operation exceeds its configured cooperative budget."""

    def __init__(self, resource: str, limit: int, current: int) -> None:
        super().__init__(
            f"Resource budget exceeded for {resource}: limit={limit}, current={current}"
        )
        self.resource = resource
        self.limit = limit
        self.current = current


class Budget:
    """Cooperative budget counter for steps, nodes, iterations, or time."""

    def __init__(
        self,
        resource: str,
        limit: int,
        timeout_seconds: float | None = None,
    ) -> None:
        self.resource = resource
        self.limit = limit
        self.timeout_seconds = timeout_seconds
        self.count = 0
        self.start_time = time.monotonic()
        self.is_truncated = False

    def tick(self, increment: int = 1) -> None:
        """Increment the budget counter and check limits.

        Raises BudgetExceededError if limit is reached.
        """
        self.count += increment
        if self.count > self.limit:
            self.is_truncated = True
            raise BudgetExceededError(self.resource, self.limit, self.count)

        if self.timeout_seconds is not None:
            elapsed = time.monotonic() - self.start_time
            if elapsed > self.timeout_seconds:
                self.is_truncated = True
                raise BudgetExceededError(
                    f"{self.resource} (time)",
                    int(self.timeout_seconds),
                    int(elapsed),
                )

    def check_soft(self, increment: int = 1) -> bool:
        """Increment count; return True if within budget, False if limit exceeded without raising."""
        self.count += increment
        if self.count > self.limit:
            self.is_truncated = True
            return False
        return True

    def reset(self) -> None:
        self.count = 0
        self.start_time = time.monotonic()
        self.is_truncated = False
