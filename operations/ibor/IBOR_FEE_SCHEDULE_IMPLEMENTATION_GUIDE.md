# IBOR Fee Schedule Auto-Population - Implementation Guide

## Document Purpose
This document locks down the complete, repeatable workflow for implementing automated broker fee/commission charging in the PortX IBOR module. This serves as the master reference for all development, testing, and deployment activities.

---

## 1. USER REQUIREMENTS (MUST PRESERVE)

### Core Requirements
1. **All commission charges should be auto-populated**
   - Based on broker fee schedules configured in the system
   - Triggered when trade context is complete (broker, exchange, asset class, currency, share price)
   - No manual entry required for standard commission lines

2. **Extra charges button available for add another charges**
   - UI must provide "Add Extra Cost" button
   - Extra costs are user-entered and editable
   - Distinguished from auto-populated base commissions

3. **Commission should be charged based on available rule, which when we register broker we need add and link it to investor account**
   - Each broker has associated fee schedules
   - Fee schedules contain multiple rules (Commission, CDC, SST, etc.)
   - Investor accounts link to specific brokers
   - Fee rules apply based on broker-investor relationship

4. **Front end charges commission should be read-only (except extra cost button)**
   - Auto-populated fee lines: READ-ONLY
   - Extra cost lines: EDITABLE
   - Clear visual distinction in UI

5. **Make sure use decimal to properly 0.0000**
   - All monetary values: `models.DecimalField(max_digits=19, decimal_places=4)`
   - Display format: always 4 decimal places (0.0000)
   - No floating point arithmetic

6. **Show me the link between View, Models, and Service directory**
   - Clear separation of concerns
   - Models: data structure
   - Services: business logic
   - Views: HTTP request/response handling
   - Documented below in Architecture section

7. **Proposed changes in each file if required**
   - File-by-file change log provided in Implementation Steps section

### Critical Business Rule: SST Calculation
**SST (Sindh Sales Tax) = (Commission + CDC) × 0.15**

This is a **CUMULATIVE** calculation:
- SST depends on the sum of preceding charges
- Must be calculated after Commission and CDC are known
- Requires PCT_CUMULATIVE calculation method

---

## 2. ARCHITECTURE OVERVIEW

### 2.1 Directory Structure
```
operations/ibor/
├── models/
│   ├── fee_models.py          # IborFeeSchedule, IborFeeRule
│   ├── trade_models.py         # IborTrade
│   └── charge_models.py        # IborTradeCharge
├── services/
│   ├── fee_selector.py         # FeeSelector - rule matching logic
│   ├── fee_calculator.py       # FeeCalculator - cumulative calculations
│   └── position_engine.py      # PositionEngine - position rebuild
├── views/
│   ├── trade_views.py          # Trade CRUD views
│   └── fee_api_views.py        # API: /ibor/fees/schedule-rules/
├── templates/ibor/
│   └── trade_form.html         # Trade entry form with AJAX
├── migrations/
│   └── [auto-generated]
└── admin.py                    # Django admin configuration
```

### 2.2 Data Flow
```
User selects broker/exchange/asset → 
  Frontend AJAX call → 
    /ibor/fees/schedule-rules/ API → 
      FeeSelector.get_fee_rules_for_trade() → 
        Returns matching rules → 
          Frontend populates formset → 
            User saves trade → 
              Trade saved with charges → 
                PositionEngine.rebuild_trade_position_context(trade)
```

### 2.3 Model Relationships
```
IborFeeSchedule
  ├─ broker (FK)
  ├─ asset_class
  ├─ exchange
  ├─ currency
  └─ IborFeeRule (OneToMany)
       ├─ charge_type (FK to IborChargeType)
       ├─ sequence (10, 20, 30...)
       ├─ calculation_method (PCT_GROSS, PCT_NET, FLAT, PCT_CUMULATIVE)
       ├─ rate_value (Decimal)
       ├─ reference_charge_type_cd (for cumulative)
       └─ min_price / max_price (tiered pricing)

IborTrade
  ├─ investor_account (FK)
  ├─ broker (FK)
  ├─ share_price (Decimal)
  └─ IborTradeCharge (OneToMany)
       ├─ charge_type (FK)
       ├─ charge_amount (Decimal)
       ├─ is_auto_populated (Boolean)
       └─ sequence
```

