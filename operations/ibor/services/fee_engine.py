from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import Any

from operations.ibor.services.fee_calculator import IborFeeCalculator
from operations.ibor.services.fee_selector import IborFeeScheduleSelector


class IborFeeEngine:
    @classmethod
    def quote_fees(
        cls,
        *,
        trade_dt,
        quantity: Decimal,
        price: Decimal,
        side: str,
        broker_id: int | None = None,
        exec_venue_id: int | None = None,
        asset_class_id: int | None = None,
        asset_sub_class_id: int | None = None,
        trade_ccy_id: int | None = None,
        source_system: str = "",
    ) -> dict[str, Any]:
        schedule = IborFeeScheduleSelector.select_schedule(
            trade_dt=trade_dt,
            broker_id=broker_id,
            exec_venue_id=exec_venue_id,
            asset_class_id=asset_class_id,
            asset_sub_class_id=asset_sub_class_id,
            trade_ccy_id=trade_ccy_id,
            side=side,
            source_system=source_system,
        )

        if schedule is None:
            gross_amount = quantity * price
            return {
                "schedule_id": None,
                "schedule_name": None,
                "gross_amount": str(gross_amount),
                "total_charges": "0.0000",
                "net_amount": str(gross_amount),
                "charges": [],
                "message": "No matching fee schedule found.",
            }

        result = IborFeeCalculator.calculate(
            schedule=schedule,
            side=side,
            quantity=quantity,
            price=price,
            trade_ccy_id=trade_ccy_id,
        )

        return {
            "schedule_id": result.schedule_id,
            "schedule_name": schedule.schedule_name,
            "gross_amount": str(result.gross_amount),
            "total_charges": str(result.total_charges),
            "net_amount": str(result.net_amount),
            "charges": [
                {
                    "sequence_no": line.sequence_no,
                    "charge_type_cd": line.charge_type_cd,
                    "description": line.description,
                    "rate": str(line.rate) if line.rate is not None else None,
                    "amount": str(line.amount),
                    "cost_ccy_id": line.cost_ccy_id,
                    "reference_charge_type_cd": line.reference_charge_type_cd,
                }
                for line in result.charges
            ],
            "message": "OK",
        }