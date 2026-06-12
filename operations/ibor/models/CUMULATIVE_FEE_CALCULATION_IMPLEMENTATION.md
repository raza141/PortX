# Cumulative Fee Calculation Implementation Guide

## Overview
This document provides complete implementation for SST (Sindh Sales Tax) calculation on cumulative charges (Commission + CDC).

## Problem Statement
**SST Formula:** `SST = (Commission + CDC) × 15%`

The system needs to calculate SST on the **sum of previous charges**, not just one charge.

---

## Step 1: Update Fee Model - Add PCT_CUMULATIVE

**File:** `operations/ibor/models/fee.py`

### Change Required:
```python
class IborFeeCalcMethod(models.TextChoices):
    PCT_GROSS = "PCT_GROSS", "Percent of gross"
    FLAT = "FLAT", "Flat amount"
    PER_UNIT = "PER_UNIT", "Per unit"
    PCT_OF_CHARGE = "PCT_OF_CHARGE", "Percent of another charge"
    MIN_OF_PCT_OR_FLAT = "MIN_OF_PCT_OR_FLAT", "Minimum of percent or flat"
    MAX_OF_PCT_OR_FLAT = "MAX_OF_PCT_OR_FLAT", "Maximum of percent or flat"
    # ADD THIS NEW LINE:
    PCT_CUMULATIVE = "PCT_CUMULATIVE", "Percent of cumulative charges"
```

**Migration Command:**
```bash
python manage.py makemigrations ibor
python manage.py migrate
```

---

## Step 2: Update Fee Calculation Engine

**File:** `operations/ibor/services/fee_selector.py`

### Add Cumulative Calculation Logic:

```python
def calculate_trade_fees(trade_context, fee_rules):
    """
    Calculate fees for a trade based on fee rules.
    Handles cumulative calculation for taxes like SST.
    
    Args:
        trade_context: dict with quantity, price, gross_amount, etc.
        fee_rules: list of IborFeeRule objects ordered by sequence_no
    
    Returns:
        list of calculated fee amounts with metadata
    """
    from decimal import Decimal
    
    calculated_fees = []
    cumulative_charges = Decimal('0.00')
    
    for rule in fee_rules:
        fee_amount = Decimal('0.00')
        
        # Calculate based on method
        if rule.calc_method == 'PER_UNIT':
            # Per share calculation (e.g., Commission Rs. 0.03/share, CDC Rs. 0.005/share)
            quantity = Decimal(str(trade_context.get('quantity', 0)))
            per_unit_amt = rule.per_unit_amount or Decimal('0')
            fee_amount = quantity * per_unit_amt
            
        elif rule.calc_method == 'PCT_GROSS':
            # Percentage of gross amount
            gross = Decimal(str(trade_context.get('gross_amount', 0)))
            rate = rule.rate or Decimal('0')
            fee_amount = gross * rate
            
        elif rule.calc_method == 'FLAT':
            # Flat amount
            fee_amount = rule.flat_amount or Decimal('0')
            
        elif rule.calc_method == 'PCT_OF_CHARGE':
            # Percentage of a specific previous charge
            ref_charge_type = rule.reference_charge_type_cd
            if ref_charge_type:
                # Find the referenced charge
                ref_charge = next(
                    (f for f in calculated_fees if f['charge_type_cd'] == ref_charge_type),
                    None
                )
                if ref_charge:
                    rate = rule.rate or Decimal('0')
                    fee_amount = ref_charge['amount'] * rate
        
        elif rule.calc_method == 'PCT_CUMULATIVE':
            # **NEW: Percentage of cumulative charges (for SST)**
            rate = rule.rate or Decimal('0')
            fee_amount = cumulative_charges * rate
            print(f"SST Calculation: {cumulative_charges} × {rate} = {fee_amount}")
        
        # Apply minimum/maximum constraints
        if rule.minimum_amount and fee_amount < rule.minimum_amount:
            fee_amount = rule.minimum_amount
        if rule.maximum_amount and fee_amount > rule.maximum_amount:
            fee_amount = rule.maximum_amount
        
        # Round to 2 decimal places
        fee_amount = fee_amount.quantize(Decimal('0.01'))
        
        # Add to calculated fees
        calculated_fees.append({
            'rule_id': rule.id,
            'sequence_no': rule.sequence_no,
            'charge_type_cd': rule.charge_type_cd,
            'description': rule.description,
            'amount': fee_amount,
            'currency_id': trade_context.get('currency_id'),
        })
        
        # Add to cumulative total (BEFORE taxes/SST)
        # Only add charges that are NOT taxes
        if rule.charge_type_cd not in ['VAT', 'SST', 'TAX']:
            cumulative_charges += fee_amount
    
    return calculated_fees
```

