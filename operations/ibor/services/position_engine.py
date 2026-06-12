from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db.models import F, Sum, DecimalField, ExpressionWrapper
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
    """
    V1 position engine.

    Source of truth:
    - open lots in IborTaxLot
    - remainingqty is the live position quantity
    - total cost = sum(remainingqty * unitcost)

    This is intentionally a read-model engine for now.
    """

    @classmethod
    def rebuild_trade_position_context(cls, trade: IborTradeEvent) -> PositionSnapshot:
        return cls.build_position_snapshot(
            portfolio_id=trade.portfolio_id,
            instrument_id=trade.instrument_id,
        )

    @classmethod
    def build_position_snapshot(cls, portfolio_id: int, instrument_id: int) -> PositionSnapshot:
        total_cost_expr = ExpressionWrapper(
            F("remainingqty") * F("unitcost"),
            output_field=DecimalField(max_digits=28, decimal_places=10),
        )

        aggregates = IborTaxLot.objects.filter(
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            remainingqty__gt=Decimal("0"),
        ).aggregate(
            quantity=Coalesce(
                Sum("remainingqty"),
                Decimal("0"),
                output_field=DecimalField(max_digits=28, decimal_places=10),
            ),
            total_cost=Coalesce(
                Sum(total_cost_expr),
                Decimal("0"),
                output_field=DecimalField(max_digits=28, decimal_places=10),
            ),
        )

        quantity = aggregates["quantity"] or Decimal("0")
        total_cost = aggregates["total_cost"] or Decimal("0")

        if quantity == Decimal("0"):
            avg_unit_cost = Decimal("0")
        else:
            avg_unit_cost = total_cost / quantity

        return PositionSnapshot(
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            quantity=quantity,
            total_cost=total_cost,
            avg_unit_cost=avg_unit_cost,
        )