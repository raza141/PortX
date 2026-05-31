"""
Data aggregation layer that pulls from your existing performance and risk modules
and transforms into PortfolioData for PDF generation.
"""

from typing import Dict, List, Tuple
from datetime import datetime
from .data_models import PortfolioData


class ReportDataAggregator:
    """
    Aggregates data from performance and risk modules to build PortfolioData.

    This is the bridge between your existing Django/MongoDB models and the PDF generator.
    """

    def __init__(self, client_id: str, month: datetime):
        self.client_id = client_id
        self.month = month

    def build_portfolio_data(self) -> PortfolioData:
        """
        Main method to aggregate all data from your database and modules.

        TODO: Update this to call your actual performance and risk calculators.
        """

        # Get data from various sources
        client_info = self._get_client_info()
        portfolio = self._get_portfolio_snapshot()
        performance = self._get_performance_data()
        risk = self._get_risk_data()
        holdings = self._get_holdings()
        transactions = self._get_transactions()
        commentary = self._get_commentary()

        # Build PortfolioData object
        return PortfolioData(
            # Client info
            client_name=client_info['name'],
            account_number=client_info['account_number'],
            client_type=client_info['type'],
            reporting_month=self.month.strftime('%B %Y'),
            report_date=datetime.now().strftime('%d %B %Y'),
            base_currency=client_info['currency'],
            benchmark=client_info['benchmark'],
            inception_date=client_info['inception_date'].strftime('%B %Y'),

            # Portfolio values
            opening_value=portfolio['opening_value'],
            contributions=portfolio['contributions'],
            withdrawals=portfolio['withdrawals'],
            ending_value=portfolio['ending_value'],
            net_invested=portfolio['net_invested'],
            cash_pct=portfolio['cash_pct'],
            invested_pct=portfolio['invested_pct'],

            # Performance (from your performance module)
            gross_month=performance['gross_month'],
            net_month=performance['net_month'],
            benchmark_month=performance['benchmark_month'],
            gross_ytd=performance['gross_ytd'],
            net_ytd=performance['net_ytd'],
            benchmark_ytd=performance['benchmark_ytd'],
            gross_inception=performance['gross_inception'],
            net_inception=performance['net_inception'],
            benchmark_inception=performance['benchmark_inception'],

            # Fees
            mgmt_fee=commentary.get('mgmt_fee', 0),
            perf_fee=commentary.get('perf_fee', 0),
            other_charges=commentary.get('other_charges', 0),

            # Risk (from your risk module)
            largest_position=risk['largest_position'],
            top5_concentration=risk['top5_concentration'],
            cash_buffer=portfolio['cash_pct'],
            max_drawdown=risk['max_drawdown'],
            beta=risk['beta'],

            # Holdings (formatted)
            holdings=self._format_holdings(holdings),

            # Transactions (formatted)
            transactions=self._format_transactions(transactions),

            # Commentary
            market_commentary=commentary.get('market_commentary', ''),
            portfolio_commentary=commentary.get('portfolio_commentary', ''),
            outlook=commentary.get('outlook', ''),
        )

    def _get_client_info(self) -> Dict:
        """
        Fetch client information from database.

        TODO: Replace with your actual client model query.
        """
        # PLACEHOLDER - Replace with your actual code
        # Example:
        # from data.models import Client
        # client = Client.objects.get(id=self.client_id)

        return {
            'name': 'Sarah Al Mansouri',
            'account_number': 'RC-2024-001',
            'type': 'UAE',
            'currency': 'AED',
            'benchmark': 'S&P 500',
            'inception_date': datetime(2024, 1, 15),
        }

    def _get_portfolio_snapshot(self) -> Dict:
        """
        Get portfolio values for the month.

        TODO: Replace with your actual MongoDB query.
        """
        # PLACEHOLDER - Replace with your actual code
        return {
            'opening_value': 250_000,
            'contributions': 10_000,
            'withdrawals': 0,
            'ending_value': 268_500,
            'net_invested': 260_000,
            'cash_pct': 8.5,
            'invested_pct': 91.5,
        }

    def _get_performance_data(self) -> Dict:
        """
        Call your existing performance module to get returns.

        TODO: Replace with actual calls to rep/performance/calculators.py
        """
        # PLACEHOLDER - Replace with actual code
        # Example:
        # from rep.performance.calculators import PerformanceCalculator
        # calc = PerformanceCalculator(self.client_id)
        # return calc.get_monthly_performance(self.month)

        return {
            'gross_month': 3.40,
            'net_month': 3.15,
            'benchmark_month': 2.10,
            'gross_ytd': 12.80,
            'net_ytd': 11.90,
            'benchmark_ytd': 8.40,
            'gross_inception': 28.50,
            'net_inception': 25.90,
            'benchmark_inception': 19.20,
        }

    def _get_risk_data(self) -> Dict:
        """
        Call your existing risk module to get risk metrics.

        TODO: Replace with actual calls to rep/risk/calculators.py
        """
        # PLACEHOLDER - Replace with actual code
        # Example:
        # from rep.risk.calculators import RiskCalculator
        # calc = RiskCalculator(self.client_id)
        # return calc.get_risk_metrics(self.month)

        return {
            'largest_position': 12.4,
            'top5_concentration': 48.2,
            'max_drawdown': -6.8,
            'beta': 0.82,
        }

    def _get_holdings(self) -> List[Dict]:
        """
        Fetch holdings from database.

        TODO: Replace with your actual MongoDB query.
        """
        # PLACEHOLDER - Replace with actual code
        return [
            {
                'security': 'NVIDIA Corp (NVDA)',
                'weight': 12.4,
                'contribution': 1.12,
                'thesis': 'AI chip leadership; strong data centre demand'
            },
            {
                'security': 'Microsoft Corp (MSFT)',
                'weight': 11.8,
                'contribution': 0.43,
                'thesis': 'Azure cloud growth; Copilot monetisation'
            },
        ]

    def _get_transactions(self) -> List[Dict]:
        """
        Fetch transactions for the month from database.

        TODO: Replace with your actual MongoDB query.
        """
        # PLACEHOLDER - Replace with actual code
        return [
            {
                'date': datetime(2026, 5, 2),
                'action': 'BUY',
                'security': 'NVIDIA Corp (NVDA)',
                'quantity': 15,
                'total_value': 4102,
                'rationale': 'Added on AI data centre demand'
            },
        ]

    def _get_commentary(self) -> Dict:
        """
        Get commentary from MonthlyReport record (manual entry or saved).

        TODO: Replace with actual model query.
        """
        # PLACEHOLDER - Replace with actual code
        return {
            'market_commentary': 'Global equity markets delivered solid gains...',
            'portfolio_commentary': 'The portfolio outperformed benchmark...',
            'outlook': 'We remain constructive on US tech equities...',
            'mgmt_fee': 325.00,
            'perf_fee': 0.00,
            'other_charges': 45.00,
        }

    def _format_holdings(self, holdings: List[Dict]) -> List[Tuple]:
        """Transform holdings to tuple format for PDF"""
        return [
            (
                h['security'],
                f"{h['weight']:.1f}%",
                f"{h['contribution']:+.2f}%",
                h['thesis']
            )
            for h in holdings[:8]  # Top 8
        ]

    def _format_transactions(self, transactions: List[Dict]) -> List[Tuple]:
        """Transform transactions to tuple format for PDF"""
        return [
            (
                t['date'].strftime('%d %b %Y'),
                t['action'],
                t['security'],
                f"{t['quantity']} shares",
                f"AED {t['total_value']:,.2f}",  # TODO: Use dynamic currency
                t['rationale']
            )
            for t in transactions
        ]