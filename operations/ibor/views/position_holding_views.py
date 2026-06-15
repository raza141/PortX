#directory path
#operations/ibor/views/position_holding_views.py

# operations/ibor/views/position_holding_views.py
from decimal import Decimal
from django.views.generic import TemplateView
from operations.ibor.models.cash_ledger import IborCashEvent
from operations.ibor.models.lot import IborTaxLot
from django.db.models import Sum, F
from governance.crm.models import Investor

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

        # 2. Group Hierarchy: Investor -> Mandate -> Instrument -> Lots
        investor_tree = {}
        active_portfolio_ids = set()

        for lot in active_lots:
            investor = lot.portfolio.mandate.investor
            if not investor:
                continue

            mandate = lot.portfolio.mandate
            instrument = lot.instrument
            active_portfolio_ids.add(lot.portfolio_id)
            
            if investor.pk not in investor_tree:
                investor_tree[investor.pk] = {
                    'investor': investor,
                    'mandates': {}
                }

            investor_node = investor_tree[investor.pk]
            if mandate.pk not in investor_node['mandates']:
                investor_node['mandates'][mandate.pk] = {
                    'mandate': mandate,
                    'holdings': {}
                }
            
            mandate_node = investor_node['mandates'][mandate.pk]
            if instrument.pk not in mandate_node['holdings']:
                mandate_node['holdings'][instrument.pk] = {
                    'instrument': instrument,
                    'total_qty': 0,
                    'total_cost': 0,
                    'lots': [],
                    'ccy_code': getattr(lot.cost_ccy, 'code', '') if lot.cost_ccy else ''
                }
            
            inst_data = mandate_node['holdings'][instrument.pk]
            inst_data['total_qty'] += lot.remaining_qty
            lot.total_cost = lot.remaining_qty * lot.unit_cost
            inst_data['total_cost'] += lot.total_cost
            inst_data['lots'].append(lot)

        # 3. Pre-calculate Averages
        for investor in investor_tree.values():
            for mandate in investor['mandates'].values():
                for inst in mandate['holdings'].values():
                    # Quantize/Round to match the 4 decimal places in the model
                    if inst['total_qty'] > 0:
                        inst['avg_cost'] = (inst['total_cost'] / inst['total_qty']).quantize(Decimal("0.0001"))
                    else:
                        inst['avg_cost'] = 0

        context['investors'] = investor_tree.values()
        context['total_aum'] = sum(lot.remaining_qty * lot.unit_cost for lot in active_lots)
        
        # Filter cash to only include portfolios currently being viewed in the holdings list
        context['total_cash'] = IborCashEvent.objects.filter(portfolio_id__in=active_portfolio_ids).aggregate(Sum('amount'))['amount__sum'] or 0
        context['active_tab'] = 'positions'
        return context