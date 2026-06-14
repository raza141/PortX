#directory path
#operations/ibor/views/position_holding_views.py

# operations/ibor/views/position_holding_views.py
from django.views.generic import TemplateView
from operations.ibor.models.cash_ledger import IborCashEvent
from operations.ibor.models.lot import IborTaxLot
from django.db.models import Sum, F

class PositionHoldingView(TemplateView):
    template_name = "ibor/trade/position_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Fetch active inventory lots. 
        # Path corrected from 'portfolio__client' to 'portfolio__mandate__investor'
        active_lots = IborTaxLot.objects.filter(remaining_qty__gt=0).select_related(
            'instrument__security', 
            'portfolio__mandate__investor', 
            'cost_ccy'
        ).order_by('instrument__ticker', 'portfolio__port_nm', 'acquired_dt')

        # 2. Group Hierarchy: Instrument -> Portfolio -> Lots
        # This structure matches your position_form.html template UI
        holdings_tree = {}
        for lot in active_lots:
            ticker = lot.instrument.ticker
            
            if ticker not in holdings_tree:
                holdings_tree[ticker] = {
                    'instrument': lot.instrument,
                    'total_qty': 0,
                    'total_cost': 0,
                    'portfolios': {},
                    'lots': []
                }
            
            inst_data = holdings_tree[ticker]
            inst_data['total_qty'] += lot.remaining_qty
            lot.total_cost = lot.remaining_qty * lot.unit_cost
            inst_data['total_cost'] += lot.total_cost

            port_id = lot.portfolio_id
            if port_id not in inst_data['portfolios']:
                inst_data['portfolios'][port_id] = {
                    'portfolio': lot.portfolio,
                    'qty': 0,
                    'cost': 0,
                    'lots': []
                }
            
            port_data = inst_data['portfolios'][port_id]
            port_data['qty'] += lot.remaining_qty
            port_data['cost'] += lot.total_cost
            inst_data['lots'].append(lot)
            port_data['lots'].append(lot)

        # 3. Pre-calculate Averages
        for inst in holdings_tree.values():
            inst['avg_cost'] = inst['total_cost'] / inst['total_qty'] if inst['total_qty'] else 0
            for port in inst['portfolios'].values():
                port['avg_cost'] = port['cost'] / port['qty'] if port['qty'] else 0

        context['holdings'] = holdings_tree.values()
        context['total_aum'] = sum(lot.remaining_qty * lot.unit_cost for lot in active_lots)
        context['total_cash'] = IborCashEvent.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        context['active_tab'] = 'positions'
        return context