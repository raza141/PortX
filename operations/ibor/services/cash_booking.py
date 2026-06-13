from __future__ import annotations

from decimal import Decimal
from datetime import date
from django.db.models import Sum

from operations.ibor.models.cash_ledger import IborCashEvent
from operations.ibor.models.trade import IborSide
from operations.ibor.services.validators import TradeValidationResult
from refdata.masters.models.fx import FxRateDaily
from operations.portfolio.models.portfolio import Portfolio


class CashBookingService:
    TRADE_SETTLE = "TRADESETTLE"
    TRADE_FEE = "TRADEFEE"
    TAX = "TAX"

    @classmethod
    def get_cash_balance(cls, portfolio_id: int, effective_dt: date) -> Decimal:
        balance = IborCashEvent.objects.filter(
            portfolio_id=portfolio_id,
            effective_dt__lte=effective_dt
        ).aggregate(total=Sum('amount'))['total']
        return balance or Decimal("0")

    @classmethod
    def get_fx_rate(cls, portfolio_id: int, event_currency_id: int, effective_dt: date) -> tuple[Decimal | None, CurrencyPair | None]:
        portfolio = Portfolio.objects.get(pk=portfolio_id)
        base_ccy_id = portfolio.base_ccy_id
        
        from refdata.masters.models.currency import Currency
        from refdata.masters.models.currency_pair import CurrencyPair
        
        pair = CurrencyPair.objects.filter(base_currency_id=event_currency_id, quote_currency_id=base_ccy_id).first()

        if not base_ccy_id or base_ccy_id == event_currency_id:
            return Decimal("1.0"), pair

        rate = FxRateDaily.objects.filter(
            rate_date=effective_dt,
            base_currency_id=event_currency_id,
            quote_currency_id=base_ccy_id
        ).first()

        return (rate.mid if rate else None), pair

    @classmethod
    def book_trade_cash(cls, validation: TradeValidationResult) -> int:
        trade = validation.trade
        created_count = 0

        settlement_amount = cls._signed_settlement_amount(trade.side, trade.net_amount)

        IborCashEvent.objects.create(
            portfolio_id=trade.portfolio_id,
            currency_id=validation.settle_ccy_id,
            amount=settlement_amount,
            effective_dt=trade.settle_dt,
            cash_event_type=cls.TRADE_SETTLE,
            trade=trade,
            description=f"Trade settlement for trade {trade.id}",
            state_cd=trade.state_cd,
        )
        created_count += 1

        for charge in trade.charges.all():
            charge_ccy_id = charge.cost_ccy_id or validation.settle_ccy_id

            IborCashEvent.objects.create(
                portfolio_id=trade.portfolio_id,
                currency_id=charge_ccy_id,
                amount=cls._negative_amount(charge.amount),
                effective_dt=trade.settle_dt,
                cash_event_type=cls._map_charge_type(charge.charge_type_cd),
                trade=trade,
                description=charge.description or f"Trade charge for trade {trade.id}",
                state_cd=trade.state_cd,
            )
            created_count += 1

        return created_count

    @staticmethod
    def _signed_settlement_amount(side: str, net_amount: Decimal) -> Decimal:
        if side == IborSide.BUY:
            return -abs(net_amount)
        if side == IborSide.SELL:
            return abs(net_amount)
        raise ValueError(f"Unsupported trade side for cash booking: {side}")

    @staticmethod
    def _negative_amount(amount: Decimal) -> Decimal:
        return -abs(amount)

    @classmethod
    def _map_charge_type(cls, charge_type_cd: str) -> str:
        if charge_type_cd == "TAX":
            return cls.TAX
        return cls.TRADE_FEE