from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce

from operations.ibor.models.lot import IborTaxLot
from operations.ibor.models.trade import IborTradeEvent


@dataclass(frozen=True)
class PositionSnapshot:
    portfolio_id: int
    instrument_id: int
    quantity: Decimal
    total_cost: Decimal
    avg_unit_cost: Decimal


class PositionEngine:
    @classmethod
    def rebuild_trade_position_context(cls, trade: IborTradeEvent) -> PositionSnapshot:
        return cls.build_position_snapshot(
            portfolio_id=trade.portfolio_id,
            instrument_id=trade.instrument_id,
        )

    @classmethod
    def build_position_snapshot(cls, portfolio_id: int, instrument_id: int) -> PositionSnapshot:
        total_cost_expr = ExpressionWrapper(
            F("remaining_qty") * F("unit_cost"),
            output_field=DecimalField(max_digits=28, decimal_places=10),
        )

        aggregates = (
            IborTaxLot.objects.filter(
                portfolio_id=portfolio_id,
                instrument_id=instrument_id,
                remaining_qty__gt=Decimal("0"),
            )
            .aggregate(
                quantity=Coalesce(
                    Sum("remaining_qty"),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=28, decimal_places=10),
                ),
                total_cost=Coalesce(
                    Sum(total_cost_expr),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=28, decimal_places=10),
                ),
            )
        )

        quantity = aggregates["quantity"] or Decimal("0")
        total_cost = aggregates["total_cost"] or Decimal("0")
        avg_unit_cost = Decimal("0") if quantity == Decimal("0") else total_cost / quantity

        return PositionSnapshot(
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            quantity=quantity,
            total_cost=total_cost,
            avg_unit_cost=avg_unit_cost,
        )