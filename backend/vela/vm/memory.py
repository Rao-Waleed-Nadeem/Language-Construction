"""Virtual Machine Segmented Memory Architecture.

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §4.1
- Master Spec P7-07
- Segments: Static Data, Stack (frames & spills), Heap (dynamic arrays).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VMMemory:
    """Segmented memory subsystem for the Virtual Machine."""

    globals: dict[str, Any] = field(default_factory=dict)
    stack: dict[int, Any] = field(default_factory=dict)
    heap: dict[int, list[Any]] = field(default_factory=dict)
    next_heap_id: int = 1000

    def alloc_array(self, size: int, fill: Any = 0) -> int:
        """Allocate a new array buffer on the heap and return its handle/address."""
        handle = self.next_heap_id
        self.next_heap_id += 1
        self.heap[handle] = [fill] * size
        return handle

    def read_array(self, handle: int, index: int) -> Any:
        """Read an element from a heap array buffer."""
        if handle not in self.heap:
            raise KeyError(f"Invalid heap array handle {handle}")
        arr = self.heap[handle]
        if index < 0 or index >= len(arr):
            raise IndexError(f"Array index {index} out of bounds (size {len(arr)})")
        return arr[index]

    def write_array(self, handle: int, index: int, val: Any) -> None:
        """Write an element into a heap array buffer."""
        if handle not in self.heap:
            raise KeyError(f"Invalid heap array handle {handle}")
        arr = self.heap[handle]
        if index < 0 or index >= len(arr):
            raise IndexError(f"Array index {index} out of bounds (size {len(arr)})")
        arr[index] = val

    def to_dict(self) -> dict[str, Any]:
        return {
            "globals": dict(self.globals),
            "stack_size": len(self.stack),
            "heap_count": len(self.heap),
        }
