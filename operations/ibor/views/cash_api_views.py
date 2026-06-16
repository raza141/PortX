from django.http import JsonResponse
from django.db.models import Sum
from operations.ibor.models.cash_ledger import IborCashEvent
from operations.portfolio.models.account import Account

def get_account_state_api(request):
    """
    Consolidated API to return both the current balance and the currency
    metadata for a specific account to reduce redundant AJAX calls.
    """
    account_id = request.GET.get('account_id')
    
    if not account_id:
        return JsonResponse({'success': False, 'error': 'account_id is required'}, status=400)

    # 1. Fetch the aggregated balance from the cash ledger
    balance = IborCashEvent.objects.filter(
        account_id=account_id
    ).aggregate(total=Sum('amount'))['total'] or 0

    # 2. Fetch account metadata (Currency)
    try:
        account = Account.objects.select_related('ccy').get(pk=account_id)
        currency_code = getattr(account.ccy, 'code', str(account.ccy))
    except Account.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    return JsonResponse({
        'success': True,
        'balance': float(balance),
        'currency_code': currency_code
    })