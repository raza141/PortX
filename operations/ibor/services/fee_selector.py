from __future__ import annotations

from datetime import date

from django.db.models import Q

from operations.ibor.models.fee import IborFeeSchedule


class IborFeeScheduleSelector:
    """
    Selects the best active fee schedule for a given trade context.
    Matching logic:
    1. Only active schedules within effective date range.
    2. Optional filters must either match exactly or be blank/null on the schedule.
    3. Lowest priority wins first.
    4. More specific schedules should be preferred over generic/default ones.
    """

    @classmethod
    def select_schedule(
        cls,
        *,
        trade_dt: date,
        broker_id: int | None = None,
        exec_venue_id: int | None = None,
        asset_class_id: int | None = None,
        asset_sub_class_id: int | None = None,
        trade_ccy_id: int | None = None,
        side: str = "",
        source_system: str = "",
    ) -> IborFeeSchedule | None:
        qs = (
            IborFeeSchedule.objects.filter(
                is_active=True,
                effective_from__lte=trade_dt,
            )
            .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=trade_dt))
        )

        qs = qs.filter(Q(broker_id=broker_id) | Q(broker__isnull=True))
        qs = qs.filter(Q(exec_venue_id=exec_venue_id) | Q(exec_venue__isnull=True))
        qs = qs.filter(Q(asset_class_id=asset_class_id) | Q(asset_class__isnull=True))
        qs = qs.filter(Q(asset_sub_class_id=asset_sub_class_id) | Q(asset_sub_class__isnull=True))
        qs = qs.filter(Q(trade_ccy_id=trade_ccy_id) | Q(trade_ccy__isnull=True))

        if side:
            qs = qs.filter(Q(side=side) | Q(side=""))
        else:
            qs = qs.filter(Q(side="") | Q(side__isnull=True))

        if source_system:
            qs = qs.filter(Q(source_system=source_system) | Q(source_system=""))
        else:
            qs = qs.filter(Q(source_system="") | Q(source_system__isnull=True))

        qs = qs.order_by(
            "priority",
            "-broker_id",
            "-exec_venue_id",
            "-asset_class_id",
            "-asset_sub_class_id",
            "-trade_ccy_id",
            "-side",
            "-source_system",
            "-effective_from",
            "id",
        )

        return qs.first()