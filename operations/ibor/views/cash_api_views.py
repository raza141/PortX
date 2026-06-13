from django.http import JsonResponse
from django.views.decorators.http import require_GET
from operations.ibor.services.cash_booking import CashBookingService
from datetime import datetime

@require_GET
def get_cash_balance_api(request):
    portfolio_id = request.GET.get("portfolio_id")
    effective_dt_raw = request.GET.get("effective_dt")
    
    if not portfolio_id:
        return JsonResponse({"ok": False, "message": "portfolio_id is required."}, status=400)
    
    effective_dt = datetime.now().date()
    if effective_dt_raw:
        try:
            effective_dt = datetime.strptime(effective_dt_raw, "%Y-%m-%d").date()
        except ValueError:
             return JsonResponse({"ok": False, "message": "Invalid date format."}, status=400)

    try:
        balance = CashBookingService.get_cash_balance(int(portfolio_id), effective_dt)
        return JsonResponse({"ok": True, "balance": str(balance)})
    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)}, status=500)


@require_GET
def get_fx_rate_api(request):
    portfolio_id = request.GET.get("portfolio_id")
    currency_id = request.GET.get("currency_id")
    effective_dt_raw = request.GET.get("effective_dt")
    
    if not portfolio_id or not currency_id:
        return JsonResponse({"ok": False, "message": "portfolio_id and currency_id are required."}, status=400)
    
    effective_dt = datetime.now().date()
    if effective_dt_raw:
        try:
            effective_dt = datetime.strptime(effective_dt_raw, "%Y-%m-%d").date()
        except ValueError:
             return JsonResponse({"ok": False, "message": "Invalid date format."}, status=400)

    try:
        rate, pair = CashBookingService.get_fx_rate(int(portfolio_id), int(currency_id), effective_dt)
        return JsonResponse({
            "ok": True, 
            "rate": str(rate) if rate else "", 
            "pair_id": pair.currency_pair_id if pair else "",
            "pair_code": str(pair) if pair else ""
        })
    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)}, status=500)
