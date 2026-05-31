"""
Test script to generate a sample monthly report.
Run this to verify the PDF generator works before integrating with Django/MongoDB.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path so we can import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rep.monthly_reports.services.data_models import PortfolioData
from rep.monthly_reports.services.report_builder import RoyeveReportGenerator


def create_sample_data():
    """Create sample portfolio data for testing"""

    return PortfolioData(
        # Client Info
        client_name='Sarah Al Mansouri',
        account_number='RC-2024-001',
        client_type='UAE',
        reporting_month='May 2026',
        report_date='30 May 2026',
        portfolio_manager='Royeve Capital',
        base_currency='AED',
        benchmark='S&P 500',
        inception_date='January 2024',

        # Portfolio Values
        opening_value=250_000,
        contributions=10_000,
        withdrawals=0,
        ending_value=268_500,
        net_invested=260_000,
        cash_pct=8.5,
        invested_pct=91.5,

        # Performance
        gross_month=3.40,
        net_month=3.15,
        benchmark_month=2.10,
        gross_ytd=12.80,
        net_ytd=11.90,
        benchmark_ytd=8.40,
        gross_inception=28.50,
        net_inception=25.90,
        benchmark_inception=19.20,

        # Fees
        mgmt_fee=325.00,
        perf_fee=0.00,
        other_charges=45.00,
        fee_basis='Net of all fees and direct trading costs',

        # Risk
        largest_position=12.4,
        top5_concentration=48.2,
        cash_buffer=8.5,
        max_drawdown=-6.8,
        beta=0.82,

        # Holdings
        holdings=[
            ('NVIDIA Corp (NVDA)', '12.4%', '+1.12%', 'AI chip leadership; strong data centre demand'),
            ('Microsoft Corp (MSFT)', '11.8%', '+0.43%', 'Azure cloud growth; Copilot monetisation'),
            ('Apple Inc (AAPL)', '10.2%', '+0.28%', 'Services revenue expansion; India manufacturing'),
            ('Alphabet Inc (GOOGL)', '8.9%', '+0.31%', 'Search dominance; YouTube ad recovery'),
            ('Amazon.com (AMZN)', '4.9%', '+0.18%', 'AWS margin improvement; logistics efficiency'),
        ],

        # Transactions
        transactions=[
            ('02 May 2026', 'BUY', 'NVIDIA Corp (NVDA)', '15 shares', 'AED 4,102', 'Added on AI data centre demand'),
            ('14 May 2026', 'SELL', 'Tesla Inc (TSLA)', '20 shares', 'AED 1,830', 'Trimmed on valuation concerns'),
            ('22 May 2026', 'BUY', 'Microsoft Corp (MSFT)', '10 shares', 'AED 1,560',
             'Increased on Copilot revenue beat'),
        ],

        # Commentary
        market_commentary=(
            'Global equity markets delivered solid gains in May 2026, supported by resilient US corporate earnings '
            'and easing inflation data. The S&P 500 rose 2.1% for the month, led by technology and communication '
            'services sectors. The Federal Reserve maintained its pause on rate hikes, with market participants now '
            'pricing two rate cuts before year-end. In the UAE, the DFM remained broadly stable while regional '
            'sentiment was supported by firm oil prices above USD 83/bbl.'
        ),
        portfolio_commentary=(
            'The portfolio outperformed its benchmark by 105 basis points on a net basis in May, driven primarily '
            'by strong contributions from our overweight position in NVIDIA (+1.12%) following another record data '
            'centre revenue quarter. Microsoft also contributed positively as Azure growth reaccelerated. We trimmed '
            'Tesla following a 22% rally in April, locking in gains and reducing single-stock concentration risk. '
            'Cash was redeployed into NVIDIA and Microsoft on the dip following initial post-earnings volatility.'
        ),
        outlook=(
            'We remain constructive on US technology equities into the second half of 2026, with AI capital expenditure '
            'cycles supporting earnings for our core holdings. Key risks being monitored include: (1) US-China trade '
            'policy developments, (2) Federal Reserve communication at the June FOMC meeting, and (3) stretched '
            'valuations in the semiconductor space. We plan to gradually reduce cash from 8.5% toward 5% over the '
            'next 60 days, selectively adding to quality growth names on any market weakness.'
        ),
    )


def main():
    """Main test function"""

    print("=" * 60)
    print("ROYEVE CAPITAL - Monthly Report Generator Test")
    print("=" * 60)
    print()

    # Create sample data
    print("Step 1: Creating sample portfolio data...")
    portfolio_data = create_sample_data()
    print(f"✓ Portfolio data created for: {portfolio_data.client_name}")
    print(f"  Ending Value: {portfolio_data.base_currency} {portfolio_data.ending_value:,.0f}")
    print(f"  Net Return (Month): {portfolio_data.net_month}%")
    print(f"  Excess Return: {portfolio_data.get_excess_return_month():.2f}%")
    print()

    # Generate PDF
    print("Step 2: Generating PDF report...")
    output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    os.makedirs(output_dir, exist_ok=True)

    pdf_filename = os.path.join(output_dir,
                                f'Royeve_Monthly_Report_Test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')

    generator = RoyeveReportGenerator(portfolio_data)
    result = generator.generate_pdf(pdf_filename)

    print()
    print("=" * 60)
    print(f"✅ SUCCESS! PDF generated at:")
    print(f"   {result}")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Open the PDF to verify it looks correct")
    print("2. If it works, integrate with your Django views")
    print("3. Replace sample data with real MongoDB queries")


if __name__ == '__main__':
    main()
