"""
t_rep.py  —  Manual run for May 2026
Usage: python manage.py shell < t_rep.py
  OR:  python t_rep.py (if Django settings are set)
"""

import os
import sys
import django
from datetime import date
from decimal import Decimal

# ── Django setup (skip if already in shell) ──────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rep.monthly_reports.services.data_models import PortfolioData
from rep.monthly_reports.services.report_builder import RoyeveReportGenerator

# ══════════════════════════════════════════════════════════
# STEP 1 — Fetch live data from DB
# ══════════════════════════════════════════════════════════
def fetch_live_data(portfolio_id: int, report_date: date) -> dict:
    with connection.cursor() as cur:

        # Portfolio + Benchmark
        cur.execute("""
            SELECT p.port_nm, p.port_cd, p.incp_dt,
                   m.mand_nm, b.benchmark_name
            FROM   pxporthdr p
            JOIN   pxmandhdr m  ON p.mand_id = m.mand_id
            LEFT JOIN benchmark b ON m.bmk_id = b.id
            WHERE  p.port_id = %s
        """, [portfolio_id])
        port = cur.fetchone()

        # Cash
        cur.execute("""
            SELECT
                ROUND(SUM(CASE WHEN cash_event_type='DEPOSIT'
                               THEN amount ELSE 0 END)::numeric,2),
                ROUND(SUM(CASE WHEN cash_event_type='WITHDRAWAL'
                               THEN amount ELSE 0 END)::numeric,2),
                ROUND(SUM(CASE WHEN cash_event_type='DIVIDEND'
                               THEN amount ELSE 0 END)::numeric,2),
                ROUND(SUM(CASE WHEN cash_event_type='TRADE_SETTLE'
                               THEN amount ELSE 0 END)::numeric,2),
                ROUND(SUM(CASE WHEN cash_event_type='OTHER'
                               THEN amount ELSE 0 END)::numeric,2),
                ROUND(SUM(amount)::numeric,2)
            FROM iborcshevt
            WHERE portfolio_id=%s AND is_active=true
        """, [portfolio_id])
        cash = cur.fetchone()

        # Holdings via listing join (fixed)
        cur.execute("""
            SELECT
                sm.security_name,
                SUM(CASE WHEN t.side='BUY'  THEN t.quantity ELSE 0 END) -
                SUM(CASE WHEN t.side='SELL' THEN t.quantity ELSE 0 END)  AS net_qty,
                ROUND(
                    SUM(CASE WHEN t.side='BUY' THEN t.quantity*t.price ELSE 0 END) /
                    NULLIF(SUM(CASE WHEN t.side='BUY' THEN t.quantity ELSE 0 END),0)
                ::numeric,4)                                              AS avg_cost,
                ROUND((
                    SUM(CASE WHEN t.side='BUY'  THEN t.quantity*t.price ELSE 0 END) -
                    SUM(CASE WHEN t.side='SELL' THEN t.quantity*t.price ELSE 0 END)
                )::numeric,2)                                             AS cost_basis
            FROM ibortrdevt t
            JOIN secsecuritylisting sl ON t.instrument_id = sl.security_listing_id
            JOIN secsecuritymaster  sm ON sl.security_id  = sm.security_id
            WHERE t.portfolio_id=%s AND t.is_active=true
            GROUP BY sm.security_name
            HAVING (
                SUM(CASE WHEN t.side='BUY'  THEN t.quantity ELSE 0 END) -
                SUM(CASE WHEN t.side='SELL' THEN t.quantity ELSE 0 END)
            ) > 0
            ORDER BY cost_basis DESC
        """, [portfolio_id])
        holdings_raw = cur.fetchall()

        # Trades this month
        cur.execute("""
            SELECT t.trade_dt, t.side, sm.security_name,
                   t.quantity, t.price, t.gross_amount
            FROM   ibortrdevt t
            JOIN   secsecuritylisting sl ON t.instrument_id = sl.security_listing_id
            JOIN   secsecuritymaster  sm ON sl.security_id  = sm.security_id
            WHERE  t.portfolio_id=%s
              AND  t.trade_dt >= date_trunc('month', %s::date)
              AND  t.trade_dt <= %s
              AND  t.is_active=true
            ORDER  BY t.trade_dt
        """, [portfolio_id, report_date, report_date])
        trades = cur.fetchall()

    # Compute weights
    cash_bal   = Decimal(str(cash[5] or 0))
    total_cost = sum(Decimal(str(h[3] or 0)) for h in holdings_raw)
    total_aum  = total_cost + cash_bal

    holdings = []
    for name, qty, avg_cost, cost_basis in holdings_raw:
        cost = Decimal(str(cost_basis or 0))
        wt   = round(float(cost / total_aum * 100), 1) if total_aum else 0.0
        holdings.append({
            'name':       name,
            'qty':        float(qty or 0),
            'avg_cost':   float(avg_cost or 0),
            'cost_basis': float(cost),
            'weight':     wt,
        })

    cash_wt = round(float(cash_bal / total_aum * 100), 1) if total_aum else 0.0

    return {
        # Portfolio info
        'client_name':   'ALYAZIA MOHAMED ALMENHALI',
        'portfolio_code': port[1] if port else 'PORT_0002',
        'portfolio_name': port[0] if port else 'Accumulation Growth Portfolio',
        'benchmark':      port[4] if port else 'N/A',
        'inception_date': str(port[2]) if port else '2025-10-26',
        'report_date':    str(report_date),
        'base_currency':  'USD',

        # Snapshot
        'opening_value':  float(total_cost),
        'net_cash_flow':  float(cash[0] or 0),
        'ending_value':   float(total_aum),
        'cash_balance':   float(cash_bal),
        'total_deposits': float(cash[0] or 0),
        'dividends':      float(cash[2] or 0),
        'rewards':        float(cash[4] or 0),

        # Holdings
        'holdings':       holdings,
        'cash_weight':    cash_wt,

        # Transactions
        'transactions': [
            {
                'date':     str(t[0]),
                'side':     t[1],
                'security': t[2],
                'qty':      float(t[3] or 0),
                'price':    float(t[4] or 0),
                'gross':    float(t[5] or 0),
            }
            for t in trades
        ],

        # PM commentary (manual input for now)
        'market_commentary': (
            'Global markets delivered mixed performance in May 2026. '
            'US equity markets were supported by resilient earnings from '
            'technology and energy sectors. Bitcoin reached new highs '
            'above $100,000 during the month driven by institutional demand '
            'and ETF inflows. Silver gained on industrial demand and '
            'inflation hedging flows. GPUS (Hyperscale Data) saw elevated '
            'volatility as AI infrastructure spending remained in focus.'
        ),
        'portfolio_commentary': (
            'The portfolio held diversified positions across US equities (GPUS), '
            'precious metals (SLV), cryptocurrency exposure via IBIT and BTC, '
            'and broad market ETF (IVV). Cash balance of $427.91 provides '
            'flexibility for future deployment. No management fees charged '
            'this month for the pilot period.'
        ),
        'outlook': (
            'We remain positioned for continued AI infrastructure growth '
            'and digital asset adoption. Silver and crypto positions provide '
            'inflation and currency hedge. Next month we will deploy remaining '
            'cash into additional positions as opportunities arise.'
        ),

        # Fees
        'mgmt_fee':   0.00,
        'perf_fee':   0.00,
        'other_fees': 0.00,
    }


# ══════════════════════════════════════════════════════════
# STEP 2 — Generate PDF
# ══════════════════════════════════════════════════════════
PORTFOLIO_ID = 2
REPORT_DATE  = date(2026, 5, 31)

data = fetch_live_data(PORTFOLIO_ID, REPORT_DATE)

output_path = os.path.join(
    os.path.dirname(__file__),
    'test_output',
    f'Royeve_{data["portfolio_code"]}_May2026.pdf'
)

build_report(data, output_path)
print(f"\n✅ Report generated: {output_path}")
print(f"   Client:    {data['client_name']}")
print(f"   Portfolio: {data['portfolio_code']}")
print(f"   AUM:       ${data['ending_value']:,.2f}")
print(f"   Holdings:  {len(data['holdings'])} positions")
print(f"   Trades:    {len(data['transactions'])} this month")