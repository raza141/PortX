"""
Main PDF report builder for Royeve Capital monthly reports.
Orchestrates all components to generate the final PDF.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak
)
from .data_models import PortfolioData
from .chart_generator import ChartGenerator
from .style_manager import StyleManager


class RoyeveReportGenerator:
    """
    Main orchestrator class that:
    1. Accepts PortfolioData input
    2. Uses ChartGenerator to create charts
    3. Uses StyleManager for formatting
    4. Builds the complete PDF report
    5. Exports to file
    """

    def __init__(self, data: PortfolioData):
        self.data = data
        self.style_mgr = StyleManager()
        self.chart_gen = ChartGenerator()
        self.story = []

    def generate_pdf(self, filename: str = 'Royeve_Monthly_Report.pdf') -> str:
        """Main function to build and export the PDF."""

        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

        # Prepare document
        doc = SimpleDocTemplate(
            filename, pagesize=A4,
            leftMargin=1.8 * cm, rightMargin=1.8 * cm,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm
        )

        # Build all sections
        self._build_cover()
        self.story.append(PageBreak())
        self._build_portfolio_snapshot()
        self._build_performance_section()
        self._build_commentary()
        self._build_holdings()
        self._build_transactions()
        self.story.append(PageBreak())
        self._build_risk_section()
        self._build_fees()
        self._build_outlook()
        self._build_disclosures()
        self._build_footer()

        # Generate PDF
        doc.build(self.story)
        print(f"✅ PDF successfully generated: {filename}")
        return filename

    def _build_cover(self):
        """
        Build professional cover page with Royeve Capital logo.
        """
        import os
        from reportlab.lib.utils import ImageReader

        st = self.style_mgr.get_style

        # LOGO - Multiple path attempts to find the logo
        logo_paths = [
            # Relative to services directory
            os.path.join(os.path.dirname(__file__), '..', 'static', 'reporting', 'images', 'royeve_logo.png'),
            # Absolute from project root
            '/Volumes/PSXDatabase/PortX/rep/monthly_reports/static/rep/images/royeve_logo.png',
            # Fallback
            'rep/monthly_reports/static/rep/images/royeve_logo.png',
        ]

        logo_found = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    # Your logo is wider, so use 8cm width, auto-height to preserve ratio
                    logo_img = Image(logo_path, width=8 * cm, height=4 * cm)
                    logo_tbl = Table([[logo_img]], colWidths=[8 * cm])
                    logo_tbl.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    self.story.append(Spacer(1, 1 * cm))
                    self.story.append(logo_tbl)
                    self.story.append(Spacer(1, 1.2 * cm))
                    logo_found = True
                    print(f"✓ Logo loaded from: {logo_path}")
                    break
                except Exception as e:
                    print(f"✗ Failed to load logo from {logo_path}: {e}")
                    continue

        if not logo_found:
            # Fallback: Text-based branding
            print("⚠ Logo not found, using text fallback")
            self.story.append(Spacer(1, 1.5 * cm))
            self.story.append(Paragraph(
                '<font size=22 color="#0D1B2A"><b>ROYEVE CAPITAL</b></font>',
                st('cover_sub')
            ))
            self.story.append(Paragraph(
                '<font size=10 color="#C9A84C"><i>Advice | Educate | Deliver</i></font>',
                st('cover_sub')
            ))
            self.story.append(Spacer(1, 0.8 * cm))

        # Main title section (cleaner, left-aligned like your reference)
        self.story.append(Paragraph(
            '<font size=24 color="#0D1B2A"><b>Monthly Portfolio Report</b></font>',
            st('cover_sub')
        ))
        self.story.append(Spacer(1, 0.3 * cm))
        self.story.append(Paragraph(
            f'<font size=14 color="#C9A84C"><b>{self.data.reporting_month}</b></font>',
            st('cover_sub')
        ))

        # Gold separator line
        self.story.append(Spacer(1, 0.4 * cm))
        self.story.append(HRFlowable(
            width='100%',
            thickness=3,
            color=self.style_mgr.GOLD,
            spaceBefore=0,
            spaceAfter=15
        ))

        self.story.append(Spacer(1, 0.8 * cm))

        # Client information box (light grey box like your reference)
        client_box_data = [
            [Paragraph('<font size=10><b>Prepared for:</b></font>', st('small')),
             Paragraph(f'<font size=10>{self.data.client_name}</font>', st('small'))],
            [Paragraph('<font size=9 color="#5A6B7B">Account Number:</font>', st('small')),
             Paragraph(f'<font size=9>{self.data.account_number}</font>', st('small'))],
        ]
        client_box = Table(client_box_data, colWidths=[4.5 * cm, 10.5 * cm])
        client_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.style_mgr.LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, self.style_mgr.MID),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        self.story.append(client_box)

        self.story.append(Spacer(1, 1.5 * cm))

        # Report details (2x2 grid like your reference)
        details_data = [
            [Paragraph('<b>Report Date</b>', st('small')),
             Paragraph(self.data.report_date, st('small')),
             Paragraph('<b>Benchmark</b>', st('small')),
             Paragraph(self.data.benchmark, st('small'))],
            [Paragraph('<b>Base Currency</b>', st('small')),
             Paragraph(self.data.base_currency, st('small')),
             Paragraph('<b>Inception Date</b>', st('small')),
             Paragraph(self.data.inception_date, st('small'))],
        ]
        details_tbl = Table(details_data, colWidths=[3.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
        details_tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.75, self.style_mgr.MID),
            ('BACKGROUND', (0, 0), (0, -1), self.style_mgr.LIGHT),
            ('BACKGROUND', (2, 0), (2, -1), self.style_mgr.LIGHT),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        self.story.append(details_tbl)

        # Footer disclaimer on cover
        self.story.append(Spacer(1, 3.5 * cm))
        self.story.append(Paragraph(
            '<font size=7 color="#5A6B7B"><i>This report contains confidential information intended solely for the named recipient. '
            'Past performance is not indicative of future results.</i></font>',
            st('small')
        ))

    def _build_portfolio_snapshot(self):
        """Build portfolio snapshot section"""
        st = self.style_mgr.get_style
        fmt_curr = self.style_mgr.fmt_currency

        # Section header with gold underline
        self.story.append(Paragraph('1. PORTFOLIO SNAPSHOT', st('section_header')))
        self.story.append(Spacer(1, 0.4 * cm))

        snap = [
            [Paragraph('<b>Opening Value</b>', st('label')),
             Paragraph(fmt_curr(self.data.opening_value, self.data.base_currency), st('body'))],
            [Paragraph('<b>Net Cash Flow</b>', st('label')),
             Paragraph(fmt_curr(self.data.get_net_cash_flow(), self.data.base_currency), st('body'))],
            [Paragraph('<b>Ending Value</b>', st('label')),
             Paragraph(f"<b>{fmt_curr(self.data.ending_value, self.data.base_currency)}</b>", st('body'))],
        ]
        snap_tbl = Table(snap, colWidths=[5 * cm, 9 * cm])
        snap_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.style_mgr.LIGHT),
            ('GRID', (0, 0), (-1, -1), 0.5, self.style_mgr.MID),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))

        alloc_chart = self.chart_gen.create_allocation_chart(self.data.cash_pct, self.data.invested_pct)
        alloc_img = Image(alloc_chart, width=4 * cm, height=4 * cm)
        layout = Table([[snap_tbl, alloc_img]], colWidths=[10 * cm, 4 * cm])
        layout.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        self.story.append(layout)

    def _build_performance_section(self):
        """Build performance summary section"""
        st = self.style_mgr.get_style
        fmt_pct = self.style_mgr.fmt_pct

        self.story.append(Spacer(1, 0.5 * cm))
        self.story.append(Paragraph('2. PERFORMANCE SUMMARY', st('section_header')))
        self.story.append(Spacer(1, 0.3 * cm))

        perf_chart = self.chart_gen.create_performance_chart(self.data)
        perf_img = Image(perf_chart, width=13 * cm, height=5.2 * cm)
        self.story.append(perf_img)
        self.story.append(Spacer(1, 0.3 * cm))

        ex_m = self.data.get_excess_return_month()
        ex_ytd = self.data.get_excess_return_ytd()
        ex_inc = self.data.get_excess_return_inception()

        perf_data = [
            [
                Paragraph('<b>Period</b>', st('table_header')),  # ← was st('label')
                Paragraph('<b>Portfolio (Net)</b>', st('table_header')),  # ← was st('label')
                Paragraph('<b>Benchmark</b>', st('table_header')),  # ← was st('label')
                Paragraph('<b>Excess</b>', st('table_header'))  # ← was st('label')
            ],
            ['This Month', fmt_pct(self.data.net_month), fmt_pct(self.data.benchmark_month),
             Paragraph(fmt_pct(ex_m), st('pos_ret') if ex_m >= 0 else st('neg_ret'))],
            ['Year-to-Date', fmt_pct(self.data.net_ytd), fmt_pct(self.data.benchmark_ytd),
             Paragraph(fmt_pct(ex_ytd), st('pos_ret') if ex_ytd >= 0 else st('neg_ret'))],
            ['Since Inception', fmt_pct(self.data.net_inception), fmt_pct(self.data.benchmark_inception),
             Paragraph(fmt_pct(ex_inc), st('pos_ret') if ex_inc >= 0 else st('neg_ret'))],
        ]
        perf_tbl = Table(perf_data, colWidths=[3.5 * cm] * 4)
        perf_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.style_mgr.NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.style_mgr.WHITE),
            ('BACKGROUND', (0, 1), (-1, -1), self.style_mgr.LIGHT),
            # Alternating rows
            ('BACKGROUND', (0, 2), (-1, 2), self.style_mgr.WHITE),
            ('BACKGROUND', (0, 3), (-1, 3), self.style_mgr.LIGHT),
            ('GRID', (0, 0), (-1, -1), 0.5, self.style_mgr.MID),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Slightly larger
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        self.story.append(perf_tbl)

    def _build_commentary(self):
        """Build market and portfolio commentary"""
        st = self.style_mgr.get_style
        self.story.append(Spacer(1, 0.5 * cm))
        self.story.append(Paragraph('3. MARKET COMMENTARY', st('section_header')))
        self.story.append(Paragraph(self.data.market_commentary, st('body')))
        self.story.append(Paragraph('4. PORTFOLIO COMMENTARY', st('section_header')))
        self.story.append(Paragraph(self.data.portfolio_commentary, st('body')))

    def _build_holdings(self):
        """Build top holdings table"""
        st = self.style_mgr.get_style
        self.story.append(Paragraph('5. TOP HOLDINGS', st('section_header')))
        self.story.append(Spacer(1, 0.3 * cm))

        hld_data = [
            [
                Paragraph('<b>Security</b>', st('table_header')),  # ← was st('label')
                Paragraph('<b>Weight</b>', st('table_header')),  # ← was st('label')
                Paragraph('<b>MTD Contrib.</b>', st('table_header')),  # ← was st('label')
                Paragraph('<b>Thesis</b>', st('table_header'))  # ← was st('label')
            ]
        ]
        for sec, wt, contrib, thesis in self.data.holdings:
            hld_data.append([
                Paragraph(sec, st('small')),
                Paragraph(wt, st('small')),
                Paragraph(contrib, st('small')),
                Paragraph(thesis, st('small'))
            ])

        hld_tbl = Table(hld_data, colWidths=[3.6 * cm, 1.8 * cm, 2.2 * cm, 6.4 * cm])
        hld_tbl.setStyle(TableStyle([
            # HEADER ROW - Navy background with WHITE TEXT
            ('BACKGROUND', (0, 0), (-1, 0), self.style_mgr.NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.style_mgr.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # ← CHANGED FROM 7 TO 9

            # DATA ROWS - Alternating light grey and white
            ('BACKGROUND', (0, 1), (-1, -1), self.style_mgr.LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.style_mgr.LIGHT, self.style_mgr.WHITE]),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),  # ← CHANGED FROM 7 TO 7.5

            # GRID AND ALIGNMENT
            ('GRID', (0, 0), (-1, -1), 0.75, self.style_mgr.MID),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # ← CHANGED FROM TOP TO MIDDLE

            # PADDING
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),  # ← CHANGED FROM 5 TO 6
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # ← CHANGED FROM 5 TO 6
        ]))
        self.story.append(hld_tbl)

    def _build_transactions(self):
        """Build transactions table"""
        st = self.style_mgr.get_style
        self.story.append(Spacer(1, 0.5 * cm))
        self.story.append(Paragraph('6. TRANSACTIONS DURING THE MONTH', st('section_header')))
        self.story.append(Spacer(1, 0.3 * cm))

        txn_data = [[
            Paragraph('<b>Date</b>', st('table_header')),
            Paragraph('<b>Action</b>', st('table_header')),
            Paragraph('<b>Security</b>', st('table_header')),
            Paragraph('<b>Qty</b>', st('table_header')),  # Shortened label
            Paragraph('<b>Avg Price</b>', st('table_header')),
            Paragraph('<b>Rationale</b>', st('table_header')),
        ]]
        for date, action, sec, qty, price, rat in self.data.transactions:
            txn_data.append([
                Paragraph(date, st('small')),
                Paragraph(f"<b>{action}</b>", st('small')),
                Paragraph(sec, st('small')),
                Paragraph(qty, st('small')),
                Paragraph(price, st('small')),
                Paragraph(rat, st('small')),
            ])

        # Column widths adjusted: Action gets more space (1.8cm instead of 1.3cm)
        txn_tbl = Table(
            txn_data,
            colWidths=[1.8 * cm, 1.8 * cm, 3.0 * cm, 1.6 * cm, 2.0 * cm, 4.0 * cm]
        )
        txn_tbl.setStyle(TableStyle([
            # HEADER - navy background, white text, centered
            ('BACKGROUND', (0, 0), (-1, 0), self.style_mgr.NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.style_mgr.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # ← Header: ALL CENTER
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

            # DATA ROWS - alternating colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.style_mgr.LIGHT, self.style_mgr.WHITE]),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # ← Action column: CENTER
            ('ALIGN', (3, 1), (4, -1), 'CENTER'),  # ← Qty + Price: CENTER
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # ← Date: LEFT
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),  # ← Security: LEFT
            ('ALIGN', (5, 1), (5, -1), 'LEFT'),  # ← Rationale: LEFT
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # GRID
            ('GRID', (0, 0), (-1, -1), 0.75, self.style_mgr.MID),

            # PADDING
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        self.story.append(txn_tbl)

    def _build_risk_section(self):
        """Build risk metrics section"""
        st = self.style_mgr.get_style
        self.story.append(Paragraph('7. RISK SNAPSHOT', st('section_header')))
        self.story.append(Spacer(1, 0.2 * cm))

        risk = [
            [Paragraph('<b>Largest Position</b>', st('label')),
             Paragraph(f"{self.data.largest_position:.1f}%", st('body'))],
            [Paragraph('<b>Top 5 Concentration</b>', st('label')),
             Paragraph(f"{self.data.top5_concentration:.1f}%", st('body'))],
            [Paragraph('<b>Cash Buffer</b>', st('label')),
             Paragraph(f"{self.data.cash_buffer:.1f}%", st('body'))],
            [Paragraph('<b>Max Drawdown</b>', st('label')),
             Paragraph(f"{self.data.max_drawdown:.1f}%", st('body'))],
            [Paragraph('<b>Beta</b>', st('label')),
             Paragraph(f"{self.data.beta:.2f}", st('body'))],
        ]
        risk_tbl = Table(risk, colWidths=[6 * cm, 6 * cm])
        risk_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.style_mgr.LIGHT),
            ('GRID', (0, 0), (-1, -1), 0.5, self.style_mgr.MID),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        self.story.append(risk_tbl)

    def _build_fees(self):
        """Build fees section"""
        st = self.style_mgr.get_style
        fmt_curr = self.style_mgr.fmt_currency
        self.story.append(Spacer(1, 0.5 * cm))
        self.story.append(Paragraph('8. FEES & CHARGES', st('section_header')))
        self.story.append(Spacer(1, 0.2 * cm))

        fees = [
            [Paragraph('<b>Management Fee</b>', st('label')),
             Paragraph(fmt_curr(self.data.mgmt_fee, self.data.base_currency), st('body'))],
            [Paragraph('<b>Performance Fee</b>', st('label')),
             Paragraph(fmt_curr(self.data.perf_fee, self.data.base_currency), st('body'))],
            [Paragraph('<b>Other Charges</b>', st('label')),
             Paragraph(fmt_curr(self.data.other_charges, self.data.base_currency), st('body'))],
        ]
        fee_tbl = Table(fees, colWidths=[4 * cm, 8 * cm])
        fee_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.style_mgr.LIGHT),
            ('GRID', (0, 0), (-1, -1), 0.5, self.style_mgr.MID),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        self.story.append(fee_tbl)

    def _build_outlook(self):
        """Build outlook section"""
        st = self.style_mgr.get_style
        self.story.append(Spacer(1, 0.5 * cm))
        self.story.append(Paragraph('9. OUTLOOK & ACTION PLAN', st('section_header')))
        self.story.append(Paragraph(self.data.outlook, st('body')))

    def _build_disclosures(self):
        """Build disclosures section"""
        st = self.style_mgr.get_style
        self.story.append(Spacer(1, 0.6 * cm))
        self.story.append(Paragraph('10. DISCLOSURES', st('section_header')))
        self.story.append(Paragraph(
            'This report is prepared by Royeve Capital. Returns are calculated on a time-weighted basis '
            'consistent with GIPS principles. Past performance is not indicative of future results. '
            'The benchmark is provided for comparison purposes only.',
            st('small')))

    def _build_footer(self):
        """Build footer with page numbers"""
        st = self.style_mgr.get_style
        self.story.append(Spacer(1, 0.8 * cm))
        self.story.append(HRFlowable(
            width='100%',
            thickness=1,
            color=self.style_mgr.GOLD,  # Gold line
            spaceBefore=6,
            spaceAfter=6
        ))
        self.story.append(Paragraph(
            f'Royeve Capital | Confidential — Prepared for: {self.data.client_name} | {self.data.report_date}',
            st('footer')
        ))