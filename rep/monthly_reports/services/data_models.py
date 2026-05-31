"""
Data models for monthly report generation.
Contains the PortfolioData dataclass that holds all report data.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class PortfolioData:
    """Encapsulates all client and portfolio data for the monthly report."""

    # Client Information
    client_name: str
    account_number: str
    client_type: str  # UAE / Pakistan / Sarwa
    reporting_month: str
    report_date: str
    portfolio_manager: str = 'Royeve Capital'
    base_currency: str = 'AED'
    benchmark: str = 'S&P 500'
    inception_date: str = 'January 2024'

    # Portfolio Values
    opening_value: float = 0.0
    contributions: float = 0.0
    withdrawals: float = 0.0
    ending_value: float = 0.0
    net_invested: float = 0.0
    cash_pct: float = 0.0
    invested_pct: float = 100.0

    # Performance (% returns)
    gross_month: float = 0.0
    net_month: float = 0.0
    benchmark_month: float = 0.0
    gross_ytd: float = 0.0
    net_ytd: float = 0.0
    benchmark_ytd: float = 0.0
    gross_inception: float = 0.0
    net_inception: float = 0.0
    benchmark_inception: float = 0.0

    # Fees
    mgmt_fee: float = 0.0
    perf_fee: float = 0.0
    other_charges: float = 0.0
    fee_basis: str = 'Net of all fees and direct trading costs'

    # Risk Metrics
    largest_position: float = 0.0
    top5_concentration: float = 0.0
    cash_buffer: float = 0.0
    max_drawdown: float = 0.0
    beta: float = 1.0

    # Holdings: List of (security, weight, contribution, thesis)
    holdings: List[Tuple[str, str, str, str]] = field(default_factory=list)

    # Transactions: List of (date, action, security, qty, price, rationale)
    transactions: List[Tuple[str, str, str, str, str, str]] = field(default_factory=list)

    # Commentary
    market_commentary: str = ''
    portfolio_commentary: str = ''
    outlook: str = ''

    def get_excess_return_month(self) -> float:
        """Calculate monthly excess return vs benchmark"""
        return self.net_month - self.benchmark_month

    def get_excess_return_ytd(self) -> float:
        """Calculate YTD excess return vs benchmark"""
        return self.net_ytd - self.benchmark_ytd

    def get_excess_return_inception(self) -> float:
        """Calculate inception excess return vs benchmark"""
        return self.net_inception - self.benchmark_inception

    def get_net_cash_flow(self) -> float:
        """Calculate net cash flow (contributions - withdrawals)"""
        return self.contributions - self.withdrawals