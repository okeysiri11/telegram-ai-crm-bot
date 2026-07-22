# Sprint 10.4 REST handlers — auctions, finance/loans, leasing, insurance, transactions, payments.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.transactions.models import (
    AdvancedAuction,
    AuctionType,
    LeaseType,
    VehicleTransaction,
)


def _parse_auction_type(value: str) -> AuctionType:
    try:
        return AuctionType(value or "english")
    except ValueError as exc:
        raise ValidationError(f"invalid auction_type: {value}") from exc


def _parse_lease_type(value: str) -> LeaseType:
    try:
        return LeaseType(value or "personal")
    except ValueError as exc:
        raise ValidationError(f"invalid lease_type: {value}") from exc


async def auctions_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "auction_engine": auto_marketplace.config.auction_engine,
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.transactions.auctions.metrics(),
        }
    )


async def auctions_list_create_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.transactions.auctions.list_auctions(
                status=request.query.get("status") or None,
                auction_type=request.query.get("auction_type") or None,
            )
            return json_response({"items": [a.to_dict() for a in items]})
        data = await request.json()
        auction = AdvancedAuction(
            listing_id=data.get("listing_id", ""),
            vehicle_id=data.get("vehicle_id", ""),
            auction_type=_parse_auction_type(data.get("auction_type", "english")),
            start_price=float(data.get("start_price", 0) or 0),
            current_price=float(data.get("current_price", 0) or 0),
            reserve_price=float(data.get("reserve_price", 0) or 0),
            buy_now_price=float(data["buy_now_price"]) if data.get("buy_now_price") is not None else None,
            currency=data.get("currency", "USD"),
            dealer_id=data.get("dealer_id", ""),
            ends_at=float(data.get("ends_at", 0) or 0),
        )
        created = auto_marketplace.transactions.auctions.create(auction)
        return json_response(created.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def auctions_start_handler(request: web.Request) -> web.Response:
    try:
        auction = auto_marketplace.transactions.auctions.start(request.match_info["auction_id"])
        return json_response(auction.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def auctions_bid_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        auction = auto_marketplace.transactions.auctions.place_bid(
            request.match_info["auction_id"],
            data.get("bidder_id", ""),
            float(data.get("amount", 0) or 0),
        )
        return json_response(auction.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def auctions_auto_bid_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        auction = auto_marketplace.transactions.auctions.register_auto_bid(
            request.match_info["auction_id"],
            data.get("bidder_id", ""),
            float(data.get("max_amount", 0) or 0),
        )
        return json_response(auction.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def auctions_buy_now_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        auction = auto_marketplace.transactions.auctions.buy_now(
            request.match_info["auction_id"],
            data.get("buyer_id", ""),
        )
        return json_response(auction.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def auctions_close_handler(request: web.Request) -> web.Response:
    try:
        auction = auto_marketplace.transactions.auctions.close(request.match_info["auction_id"])
        return json_response(auction.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def finance_calculator_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        result = auto_marketplace.transactions.financing.calculate_payment(
            float(data.get("principal", 0) or 0),
            float(data.get("annual_rate_pct", 0) or 0),
            int(data.get("term_months", 36) or 36),
        )
        return json_response(result)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def finance_compare_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        items = auto_marketplace.transactions.financing.compare_rates(
            float(data.get("principal", 0) or 0),
            int(data.get("term_months", 36) or 36),
        )
        return json_response({"items": items, "finance_engine": auto_marketplace.config.finance_engine})
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def finance_loans_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.transactions.financing.list_offers(
                buyer_id=request.query.get("buyer_id", "")
            )
            return json_response({"items": [o.to_dict() for o in items]})
        data = await request.json()
        offer = auto_marketplace.transactions.financing.create_offer(
            buyer_id=data.get("buyer_id", ""),
            vehicle_id=data.get("vehicle_id", ""),
            principal=float(data.get("principal", 0) or 0),
            annual_rate_pct=float(data.get("annual_rate_pct", 9.5) or 9.5),
            term_months=int(data.get("term_months", 36) or 36),
            bank=data.get("bank", "AutoBank"),
            currency=data.get("currency", "USD"),
        )
        return json_response(offer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def finance_approve_handler(request: web.Request) -> web.Response:
    try:
        offer = auto_marketplace.transactions.financing.approve(request.match_info["offer_id"])
        return json_response(offer.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def leasing_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.transactions.leasing.metrics(),
        }
    )


async def leasing_quote_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        offer = auto_marketplace.transactions.leasing.quote(
            buyer_id=data.get("buyer_id", ""),
            vehicle_price=float(data.get("vehicle_price", 0) or 0),
            lease_type=_parse_lease_type(data.get("lease_type", "personal")),
            term_months=int(data.get("term_months", 36) or 36),
            residual_pct=float(data.get("residual_pct", 0.45) or 0.45),
            vehicle_id=data.get("vehicle_id", ""),
            mileage_limit_km=int(data.get("mileage_limit_km", 15000) or 15000),
            currency=data.get("currency", "USD"),
        )
        return json_response(offer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def leasing_compare_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        items = auto_marketplace.transactions.leasing.compare(
            float(data.get("vehicle_price", 0) or 0),
            int(data.get("term_months", 36) or 36),
        )
        return json_response({"items": items})
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def leasing_contract_handler(request: web.Request) -> web.Response:
    try:
        offer = auto_marketplace.transactions.leasing.generate_contract(request.match_info["lease_id"])
        return json_response(offer.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def insurance_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "insurance_engine": auto_marketplace.config.insurance_engine,
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.transactions.insurance.metrics(),
        }
    )


async def insurance_quote_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        quote = auto_marketplace.transactions.insurance.quote(
            buyer_id=data.get("buyer_id", ""),
            vehicle_id=data.get("vehicle_id", ""),
            coverage=data.get("coverage", "comprehensive"),
            year=int(data.get("year", 2020) or 2020),
            mileage_km=int(data.get("mileage_km", 50000) or 50000),
            claims_count=int(data.get("claims_count", 0) or 0),
            provider=data.get("provider", ""),
            currency=data.get("currency", "USD"),
        )
        return json_response(quote.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def insurance_compare_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = auto_marketplace.transactions.insurance.compare(
        buyer_id=data.get("buyer_id", "buyer"),
        vehicle_id=data.get("vehicle_id", ""),
        year=int(data.get("year", 2020) or 2020),
        mileage_km=int(data.get("mileage_km", 50000) or 50000),
    )
    return json_response({"items": items})


async def insurance_claim_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        claim = auto_marketplace.transactions.insurance.open_claim(
            request.match_info["quote_id"],
            data.get("description", ""),
        )
        return json_response(claim)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def transactions_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "transaction_engine": auto_marketplace.config.transaction_engine,
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.transactions.metrics(),
        }
    )


async def transactions_list_create_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.transactions.transactions.list_transactions(
                buyer_id=request.query.get("buyer_id", ""),
                status=request.query.get("status", ""),
            )
            return json_response({"items": [t.to_dict() for t in items]})
        data = await request.json()
        tx = VehicleTransaction(
            vehicle_id=data.get("vehicle_id", ""),
            buyer_id=data.get("buyer_id", ""),
            seller_id=data.get("seller_id", ""),
            dealer_id=data.get("dealer_id", ""),
            price=float(data.get("price", 0) or 0),
            currency=data.get("currency", "USD"),
        )
        created = auto_marketplace.transactions.transactions.create(tx)
        return json_response(created.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def transactions_reserve_handler(request: web.Request) -> web.Response:
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        tx = auto_marketplace.transactions.transactions.reserve(
            request.match_info["transaction_id"],
            deposit=float((data or {}).get("deposit", 0) or 0),
        )
        return json_response(tx.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transactions_offer_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        tx = auto_marketplace.transactions.transactions.make_offer(
            request.match_info["transaction_id"],
            float(data.get("amount", 0) or 0),
            data.get("from_party", "buyer"),
        )
        return json_response(tx.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transactions_counter_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        tx = auto_marketplace.transactions.transactions.counter_offer(
            request.match_info["transaction_id"],
            float(data.get("amount", 0) or 0),
            data.get("from_party", "seller"),
        )
        return json_response(tx.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transactions_contract_handler(request: web.Request) -> web.Response:
    try:
        tx = auto_marketplace.transactions.transactions.create_contract(request.match_info["transaction_id"])
        return json_response(tx.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transactions_sign_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        tx = auto_marketplace.transactions.transactions.sign(
            request.match_info["transaction_id"],
            data.get("signed_by", ""),
        )
        return json_response(tx.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transactions_pay_handler(request: web.Request) -> web.Response:
    try:
        tx = auto_marketplace.transactions.transactions.fund_escrow(request.match_info["transaction_id"])
        return json_response(tx.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transactions_transfer_handler(request: web.Request) -> web.Response:
    try:
        tx = auto_marketplace.transactions.transactions.transfer_ownership(request.match_info["transaction_id"])
        return json_response(tx.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transactions_deliver_handler(request: web.Request) -> web.Response:
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        data = data or {}
        tx = auto_marketplace.transactions.transactions.deliver(
            request.match_info["transaction_id"],
            location=data.get("location", ""),
            carrier=data.get("carrier", ""),
        )
        return json_response(tx.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transactions_complete_handler(request: web.Request) -> web.Response:
    try:
        tx = auto_marketplace.transactions.transactions.complete(request.match_info["transaction_id"])
        return json_response(tx.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def payments_list_create_handler(request: web.Request) -> web.Response:
    try:
        engine = auto_marketplace.transactions.transactions.payments
        if request.method == "GET":
            items = engine.history(transaction_id=request.query.get("transaction_id", ""))
            return json_response({"items": [p.to_dict() for p in items]})
        data = await request.json()
        payment = engine.create(
            transaction_id=data.get("transaction_id", ""),
            amount=float(data.get("amount", 0) or 0),
            kind=data.get("kind", "invoice"),
            currency=data.get("currency", "USD"),
            installment_no=int(data.get("installment_no", 0) or 0),
        )
        return json_response(payment.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def payments_capture_handler(request: web.Request) -> web.Response:
    try:
        payment = auto_marketplace.transactions.transactions.payments.capture(request.match_info["payment_id"])
        return json_response(payment.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def payments_refund_handler(request: web.Request) -> web.Response:
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        amount = (data or {}).get("amount")
        payment = auto_marketplace.transactions.transactions.payments.refund(
            request.match_info["payment_id"],
            float(amount) if amount is not None else None,
        )
        return json_response(payment.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def payments_installments_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        items = auto_marketplace.transactions.transactions.payments.schedule_installments(
            transaction_id=data.get("transaction_id", ""),
            total=float(data.get("total", 0) or 0),
            count=int(data.get("count", 3) or 3),
            currency=data.get("currency", "USD"),
        )
        return json_response({"items": [p.to_dict() for p in items]}, status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)