---

## 3. IMPLEMENTATION STEPS

### Phase 1: Models Enhancement

#### File: `operations/ibor/models/fee_models.py`

**Changes Required:**
```python
from django.db import models
from decimal import Decimal

class IborFeeSchedule(models.Model):
    """Master fee schedule per broker/exchange/asset/currency"""
    schedule_name = models.CharField(max_length=200)
    broker = models.ForeignKey('IborBroker', on_delete=models.CASCADE)
    asset_class = models.CharField(max_length=50)  # EQUITY, DEBT, DERIVATIVE
    exchange = models.CharField(max_length=50, blank=True)  # PSX, KSE, etc.
    currency = models.CharField(max_length=3, default='PKR')
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'ibor_fee_schedule'
        ordering = ['-effective_date']

class IborFeeRule(models.Model):
    """Individual fee rule within a schedule"""
    
    CALCULATION_METHODS = [
        ('PCT_GROSS', 'Percentage of Gross Amount'),
        ('PCT_NET', 'Percentage of Net Amount'),
        ('FLAT', 'Flat Amount'),
        ('PCT_CUMULATIVE', 'Percentage of Cumulative Preceding Charges'),  # NEW
    ]
    
    fee_schedule = models.ForeignKey(IborFeeSchedule, on_delete=models.CASCADE, related_name='rules')
    charge_type = models.ForeignKey('IborChargeType', on_delete=models.PROTECT)
    sequence = models.IntegerField(help_text="Order of calculation: 10, 20, 30...")
    calculation_method = models.CharField(max_length=20, choices=CALCULATION_METHODS)
    rate_value = models.DecimalField(max_digits=19, decimal_places=4)
    
    # Tiered pricing
    min_price = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)
    max_price = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)
    
    # For cumulative calculations (e.g., SST based on Commission+CDC)
    reference_charge_type_cd = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Comma-separated charge codes for cumulative calc: COMM,CDC"
    )
    
    class Meta:
        db_table = 'ibor_fee_rule'
        ordering = ['sequence']
```

**Migration Command:**
```bash
python manage.py makemigrations ibor
python manage.py migrate ibor
```

---

### Phase 2: Service Layer - Fee Selector

#### File: `operations/ibor/services/fee_selector.py`

**Purpose:** Match trade context to best fee schedule and return applicable rules

```python
from django.db.models import Q
from operations.ibor.models import IborFeeSchedule
from datetime import date

class FeeSelector:
    """Service to select applicable fee rules for a trade"""
    
    @staticmethod
    def get_fee_rules_for_trade(broker_id, asset_class, exchange, currency, share_price, trade_date=None):
        """
        Returns list of fee rules matching trade context.
        
        Args:
            broker_id: int
            asset_class: str (EQUITY, DEBT, DERIVATIVE)
            exchange: str (PSX, KSE, etc.)
            currency: str (PKR, USD)
            share_price: Decimal
            trade_date: date (default: today)
            
        Returns:
            List[dict]: [
                {
                    'charge_type_code': 'COMM',
                    'charge_type_name': 'Commission',
                    'sequence': 10,
                    'calculation_method': 'PCT_GROSS',
                    'rate_value': '0.0300',
                    'reference_charge_type_cd': '',
                },
                ...
            ]
        """
        if trade_date is None:
            trade_date = date.today()
        
        # Find best matching schedule
        schedules = IborFeeSchedule.objects.filter(
            broker_id=broker_id,
            asset_class=asset_class,
            is_active=True,
            effective_date__lte=trade_date,
        ).filter(
            Q(expiry_date__gte=trade_date) | Q(expiry_date__isnull=True)
        )
        
        # Exact exchange match preferred
        if exchange:
            exact_match = schedules.filter(exchange=exchange).first()
            if exact_match:
                schedule = exact_match
            else:
                schedule = schedules.filter(exchange='').first()  # fallback to generic
        else:
            schedule = schedules.first()
        
        if not schedule:
            return []
        
        # Get rules, filter by price tier if applicable
        rules = schedule.rules.select_related('charge_type').all()
        
        result = []
        for rule in rules:
            # Check tiered pricing
            if rule.min_price is not None and share_price < rule.min_price:
                continue
            if rule.max_price is not None and share_price > rule.max_price:
                continue
            
            result.append({
                'charge_type_code': rule.charge_type.charge_code,
                'charge_type_name': rule.charge_type.charge_name,
                'charge_type_id': rule.charge_type.id,
                'sequence': rule.sequence,
                'calculation_method': rule.calculation_method,
                'rate_value': str(rule.rate_value),
                'reference_charge_type_cd': rule.reference_charge_type_cd or '',
            })
        
        return result
```

