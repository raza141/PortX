# -*- coding: utf-8 -*-
# operations/ibor/views/fee_api_views.py

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from operations.ibor.services import IborFeeEngine


@require_GET
def ibor_fee_quote_api(request):
    try:
        trade_dt_raw = request.GET.get("trade_dt", "")
        quantity_raw = request.GET.get("quantity", "")
        price_raw = request.GET.get("price", "")
        side = request.GET.get("side", "").strip().upper()
        source_system = request.GET.get("source_system", "").strip()

        broker_id = _to_int(request.GET.get("broker_id"))
        exec_venue_id = _to_int(request.GET.get("exec_venue_id"))
        asset_class_id = _to_int(request.GET.get("asset_class_id"))
        asset_sub_class_id = _to_int(request.GET.get("asset_sub_class_id"))
        trade_ccy_id = _to_int(request.GET.get("trade_ccy_id"))

        instrument_id = _to_int(request.GET.get("instrument_id"))
        security_id = _to_int(request.GET.get("security_id"))

        if not trade_dt_raw:
            return JsonResponse({"ok": False, "message": "trade_dt is required."}, status=400)

        if not quantity_raw:
            return JsonResponse({"ok": False, "message": "quantity is required."}, status=400)

        if not price_raw:
            return JsonResponse({"ok": False, "message": "price is required."}, status=400)

        if side not in {"BUY", "SELL"}:
            return JsonResponse({"ok": False, "message": "side must be BUY or SELL."}, status=400)

        trade_dt = datetime.strptime(trade_dt_raw, "%Y-%m-%d").date()
        quantity = Decimal(quantity_raw)
        price = Decimal(price_raw)

        resolved_from = "request"

        if asset_class_id is None or asset_sub_class_id is None:
            resolved = _resolve_instrument_or_security(
                instrument_id=instrument_id,
                security_id=security_id,
            )

            if asset_class_id is None:
                asset_class_id = resolved.get("asset_class_id")

            if asset_sub_class_id is None:
                asset_sub_class_id = resolved.get("asset_sub_class_id")

            resolved_from = resolved.get("resolved_from", "request")

        result = IborFeeEngine.quote_fees(
            trade_dt=trade_dt,
            quantity=quantity,
            price=price,
            side=side,
            broker_id=broker_id,
            exec_venue_id=exec_venue_id,
            asset_class_id=asset_class_id,
            asset_sub_class_id=asset_sub_class_id,
            trade_ccy_id=trade_ccy_id,
            source_system=source_system,
        )

        return JsonResponse({
            "ok": True,
            **result,
            "debug": {
                "trade_dt": trade_dt_raw,
                "quantity": quantity_raw,
                "price": price_raw,
                "side": side,
                "broker_id": broker_id,
                "exec_venue_id": exec_venue_id,
                "asset_class_id": asset_class_id,
                "asset_sub_class_id": asset_sub_class_id,
                "trade_ccy_id": trade_ccy_id,
                "instrument_id": instrument_id,
                "security_id": security_id,
                "source_system": source_system,
                "resolved_from": resolved_from,
            }
        })

    except InvalidOperation:
        return JsonResponse({"ok": False, "message": "quantity or price is not a valid decimal."}, status=400)

    except ValueError:
        return JsonResponse({"ok": False, "message": "trade_dt must be in YYYY-MM-DD format."}, status=400)

    except Exception as exc:
        return JsonResponse({"ok": False, "message": str(exc)}, status=500)


@require_GET
def get_fee_schedule_rules_api(request):
    try:
        from operations.ibor.services.fee_selector import IborFeeScheduleSelector

        trade_dt_raw = request.GET.get("trade_dt", "")
        if not trade_dt_raw:
            return JsonResponse({
                "success": False,
                "error": "trade_dt is required"
            }, status=400)

        trade_dt = datetime.strptime(trade_dt_raw, "%Y-%m-%d").date()

        broker_id = _to_int(request.GET.get("broker_id"))
        exec_venue_id = _to_int(request.GET.get("exec_venue_id"))
        asset_class_id = _to_int(request.GET.get("asset_class_id"))
        asset_sub_class_id = _to_int(request.GET.get("asset_sub_class_id"))
        trade_ccy_id = _to_int(request.GET.get("trade_ccy_id"))
        side = request.GET.get("side", "").strip().upper()
        source_system = request.GET.get("source_system", "").strip()

        instrument_id = _to_int(request.GET.get("instrument_id"))
        security_id = _to_int(request.GET.get("security_id"))

        resolved_from = "request"

        if asset_class_id is None or asset_sub_class_id is None:
            resolved = _resolve_instrument_or_security(
                instrument_id=instrument_id,
                security_id=security_id,
            )

            if asset_class_id is None:
                asset_class_id = resolved.get("asset_class_id")

            if asset_sub_class_id is None:
                asset_sub_class_id = resolved.get("asset_sub_class_id")

            resolved_from = resolved.get("resolved_from", "request")

        share_price_raw = request.GET.get("share_price")
        share_price = None
        if share_price_raw:
            try:
                share_price = Decimal(share_price_raw)
            except (InvalidOperation, ValueError):
                pass

        fee_rules = IborFeeScheduleSelector.get_fee_rules_for_trade(
            trade_dt=trade_dt,
            broker_id=broker_id,
            exec_venue_id=exec_venue_id,
            asset_class_id=asset_class_id,
            asset_sub_class_id=asset_sub_class_id,
            trade_ccy_id=trade_ccy_id,
            side=side,
            source_system=source_system,
            share_price=share_price,
        )

        return JsonResponse({
            "success": True,
            "fee_rules": fee_rules,
            "count": len(fee_rules),
            "debug": {
                "broker_id": broker_id,
                "exec_venue_id": exec_venue_id,
                "asset_class_id": asset_class_id,
                "asset_sub_class_id": asset_sub_class_id,
                "trade_ccy_id": trade_ccy_id,
                "instrument_id": instrument_id,
                "security_id": security_id,
                "source_system": source_system,
                "resolved_from": resolved_from,
            }
        })

    except ValueError as e:
        return JsonResponse({
            "success": False,
            "error": f"Invalid date format: {str(e)}"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


def _to_int(value):
    if value in (None, "", "null", "None"):
        return None
    return int(value)


def _resolve_instrument_or_security(instrument_id=None, security_id=None):
    result = {
        "asset_class_id": None,
        "asset_sub_class_id": None,
        "resolved_from": "request",
    }

    try:
        from refdata.instruments.models import SecurityListing, AssetSubClass
    except Exception:
        return result

    lookup_security_id = instrument_id or security_id
    if not lookup_security_id:
        return result

    try:
        # First try assuming lookup_security_id is SecurityMaster.security_id
        listing = (
            SecurityListing.objects
            .select_related("security")
            .filter(security_id=lookup_security_id)
            .first()
        )
        
        # If not found, try assuming lookup_security_id is SecurityListing.pk (security_listing_id)
        if not listing:
            listing = (
                SecurityListing.objects
                .select_related("security")
                .filter(pk=lookup_security_id)
                .first()
            )

        if not listing or not listing.security:
            return result

        sub_class_id = getattr(listing.security, "sub_class_id", None)
        result["asset_sub_class_id"] = sub_class_id
        result["resolved_from"] = "security_listing"

        if sub_class_id:
            sub_cls = AssetSubClass.objects.filter(sub_asset_class_id=sub_class_id).first()

            if sub_cls:
                result["asset_class_id"] = getattr(sub_cls, "asset_class_id", None)

        return result

    except Exception:
        return result