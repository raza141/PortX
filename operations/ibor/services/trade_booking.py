# core/operations/ibor/services/trade_booking.py
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from operations.ibor.models.trade import (
    IborChargeComponent,
    IborSide,
    IborTradeEvent,
)


AMT_DP = Decimal("0.0000000001")


def q(value: Decimal) -> Decimal:
    """
    Standard 10‑dp quantizer for amounts.
    """
    return Decimal(value).quantize(AMT_DP, rounding=ROUND_HALF_UP)


class TradeChargeCalculator:
    """
    Pure calculator for trade charges.
    """

    @staticmethod
    def total_for_trade(trade: IborTradeEvent) -> Decimal:
        total = Decimal("0")
        # Sum all linked charges in their recorded currency (policy: assume same as settle_ccy V1)
        for charge in trade.charges.all():
            total += Decimal(charge.amount)
        return q(total)


class TradeBookingService:
    """
    Booking orchestration for IBOR trades.

    Responsibilities:
    - validate forms (already done in forms layer)
    - create/update IborTradeEvent and IborChargeComponent rows
    - derive gross/total_charges/net/settlement_cash_amount
    - default settle_ccy when missing
    - leave cash/lot posting to other services
    """

    @staticmethod
    @transaction.atomic
    def derive_amounts(trade: IborTradeEvent) -> IborTradeEvent:
        """
        Derive gross, total_charges, net, settlement_cash_amount and settle_ccy.
        """
        # Gross
        trade.gross_amount = q(Decimal(trade.quantity) * Decimal(trade.price))

        # Total charges
        trade.total_charges = TradeChargeCalculator.total_for_trade(trade)

        # Net & settlement cash
        if trade.side == IborSide.BUY:
            trade.net_amount = q(trade.gross_amount + trade.total_charges)
        else:  # SELL
            trade.net_amount = q(trade.gross_amount - trade.total_charges)

        trade.settlement_cash_amount = trade.net_amount

        # Default settlement currency to trade currency if empty
        if trade.settle_ccy_id is None:
            trade.settle_ccy = trade.trade_ccy

        trade.save(
            update_fields=[
                "gross_amount",
                "total_charges",
                "net_amount",
                "settlement_cash_amount",
                "settle_ccy",
                "updated_at",
            ]
        )
        return trade

    @staticmethod
    @transaction.atomic
    def create_from_forms(trade_form, charge_formset, *, created_by=None) -> IborTradeEvent:
        """
        Create a new trade + charges from validated forms and derive amounts.

        Usage:
            trade = TradeBookingService.create_from_forms(form, formset, created_by=request.user)
        """
        if not trade_form.is_valid() or not charge_formset.is_valid():
            # Defensive — your view should normally check is_valid first.
            raise ValueError("Trade form or charge formset is invalid.")

        # Parent trade
        trade: IborTradeEvent = trade_form.save(commit=False)
        if created_by is not None:
            trade.created_by = created_by
        trade.save()

        # Attach and save child charges
        charge_formset.instance = trade
        charge_formset.save()

        # Derive economics
        return TradeBookingService.derive_amounts(trade)

    @staticmethod
    @transaction.atomic
    def update_from_forms(trade: IborTradeEvent, trade_form, charge_formset) -> IborTradeEvent:
        """
        Update existing trade + charges (e.g. CONF correction) and re‑derive amounts.
        """
        if not trade_form.is_valid() or not charge_formset.is_valid():
            raise ValueError("Trade form or charge formset is invalid.")

        # Update parent
        trade = trade_form.save(commit=False)
        trade.id = trade_form.instance.id  # ensure we don't create a new row
        trade.save()

        # Update charges
        charge_formset.instance = trade
        charge_formset.save()

        return TradeBookingService.derive_amounts(trade)