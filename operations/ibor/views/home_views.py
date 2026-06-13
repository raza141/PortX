from django.shortcuts import render
from django.views import View
from operations.ibor.models.trade import IborTradeEvent
from operations.ibor.models.cash_ledger import IborCashEvent
from django.db.models import Sum
from governance.crm.models import Investor

class IborHomeView(View):
    template_name = "ibor/home.html"

    def get(self, request, *args, **kwargs):
        trade_count = IborTradeEvent.objects.count()
        cash_count = IborCashEvent.objects.count()
        # Simple balance: sum of amount for all cash events.
        total_cash_balance = IborCashEvent.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        
        client_count = Investor.objects.count()
        clients = Investor.objects.annotate(balance=Sum('mandates__portfolios__ibor_cash_events__amount'))
        
        context = {
            'trade_count': trade_count,
            'cash_count': cash_count,
            'total_cash_balance': total_cash_balance,
            'client_count': client_count,
            'clients': clients,
            'active_tab': 'home'
        }
        return render(request, self.template_name, context)
