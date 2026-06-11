from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from operations.ibor.models.fee import (
    IborFeeApplyOn,
    IborFeeCalcMethod,
    IborFeeRule,
    IborFeeSchedule,
)
from operations.ibor.models.trade import IborChargeType, IborSide


FOUR_DP = Decimal("0.0001")
ZERO = Decimal("0")


@dataclass
class CalculatedFeeLine:
    sequence_no: int
    charge_type_cd: str
    description: str
    rate: Decimal | None
    amount: Decimal
    cost_ccy_id: int | None
    reference_charge_type_cd: str


@dataclass
class CalculatedFeeResult:
    schedule_id: int | None
    gross_amount: Decimal
    total_charges: Decimal
    net_amount: Decimal
    charges: list[CalculatedFeeLine]


class IborFeeCalculator:
    @classmethod
    def calculate(
        cls,
        *,
        schedule: IborFeeSchedule,
        side: str,
        quantity: Decimal,
        price: Decimal,
        trade_ccy_id: int | None = None,
    ) -> CalculatedFeeResult:
        gross_amount = (quantity * price).quantize(FOUR_DP, rounding=ROUND_HALF_UP)
        calculated_lines: list[CalculatedFeeLine] = []

        for rule in schedule.rules.filter(is_active=True).order_by("sequence_no", "id"):
            amount = cls._calculate_rule_amount(
                rule=rule,
                gross_amount=gross_amount,
                quantity=quantity,
                calculated_lines=calculated_lines,
            )

            if amount <= ZERO and rule.is_mandatory:
                amount = ZERO.quantize(FOUR_DP, rounding=ROUND_HALF_UP)

            if amount > ZERO or rule.is_mandatory:
                calculated_lines.append(
                    CalculatedFeeLine(
                        sequence_no=rule.sequence_no,
                        charge_type_cd=rule.charge_type_cd,
                        description=rule.description or dict(IborChargeType.choices).get(rule.charge_type_cd, ""),
                        rate=rule.rate,
                        amount=amount,
                        cost_ccy_id=rule.currency_id or trade_ccy_id,
                        reference_charge_type_cd=rule.reference_charge_type_cd,
                    )
                )

        total_charges = sum((line.amount for line in calculated_lines), start=ZERO).quantize(
            FOUR_DP,
            rounding=ROUND_HALF_UP,
        )

        if side == IborSide.BUY:
            net_amount = (gross_amount + total_charges).quantize(FOUR_DP, rounding=ROUND_HALF_UP)
        else:
            net_amount = (gross_amount - total_charges).quantize(FOUR_DP, rounding=ROUND_HALF_UP)

        return CalculatedFeeResult(
            schedule_id=schedule.id,
            gross_amount=gross_amount,
            total_charges=total_charges,
            net_amount=net_amount,
            charges=calculated_lines,
        )

    @classmethod
    def _calculate_rule_amount(
        cls,
        *,
        rule: IborFeeRule,
        gross_amount: Decimal,
        quantity: Decimal,
        calculated_lines: list[CalculatedFeeLine],
    ) -> Decimal:
        base_value = cls._get_base_value(
            rule=rule,
            gross_amount=gross_amount,
            quantity=quantity,
            calculated_lines=calculated_lines,
        )

        amount = ZERO

        if rule.calc_method == IborFeeCalcMethod.PCT_GROSS:
            amount = base_value * (rule.rate or ZERO)

        elif rule.calc_method == IborFeeCalcMethod.FLAT:
            amount = rule.flat_amount or ZERO

        elif rule.calc_method == IborFeeCalcMethod.PER_UNIT:
            amount = quantity * (rule.per_unit_amount or ZERO)

        elif rule.calc_method == IborFeeCalcMethod.PCT_OF_CHARGE:
            amount = base_value * (rule.rate or ZERO)

        elif rule.calc_method == IborFeeCalcMethod.MIN_OF_PCT_OR_FLAT:
            pct_amount = base_value * (rule.rate or ZERO)
            flat_amount = rule.flat_amount or ZERO
            amount = max(pct_amount, flat_amount)

        elif rule.calc_method == IborFeeCalcMethod.MAX_OF_PCT_OR_FLAT:
            pct_amount = base_value * (rule.rate or ZERO)
            flat_amount = rule.flat_amount or ZERO
            amount = min(pct_amount, flat_amount)

        if rule.minimum_amount is not None:
            amount = max(amount, rule.minimum_amount)

        if rule.maximum_amount is not None:
            amount = min(amount, rule.maximum_amount)

        quant = Decimal("1").scaleb(-(rule.rounding_dp or 4))
        return amount.quantize(quant, rounding=ROUND_HALF_UP)

    @classmethod
    def _get_base_value(
        cls,
        *,
        rule: IborFeeRule,
        gross_amount: Decimal,
        quantity: Decimal,
        calculated_lines: list[CalculatedFeeLine],
    ) -> Decimal:
        if rule.apply_on == IborFeeApplyOn.GROSS:
            return gross_amount

        if rule.apply_on == IborFeeApplyOn.QUANTITY:
            return quantity

        if rule.apply_on == IborFeeApplyOn.COMMISSION:
            for line in calculated_lines:
                if line.charge_type_cd == IborChargeType.COMM:
                    return line.amount
            return ZERO

        if rule.reference_charge_type_cd:
            for line in calculated_lines:
                if line.charge_type_cd == rule.reference_charge_type_cd:
                    return line.amount

        return gross_amount