---

## Step 3: Update API View

**File:** `operations/ibor/views/fee_api_views.py`

### Update `get_fee_schedule_rules_api` to use new calculation:

```python
from operations.ibor.services.fee_selector import calculate_trade_fees

@require_http_methods(["GET"])
def get_fee_schedule_rules_api(request):
    """
    API endpoint to get calculated fee amounts for a trade.
    """
    try:
        # Parse request parameters
        broker_id = request.GET.get('broker_id')
        exec_venue_id = request.GET.get('exec_venue_id')
        quantity = Decimal(request.GET.get('quantity', '0'))
        price = Decimal(request.GET.get('price', '0'))
        
        # Get fee rules
        fee_rules = IborFeeScheduleSelector.get_fee_rules_for_trade(
            trade_dt=request.GET.get('trade_dt'),
            broker_id=broker_id,
            exec_venue_id=exec_venue_id,
            # ... other params
        )
        
        # Calculate fees
        trade_context = {
            'quantity': quantity,
            'price': price,
            'gross_amount': quantity * price,
            'currency_id': request.GET.get('trade_ccy_id'),
        }
        
        calculated_fees = calculate_trade_fees(trade_context, fee_rules)
        
        return JsonResponse({
            'success': True,
            'fees': calculated_fees,
            'count': len(calculated_fees)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
```

---

## Step 4: Configure Fee Rules in Admin

### Rule #1: Commission (Sequence 10)
| Field | Value |
|-------|-------|
| Sequence | 10 |
| Charge Type | Commission |
| Description | Broker Trading Commission |
| Calc Method | **Per unit** |
| Per Unit Amount | **0.03** |

### Rule #2: CDC (Sequence 20)
| Field | Value |
|-------|-------|
| Sequence | 20 |
| Charge Type | Levy/Fee |
| Description | CDC Charges |
| Calc Method | **Per unit** |
| Per Unit Amount | **0.005** |
| Minimum Amount | 0.03 |

### Rule #3: SST (Sequence 30) - **NEW**
| Field | Value |
|-------|-------|
| Sequence | 30 |
| Charge Type | VAT/GST/SST |
| Description | Sindh Sales Tax (SST) 15% |
| Calc Method | **PCT_CUMULATIVE** ← NEW |
| Rate | **0.15** (15%) |
| Reference Charge Type | Leave empty |

---

## Step 5: Test the Implementation

### Test Case: SHNI Trade (500 shares at Rs. 9.54)

**Expected Calculation:**
```
Commission = 500 × 0.03 = Rs. 15.00
CDC = 500 × 0.005 = Rs. 2.50
--------------------------------------------
Cumulative = Rs. 17.50
SST = 17.50 × 0.15 = Rs. 2.625 ≈ Rs. 2.63 ✅
```

### API Test:
```bash
curl "http://127.0.0.1:8000/ibor/fees/schedule-rules/?broker_id=1&exec_venue_id=2&quantity=500&price=9.54&trade_ccy_id=3"
```

**Expected Response:**
```json
{
  "success": true,
  "fees": [
    {"sequence_no": 10, "charge_type_cd": "COMM", "amount": "15.00"},
    {"sequence_no": 20, "charge_type_cd": "LEVY", "amount": "2.50"},
    {"sequence_no": 30, "charge_type_cd": "SST", "amount": "2.63"}
  ],
  "count": 3
}
```

---

## Summary

✅ Added `PCT_CUMULATIVE` calculation method
✅ Implemented cumulative charge tracking
✅ SST now calculates on (Commission + CDC)
✅ Proper sequence-based calculation
✅ Supports future additions (PSX Laga, SECP Fee, etc.)

## Next Steps
1. Run migrations
2. Add the three fee rules in admin
3. Test with real trade data
4. Verify calculations match broker statements
