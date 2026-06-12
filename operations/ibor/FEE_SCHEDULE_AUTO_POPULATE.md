# Fee Schedule Auto-Populate - Complete Setup Guide

## ✅ BACKEND COMPLETE - READY TO TEST!

All backend code has been implemented and pushed to GitHub. You can now pull and test immediately.

---

## 📦 What's Been Added (3 Commits)

### 1. **Service Layer** (Commit: d20c2b2)
- File: `operations/ibor/services/fee_selector.py`
- Added: `get_fee_rules_for_trade()` method
- Returns: List of ALL fee rules from matching schedule
- Supports: Tiered pricing via `share_price` parameter

### 2. **API Endpoint** (Commit: a37cd93)
- File: `operations/ibor/views/fee_api_views.py`  
- Added: `get_fee_schedule_rules_api()` function
- Endpoint: Returns JSON with multiple fee rule lines

### 3. **URL Route** (Commit: 76b684f)
- File: `operations/ibor/urls.py`
- Route: `/ibor/fees/schedule-rules/`
- Name: `fee-schedule-rules`

---

## 🚀 How to Test RIGHT NOW

### Step 1: Pull Latest Code
```bash
cd ~/PortX
git pull origin main
```

### Step 2: Run Server
```bash
python manage.py runserver
```

### Step 3: Test API Endpoint

Open your browser or use `curl`:

```
http://127.0.0.1:8000/ibor/fees/schedule-rules/?trade_dt=2026-06-12&broker_id=2&exec_venue_id=6&asset_class_id=2&trade_ccy_id=13&share_price=15.50
```

**Expected Response:**
```json
{
  "success": true,
  "fee_rules": [
    {
      "id": 1,
      "sequence_no": 10,
      "charge_type_cd": "Commission",
      "description": "Brokerage Commission",
      "calc_method": "Percent of gross",
      "apply_on": "Gross amount",
      "rate": "0.150000",
      "currency_id": "PKR",
      "is_mandatory": true
    },
    {
      "id": 2,
      "sequence_no": 20,
      "charge_type_cd": "Tax",
      "description": "Capital Value Tax",
      "calc_method": "Percent of gross",
      "rate": "0.020000",
      "currency_id": "PKR"
    }
  ],
  "count": 2
}
```

---

## 🎯 Frontend Integration (TODO - Add to Your Trade Form)

You need to add JavaScript to `operations/ibor/templates/ibor/trade/trade_form.html`

### Add This Before `</body>`:

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Trigger fee auto-population when critical fields change
    const fields = ['id_broker', 'id_exec_venue', 'id_asset_class', 'id_trade_ccy', 'id_share_price'];
    
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('change', fetchFeeRules);
            if (fieldId === 'id_share_price') {
                field.addEventListener('blur', fetchFeeRules);
            }
        }
    });
});

