from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError

from operations.ibor.models.trade import IborSide, IborTradeEvent, IborBookStatus


@dataclass(frozen=True)
class TradeValidationResult:
    trade: IborTradeEvent
    settle_ccy_id: int
    total_charges: Decimal


def validate_trade_for_booking(trade: IborTradeEvent) -> TradeValidationResult:
    errors: dict[str, list[str]] = {}

    if trade is None:
        raise ValidationError("Trade is required for booking.")

    if trade.book_sts_cd == IborBookStatus.REVERSED:
        errors.setdefault("book_sts_cd", []).append("Reversed trade cannot be booked again.")

    if trade.side not in {IborSide.BUY, IborSide.SELL}:
        errors.setdefault("side", []).append("Trade side must be BUY or SELL.")

    if trade.quantity is None or trade.quantity <= Decimal("0"):
        errors.setdefault("quantity", []).append("Quantity must be greater than 0.")

    if trade.price is None or trade.price <= Decimal("0"):
        errors.setdefault("price", []).append("Price must be greater than 0.")

    if trade.gross_amount is None or trade.gross_amount <= Decimal("0"):
        errors.setdefault("gross_amount", []).append("Gross amount must be greater than 0.")

    if trade.trade_dt is None:
        errors.setdefault("trade_dt", []).append("Trade date is required.")

    if trade.settle_dt is None:
        errors.setdefault("settle_dt", []).append("Settlement date is required.")

    if trade.trade_dt and trade.settle_dt and trade.settle_dt < trade.trade_dt:
        errors.setdefault("settle_dt", []).append("Settlement date cannot be earlier than trade date.")

    if trade.portfolio_id is None:
        errors.setdefault("portfolio", []).append("Portfolio is required.")

    if trade.account_id is None:
        errors.setdefault("account", []).append("Account is required.")

    if trade.instrument_id is None:
        errors.setdefault("instrument", []).append("Instrument is required.")

    if trade.trade_ccy_id is None:
        errors.setdefault("trade_ccy", []).append("Trade currency is required.")

    settle_ccy_id = trade.settle_ccy_id or trade.trade_ccy_id
    if settle_ccy_id is None:
        errors.setdefault("settle_ccy", []).append("Settlement currency could not be resolved.")

    charges = list(trade.charges.all())
    total_charges = Decimal("0")

    for charge in charges:
        if charge.amount is None or charge.amount < Decimal("0"):
            errors.setdefault("charges", []).append(
                f"Charge {charge.pk or ''} amount must be zero or positive."
            )
        else:
            total_charges += charge.amount

    if errors:
        raise ValidationError(errors)

    return TradeValidationResult(
        trade=trade,
        settle_ccy_id=settle_ccy_id,
        total_charges=total_charges,
    )