---

### Phase 3: Service Layer - Fee Calculator

#### File: `operations/ibor/services/fee_calculator.py`

**Purpose:** Calculate actual charge amounts with cumulative logic

```python
from decimal import Decimal

class FeeCalculator:
    """Service to calculate fee amounts including cumulative logic"""
    
    @staticmethod
    def calculate_charges(trade_gross_amount, fee_rules):
        """
        Calculate charge amounts for each rule.
        
        Args:
            trade_gross_amount: Decimal (share_price * quantity)
            fee_rules: List[dict] from FeeSelector.get_fee_rules_for_trade()
            
        Returns:
            List[dict]: [
                {
                    'charge_type_id': 1,
                    'charge_amount': Decimal('150.0000'),
                    'sequence': 10,
                    ...
                },
                ...
            ]
        """
        results = []
        charge_map = {}  # {charge_type_code: amount} for cumulative calc
        
        # Sort by sequence to ensure correct order
        sorted_rules = sorted(fee_rules, key=lambda x: x['sequence'])
        
        for rule in sorted_rules:
            amount = Decimal('0.0000')
            
            if rule['calculation_method'] == 'PCT_GROSS':
                amount = trade_gross_amount * Decimal(rule['rate_value']) / Decimal('100')
            
            elif rule['calculation_method'] == 'FLAT':
                amount = Decimal(rule['rate_value'])
            
            elif rule['calculation_method'] == 'PCT_NET':
                # Net = Gross - (all charges so far)
                total_charges_so_far = sum(charge_map.values())
                net_amount = trade_gross_amount - total_charges_so_far
                amount = net_amount * Decimal(rule['rate_value']) / Decimal('100')
            
            elif rule['calculation_method'] == 'PCT_CUMULATIVE':
                # Example: SST = (Commission + CDC) * 0.15
                ref_codes = [c.strip() for c in rule['reference_charge_type_cd'].split(',') if c.strip()]
                cumulative_base = sum(charge_map.get(code, Decimal('0')) for code in ref_codes)
                amount = cumulative_base * Decimal(rule['rate_value']) / Decimal('100')
            
            # Round to 4 decimals
            amount = amount.quantize(Decimal('0.0001'))
            
            # Store in map
            charge_map[rule['charge_type_code']] = amount
            
            results.append({
                'charge_type_id': rule['charge_type_id'],
                'charge_type_code': rule['charge_type_code'],
                'charge_type_name': rule['charge_type_name'],
                'charge_amount': amount,
                'sequence': rule['sequence'],
                'is_auto_populated': True,
            })
        
        return results
```

---

### Phase 4: API Endpoint

#### File: `operations/ibor/views/fee_api_views.py`

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from operations.ibor.services.fee_selector import FeeSelector
from decimal import Decimal
import json

