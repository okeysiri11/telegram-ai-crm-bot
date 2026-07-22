# Yard Management Engine — blocks, rows, slots, assignment, relocation, density.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.shared.events import ContainerReleasedEvent
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminal_operations.events import (
    ContainerMovedEvent,
    ContainerStoredEvent,
)
from applications.port_erp.terminal_operations.models import (
    YardBlock,
    YardRelocation,
    YardSlot,
    YardSlotStatus,
)


class YardManagementEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def create_block(self, block: YardBlock) -> YardBlock:
        if not block.name:
            raise ValidationError("name is required")
        if block.rows <= 0 or block.slots_per_row <= 0:
            raise ValidationError("rows and slots_per_row must be positive")
        saved = self._store.yard_blocks.save(block.block_id, block)
        for row in range(1, block.rows + 1):
            for bay in range(1, block.slots_per_row + 1):
                slot = YardSlot(
                    block_id=block.block_id,
                    terminal_id=block.terminal_id,
                    row=row,
                    bay=bay,
                    tier=1,
                )
                self._store.yard_slots.save(slot.slot_id, slot)
        return saved

    def get_block(self, block_id: str) -> YardBlock:
        block = self._store.yard_blocks.get(block_id)
        if block is None:
            raise NotFoundError("YardBlock", block_id)
        return block

    def list_blocks(self, *, terminal_id: str | None = None) -> list[YardBlock]:
        items = self._store.yard_blocks.list_all()
        if terminal_id:
            items = [b for b in items if b.terminal_id == terminal_id]
        return items

    def list_slots(self, *, block_id: str | None = None, status: YardSlotStatus | None = None) -> list[YardSlot]:
        items = self._store.yard_slots.list_all()
        if block_id:
            items = [s for s in items if s.block_id == block_id]
        if status:
            items = [s for s in items if s.status == status]
        return items

    def get_slot(self, slot_id: str) -> YardSlot:
        slot = self._store.yard_slots.get(slot_id)
        if slot is None:
            raise NotFoundError("YardSlot", slot_id)
        return slot

    def _empty_slots(self, *, terminal_id: str = "", block_id: str = "") -> list[YardSlot]:
        slots = self.list_slots(status=YardSlotStatus.EMPTY)
        if block_id:
            slots = [s for s in slots if s.block_id == block_id]
        if terminal_id:
            slots = [s for s in slots if s.terminal_id == terminal_id]
        return sorted(slots, key=lambda s: (s.block_id, s.row, s.bay, s.tier))

    async def assign_slot(
        self,
        container_id: str,
        *,
        terminal_id: str = "",
        block_id: str = "",
    ) -> YardSlot:
        if not container_id:
            raise ValidationError("container_id is required")
        candidates = self._empty_slots(terminal_id=terminal_id, block_id=block_id)
        if not candidates:
            raise ValidationError("no empty yard slots available")
        slot = candidates[0]
        slot.status = YardSlotStatus.OCCUPIED
        slot.container_id = container_id
        saved = self._store.yard_slots.save(slot.slot_id, slot)
        await publish(
            ContainerStoredEvent(
                container_id=container_id,
                slot_id=saved.slot_id,
                block_id=saved.block_id,
                terminal_id=saved.terminal_id,
            )
        )
        return saved

    async def relocate(
        self,
        container_id: str,
        *,
        to_slot_id: str = "",
        reason: str = "optimize",
    ) -> YardRelocation:
        current = next(
            (s for s in self._store.yard_slots.list_all() if s.container_id == container_id),
            None,
        )
        if current is None:
            raise NotFoundError("YardSlot(container)", container_id)
        if to_slot_id:
            target = self.get_slot(to_slot_id)
            if target.status != YardSlotStatus.EMPTY:
                raise ValidationError("target slot is not empty")
        else:
            candidates = self._empty_slots(terminal_id=current.terminal_id)
            if not candidates:
                raise ValidationError("no empty yard slots available")
            target = candidates[0]

        from_id = current.slot_id
        current.status = YardSlotStatus.EMPTY
        current.container_id = ""
        self._store.yard_slots.save(current.slot_id, current)

        target.status = YardSlotStatus.OCCUPIED
        target.container_id = container_id
        self._store.yard_slots.save(target.slot_id, target)

        relocation = YardRelocation(
            container_id=container_id,
            from_slot_id=from_id,
            to_slot_id=target.slot_id,
            reason=reason,
        )
        saved = self._store.yard_relocations.save(relocation.relocation_id, relocation)
        await publish(
            ContainerMovedEvent(
                container_id=container_id,
                from_slot_id=from_id,
                to_slot_id=target.slot_id,
                terminal_id=target.terminal_id,
            )
        )
        return saved

    async def release_container(self, container_id: str) -> YardSlot:
        current = next(
            (s for s in self._store.yard_slots.list_all() if s.container_id == container_id),
            None,
        )
        if current is None:
            raise NotFoundError("YardSlot(container)", container_id)
        slot_id = current.slot_id
        terminal_id = current.terminal_id
        current.status = YardSlotStatus.EMPTY
        current.container_id = ""
        saved = self._store.yard_slots.save(current.slot_id, current)
        await publish(
            ContainerReleasedEvent(
                container_id=container_id,
                terminal_id=terminal_id,
                container_number="",
            )
        )
        return saved

    def stack_plan(self, block_id: str) -> dict:
        block = self.get_block(block_id)
        slots = self.list_slots(block_id=block_id)
        occupied = [s for s in slots if s.status == YardSlotStatus.OCCUPIED]
        return {
            "block_id": block_id,
            "name": block.name,
            "max_tiers": block.max_tiers,
            "total_slots": len(slots),
            "occupied": len(occupied),
            "by_row": {
                str(row): len([s for s in occupied if s.row == row])
                for row in range(1, block.rows + 1)
            },
        }

    def density(self, *, terminal_id: str = "") -> dict:
        slots = self.list_slots()
        if terminal_id:
            slots = [s for s in slots if s.terminal_id == terminal_id]
        total = len(slots)
        occupied = len([s for s in slots if s.status == YardSlotStatus.OCCUPIED])
        return {
            "terminal_id": terminal_id,
            "total_slots": total,
            "occupied": occupied,
            "empty": total - occupied,
            "density": round(occupied / total, 4) if total else 0.0,
        }

    def optimize_density(self, *, terminal_id: str = "") -> dict:
        """Prefer filling lower rows/bays first — report imbalance for planning."""
        density = self.density(terminal_id=terminal_id)
        blocks = self.list_blocks(terminal_id=terminal_id or None)
        suggestions = []
        for block in blocks:
            plan = self.stack_plan(block.block_id)
            if plan["occupied"] and plan["total_slots"]:
                row_counts = [plan["by_row"].get(str(r), 0) for r in range(1, block.rows + 1)]
                if max(row_counts) - min(row_counts) > 1:
                    suggestions.append(
                        {
                            "block_id": block.block_id,
                            "action": "rebalance_rows",
                            "row_counts": row_counts,
                        }
                    )
        return {"density": density, "suggestions": suggestions}


yard_management_engine = YardManagementEngine()
