"""
Chart generation for monthly reports using matplotlib.
"""

import matplotlib

matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
from .data_models import PortfolioData


class ChartGenerator:
    """Generates performance and allocation charts."""

    def __init__(self, navy='#0D1B2A', gold='#C9A84C', light='#F4F6F9'):
        self.navy = navy
        self.gold = gold
        self.light = light

    def create_performance_chart(self, data: PortfolioData) -> io.BytesIO:
        """Bar chart: Portfolio vs Benchmark for 3 periods."""
        fig, ax = plt.subplots(figsize=(6.5, 2.6))
        periods = ['This Month', 'Year-to-Date', 'Since Inception']
        port_vals = [data.net_month, data.net_ytd, data.net_inception]
        bench_vals = [data.benchmark_month, data.benchmark_ytd, data.benchmark_inception]

        x = range(len(periods))
        w = 0.35
        bars1 = ax.bar([i - w / 2 for i in x], port_vals, w, label='Portfolio (Net)',
                       color=self.navy, zorder=3)
        bars2 = ax.bar([i + w / 2 for i in x], bench_vals, w, label=data.benchmark,
                       color=self.gold, zorder=3)

        ax.set_xticks(list(x))
        ax.set_xticklabels(periods, fontsize=8)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.1f}%'))
        ax.tick_params(axis='y', labelsize=7)
        ax.set_facecolor(self.light)
        fig.patch.set_facecolor('white')
        ax.grid(axis='y', alpha=0.4, zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(fontsize=7, loc='upper left')
        ax.set_title('Portfolio vs Benchmark Returns (%)', fontsize=9, pad=8, fontweight='bold')

        # Annotations
        for bar in bars1:
            h = bar.get_height()
            ax.annotate(f'{h:.1f}%', xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', fontsize=6.5, color=self.navy)
        for bar in bars2:
            h = bar.get_height()
            ax.annotate(f'{h:.1f}%', xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', fontsize=6.5, color='#8B6914')

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf

    def create_allocation_chart(self, cash_pct: float, invested_pct: float) -> io.BytesIO:
        """Donut chart: Cash vs Invested."""
        fig, ax = plt.subplots(figsize=(2.2, 2.2))
        vals = [invested_pct, cash_pct]
        lbls = [f'Invested\n{invested_pct}%', f'Cash\n{cash_pct}%']
        clrs = [self.navy, self.gold]

        wedges, texts = ax.pie(vals, labels=lbls, colors=clrs, startangle=90,
                               wedgeprops=dict(width=0.55), textprops={'fontsize': 7})
        ax.set_title('Allocation', fontsize=8, fontweight='bold', pad=4)
        fig.patch.set_facecolor('white')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf