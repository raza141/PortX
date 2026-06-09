from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from operations.ibor.models.ingest import IborStagedTrade
from operations.ibor.models.trade import IborTradeEvent


@dataclass(frozen=True)
class IngestPostingResult:
    staged_trade_id: int
    trade_id: int
    staged_status: str


class IngestPostingService:
    """
    Posts one approved staged trade into canonical IborTradeEvent.

    MVP assumptions:
    - portfolio/account/instrument resolution is handled before approval
    - raw staged fields are already normalized enough for posting
    - booking of cash/lots happens later through TradeBookingService
    """

    @classmethod
    def post_staged_trade(
        cls,
        staged_trade_id: int,
        *,
        portfolio_id: int,
        account_id: int,
        instrument_id: int,
        trade_ccy_id: int,
        settle_ccy_id: int | None = None,
    ) -> IngestPostingResult:
        with transaction.atomic():
            staged = (
                IborStagedTrade.objects
                .select_for_update()
                .get(pk=staged_trade_id)
            )

            if staged.status != IborStagedTrade.Status.APPROVED:
                raise ValidationError(
                    {"status": [f"Only approved staged trades can be posted. Current status: {staged.status}"]}
                )

            if not staged.side:
                raise ValidationError({"side": ["Staged trade side is required."]})

            if staged.quantity is None or staged.quantity <= Decimal("0"):
                raise ValidationError({"quantity": ["Staged trade quantity must be greater than 0."]})

            if staged.price is None or staged.price <= Decimal("0"):
                raise ValidationError({"price": ["Staged trade price must be greater than 0."]})

            if staged.tradedt is None:
                raise ValidationError({"tradedt": ["Staged trade date is required."]})

            if staged.settledt is None:
                raise ValidationError({"settledt": ["Staged settlement date is required."]})

            gross_amount = staged.quantity * staged.price

            trade = IborTradeEvent.objects.create(
                sourcesystem=staged.sourcesystem,
                externalref=staged.externalref,
                versionno=1,
                portfolio_id=portfolio_id,
                account_id=account_id,
                instrument_id=instrument_id,
                side=staged.side,
                quantity=staged.quantity,
                price=staged.price,
                tradeccy_id=trade_ccy_id,
                settleccy_id=settle_ccy_id or trade_ccy_id,
                tradedt=staged.tradedt,
                settledt=staged.settledt,
                grossamount=gross_amount,
                netamount=gross_amount,
                memo=f"Posted from staged trade {staged.id}",
            )

            staged.status = IborStagedTrade.Status.POSTED
            staged.save(update_fields=["status", "updatedat"])

            return IngestPostingResult(
                staged_trade_id=staged.id,
                trade_id=trade.id,
                staged_status=staged.status,
            )