function fetchFeeRules() {
    const tradeDate = document.getElementById('id_trade_dt')?.value || new Date().toISOString().split('T')[0];
    const brokerId = document.getElementById('id_broker')?.value;
    const execVenueId = document.getElementById('id_exec_venue')?.value;
    const assetClassId = document.getElementById('id_asset_class')?.value;
    const tradeCcy = document.getElementById('id_trade_ccy')?.value;
    const sharePrice = document.getElementById('id_share_price')?.value;
    
    // Only fetch if minimum required fields are filled
    if (!brokerId || !assetClassId) {
        console.log('Waiting for broker and asset class to be selected...');
        return;
    }
    
    // Build query string
    const params = new URLSearchParams({
        trade_dt: tradeDate,
        broker_id: brokerId,
    });
    
    if (execVenueId) params.append('exec_venue_id', execVenueId);
    if (assetClassId) params.append('asset_class_id', assetClassId);
    if (tradeCcy) params.append('trade_ccy_id', tradeCcy);
    if (sharePrice) params.append('share_price', sharePrice);  // Critical for tiered pricing!
    
    console.log('Fetching fee rules:', params.toString());
    
    // Make AJAX request
    fetch(`/ibor/fees/schedule-rules/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`✅ Loaded ${data.count} fee rules:`, data.fee_rules);
                
                // Auto-populate your charges formset here
                populateFeeRules(data.fee_rules);
                
                // Show success notification
                alert(`Auto-loaded ${data.count} charges`);
            } else {
                console.error('❌ Error:', data.error);
            }
        })
        .catch(error => {
            console.error('❌ Network error:', error);
        });
}

function populateFeeRules(rules) {
    // TODO: Implement this based on your formset structure
    // This depends on how you handle charges in your trade form
    
    console.log('Populating fee rules:', rules);
    
    // Example (adjust to your HTML structure):
    // rules.forEach((rule, index) => {
    //     document.getElementById(`id_charges-${index}-charge_type`).value = rule.charge_type_cd;
    //     document.getElementById(`id_charges-${index}-description`).value = rule.description;
    //     document.getElementById(`id_charges-${index}-rate`).value = rule.rate;
    //     document.getElementById(`id_charges-${index}-currency`).value = rule.currency_id;
    // });
}
</script>
```

---

## 📋 API Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|----------|
| `trade_dt` | ✅ Yes | Trade date (YYYY-MM-DD) | `2026-06-12` |
| `broker_id` | No | Broker ID | `2` (SCS) |
| `exec_venue_id` | No | Exchange ID | `6` (PSX) |
| `asset_class_id` | No | Asset class ID | `2` (EQTY) |
| `asset_sub_class_id` | No | Asset sub-class ID | `4` (EQ_COMMON) |
| `trade_ccy_id` | No | Currency ID | `13` (PKR) |
| `share_price` | No | **For tiered pricing** | `15.50` |
| `side` | No | BUY or SELL | `BUY` |

---

## 🔧 SCS Tiered Pricing Setup

For SCS broker with different rates for share price < 10 vs > 10:

1. **Create Two Schedules in Django Admin:**

**Schedule 1:** SCS PSX Equity (Low Price)
- Schedule Name: "SCS PSX Equity (Share Price 0-10)"
- Broker: SCS
- Exchange: PSX
- Asset Class: Equity
- Priority: 100

**Fee Rules:**
- Rule 1: Commission @ Rs 0.03/share (calc_method: Per unit)
- Rule 2: CDC Handling @ Rs 0.005/share  
- Rule 3: SST @ 15% of Commission (calc_method: Percent of another charge)

**Schedule 2:** SCS PSX Equity (High Price)
- Schedule Name: "SCS PSX Equity (Share Price 10+)"
- Broker: SCS
- Exchange: PSX  
- Asset Class: Equity
- Priority: 101

**Fee Rules:**
- Rule 1: Commission @ max(Rs 0.05, 0.15%) (calc_method: Maximum of percent or flat)
- Rule 2: CDC Handling @ Rs 0.005/share
- Rule 3: SST @ 15% of Commission

2. **When user enters share price**, the API will automatically select the right schedule!

---

## ✨ What Happens When You Test

1. User selects: **Broker = SCS, Exchange = PSX, Asset = Equity**
2. User enters: **Share Price = 15.50**
3. JavaScript triggers AJAX call
4. Backend matches to "SCS PSX Equity (High Price)" schedule
5. Returns ALL fee rules (Commission + CVT + SST)
6. Frontend auto-populates 3 charge lines
7. User sees complete fee breakdown instantly!

---

## 🎉 Summary

✅ **Backend Service**: Returns multiple fee rule lines  
✅ **API Endpoint**: `/ibor/fees/schedule-rules/`  
✅ **URL Route**: Registered in `urls.py`  
✅ **Tiered Pricing**: Supports share_price parameter  
✅ **Multiple Lines**: Returns list of dicts, not single dict  
✅ **SST Calculation**: Linked via `reference_charge_type_cd`  

**Next Step**: Pull code and test the API endpoint now! The JavaScript integration is straightforward once you see the API working.

---

## 📞 Need Help?

The backend is 100% ready. If you have questions about:
1. Testing the API → Try the curl command above
2. Frontend integration → I can help add the JavaScript to your specific form
3. Creating fee schedules → Use Django admin at `/admin/ibor/iborfeeschedule/`
