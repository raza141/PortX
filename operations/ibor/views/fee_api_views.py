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
        side = request.GET.get("side", "").strip()
        source_system = request.GET.get("source_system", "").strip()

        broker_id = _to_int(request.GET.get("broker_id"))
        exec_venue_id = _to_int(request.GET.get("exec_venue_id"))
        asset_class_id = _to_int(request.GET.get("asset_class_id"))
        asset_sub_class_id = _to_int(request.GET.get("asset_sub_class_id"))
        trade_ccy_id = _to_int(request.GET.get("trade_ccy_id"))

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

        return JsonResponse({"ok": True, **result})

    except InvalidOperation:
        return JsonResponse({"ok": False, "message": "quantity or price is not a valid decimal."}, status=400)

    except ValueError:
        return JsonResponse({"ok": False, "message": "trade_dt must be in YYYY-MM-DD format."}, status=400)

    except Exception as exc:
        return JsonResponse({"ok": False, "message": str(exc)}, status=500)


def _to_int(value):
    if value in (None, "", "null", "None"):
        return None
    return int(value)


@require_GET
def get_fee_schedule_rules_api(request):
    """
    API endpoint to fetch fee rules for auto-populating charges in trade form.
    
    Called when user selects broker, asset class, and enters share price.
    Returns ALL fee rules (multiple lines) from the best matching schedule.
    
    GET Parameters:
        - trade_dt: Trade date (YYYY-MM-DD)
        - broker_id: Broker ID
        - exec_venue_id: Exchange ID (optional)
        - asset_class_id: Asset class ID (optional)
        - asset_sub_class_id: Asset sub-class ID (optional)
        - trade_ccy_id: Trade currency ID (optional)
        - share_price: Share price for tiered pricing (optional)
        - side: BUY or SELL (optional)
    
    Returns:
        JSON with:
        {
            "success": true,
            "fee_rules": [
                {
                    "id": 1,
                    "sequence_no": 10,
                    "charge_type_cd": "Commission",
                    "description": "Brokerage Commission",
                    "calc_method": "Percent of gross",
                    "rate": "0.15",
                    "currency_id": "PKR",
                    ...
                },
                {...}
            ],
            "count": 3
        }
    """
    try:
        from operations.ibor.services.fee_selector import IborFeeScheduleSelector
        
        # Parse parameters
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
        
        # Parse share_price for tiered pricing
        share_price_raw = request.GET.get("share_price")
        share_price = None
        if share_price_raw:
            try:
                share_price = Decimal(share_price_raw)
            except (InvalidOperation, ValueError):
                pass  # Ignore invalid share price
        
        # Get all fee rules for matching schedule
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
