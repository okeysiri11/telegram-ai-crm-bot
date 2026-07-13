# AI Procurement Agent v1 — market analysis, undervalued vehicles, repair/sale/ROI estimates.

from __future__ import annotations

import statistics
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import select

from config import OWNER_ID
from database.models.ai_procurement_agent import (
    ProcurementAnalysisType,
    ProcurementOpportunityStatus,
    ProcurementSubjectType,
)
from database.models.automotive_cost import CostType
from database.models.automotive_procurement import (
    AuctionLotStatus,
    SupplierOffer,
    SupplierOfferStatus,
    VehicleSourceType,
)
from database.session import get_session
from repositories.ai_procurement_agent_repository import (
    ProcurementAnalysisRepository,
    ProcurementOpportunityRepository,
)
from repositories.automotive_cost_repository import VehicleCostItemRepository
from repositories.automotive_inventory_repository import VehicleRepository
from repositories.automotive_procurement_repository import AuctionLotRepository
from repositories.user_role_repository import UserRoleRepository

PROCUREMENT_AGENT_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MODEL_VERSION = "ai-procurement-agent-v1.0.0"
MONEY = Decimal("0.01")
CONF = Decimal("0.0001")
DEFAULT_AUCTION_FEE_PERCENT = Decimal("12")
DEFAULT_TRANSPORT_FEE = Decimal("800")
DEFAULT_RECON_PERCENT = Decimal("8")


class AiProcurementAgentError(Exception):
    pass


