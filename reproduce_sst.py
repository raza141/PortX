import os
import django
from decimal import Decimal
from django.conf import settings

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from operations.ibor.services.fee_calculator import IborFeeCalculator
from operations.ibor.models.fee import IborFeeRule, IborFeeSchedule
from operations.ibor.services.fee_calculator import CalculatedFeeLine

# Create a mock calculation
# We need CalculatedFeeLine for COMM and LEVY
# And then an SST rule that uses them.

# Mocking the rule
# This is tricky because we need IborFeeRule instance.
# Let's try to fetch an existing one if possible, or create a mock.
# Fetching is better to see the actual config.

rule = IborFeeRule.objects.filter(charge_type_cd='VAT').first()
if not rule:
    print("VAT rule not found.")
else:
    print(f"VAT Rule: {rule}")
    print(f"Reference charge type: {rule.reference_charge_type_cd}")
    print(f"Calc method: {rule.calc_method}")
    print(f"Rate: {rule.rate}")

    # Simulate calculated lines
    comm_line = CalculatedFeeLine(sequence_no=10, charge_type_cd='COMM', description='COMM', rate=None, amount=Decimal('15.0000'), cost_ccy_id=1, reference_charge_type_cd='')
    levy_line = CalculatedFeeLine(sequence_no=30, charge_type_cd='LEVY', description='CDC Charges', rate=None, amount=Decimal('2.5000'), cost_ccy_id=1, reference_charge_type_cd='')
    
    calculated_lines = [comm_line, levy_line]
    
    # Simulate rule with correct charge types
    rule.reference_charge_type_cd = "COMM,LEVY"
    
    # Calculate base value for VAT rule
    base_value = IborFeeCalculator._get_cumulative_reference_base(rule, calculated_lines)
    print(f"Base value for VAT: {base_value}")
    
    amount = base_value * (rule.rate or Decimal('0'))
    print(f"Calculated amount: {amount}")

