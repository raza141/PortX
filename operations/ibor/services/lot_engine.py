from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from operations.ibor.models.lot import IborLotConsumption, IborTaxLot
from operations.ibor.models.trade import IborSide
from operations.ibor.services.validators import TradeValidationResult


@dataclass(frozen=True)
class LotBookingResult:
    lot_count: int = 0
    lot_consumption_count: int = 0


class LotEngine:
    @classmethod
    def book_trade_lots(cls, validation: TradeValidationResult) -> LotBookingResult:
        trade = validation.trade

        if trade.side == IborSide.BUY:
            cls._create_buy_lot(validation)
            return LotBookingResult(lot_count=1, lot_consumption_count=0)

        if trade.side == IborSide.SELL:
            consumption_count = cls._consume_sell_fifo(validation)
            return LotBookingResult(lot_count=0, lot_consumption_count=consumption_count)

        raise ValidationError({"side": [f"Unsupported trade side: {trade.side}"]})

    @classmethod
    def _create_buy_lot(cls, validation: TradeValidationResult) -> IborTaxLot:
        trade = validation.trade

        total_cost = abs(trade.net_amount)
        unit_cost = total_cost / trade.quantity

        return IborTaxLot.objects.create(
            portfolio_id=trade.portfolio_id,
            instrument_id=trade.instrument_id,
            acquired_dt=trade.trade_dt,
            trade=trade,
            open_qty=trade.quantity,
            remaining_qty=trade.quantity,
            unit_cost=unit_cost,
            cost_ccy_id=validation.settle_ccy_id,
        )

    @classmethod
    def _consume_sell_fifo(cls, validation: TradeValidationResult) -> int:
        trade = validation.trade
        remaining_to_sell = trade.quantity
        created_count = 0

        open_lots = (
            IborTaxLot.objects
            .select_for_update()
            .filter(
                portfolio_id=trade.portfolio_id,
                instrument_id=trade.instrument_id,
                remaining_qty__gt=Decimal("0"),
                is_active=True,
            )
            .order_by("acquired_dt", "id")
        )

        if not open_lots.exists():
            raise ValidationError({"quantity": ["No open lots available for this sell trade."]})

        net_proceeds_total = abs(trade.net_amount)
        sell_unit_proceeds = net_proceeds_total / trade.quantity

        with transaction.atomic():
            for lot in open_lots:
                if remaining_to_sell <= Decimal("0"):
                    break

                consumed_qty = min(remaining_to_sell, lot.remaining_qty)
                cost_basis = consumed_qty * lot.unit_cost
                proceeds_amt = consumed_qty * sell_unit_proceeds
                realized_pnl = proceeds_amt - cost_basis

                IborLotConsumption.objects.create(
                    sell_trade=trade,
                    lot=lot,
                    consumed_qty=consumed_qty,
                    unit_cost=lot.unit_cost,
                    cost_ccy_id=lot.cost_ccy_id,
                    cost_basis=cost_basis,
                    proceeds_amt=proceeds_amt,
                    rlzd_pnl_amt=realized_pnl,
                )

                lot.remaining_qty = lot.remaining_qty - consumed_qty
                lot.save(update_fields=["remaining_qty", "updated_at"])

                remaining_to_sell -= consumed_qty
                created_count += 1

        if remaining_to_sell > Decimal("0"):
            raise ValidationError(
                {"quantity": [f"Insufficient open lot quantity. Unallocated sell quantity: {remaining_to_sell}"]}
            )

        return created_count