from __future__ import annotations

from datetime import date
from decimal import Decimal

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
        share_price: Decimal | None = None,
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

        # TODO: Add share price filtering when min/max_share_price fields are added to model
        # if share_price is not None:
        #     qs = qs.filter(
        #         Q(min_share_price__isnull=True) | Q(min_share_price__lte=share_price),
        #         Q(max_share_price__isnull=True) | Q(max_share_price__gte=share_price),
        #     )

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

    @classmethod
    def get_fee_rules_for_trade(
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
        share_price: Decimal | None = None,
    ) -> list[dict]:
        """
        Returns ALL fee rules for the best matching schedule.

        This is the main method to call when auto-populating fee charges
        in the trade booking form. It returns multiple fee rule lines.

        Args:
            trade_dt: Trade date for effective date filtering
            broker_id: Broker for fee schedule matching
            exec_venue_id: Exchange for fee schedule matching
            asset_class_id: Asset class for fee schedule matching
            asset_sub_class_id: Asset sub-class for fee schedule matching
            trade_ccy_id: Trade currency for fee schedule matching
            side: 'Buy' or 'Sell' for fee schedule matching
            source_system: Source system identifier
            share_price: Share price for tiered pricing (e.g., SCS <10 vs >10)

        Returns:
            List of dicts with fee rule details:
            [
                {
                    'id': 1,
                    'sequence_no': 10,
                    'charge_type_cd': 'Commission',
                    'description': 'Brokerage Commission',
                    'calc_method': 'Percent of gross',
                    'apply_on': 'Gross amount',
                    'rate': Decimal('0.15'),
                    'currency_id': 'PKR',
                    'is_mandatory': True,
                    ...
                },
                {
                    'id': 2,
                    'sequence_no': 20,
                    'charge_type_cd': 'Tax',
                    'description': 'Capital Value Tax',
                    'calc_method': 'Percent of gross',
                    'rate': Decimal('0.02'),
                    ...
                },
                {
                    'id': 3,
                    'sequence_no': 30,
                    'charge_type_cd': 'VAT/GST/SST',
                    'description': 'SST on Commission',
                    'calc_method': 'Percent of another charge',
                    'apply_on': 'Commission',
                    'rate': Decimal('15.00'),
                    'reference_charge_type_cd': 'Commission',
                    ...
                }
            ]

        Example usage in view:
            >>> from operations.ibor.services.fee_selector import IborFeeScheduleSelector
            >>> from datetime import date
            >>> from decimal import Decimal
            >>>
            >>> # User selects: Broker=SCS, Exchange=PSX, Asset=Equity, Share Price=15.50
            >>> rules = IborFeeScheduleSelector.get_fee_rules_for_trade(
            ...     trade_dt=date(2026, 6, 12),
            ...     broker_id=2,  # SCS
            ...     exec_venue_id=6,  # PSX
            ...     asset_class_id=2,  # EQTY
            ...     trade_ccy_id=13,  # PKR
            ...     share_price=Decimal('15.50'),  # > 10, so high price schedule
            ... )
            >>>
            >>> # Returns 3 fee rules: Commission, CVT, SST
            >>> len(rules)
            3
            >>> rules[0]['description']
            'Brokerage Commission'
            >>> rules[2]['reference_charge_type_cd']  # SST references commission
            'Commission'
        """
        # 1. Find the best matching schedule
        schedule = cls.select_schedule(
            trade_dt=trade_dt,
            broker_id=broker_id,
            exec_venue_id=exec_venue_id,
            asset_class_id=asset_class_id,
            asset_sub_class_id=asset_sub_class_id,
            trade_ccy_id=trade_ccy_id,
            side=side,
            source_system=source_system,
            share_price=share_price,
        )

        if not schedule:
            return []

        # 2. Get ALL active rules for this schedule (ordered by sequence)
        rules = (
            schedule.rules.filter(is_active=True)
            .order_by('sequence_no')
            .values(
                'id',
                'sequence_no',
                'charge_type_cd',
                'description',
                'calc_method',
                'apply_on',
                'rate',
                'flat_amount',
                'per_unit_amount',
                'minimum_amount',
                'maximum_amount',
                'currency_id',
                'reference_charge_type_cd',
                'rounding_dp',
                'is_mandatory',
            )
        )

        return list(rules)
