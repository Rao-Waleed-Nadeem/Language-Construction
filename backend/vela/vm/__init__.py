"""Virtual Machine Package (Phase 7).

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §4
- Master Spec P7-07
"""

from vela.vm.cpu import CPUState
from vela.vm.machine import VirtualMachine, VMResult, VMSnapshot
from vela.vm.memory import VMMemory

__all__ = [
    "CPUState",
    "VMMemory",
    "VMResult",
    "VMSnapshot",
    "VirtualMachine",
]