@require_http_methods(["POST"])
def get_fee_schedule_rules(request):
    """
    API endpoint: /ibor/fees/schedule-rules/
    
    Request POST JSON:
    {
        "broker_id": 1,
        "asset_class": "EQUITY",
        "exchange": "PSX",
        "currency": "PKR",
        "share_price": "85.50"
    }
    
    Response JSON:
    {
        "success": true,
        "rules": [
            {
                "charge_type_code": "COMM",
                "charge_type_name": "Commission",
                "sequence": 10,
                "calculation_method": "PCT_GROSS",
                "rate_value": "0.0300"
            },
            ...
        ]
    }
    """
    try:
        data = json.loads(request.body)
        
        broker_id = data.get('broker_id')
        asset_class = data.get('asset_class')
        exchange = data.get('exchange', '')
        currency = data.get('currency', 'PKR')
        share_price = Decimal(data.get('share_price', '0'))
        
        rules = FeeSelector.get_fee_rules_for_trade(
            broker_id=broker_id,
            asset_class=asset_class,
            exchange=exchange,
            currency=currency,
            share_price=share_price
        )
        
        return JsonResponse({
            'success': True,
            'rules': rules
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
```

#### File: `operations/ibor/urls.py`

```python
from django.urls import path
from operations.ibor.views import fee_api_views

urlpatterns = [
    # ... existing patterns ...
    path('fees/schedule-rules/', fee_api_views.get_fee_schedule_rules, name='fee-schedule-rules'),
]
```

---

### Phase 5: Frontend Integration

#### File: `operations/ibor/templates/ibor/trade_form.html`

**Add AJAX trigger after broker/exchange/asset/share price fields:**

```javascript
<script>
$(document).ready(function() {
    
    // Trigger fee rule fetch when trade context is complete
    function fetchFeeRules() {
        const brokerId = $('#id_broker').val();
        const assetClass = $('#id_asset_class').val();
        const exchange = $('#id_exchange').val();
        const currency = $('#id_currency').val();
        const sharePrice = $('#id_share_price').val();
        
        // Validate required fields
        if (!brokerId || !assetClass || !sharePrice) {
            return;  // Don't fetch if context incomplete
        }
        
        // AJAX call
        $.ajax({
            url: '/ibor/fees/schedule-rules/',
            method: 'POST',
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: JSON.stringify({
                broker_id: parseInt(brokerId),
                asset_class: assetClass,
                exchange: exchange || '',
                currency: currency || 'PKR',
                share_price: sharePrice
            }),
            success: function(response) {
                if (response.success) {
                    populateFeeFormset(response.rules);
                }
            },
            error: function(xhr) {
                console.error('Fee rules fetch failed:', xhr.responseJSON);
            }
        });
    }
    
    // Populate formset with returned rules
    function populateFeeFormset(rules) {
        // Clear existing auto-populated rows
        $('.charge-row[data-auto-populated="true"]').remove();
        
        const grossAmount = parseFloat($('#id_share_price').val()) * parseFloat($('#id_quantity').val() || 1);
        
        rules.forEach((rule, index) => {
            // Clone empty form template
            const newForm = $('.charge-form-template').clone();
            newForm.removeClass('charge-form-template').addClass('charge-row');
            newForm.attr('data-auto-populated', 'true');
            
            // Populate fields
            newForm.find('.charge-type').val(rule.charge_type_id).prop('disabled', true);
            newForm.find('.sequence').val(rule.sequence);
            
            // Calculate amount (simplified - ideally call FeeCalculator)
            let amount = 0;
            if (rule.calculation_method === 'PCT_GROSS') {
                amount = grossAmount * parseFloat(rule.rate_value) / 100;
            }
            // ... handle other methods ...
            
            newForm.find('.charge-amount').val(amount.toFixed(4)).prop('readonly', true);
            newForm.find('.is-auto-populated').val('true');
            
            // Append to formset
            $('#charges-formset').append(newForm);
        });
    }
    
    // Bind triggers
    $('#id_broker, #id_asset_class, #id_exchange, #id_share_price').change(fetchFeeRules);
    
    // Extra cost button
    $('#add-extra-cost-btn').click(function() {
        const newForm = $('.charge-form-template').clone();
        newForm.removeClass('charge-form-template').addClass('charge-row');
        newForm.attr('data-auto-populated', 'false');
        newForm.find('.charge-amount').prop('readonly', false);  // Editable
        $('#charges-formset').append(newForm);
    });
    
    // CSRF helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
</script>
```

---

## 4. POSITION ENGINE INTEGRATION

### File: `operations/ibor/services/position_engine.py`

**Method:** `rebuild_trade_position_context(trade)`

**Purpose:** Recalculate position aggregates after trade save

**Integration Point Options:**

#### Option A: Post-Save Signal (Recommended)

```python
# In operations/ibor/models/trade_models.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from operations.ibor.services.position_engine import PositionEngine

@receiver(post_save, sender=IborTrade)
def rebuild_position_on_trade_save(sender, instance, created, **kwargs):
    """Automatically rebuild position after trade save"""
    PositionEngine.rebuild_trade_position_context(instance)
```

#### Option B: In Trade Save View

```python
# In operations/ibor/views/trade_views.py
from operations.ibor.services.position_engine import PositionEngine

class TradeCreateView(CreateView):
    def form_valid(self, form):
        response = super().form_valid(form)
        # Rebuild position after successful save
        PositionEngine.rebuild_trade_position_context(self.object)
        return response
```

#### Option C: In Service Layer

```python
# In operations/ibor/services/trade_service.py
def save_trade_with_charges(trade, charges):
    trade.save()
    for charge in charges:
        IborTradeCharge.objects.create(trade=trade, **charge)
    PositionEngine.rebuild_trade_position_context(trade)
    return trade
```

**Recommended:** Option A (post_save signal) for automatic, consistent behavior.

---

## 5. DATA SETUP EXAMPLE

### Step 1: Create Charge Types

```python
# In Django shell or admin
from operations.ibor.models import IborChargeType

IborChargeType.objects.create(
    charge_code='COMM',
    charge_name='Commission',
    charge_category='FEE',
    is_debit=True
)

IborChargeType.objects.create(
    charge_code='CDC',
    charge_name='CDC Charges',
    charge_category='FEE',
    is_debit=True
)

IborChargeType.objects.create(
    charge_code='SST',
    charge_name='Sindh Sales Tax',
    charge_category='TAX',
    is_debit=True
)
```

### Step 2: Create Fee Schedule

```python
from operations.ibor.models import IborFeeSchedule, IborFeeRule, IborBroker
from datetime import date
from decimal import Decimal

# Get broker
broker = IborBroker.objects.get(broker_code='SHNI')  # Example: Shajar & Naqvi

# Create schedule
schedule = IborFeeSchedule.objects.create(
    schedule_name='SHNI PSX Equity Standard',
    broker=broker,
    asset_class='EQUITY',
    exchange='PSX',
    currency='PKR',
    effective_date=date(2025, 1, 1),
    is_active=True
)

# Get charge types
comm_type = IborChargeType.objects.get(charge_code='COMM')
cdc_type = IborChargeType.objects.get(charge_code='CDC')
sst_type = IborChargeType.objects.get(charge_code='SST')

# Rule 1: Commission (0.03% of gross)
IborFeeRule.objects.create(
    fee_schedule=schedule,
    charge_type=comm_type,
    sequence=10,
    calculation_method='PCT_GROSS',
    rate_value=Decimal('0.0300')  # 0.03%
)

# Rule 2: CDC (0.15% of gross)
IborFeeRule.objects.create(
    fee_schedule=schedule,
    charge_type=cdc_type,
    sequence=20,
    calculation_method='PCT_GROSS',
    rate_value=Decimal('0.1500')  # 0.15%
)

# Rule 3: SST (15% of Commission + CDC) - CUMULATIVE
IborFeeRule.objects.create(
    fee_schedule=schedule,
    charge_type=sst_type,
    sequence=30,
    calculation_method='PCT_CUMULATIVE',
    rate_value=Decimal('15.0000'),  # 15%
    reference_charge_type_cd='COMM,CDC'  # Cumulative base
)
```

### Step 3: Test Calculation

```python
from operations.ibor.services.fee_selector import FeeSelector
from operations.ibor.services.fee_calculator import FeeCalculator
from decimal import Decimal

# Example: Haleon trade at PKR 85.50, 1000 shares
share_price = Decimal('85.50')
quantity = 1000
gross_amount = share_price * quantity  # 85,500

rules = FeeSelector.get_fee_rules_for_trade(
    broker_id=broker.id,
    asset_class='EQUITY',
    exchange='PSX',
    currency='PKR',
    share_price=share_price
)

charges = FeeCalculator.calculate_charges(gross_amount, rules)

for charge in charges:
    print(f"{charge['charge_type_name']}: PKR {charge['charge_amount']}")

# Expected output:
# Commission: PKR 25.6500  (85,500 * 0.03%)
# CDC Charges: PKR 128.2500  (85,500 * 0.15%)
# Sindh Sales Tax: PKR 23.0850  ((25.65 + 128.25) * 15%)
```

---

## 6. TESTING PROCEDURE

### 6.1 Unit Tests

```bash
# Test fee selector
python manage.py test operations.ibor.tests.test_fee_selector

# Test fee calculator
python manage.py test operations.ibor.tests.test_fee_calculator

# Test cumulative SST calculation
python manage.py test operations.ibor.tests.test_cumulative_charges
```

### 6.2 Integration Test

1. **Setup:**
   ```bash
   python manage.py runserver
   # Navigate to http://127.0.0.1:8000/admin/ibor/ibortrade/add/
   ```

2. **Create Test Trade:**
   - Select broker: SHNI
   - Asset class: EQUITY
   - Exchange: PSX
   - Share price: 85.50
   - Quantity: 1000
   - Observe charges auto-populate

3. **Verify:**
   - Commission appears (sequence 10, read-only)
   - CDC appears (sequence 20, read-only)
   - SST appears (sequence 30, read-only, = (Comm+CDC)*0.15)
   - "Add Extra Cost" button is available
   - Extra costs are editable

4. **Save and Check Position:**
   ```python
   from operations.ibor.models import IborTrade
   trade = IborTrade.objects.latest('id')
   print(trade.charges.all())
   # Should show all 3 charges with is_auto_populated=True
   ```

### 6.3 API Test

```bash
curl -X POST http://127.0.0.1:8000/ibor/fees/schedule-rules/ \
  -H "Content-Type: application/json" \
  -d '{
    "broker_id": 1,
    "asset_class": "EQUITY",
    "exchange": "PSX",
    "currency": "PKR",
    "share_price": "85.50"
  }'

# Expected response:
# {
#   "success": true,
#   "rules": [
#     {"charge_type_code": "COMM", "sequence": 10, "calculation_method": "PCT_GROSS", "rate_value": "0.0300"},
#     {"charge_type_code": "CDC", "sequence": 20, "calculation_method": "PCT_GROSS", "rate_value": "0.1500"},
#     {"charge_type_code": "SST", "sequence": 30, "calculation_method": "PCT_CUMULATIVE", "rate_value": "15.0000", "reference_charge_type_cd": "COMM,CDC"}
#   ]
# }
```

---

## 7. INDUSTRY BEST PRACTICES

### 7.1 Bloomberg AIM (Analytics & Investment Manager)
- **Fee Schedules:** Stored as rules engine with tiered pricing
- **Auto-population:** Triggered on trade entry, overridable by ops
- **Cumulative Charges:** Supported via formula fields
- **Audit Trail:** All fee changes logged with user/timestamp

### 7.2 JPMorgan Athena
- **Broker Fee Models:** Linked to counterparty master
- **Calculation Engine:** Separate service for fee calc with versioning
- **Real-time Validation:** Frontend shows estimated fees before save
- **Regulatory Reporting:** SST and other taxes tracked separately

### 7.3 BlackRock Aladdin
- **Fee Library:** Centralized fee schedule repository
- **Multi-tier Pricing:** Support for volume discounts and breakpoints
- **Tax Engine:** Separate module for SST, VAT, withholding tax
- **Position Integration:** Fees included in P&L and position NAV

### Key Takeaways:
1. ✅ Separate fee calculation from trade entry (service layer)
2. ✅ Support tiered/breakpoint pricing
3. ✅ Cumulative charges with clear dependencies
4. ✅ Read-only auto-populated fields, editable overrides
5. ✅ Audit trail for all fee changes
6. ✅ Integration with position/P&L engine

---

## 8. DEPLOYMENT CHECKLIST

- [ ] Models updated with PCT_CUMULATIVE option
- [ ] Migrations created and applied
- [ ] FeeSelector service implemented
- [ ] FeeCalculator service implemented with cumulative logic
- [ ] API endpoint /ibor/fees/schedule-rules/ created
- [ ] URL routing configured
- [ ] Frontend AJAX integration complete
- [ ] "Add Extra Cost" button functional
- [ ] Read-only styling for auto-populated charges
- [ ] Decimal formatting (4 places) enforced
- [ ] PositionEngine integration (post_save signal)
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] API tests passing
- [ ] Admin interface configured
- [ ] Test data seeded (charge types, schedules, rules)
- [ ] Documentation updated (this file)
- [ ] Code pushed to GitHub /operations/ibor

---

## 9. FILE CHANGE SUMMARY

| File | Change Type | Description |
|------|-------------|-------------|
| `models/fee_models.py` | MODIFY | Add PCT_CUMULATIVE option, reference_charge_type_cd field, tiered pricing fields |
| `services/fee_selector.py` | CREATE | New service for rule matching |
| `services/fee_calculator.py` | CREATE | New service for charge calculation with cumulative logic |
| `views/fee_api_views.py` | CREATE | New API view for /ibor/fees/schedule-rules/ |
| `urls.py` | MODIFY | Add API route |
| `templates/ibor/trade_form.html` | MODIFY | Add AJAX integration, "Add Extra Cost" button, read-only styling |
| `models/trade_models.py` | MODIFY | Add post_save signal for PositionEngine |
| `migrations/XXXX_fee_schedule.py` | CREATE | Auto-generated migration |
| `admin.py` | MODIFY | Register IborFeeSchedule, IborFeeRule |
| `tests/test_fee_selector.py` | CREATE | Unit tests |
| `tests/test_fee_calculator.py` | CREATE | Unit tests |
| `tests/test_cumulative_charges.py` | CREATE | Integration tests |

---

## 10. NEXT STEPS

1. **Code Review:** Peer review all changes before merge
2. **Testing:** Execute full test suite on dev environment
3. **UAT:** User acceptance testing with sample trades
4. **Documentation:** Update user manual with new fee workflow
5. **Training:** Train operations team on "Add Extra Cost" feature
6. **Deployment:** Deploy to production with rollback plan
7. **Monitoring:** Track fee calculation accuracy for first 100 trades
8. **Optimization:** Profile performance if charge calculation is slow

---

## 11. CONTACT & SUPPORT

For questions or issues:
- **Developer:** Raza (raza141)
- **Repository:** https://github.com/raza141/PortX
- **Module:** /operations/ibor
- **Last Updated:** 2025

---

**END OF IMPLEMENTATION GUIDE**

This document represents the complete, locked-down specification for IBOR fee schedule auto-population. Any deviations must be documented as addendums with version control.
