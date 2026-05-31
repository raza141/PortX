"""
PDF style management for Royeve Capital monthly reports.
"""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


class StyleManager:
    """Manages all PDF paragraph styles and brand colors."""

    # Brand Colors (class variables - defined before __init__)
    NAVY = colors.HexColor('#0D1B2A')
    GOLD = colors.HexColor('#C9A84C')
    LIGHT = colors.HexColor('#F4F6F9')
    WHITE = colors.white
    GREEN = colors.HexColor('#1A7A4A')
    RED = colors.HexColor('#C0392B')
    MID = colors.HexColor('#5A6B7B')

    def __init__(self):
        """Initialize style manager with optional custom fonts"""
        self._register_fonts()
        self.styles = self._create_styles()

    def _register_fonts(self):
        """Register custom fonts (optional)"""
        try:
            font_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'reporting', 'fonts')
            pdfmetrics.registerFont(TTFont('Montserrat-Bold', os.path.join(font_dir, 'Montserrat-Bold.ttf')))
            pdfmetrics.registerFont(TTFont('Montserrat-Regular', os.path.join(font_dir, 'Montserrat-Regular.ttf')))
        except:
            pass  # Fallback to Helvetica if custom fonts not available

    def _create_styles(self) -> dict:
        """Build custom paragraph styles for the report."""
        s = {}

        # Cover page styles
        s['cover_firm'] = ParagraphStyle('cover_firm',
            fontSize=24,
            fontName='Helvetica-Bold',
            textColor=self.NAVY,
            alignment=TA_LEFT,
            spaceAfter=4)

        s['cover_title'] = ParagraphStyle('cover_title',
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=self.NAVY,
            alignment=TA_LEFT,
            spaceAfter=2)

        s['cover_sub'] = ParagraphStyle('cover_sub',
            fontSize=10,
            fontName='Helvetica',
            textColor=self.MID,
            alignment=TA_LEFT,
            spaceAfter=2)

        # SECTION HEADER - WHITE TEXT ON NAVY BACKGROUND (THE FIX!)
        s['section_header'] = ParagraphStyle('section_header',
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=self.WHITE,      # ← WHITE TEXT
            backColor=self.NAVY,        # ← NAVY BACKGROUND
            spaceBefore=16,
            spaceAfter=10,
            leftIndent=10,
            rightIndent=10,
            borderPadding=8,
            leading=16,
        )

        # Gold underline divider
        s['section_divider'] = ParagraphStyle('section_divider',
            fontSize=1,
            backColor=self.GOLD,
            spaceBefore=0,
            spaceAfter=6,
        )

        # Body text styles
        s['label'] = ParagraphStyle('label',
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=self.NAVY,
            spaceAfter=1)

        s['body'] = ParagraphStyle('body',
            fontSize=9,
            fontName='Helvetica',
            textColor=colors.HexColor('#2C2C2C'),
            spaceAfter=6,
            leading=13,
            alignment=TA_LEFT
        )

        s['small'] = ParagraphStyle('small',
            fontSize=7.5,
            fontName='Helvetica',
            textColor=self.MID,
            spaceAfter=3,
            leading=11
        )

        # Footer
        s['footer'] = ParagraphStyle('footer',
            fontSize=6.5,
            fontName='Helvetica',
            textColor=self.MID,
            alignment=TA_CENTER)

        # Performance numbers (colored)
        s['pos_ret'] = ParagraphStyle('pos_ret',
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=self.GREEN,
            alignment=TA_CENTER)

        s['neg_ret'] = ParagraphStyle('neg_ret',
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=self.RED,
            alignment=TA_CENTER)

        # WHITE label for use inside navy table headers
        s['table_header'] = ParagraphStyle('table_header',
                                           fontSize=8,
                                           fontName='Helvetica-Bold',
                                           textColor=self.WHITE,  # ← WHITE so it shows on navy background
                                           spaceAfter=0,
                                           leading=11,
                                           )

        return s

    def get_style(self, name: str) -> ParagraphStyle:
        """Get a style by name"""
        return self.styles[name]

    @staticmethod
    def fmt_currency(val: float, currency: str = 'AED') -> str:
        """Format currency value"""
        return f"{currency} {val:,.0f}"

    @staticmethod
    def fmt_pct(val: float) -> str:
        """Format percentage value"""
        sign = '+' if val >= 0 else ''
        return f"{sign}{val:.2f}%"