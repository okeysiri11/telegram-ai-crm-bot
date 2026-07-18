# Automotive Marketplace Connector Layer v1 — unified vehicle import orchestration.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from connectors.automotive_marketplace_connectors import (
    NormalizedListing,
    get_connector,
)
from database.models.automotive_marketplace import (
    ConnectorType,
    ImportJobStatus,
    ImportLogAction,
    ImportLogLevel,
)
from database.models.automotive_inventory import VehicleStatus
from database.session import get_session
from repositories.automotive_inventory_repository import (
    VehicleImageRepository,
    VehicleRepository,
)
from repositories.automotive_marketplace_repository import (
    ConnectorCredentialRepository,
    VehicleImportJobRepository,
    VehicleImportLogRepository,
)
from repositories.user_role_repository import UserRoleRepository

MARKETPLACE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class AutomotiveMarketplaceEngineError(Exception):
    pass


class AutomotiveMarketplaceEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in MARKETPLACE_ROLES for role in roles)

    @staticmethod
    async def _publish_event(
        event_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from events.crm_publisher import publish_crm_event

            await publish_crm_event(
                event_type,
                "vehicle",
                aggregate_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    def _credential_snapshot(cred) -> dict[str, Any]:
        return {
            "id": str(cred.id),
            "connector_type": cred.connector_type,
            "base_url": cred.base_url,
            "is_active": cred.is_active,
            "sync_interval_minutes": cred.sync_interval_minutes,
            "last_sync_at": (
                cred.last_sync_at.isoformat() if cred.last_sync_at else None
            ),
            "has_api_key": bool(cred.api_key),
        }

    @staticmethod
    def _job_snapshot(job) -> dict[str, Any]:
        return {
            "id": str(job.id),
            "connector_type": job.connector_type,
            "status": job.status,
            "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "is_scheduled": job.is_scheduled,
            "created_count": job.created_count,
            "updated_count": job.updated_count,
            "skipped_count": job.skipped_count,
            "duplicate_count": job.duplicate_count,
            "images_synced": job.images_synced,
            "price_changes": job.price_changes,
            "error_message": job.error_message,
        }

    @staticmethod
    def _log_snapshot(log) -> dict[str, Any]:
        return {
            "id": str(log.id),
            "action": log.action,
            "level": log.level,
            "external_id": log.external_id,
            "vin": log.vin,
            "vehicle_id": str(log.vehicle_id) if log.vehicle_id else None,
            "message": log.message,
            "old_price": str(log.old_price) if log.old_price is not None else None,
            "new_price": str(log.new_price) if log.new_price is not None else None,
            "created_at": log.created_at.isoformat(),
        }

    @staticmethod
    def _stock_number(connector_type: str, external_id: str) -> str:
        prefix = connector_type[:3]
        safe = external_id.replace(" ", "")[:20]
        return f"{prefix}-{safe}"

    @staticmethod
    async def register_connector_credentials(
        actor_id: int,
        *,
        connector_type: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not await AutomotiveMarketplaceEngineV1.user_can_access(actor_id):
            raise AutomotiveMarketplaceEngineError("Access denied")
        if connector_type not in {t.value for t in ConnectorType}:
            raise AutomotiveMarketplaceEngineError(f"Invalid connector: {connector_type}")

        async with get_session() as session:
            cred = await ConnectorCredentialRepository(session).upsert(
                connector_type=connector_type,
                **fields,
            )
            return AutomotiveMarketplaceEngineV1._credential_snapshot(cred)

    @staticmethod
    async def schedule_import_job(
        actor_id: int,
        connector_type: str,
        *,
        scheduled_at: datetime | None = None,
    ) -> dict[str, Any]:
        if not await AutomotiveMarketplaceEngineV1.user_can_access(actor_id):
            raise AutomotiveMarketplaceEngineError("Access denied")

        when = scheduled_at or datetime.now(timezone.utc)
        async with get_session() as session:
            job = await VehicleImportJobRepository(session).create(
                connector_type=connector_type,
                scheduled_at=when,
                triggered_by=actor_id,
                is_scheduled=True,
            )
            return AutomotiveMarketplaceEngineV1._job_snapshot(job)

    @staticmethod
    async def _sync_images(
        session,
        *,
        vehicle_id: uuid.UUID,
        images: list[str],
        job_id: uuid.UUID,
        log_repo: VehicleImportLogRepository,
        vin: str,
    ) -> int:
        if not images:
            return 0

        image_repo = VehicleImageRepository(session)
        existing = await image_repo.list_by_vehicle(vehicle_id)
        existing_urls = {img.url for img in existing}
        synced = 0

        for index, url in enumerate(images):
            if url in existing_urls:
                continue
            await image_repo.create(
                vehicle_id=vehicle_id,
                url=url,
                image_type="EXTERIOR" if index == 0 else "DETAIL",
                sort_order=index,
            )
            synced += 1

        if synced:
            await log_repo.record(
                job_id=job_id,
                action=ImportLogAction.IMAGE_SYNCED.value,
                vin=vin,
                vehicle_id=vehicle_id,
                message=f"Synced {synced} image(s)",
            )
        return synced

    @staticmethod
    async def _process_listing(
        session,
        *,
        job_id: uuid.UUID,
        connector_type: str,
        listing: NormalizedListing,
        auto_update: bool,
        skip_duplicates: bool,
    ) -> dict[str, int]:
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "duplicate": 0,
            "images": 0,
            "price_changes": 0,
        }
        vehicle_repo = VehicleRepository(session)
        log_repo = VehicleImportLogRepository(session)

        if not listing.vin:
            await log_repo.record(
                job_id=job_id,
                action=ImportLogAction.ERROR.value,
                level=ImportLogLevel.ERROR.value,
                external_id=listing.external_id,
                message="Missing VIN",
            )
            stats["skipped"] += 1
            return stats

        existing = await vehicle_repo.get_by_vin(listing.vin)
        if existing is not None:
            if skip_duplicates and not auto_update:
                await log_repo.record(
                    job_id=job_id,
                    action=ImportLogAction.SKIPPED_DUPLICATE.value,
                    level=ImportLogLevel.WARNING.value,
                    external_id=listing.external_id,
                    vin=listing.vin,
                    vehicle_id=existing.id,
                    message="Duplicate VIN detected",
                )
                stats["duplicate"] += 1
                return stats

            old_price = existing.purchase_price or existing.target_price
            new_price = listing.price
            updates: dict[str, Any] = {}
            if listing.make:
                updates["make"] = listing.make
            if listing.model:
                updates["model"] = listing.model
            if listing.year:
                updates["year"] = listing.year
            if listing.mileage is not None:
                updates["mileage"] = listing.mileage
            if listing.color:
                updates["color"] = listing.color
            if new_price is not None:
                updates["purchase_price"] = new_price
                updates["target_price"] = new_price

            if updates:
                await vehicle_repo.update_fields(existing.id, **updates)

            if (
                new_price is not None
                and old_price is not None
                and new_price != old_price
            ):
                await log_repo.record(
                    job_id=job_id,
                    action=ImportLogAction.PRICE_CHANGED.value,
                    external_id=listing.external_id,
                    vin=listing.vin,
                    vehicle_id=existing.id,
                    old_price=old_price,
                    new_price=new_price,
                    currency=listing.currency,
                    message="Price updated from marketplace",
                )
                await AutomotiveMarketplaceEngineV1._publish_event(
                    "vehicle.price.changed",
                    existing.id,
                    {
                        "vehicle_id": str(existing.id),
                        "vin": listing.vin,
                        "old_price": str(old_price),
                        "new_price": str(new_price),
                        "connector_type": connector_type,
                    },
                )
                stats["price_changes"] += 1

            stats["images"] += await AutomotiveMarketplaceEngineV1._sync_images(
                session,
                vehicle_id=existing.id,
                images=listing.images,
                job_id=job_id,
                log_repo=log_repo,
                vin=listing.vin,
            )

            await log_repo.record(
                job_id=job_id,
                action=ImportLogAction.UPDATED.value,
                external_id=listing.external_id,
                vin=listing.vin,
                vehicle_id=existing.id,
                message="Vehicle updated from import",
            )
            stats["updated"] += 1
            return stats

        stock_number = AutomotiveMarketplaceEngineV1._stock_number(
            connector_type,
            listing.external_id,
        )

        vehicle = await vehicle_repo.create(
            vin=listing.vin,
            stock_number=stock_number,
            make=listing.make,
            model=listing.model,
            year=listing.year,
            mileage=listing.mileage,
            color=listing.color,
            fuel_type=listing.fuel_type,
            transmission=listing.transmission,
            purchase_price=listing.price,
            target_price=listing.price,
            currency=listing.currency,
            status=VehicleStatus.IN_TRANSIT.value,
            notes=f"Imported from {connector_type} ({listing.external_id})",
        )
        stats["images"] += await AutomotiveMarketplaceEngineV1._sync_images(
            session,
            vehicle_id=vehicle.id,
            images=listing.images,
            job_id=job_id,
            log_repo=log_repo,
            vin=listing.vin,
        )
        await log_repo.record(
            job_id=job_id,
            action=ImportLogAction.CREATED.value,
            external_id=listing.external_id,
            vin=listing.vin,
            vehicle_id=vehicle.id,
            message="Vehicle created from import",
        )
        stats["created"] += 1
        return stats

    @staticmethod
    async def run_import_job(
        actor_id: int,
        job_id: uuid.UUID,
        *,
        listings: list[NormalizedListing] | None = None,
        auto_update: bool = True,
        skip_duplicates: bool = True,
        limit: int = 100,
    ) -> dict[str, Any]:
        if not await AutomotiveMarketplaceEngineV1.user_can_access(actor_id):
            raise AutomotiveMarketplaceEngineError("Access denied")

        async with get_session() as session:
            job_repo = VehicleImportJobRepository(session)
            job = await job_repo.get_by_id(job_id)
            if job is None:
                raise AutomotiveMarketplaceEngineError(f"Import job not found: {job_id}")
            if job.status not in {
                ImportJobStatus.PENDING.value,
                ImportJobStatus.FAILED.value,
            }:
                raise AutomotiveMarketplaceEngineError(
                    f"Import job cannot run in status: {job.status}"
                )

            job = await job_repo.start(job_id)
            await AutomotiveMarketplaceEngineV1._publish_event(
                "vehicle.import.started",
                job_id,
                {
                    "job_id": str(job_id),
                    "connector_type": job.connector_type,
                    "triggered_by": actor_id,
                },
            )

            totals = {
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "duplicate": 0,
                "images": 0,
                "price_changes": 0,
            }

            try:
                cred_repo = ConnectorCredentialRepository(session)
                credentials = await cred_repo.get_by_type(job.connector_type)
                if listings is None:
                    connector = get_connector(job.connector_type)
                    listings = await connector.fetch_listings(
                        credentials,
                        limit=limit,
                    )

                for listing in listings:
                    result = await AutomotiveMarketplaceEngineV1._process_listing(
                        session,
                        job_id=job_id,
                        connector_type=job.connector_type,
                        listing=listing,
                        auto_update=auto_update,
                        skip_duplicates=skip_duplicates,
                    )
                    for key in totals:
                        totals[key] += result.get(key, 0)

                await cred_repo.mark_synced(job.connector_type)
                job = await job_repo.complete(
                    job_id,
                    created_count=totals["created"],
                    updated_count=totals["updated"],
                    skipped_count=totals["skipped"],
                    duplicate_count=totals["duplicate"],
                    images_synced=totals["images"],
                    price_changes=totals["price_changes"],
                )
            except Exception as exc:
                await VehicleImportLogRepository(session).record(
                    job_id=job_id,
                    action=ImportLogAction.ERROR.value,
                    level=ImportLogLevel.ERROR.value,
                    message=str(exc),
                )
                job = await job_repo.complete(
                    job_id,
                    status=ImportJobStatus.FAILED.value,
                    error_message=str(exc),
                )
                raise AutomotiveMarketplaceEngineError(str(exc)) from exc

            await AutomotiveMarketplaceEngineV1._publish_event(
                "vehicle.import.completed",
                job_id,
                {
                    "job_id": str(job_id),
                    "connector_type": job.connector_type,
                    **totals,
                },
            )

            logs = await VehicleImportLogRepository(session).list_by_job(job_id)
            return {
                "job": AutomotiveMarketplaceEngineV1._job_snapshot(job),
                "logs": [AutomotiveMarketplaceEngineV1._log_snapshot(l) for l in logs],
            }

    @staticmethod
    async def run_scheduled_syncs(
        actor_id: int,
    ) -> list[dict[str, Any]]:
        if not await AutomotiveMarketplaceEngineV1.user_can_access(actor_id):
            raise AutomotiveMarketplaceEngineError("Access denied")

        now = datetime.now(timezone.utc)
        results: list[dict[str, Any]] = []

        async with get_session() as session:
            cred_repo = ConnectorCredentialRepository(session)
            due_creds = await cred_repo.list_due_for_sync(now)
            job_repo = VehicleImportJobRepository(session)

            for cred in due_creds:
                job = await job_repo.create(
                    connector_type=cred.connector_type,
                    scheduled_at=now,
                    triggered_by=actor_id,
                    is_scheduled=True,
                )
                results.append({"scheduled_job": AutomotiveMarketplaceEngineV1._job_snapshot(job)})

            pending = await job_repo.list_pending_scheduled(now)

        for entry in results:
            job_id = uuid.UUID(entry["scheduled_job"]["id"])
            entry["result"] = await AutomotiveMarketplaceEngineV1.run_import_job(
                actor_id,
                job_id,
            )

        for job in pending:
            if any(r["scheduled_job"]["id"] == str(job.id) for r in results):
                continue
            result = await AutomotiveMarketplaceEngineV1.run_import_job(
                actor_id,
                job.id,
            )
            results.append({
                "scheduled_job": AutomotiveMarketplaceEngineV1._job_snapshot(job),
                "result": result,
            })

        return results

    @staticmethod
    async def import_listings(
        actor_id: int,
        connector_type: str,
        listings: list[NormalizedListing],
        *,
        auto_update: bool = True,
        skip_duplicates: bool = True,
    ) -> dict[str, Any]:
        if not await AutomotiveMarketplaceEngineV1.user_can_access(actor_id):
            raise AutomotiveMarketplaceEngineError("Access denied")

        async with get_session() as session:
            job = await VehicleImportJobRepository(session).create(
                connector_type=connector_type,
                triggered_by=actor_id,
                is_scheduled=False,
            )
            job_id = job.id

        return await AutomotiveMarketplaceEngineV1.run_import_job(
            actor_id,
            job_id,
            listings=listings,
            auto_update=auto_update,
            skip_duplicates=skip_duplicates,
        )

    @staticmethod
    async def get_import_job(
        actor_id: int,
        job_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await AutomotiveMarketplaceEngineV1.user_can_access(actor_id):
            raise AutomotiveMarketplaceEngineError("Access denied")

        async with get_session() as session:
            job = await VehicleImportJobRepository(session).get_by_id(job_id)
            if job is None:
                raise AutomotiveMarketplaceEngineError(f"Import job not found: {job_id}")
            logs = await VehicleImportLogRepository(session).list_by_job(job_id)
            return {
                "job": AutomotiveMarketplaceEngineV1._job_snapshot(job),
                "logs": [AutomotiveMarketplaceEngineV1._log_snapshot(l) for l in logs],
            }

    @staticmethod
    async def list_connectors(actor_id: int) -> list[dict[str, Any]]:
        if not await AutomotiveMarketplaceEngineV1.user_can_access(actor_id):
            raise AutomotiveMarketplaceEngineError("Access denied")

        async with get_session() as session:
            creds = await ConnectorCredentialRepository(session).list_active()
            registered = {c.connector_type for c in creds}
            result = []
            for connector_type in ConnectorType:
                cred = next(
                    (c for c in creds if c.connector_type == connector_type.value),
                    None,
                )
                result.append({
                    "connector_type": connector_type.value,
                    "registered": connector_type.value in registered,
                    "credentials": (
                        AutomotiveMarketplaceEngineV1._credential_snapshot(cred)
                        if cred
                        else None
                    ),
                })
            return result
