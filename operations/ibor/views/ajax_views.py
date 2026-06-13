from django.http import JsonResponse
from django.views import View
from refdata.masters.models.fx import FxRateDaily
from refdata.masters.models.currency_pair import CurrencyPair
from operations.portfolio.models.account import Account
from datetime import datetime

class GetFxRateView(View):
    def get(self, request, *args, **kwargs):
        currency_pair_id = request.GET.get('currency_pair_id')
        effective_date_str = request.GET.get('effective_date')
        
        if not currency_pair_id or not effective_date_str:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
            
        try:
            effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d').date()
            currency_pair = CurrencyPair.objects.get(pk=currency_pair_id)
            
            # Find the rate for the pair and date
            # Assuming FX rate table uses the base/quote currency directly
            fx_rate = FxRateDaily.objects.filter(
                base_currency=currency_pair.base_currency,
                quote_currency=currency_pair.quote_currency,
                rate_date=effective_date
            ).order_by('-created_at').first()
            
            if fx_rate:
                return JsonResponse({'fx_rate': float(fx_rate.mid)})
            else:
                return JsonResponse({'error': 'No FX rate found for the given date'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class GetCurrencyPairView(View):
    def get(self, request, *args, **kwargs):
        base_currency_id = request.GET.get('base_currency_id')
        quote_currency_id = request.GET.get('quote_currency_id')
        
        if not base_currency_id or not quote_currency_id:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
            
        try:
            pair = CurrencyPair.objects.filter(
                base_currency_id=base_currency_id,
                quote_currency_id=quote_currency_id
            ).first()
            
            if pair:
                return JsonResponse({'pair_id': pair.pk, 'pair_code': pair.code})
            else:
                return JsonResponse({'error': 'Currency pair not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class GetAccountCurrencyView(View):
    def get(self, request, *args, **kwargs):
        account_id = request.GET.get('account_id')
        
        if not account_id:
            return JsonResponse({'error': 'Missing account_id'}, status=400)
            
        try:
            account = Account.objects.get(pk=account_id)
            if account.ccy:
                return JsonResponse({'currency_id': account.ccy.pk, 'currency_code': account.ccy.code})
            else:
                return JsonResponse({'error': 'Account has no currency'}, status=404)
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
