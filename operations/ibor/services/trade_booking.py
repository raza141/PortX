from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from operations.ibor.models.trade import IborTradeEvent
from operations.ibor.services.cash_booking import CashBookingService
from operations.ibor.services.lot_engine import LotEngine
from operations.ibor.services.position_engine import PositionEngine
from operations.ibor.services.validators import validate_trade_for_booking


@dataclass(frozen=True)
class TradeBookingResult:
    trade_id: int
    booking_status: str
    cash_event_count: int = 0
    lot_count: int = 0
    lot_consumption_count: int = 0


class TradeBookingService:
    @classmethod
    def book_trade(cls, trade_id: int) -> TradeBookingResult:
        try:
            with transaction.atomic():
                trade = (
                    IborTradeEvent.objects
                    .select_for_update()
                    .prefetch_related("charges")
                    .get(pk=trade_id)
                )

                if trade.book_sts_cd == IborTradeEvent.IborBookStatus.BOOKED:
                    return TradeBookingResult(
                        trade_id=trade.id,
                        booking_status=trade.book_sts_cd,
                    )

                validation = validate_trade_for_booking(trade)

                trade.book_err_txt = ""
                trade.book_sts_cd = IborTradeEvent.IborBookStatus.NEW
                trade.save(update_fields=["book_err_txt", "book_sts_cd", "updated_at"])

                cash_event_count = CashBookingService.book_trade_cash(validation)

                lot_result = LotEngine.book_trade_lots(validation)
                lot_count = lot_result.lot_count
                lot_consumption_count = lot_result.lot_consumption_count

                PositionEngine.rebuild_trade_position_context(trade)

                trade.book_sts_cd = IborTradeEvent.IborBookStatus.BOOKED
                trade.book_ts = timezone.now()
                trade.book_err_txt = ""
                trade.save(update_fields=["book_sts_cd", "book_ts", "book_err_txt", "updated_at"])

                return TradeBookingResult(
                    trade_id=trade.id,
                    booking_status=trade.book_sts_cd,
                    cash_event_count=cash_event_count,
                    lot_count=lot_count,
                    lot_consumption_count=lot_consumption_count,
                )

        except IborTradeEvent.DoesNotExist as exc:
            raise ValidationError({"trade": [f"Trade {trade_id} does not exist."]}) from exc

        except Exception as exc:
            cls._mark_trade_error(trade_id=trade_id, error_text=str(exc))
            raise

    @classmethod
    def _mark_trade_error(cls, trade_id: int, error_text: str) -> None:
        IborTradeEvent.objects.filter(pk=trade_id).update(
            book_sts_cd=IborTradeEvent.IborBookStatus.ERROR,
            book_err_txt=str(error_text)[:400],
        )