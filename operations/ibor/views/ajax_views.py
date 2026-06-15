from django.http import JsonResponse
from django.views import View
from refdata.masters.models.fx import FxRateDaily
from refdata.masters.models.currency_pair import CurrencyPair
from operations.portfolio.models.account import Account
from operations.portfolio.models.portfolio import Portfolio
from operations.portfolio.models.portfolio_account import PortfolioAccountMap
from refdata.masters.models.broker import Broker
from refdata.masters.models.exchange import Exchange
from datetime import datetime, timedelta

class GetAccountsByPortfolioView(View):
    def get(self, request, *args, **kwargs):
        portfolio_id = request.GET.get('portfolio_id')
        if not portfolio_id:
            return JsonResponse({'error': 'Missing portfolio_id'}, status=400)
        
        accounts = PortfolioAccountMap.objects.filter(portfolio_id=portfolio_id).values('account_id', 'account__acct_cd')
        return JsonResponse(list(accounts), safe=False)

class GetBrokerByAccountView(View):
    def get(self, request, *args, **kwargs):
        account_id = request.GET.get('account_id')
        if not account_id:
            return JsonResponse({'error': 'Missing account_id'}, status=400)
        
        try:
            account = Account.objects.get(pk=account_id)
            if account.broker:
                return JsonResponse({'broker_id': account.broker.pk, 'broker_name': str(account.broker)})
            return JsonResponse({'error': 'No broker for account'}, status=404)
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)

class GetExchangeByBrokerView(View):
    def get(self, request, *args, **kwargs):
        broker_id = request.GET.get('broker_id')
        if not broker_id:
            return JsonResponse({'error': 'Missing broker_id'}, status=400)
        
        try:
            broker = Broker.objects.get(pk=broker_id)
            if broker.exchange:
                return JsonResponse({
                    'exchange_id': broker.exchange.pk, 
                    'exchange_name': str(broker.exchange),
                    'settlement_days': getattr(broker.exchange, 'settlement_days', 2)  # Default to T+2 if not set
                })
            return JsonResponse({'error': 'No exchange for broker'}, status=404)
        except Broker.DoesNotExist:
            return JsonResponse({'error': 'Broker not found'}, status=404)

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


class GetBrokerCurrencyView(View):
    """
    Returns the default base currency for a given broker.
    """
    def get(self, request, *args, **kwargs):
        broker_id = request.GET.get('broker_id')
        if not broker_id:
            return JsonResponse({'error': 'Missing broker_id'}, status=400)
        
        try:
            broker = Broker.objects.get(pk=broker_id)
            if broker.default_base_currency:
                return JsonResponse({
                    'currency_id': broker.default_base_currency.pk,
                    'currency_code': broker.default_base_currency.code
                })
            return JsonResponse({'error': 'Broker has no default currency'}, status=404)
        except Broker.DoesNotExist:
            return JsonResponse({'error': 'Broker not found'}, status=404)


class GetPortfolioControlsView(View):
    def get(self, request):
        portfolio_id = request.GET.get('portfolio_id')
        if not portfolio_id:
            return JsonResponse({'trading_enabled': False, 'discretion_enabled': False})

        try:
            # trd_enbl_flg is the correct field for Portfolio
            # discretion is typically a Mandate property (pm_discretion_allowed)
            portfolio = Portfolio.objects.select_related('mandate').get(pk=portfolio_id)
            return JsonResponse({
                'trading_enabled': portfolio.trd_enbl_flg,
                'discretion_enabled': getattr(portfolio.mandate, 'pm_discretion_allowed', False)
            })
        except Portfolio.DoesNotExist:
            return JsonResponse({'error': 'Portfolio not found'}, status=404)

class CalculateSettlementDateView(View):
    def get(self, request):
        trade_dt_str = request.GET.get('trade_dt')
        exchange_id = request.GET.get('exchange_id')

        if not trade_dt_str or not exchange_id:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        try:
            trade_dt = datetime.strptime(trade_dt_str, '%Y-%m-%d').date()
            exchange = Exchange.objects.get(pk=exchange_id)
            settle_days = getattr(exchange, 'settlement_days', 2)
            settle_dt = trade_dt + timedelta(days=settle_days)

            return JsonResponse({
                'trade_dt': trade_dt_str,
                'exchange_id': exchange_id,
                'settlement_days': settle_days,
                'settlement_dt': settle_dt.strftime('%Y-%m-%d')
            })
        except Exchange.DoesNotExist:
            return JsonResponse({'error': 'Invalid exchange_id'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid trade_dt format. Use YYYY-MM-DD'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)