class AiProcurementAgentV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PROCUREMENT_AGENT_ROLES for role in roles)

    @staticmethod
    async def _require_access(actor_id: int) -> None:
        if not await AiProcurementAgentV1.user_can_access(actor_id):
            raise AiProcurementAgentError("Procurement agent access denied")

    @staticmethod
    def _quantize(amount: Decimal) -> Decimal:
        return amount.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _confidence(score: float) -> Decimal:
        return Decimal(str(max(0.0, min(1.0, score)))).quantize(CONF)

    @staticmethod
    def _analysis_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "analysis_type": row.analysis_type,
            "subject_type": row.subject_type,
            "subject_id": row.subject_id,
            "input_context": row.input_context,
            "result": row.result,
            "confidence_score": str(row.confidence_score),
            "model_version": row.model_version,
            "summary": row.summary,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _opportunity_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "auction_lot_id": str(row.auction_lot_id) if row.auction_lot_id else None,
            "vehicle_id": str(row.vehicle_id) if row.vehicle_id else None,
            "analysis_id": str(row.analysis_id) if row.analysis_id else None,
            "make": row.make,
            "model": row.model,
            "year": row.year,
            "source": row.source,
            "acquisition_price": str(row.acquisition_price),
            "estimated_market_value": str(row.estimated_market_value),
            "discount_percent": str(row.discount_percent),
            "undervaluation_score": row.undervaluation_score,
            "repair_cost_estimate": (
                str(row.repair_cost_estimate) if row.repair_cost_estimate is not None else None
            ),
            "sale_price_estimate": (
                str(row.sale_price_estimate) if row.sale_price_estimate is not None else None
            ),
            "roi_percent": str(row.roi_percent) if row.roi_percent is not None else None,
            "currency": row.currency,
            "status": row.status,
            "notes": row.notes,
            "metadata": row.metadata_ or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _vehicle_age(year: int) -> int:
        return max(0, datetime.now(timezone.utc).year - year)

    @staticmethod
    async def _market_comps(
        session,
        make: str,
        model: str,
        *,
        year: int | None = None,
    ) -> dict[str, Any]:
        vehicles = await VehicleRepository(session).list_all(limit=500)
        sale_prices: list[float] = []
        purchase_prices: list[float] = []
        for vehicle in vehicles:
            if vehicle.make.lower() != make.lower() or vehicle.model.lower() != model.lower():
                continue
            if year is not None and abs(vehicle.year - year) > 2:
                continue
            if vehicle.sale_price:
                sale_prices.append(float(vehicle.sale_price))
            if vehicle.purchase_price:
                purchase_prices.append(float(vehicle.purchase_price))

        avg_sale = Decimal(str(statistics.mean(sale_prices))) if sale_prices else None
        avg_purchase = Decimal(str(statistics.mean(purchase_prices))) if purchase_prices else None
        return {
            "sample_size": max(len(sale_prices), len(purchase_prices)),
            "avg_sale_price": avg_sale,
            "avg_purchase_price": avg_purchase,
            "median_sale_price": (
                Decimal(str(statistics.median(sale_prices))) if sale_prices else None
            ),
        }

    @staticmethod
    def _estimate_market_value(
        *,
        make: str,
        model: str,
        year: int,
        comps: dict[str, Any],
        reference_price: Decimal | None = None,
    ) -> tuple[Decimal, float]:
        if comps.get("avg_sale_price"):
            value = AiProcurementAgentV1._quantize(comps["avg_sale_price"])
            confidence = min(0.95, 0.55 + comps["sample_size"] * 0.05)
            return value, confidence

        if comps.get("avg_purchase_price"):
            value = AiProcurementAgentV1._quantize(comps["avg_purchase_price"] * Decimal("1.18"))
            confidence = min(0.85, 0.45 + comps["sample_size"] * 0.04)
            return value, confidence

        if reference_price is not None:
            age = AiProcurementAgentV1._vehicle_age(year)
            depreciation = Decimal("0.12") * Decimal(str(min(age, 8)))
            value = AiProcurementAgentV1._quantize(reference_price * (Decimal("1") - depreciation))
            return value, 0.4

        base = Decimal("15000") + Decimal(str(max(0, 2020 - year))) * Decimal("500")
        return AiProcurementAgentV1._quantize(base), 0.25

    @staticmethod
    def _estimate_repair_cost_rule(
        *,
        year: int,
        mileage: int | None = None,
        damage_notes: str | None = None,
        vehicle_repair_history: Decimal | None = None,
    ) -> tuple[Decimal, dict[str, str], float]:
        age = AiProcurementAgentV1._vehicle_age(year)
        if age <= 3:
            base = Decimal("500")
        elif age <= 7:
            base = Decimal("1200")
        elif age <= 12:
            base = Decimal("2200")
        else:
            base = Decimal("3500")

        breakdown: dict[str, str] = {"base_by_age": str(base)}
        total = base

        if mileage is not None and mileage > 80000:
            mileage_extra = AiProcurementAgentV1._quantize(
                Decimal(str(mileage - 80000)) * Decimal("0.05")
            )
            breakdown["mileage_surcharge"] = str(mileage_extra)
            total += mileage_extra

        if vehicle_repair_history is not None and vehicle_repair_history > 0:
            breakdown["historical_repair_avg"] = str(vehicle_repair_history)
            total = max(total, vehicle_repair_history)

        notes = (damage_notes or "").lower()
        damage_keywords = {
            "frame": Decimal("4000"),
            "airbag": Decimal("2500"),
            "engine": Decimal("3500"),
            "transmission": Decimal("3000"),
            "flood": Decimal("5000"),
            "salvage": Decimal("2000"),
            "collision": Decimal("1500"),
        }
        for keyword, amount in damage_keywords.items():
            if keyword in notes:
                breakdown[f"damage_{keyword}"] = str(amount)
                total += amount

        confidence = 0.75 if vehicle_repair_history else 0.6
        if damage_notes:
            confidence = min(0.9, confidence + 0.1)
        return AiProcurementAgentV1._quantize(total), breakdown, confidence

    @staticmethod
    def _estimate_sale_price(
        *,
        market_value: Decimal,
        repair_cost: Decimal,
        make: str,
        model: str,
    ) -> tuple[Decimal, float]:
        recon_markup = AiProcurementAgentV1._quantize(
            repair_cost * Decimal("0.15")
        )
        sale = AiProcurementAgentV1._quantize(market_value * Decimal("0.98") + recon_markup)
        confidence = 0.7 if market_value > 0 else 0.35
        if make and model:
            confidence = min(0.88, confidence + 0.05)
        return sale, confidence

    @staticmethod
    def _calculate_roi(
        *,
        acquisition_price: Decimal,
        repair_cost: Decimal,
        sale_price: Decimal,
        auction_fee_percent: Decimal = DEFAULT_AUCTION_FEE_PERCENT,
        transport_fee: Decimal = DEFAULT_TRANSPORT_FEE,
    ) -> tuple[Decimal, dict[str, str]]:
        auction_fee = AiProcurementAgentV1._quantize(
            acquisition_price * auction_fee_percent / Decimal("100")
        )
        total_investment = acquisition_price + repair_cost + auction_fee + transport_fee
        profit = sale_price - total_investment
        roi = (
            AiProcurementAgentV1._quantize(profit / total_investment * Decimal("100"))
            if total_investment > 0
            else Decimal("0")
        )
        breakdown = {
            "acquisition_price": str(acquisition_price),
            "repair_cost": str(repair_cost),
            "auction_fee": str(auction_fee),
            "transport_fee": str(transport_fee),
            "total_investment": str(total_investment),
            "sale_price": str(sale_price),
            "profit": str(AiProcurementAgentV1._quantize(profit)),
            "roi_percent": str(roi),
        }
        return roi, breakdown

    @staticmethod
    def _undervaluation_score(discount_percent: Decimal, roi_percent: Decimal | None) -> int:
        score = min(70, int(discount_percent * 2))
        if roi_percent is not None and roi_percent > 0:
            score += min(30, int(roi_percent))
        return min(100, max(0, score))

    @staticmethod
    async def _avg_repair_from_costs(session, vehicle_id: uuid.UUID) -> Decimal | None:
        items = await VehicleCostItemRepository(session).list_by_vehicle(vehicle_id)
        repair_items = [
            item.amount for item in items if item.cost_type == CostType.REPAIR.value
        ]
        if not repair_items:
            return None
        return AiProcurementAgentV1._quantize(
            sum((Decimal(str(a)) for a in repair_items), Decimal("0"))
            / Decimal(str(len(repair_items)))
        )

    @staticmethod
    async def analyze_market(
        actor_id: int,
        *,
        make: str | None = None,
        model: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        await AiProcurementAgentV1._require_access(actor_id)

        async with get_session() as session:
            lots = await AuctionLotRepository(session).list_by_status(
                AuctionLotStatus.WATCHING.value,
                limit=200,
            )
            if source:
                lots = [lot for lot in lots if lot.source == source]
            if make:
                lots = [lot for lot in lots if lot.make.lower() == make.lower()]
            if model:
                lots = [lot for lot in lots if lot.model.lower() == model.lower()]

            bid_prices = [
                float(lot.current_bid or lot.buy_now_price)
                for lot in lots
                if lot.current_bid or lot.buy_now_price
            ]
            segment_comps = None
            if make and model:
                segment_comps = await AiProcurementAgentV1._market_comps(session, make, model)

            result = {
                "filters": {"make": make, "model": model, "source": source},
                "active_lots": len(lots),
                "avg_auction_price": (
                    str(AiProcurementAgentV1._quantize(Decimal(str(statistics.mean(bid_prices)))))
                    if bid_prices
                    else None
                ),
                "median_auction_price": (
                    str(AiProcurementAgentV1._quantize(Decimal(str(statistics.median(bid_prices)))))
                    if bid_prices
                    else None
                ),
                "by_source": {},
            }
            by_source: dict[str, list[float]] = {}
            for lot in lots:
                price = lot.current_bid or lot.buy_now_price
                if price:
                    by_source.setdefault(lot.source, []).append(float(price))
            for src, prices in by_source.items():
                result["by_source"][src] = {
                    "count": len(prices),
                    "avg_price": str(
                        AiProcurementAgentV1._quantize(Decimal(str(statistics.mean(prices))))
                    ),
                }

            if segment_comps:
                result["inventory_comps"] = {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in segment_comps.items()
                }

            confidence = 0.55 if bid_prices else 0.3
            if segment_comps and segment_comps.get("sample_size", 0) > 0:
                confidence = min(0.92, confidence + 0.2)

            summary = (
                f"Market scan: {len(lots)} active lots"
                + (f" for {make} {model}" if make and model else "")
            )
            row = await ProcurementAnalysisRepository(session).create(
                analysis_type=ProcurementAnalysisType.MARKET_ANALYSIS.value,
                subject_type=ProcurementSubjectType.MARKET_SEGMENT.value,
                subject_id=f"{make or '*'}:{model or '*'}:{source or '*'}",
                input_context={"make": make, "model": model, "source": source},
                result=result,
                confidence_score=AiProcurementAgentV1._confidence(confidence),
                model_version=MODEL_VERSION,
                summary=summary,
                created_by=actor_id,
            )
            await session.refresh(row)
            return AiProcurementAgentV1._analysis_snapshot(row)

    @staticmethod
    async def estimate_repair_costs(
        actor_id: int,
        *,
        auction_lot_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        make: str | None = None,
        model: str | None = None,
        year: int | None = None,
        mileage: int | None = None,
        damage_notes: str | None = None,
    ) -> dict[str, Any]:
        await AiProcurementAgentV1._require_access(actor_id)

        async with get_session() as session:
            lot = None
            vehicle = None
            if auction_lot_id is not None:
                lot = await AuctionLotRepository(session).get_by_id(auction_lot_id)
                if lot is None:
                    raise AiProcurementAgentError(f"Auction lot not found: {auction_lot_id}")
                make = lot.make
                model = lot.model
                year = lot.year
                mileage = lot.mileage
                damage_notes = damage_notes or lot.notes
            elif vehicle_id is not None:
                vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
                if vehicle is None:
                    raise AiProcurementAgentError(f"Vehicle not found: {vehicle_id}")
                make = vehicle.make
                model = vehicle.model
                year = vehicle.year
                mileage = vehicle.mileage
                damage_notes = damage_notes or vehicle.notes

            if year is None or make is None or model is None:
                raise AiProcurementAgentError("make, model, and year are required")

            repair_history = None
            if vehicle is not None:
                repair_history = await AiProcurementAgentV1._avg_repair_from_costs(
                    session, vehicle.id
                )

            repair_cost, breakdown, confidence = AiProcurementAgentV1._estimate_repair_cost_rule(
                year=year,
                mileage=mileage,
                damage_notes=damage_notes,
                vehicle_repair_history=repair_history,
            )

            ai_notes = await AiProcurementAgentV1._optional_ai_repair_notes(
                make=make,
                model=model,
                year=year,
                mileage=mileage,
                damage_notes=damage_notes,
                estimated_cost=str(repair_cost),
            )
            if ai_notes:
                breakdown["ai_notes"] = ai_notes

            subject_type = None
            subject_id = None
            if lot is not None:
                subject_type = ProcurementSubjectType.AUCTION_LOT.value
                subject_id = str(lot.id)
            elif vehicle is not None:
                subject_type = ProcurementSubjectType.VEHICLE.value
                subject_id = str(vehicle.id)

            result = {
                "make": make,
                "model": model,
                "year": year,
                "mileage": mileage,
                "repair_cost": str(repair_cost),
                "breakdown": breakdown,
                "currency": lot.currency if lot else (vehicle.currency if vehicle else "USD"),
            }
            row = await ProcurementAnalysisRepository(session).create(
                analysis_type=ProcurementAnalysisType.REPAIR_ESTIMATE.value,
                subject_type=subject_type,
                subject_id=subject_id,
                input_context={
                    "auction_lot_id": str(auction_lot_id) if auction_lot_id else None,
                    "vehicle_id": str(vehicle_id) if vehicle_id else None,
                    "damage_notes": damage_notes,
                },
                result=result,
                confidence_score=AiProcurementAgentV1._confidence(confidence),
                model_version=MODEL_VERSION,
                summary=f"Estimated repair cost for {year} {make} {model}: ${repair_cost}",
                created_by=actor_id,
            )
            await session.refresh(row)
            return AiProcurementAgentV1._analysis_snapshot(row)

    @staticmethod
    async def estimate_final_sale_price(
        actor_id: int,
        *,
        auction_lot_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        make: str | None = None,
        model: str | None = None,
        year: int | None = None,
        repair_cost: Decimal | float | int | None = None,
    ) -> dict[str, Any]:
        await AiProcurementAgentV1._require_access(actor_id)

        async with get_session() as session:
            lot = None
            vehicle = None
            if auction_lot_id is not None:
                lot = await AuctionLotRepository(session).get_by_id(auction_lot_id)
                if lot is None:
                    raise AiProcurementAgentError(f"Auction lot not found: {auction_lot_id}")
                make, model, year = lot.make, lot.model, lot.year
            elif vehicle_id is not None:
                vehicle = await VehicleRepository(session).get_by_id(vehicle_id)
                if vehicle is None:
                    raise AiProcurementAgentError(f"Vehicle not found: {vehicle_id}")
                make, model, year = vehicle.make, vehicle.model, vehicle.year

            if year is None or make is None or model is None:
                raise AiProcurementAgentError("make, model, and year are required")

            comps = await AiProcurementAgentV1._market_comps(session, make, model, year=year)
            ref_price = None
            if lot and (lot.current_bid or lot.buy_now_price):
                ref_price = lot.current_bid or lot.buy_now_price
            elif vehicle and vehicle.purchase_price:
                ref_price = vehicle.purchase_price

            market_value, mv_confidence = AiProcurementAgentV1._estimate_market_value(
                make=make,
                model=model,
                year=year,
                comps=comps,
                reference_price=ref_price,
            )

            if repair_cost is None:
                repair_cost, _, _ = AiProcurementAgentV1._estimate_repair_cost_rule(year=year)
            else:
                repair_cost = AiProcurementAgentV1._quantize(Decimal(str(repair_cost)))

            sale_price, sale_confidence = AiProcurementAgentV1._estimate_sale_price(
                market_value=market_value,
                repair_cost=repair_cost,
                make=make,
                model=model,
            )
            confidence = (mv_confidence + sale_confidence) / 2

            result = {
                "make": make,
                "model": model,
                "year": year,
                "market_value": str(market_value),
                "repair_cost": str(repair_cost),
                "sale_price": str(sale_price),
                "comps_sample_size": comps.get("sample_size", 0),
                "currency": lot.currency if lot else (vehicle.currency if vehicle else "USD"),
            }

            subject_type = None
            subject_id = None
            if lot is not None:
                subject_type = ProcurementSubjectType.AUCTION_LOT.value
                subject_id = str(lot.id)
            elif vehicle is not None:
                subject_type = ProcurementSubjectType.VEHICLE.value
                subject_id = str(vehicle.id)

            row = await ProcurementAnalysisRepository(session).create(
                analysis_type=ProcurementAnalysisType.SALE_PRICE_ESTIMATE.value,
                subject_type=subject_type,
                subject_id=subject_id,
                input_context=result,
                result=result,
                confidence_score=AiProcurementAgentV1._confidence(confidence),
                model_version=MODEL_VERSION,
                summary=f"Estimated sale price for {year} {make} {model}: ${sale_price}",
                created_by=actor_id,
            )
            await session.refresh(row)
            return AiProcurementAgentV1._analysis_snapshot(row)

    @staticmethod
    async def estimate_roi(
        actor_id: int,
        *,
        acquisition_price: Decimal | float | int,
        repair_cost: Decimal | float | int | None = None,
        sale_price: Decimal | float | int | None = None,
        auction_lot_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        make: str | None = None,
        model: str | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        await AiProcurementAgentV1._require_access(actor_id)
        acq = AiProcurementAgentV1._quantize(Decimal(str(acquisition_price)))

        async with get_session() as session:
            lot = None
            if auction_lot_id is not None:
                lot = await AuctionLotRepository(session).get_by_id(auction_lot_id)
                if lot is None:
                    raise AiProcurementAgentError(f"Auction lot not found: {auction_lot_id}")
                make, model, year = lot.make, lot.model, lot.year
                if lot.current_bid or lot.buy_now_price:
                    acq = AiProcurementAgentV1._quantize(
                        lot.current_bid or lot.buy_now_price or acq
                    )

            if repair_cost is None and year is not None:
                mileage = lot.mileage if lot else None
                repair_cost, _, _ = AiProcurementAgentV1._estimate_repair_cost_rule(
                    year=year,
                    mileage=mileage,
                    damage_notes=lot.notes if lot else None,
                )
            repair = AiProcurementAgentV1._quantize(Decimal(str(repair_cost or 0)))

            if sale_price is None and make and model and year:
                comps = await AiProcurementAgentV1._market_comps(session, make, model, year=year)
                market_value, _ = AiProcurementAgentV1._estimate_market_value(
                    make=make,
                    model=model,
                    year=year,
                    comps=comps,
                    reference_price=acq,
                )
                sale_price, _ = AiProcurementAgentV1._estimate_sale_price(
                    market_value=market_value,
                    repair_cost=repair,
                    make=make,
                    model=model,
                )
            if sale_price is None:
                raise AiProcurementAgentError("sale_price required or provide make/model/year")

            sale = AiProcurementAgentV1._quantize(Decimal(str(sale_price)))
            roi, breakdown = AiProcurementAgentV1._calculate_roi(
                acquisition_price=acq,
                repair_cost=repair,
                sale_price=sale,
            )
            confidence = 0.65 if make and model else 0.45

            result = {
                "make": make,
                "model": model,
                "year": year,
                **breakdown,
            }
            row = await ProcurementAnalysisRepository(session).create(
                analysis_type=ProcurementAnalysisType.ROI_ESTIMATE.value,
                subject_type=(
                    ProcurementSubjectType.AUCTION_LOT.value
                    if lot
                    else ProcurementSubjectType.VEHICLE.value if vehicle_id else None
                ),
                subject_id=str(auction_lot_id or vehicle_id) if (auction_lot_id or vehicle_id) else None,
                input_context={
                    "acquisition_price": str(acq),
                    "repair_cost": str(repair),
                    "sale_price": str(sale),
                },
                result=result,
                confidence_score=AiProcurementAgentV1._confidence(confidence),
                model_version=MODEL_VERSION,
                summary=f"Estimated ROI: {roi}%",
                created_by=actor_id,
            )
            await session.refresh(row)
            return AiProcurementAgentV1._analysis_snapshot(row)

    @staticmethod
    async def identify_undervalued_vehicles(
        actor_id: int,
        *,
        source: str | None = None,
        min_discount_percent: Decimal | float | int = 10,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        await AiProcurementAgentV1._require_access(actor_id)
        min_discount = Decimal(str(min_discount_percent))
        results: list[dict[str, Any]] = []

        async with get_session() as session:
            lots = await AuctionLotRepository(session).list_by_status(
                AuctionLotStatus.WATCHING.value,
                limit=300,
            )
            if source:
                lots = [lot for lot in lots if lot.source == source]

            for lot in lots:
                acquisition = lot.current_bid or lot.buy_now_price
                if acquisition is None or acquisition <= 0:
                    continue

                comps = await AiProcurementAgentV1._market_comps(
                    session, lot.make, lot.model, year=lot.year
                )
                market_value, _ = AiProcurementAgentV1._estimate_market_value(
                    make=lot.make,
                    model=lot.model,
                    year=lot.year,
                    comps=comps,
                    reference_price=acquisition,
                )
                if market_value <= 0:
                    continue

                discount = AiProcurementAgentV1._quantize(
                    (market_value - acquisition) / market_value * Decimal("100")
                )
                if discount < min_discount:
                    continue

                repair_cost, _, _ = AiProcurementAgentV1._estimate_repair_cost_rule(
                    year=lot.year,
                    mileage=lot.mileage,
                    damage_notes=lot.notes,
                )
                sale_price, _ = AiProcurementAgentV1._estimate_sale_price(
                    market_value=market_value,
                    repair_cost=repair_cost,
                    make=lot.make,
                    model=lot.model,
                )
                roi, _ = AiProcurementAgentV1._calculate_roi(
                    acquisition_price=acquisition,
                    repair_cost=repair_cost,
                    sale_price=sale_price,
                )
                score = AiProcurementAgentV1._undervaluation_score(discount, roi)

                existing = await ProcurementOpportunityRepository(session).get_by_auction_lot(
                    lot.id,
                    status=ProcurementOpportunityStatus.OPEN.value,
                )
                if existing is not None:
                    existing.acquisition_price = acquisition
                    existing.estimated_market_value = market_value
                    existing.discount_percent = discount
                    existing.undervaluation_score = score
                    existing.repair_cost_estimate = repair_cost
                    existing.sale_price_estimate = sale_price
                    existing.roi_percent = roi
                    await session.flush()
                    results.append(AiProcurementAgentV1._opportunity_snapshot(existing))
                else:
                    row = await ProcurementOpportunityRepository(session).create(
                        auction_lot_id=lot.id,
                        make=lot.make,
                        model=lot.model,
                        year=lot.year,
                        source=lot.source,
                        acquisition_price=acquisition,
                        estimated_market_value=market_value,
                        discount_percent=discount,
                        undervaluation_score=score,
                        repair_cost_estimate=repair_cost,
                        sale_price_estimate=sale_price,
                        roi_percent=roi,
                        currency=lot.currency,
                        metadata={"lot_number": lot.lot_number},
                    )
                    results.append(AiProcurementAgentV1._opportunity_snapshot(row))

                if len(results) >= limit:
                    break

        results.sort(key=lambda item: int(item["undervaluation_score"]), reverse=True)
        return results

    @staticmethod
    async def evaluate_auction_lot(
        actor_id: int,
        auction_lot_id: uuid.UUID,
    ) -> dict[str, Any]:
        await AiProcurementAgentV1._require_access(actor_id)

        repair = await AiProcurementAgentV1.estimate_repair_costs(
            actor_id, auction_lot_id=auction_lot_id
        )
        sale = await AiProcurementAgentV1.estimate_final_sale_price(
            actor_id,
            auction_lot_id=auction_lot_id,
            repair_cost=Decimal(repair["result"]["repair_cost"]),
        )
        roi = await AiProcurementAgentV1.estimate_roi(
            actor_id,
            acquisition_price=Decimal("0"),
            repair_cost=Decimal(repair["result"]["repair_cost"]),
            sale_price=Decimal(sale["result"]["sale_price"]),
            auction_lot_id=auction_lot_id,
        )

        async with get_session() as session:
            lot = await AuctionLotRepository(session).get_by_id(auction_lot_id)
            if lot is None:
                raise AiProcurementAgentError(f"Auction lot not found: {auction_lot_id}")

            combined = {
                "auction_lot_id": str(auction_lot_id),
                "make": lot.make,
                "model": lot.model,
                "year": lot.year,
                "repair_analysis_id": repair["id"],
                "sale_analysis_id": sale["id"],
                "roi_analysis_id": roi["id"],
                "repair_cost": repair["result"]["repair_cost"],
                "sale_price": sale["result"]["sale_price"],
                "roi_percent": roi["result"]["roi_percent"],
                "recommendation": (
                    "PURSUE" if Decimal(roi["result"]["roi_percent"]) >= Decimal("15") else "REVIEW"
                ),
            }
            row = await ProcurementAnalysisRepository(session).create(
                analysis_type=ProcurementAnalysisType.FULL_EVALUATION.value,
                subject_type=ProcurementSubjectType.AUCTION_LOT.value,
                subject_id=str(auction_lot_id),
                input_context={"auction_lot_id": str(auction_lot_id)},
                result=combined,
                confidence_score=AiProcurementAgentV1._confidence(0.8),
                model_version=MODEL_VERSION,
                summary=(
                    f"Full evaluation {lot.year} {lot.make} {lot.model}: "
                    f"ROI {roi['result']['roi_percent']}%"
                ),
                created_by=actor_id,
            )
            await session.refresh(row)
            return AiProcurementAgentV1._analysis_snapshot(row)

    @staticmethod
    async def list_opportunities(
        actor_id: int,
        *,
        min_score: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await AiProcurementAgentV1._require_access(actor_id)
        async with get_session() as session:
            rows = await ProcurementOpportunityRepository(session).list_open(
                min_score=min_score,
                limit=limit,
            )
            return [AiProcurementAgentV1._opportunity_snapshot(r) for r in rows]

    @staticmethod
    async def dismiss_opportunity(
        actor_id: int,
        opportunity_id: uuid.UUID,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        await AiProcurementAgentV1._require_access(actor_id)
        async with get_session() as session:
            row = await ProcurementOpportunityRepository(session).update_status(
                opportunity_id,
                status=ProcurementOpportunityStatus.DISMISSED.value,
                notes=notes,
            )
            if row is None:
                raise AiProcurementAgentError(f"Opportunity not found: {opportunity_id}")
            await session.refresh(row)
            return AiProcurementAgentV1._opportunity_snapshot(row)

    @staticmethod
    async def list_analyses(
        actor_id: int,
        *,
        analysis_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await AiProcurementAgentV1._require_access(actor_id)
        async with get_session() as session:
            if analysis_type:
                rows = await ProcurementAnalysisRepository(session).list_by_type(
                    analysis_type, limit=limit
                )
            else:
                rows = []
                for atype in ProcurementAnalysisType:
                    rows.extend(
                        await ProcurementAnalysisRepository(session).list_by_type(
                            atype.value, limit=max(5, limit // len(ProcurementAnalysisType))
                        )
                    )
                rows.sort(key=lambda r: r.created_at, reverse=True)
                rows = rows[:limit]
            return [AiProcurementAgentV1._analysis_snapshot(r) for r in rows]

    @staticmethod
    async def score_suppliers(
        actor_id: int,
        *,
        source: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        await AiProcurementAgentV1._require_access(actor_id)

        async with get_session() as session:
            lot_repo = AuctionLotRepository(session)

            offers_result = await session.execute(
                select(SupplierOffer).order_by(SupplierOffer.created_at.desc()).limit(500)
            )
            offers = list(offers_result.scalars().all())
            lots = await lot_repo.list_by_status(AuctionLotStatus.WATCHING.value, limit=500)
            won_lots = await lot_repo.list_by_status(AuctionLotStatus.WON.value, limit=200)
            all_lots = lots + won_lots

            supplier_stats: dict[str, dict[str, Any]] = {}

            for src in VehicleSourceType:
                supplier_stats[src.value] = {
                    "source": src.value,
                    "pending_offers": 0,
                    "accepted_offers": 0,
                    "watching_lots": 0,
                    "won_lots": 0,
                    "avg_offer_price": None,
                    "avg_lot_bid": None,
                    "score": 0,
                }

            offer_prices: dict[str, list[float]] = {}
            for offer in offers:
                if source and offer.source != source:
                    continue
                stats = supplier_stats.get(offer.source)
                if stats is None:
                    continue
                if offer.status == SupplierOfferStatus.PENDING.value:
                    stats["pending_offers"] += 1
                elif offer.status == SupplierOfferStatus.ACCEPTED.value:
                    stats["accepted_offers"] += 1
                offer_prices.setdefault(offer.source, []).append(float(offer.offer_price))

            lot_bids: dict[str, list[float]] = {}
            for lot in all_lots:
                if source and lot.source != source:
                    continue
                stats = supplier_stats.get(lot.source)
                if stats is None:
                    continue
                if lot.status == AuctionLotStatus.WATCHING.value:
                    stats["watching_lots"] += 1
                elif lot.status == AuctionLotStatus.WON.value:
                    stats["won_lots"] += 1
                bid = lot.current_bid or lot.buy_now_price
                if bid:
                    lot_bids.setdefault(lot.source, []).append(float(bid))

            scored: list[dict[str, Any]] = []
            for src, stats in supplier_stats.items():
                if source and src != source:
                    continue
                total_offers = stats["pending_offers"] + stats["accepted_offers"]
                if total_offers == 0 and stats["watching_lots"] == 0 and stats["won_lots"] == 0:
                    continue

                if offer_prices.get(src):
                    stats["avg_offer_price"] = str(
                        AiProcurementAgentV1._quantize(
                            Decimal(str(statistics.mean(offer_prices[src])))
                        )
                    )
                if lot_bids.get(src):
                    stats["avg_lot_bid"] = str(
                        AiProcurementAgentV1._quantize(
                            Decimal(str(statistics.mean(lot_bids[src])))
                        )
                    )

                score = 40
                if stats["accepted_offers"]:
                    score += min(25, stats["accepted_offers"] * 5)
                if stats["won_lots"]:
                    score += min(20, stats["won_lots"] * 4)
                if stats["watching_lots"]:
                    score += min(10, stats["watching_lots"])
                if stats["pending_offers"] > 10:
                    score -= 5
                stats["score"] = min(100, max(0, score))
                scored.append(stats)

            scored.sort(key=lambda item: item["score"], reverse=True)
            scored = scored[:limit]

            result = {"suppliers": scored, "count": len(scored)}
            row = await ProcurementAnalysisRepository(session).create(
                analysis_type=ProcurementAnalysisType.SUPPLIER_SCORING.value,
                subject_type=ProcurementSubjectType.MARKET_SEGMENT.value,
                subject_id=source or "all",
                input_context={"source": source, "limit": limit},
                result=result,
                confidence_score=AiProcurementAgentV1._confidence(0.75 if scored else 0.4),
                model_version=MODEL_VERSION,
                summary=f"Scored {len(scored)} suppliers",
                created_by=actor_id,
            )
            await session.refresh(row)
            return {
                "analysis": AiProcurementAgentV1._analysis_snapshot(row),
                **result,
            }

    @staticmethod
    async def _optional_ai_repair_notes(
        *,
        make: str,
        model: str,
        year: int,
        mileage: int | None,
        damage_notes: str | None,
        estimated_cost: str,
    ) -> str | None:
        try:
            from config import OPENROUTER_API_KEY
            if not OPENROUTER_API_KEY:
                return None
            from openrouter import ask_openrouter

            prompt = (
                f"Vehicle: {year} {make} {model}, mileage={mileage}, "
                f"damage notes={damage_notes or 'none'}. "
                f"Rule-based repair estimate=${estimated_cost}. "
                "In 1-2 sentences, note any major repair risks for a US auction flip dealer."
            )
            text = await ask_openrouter(
                [{"role": "user", "content": prompt}],
                ai_settings={"language": "en", "tone": "formal"},
            )
            return text.strip()[:500] if text else None
        except Exception:
            return None
