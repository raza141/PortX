# refdata/masters/choices.py

from django.db import models


class VenueChoices(models.TextChoices):
    EXCHANGE = "EXCHANGE", "Exchange"
    PLATFORM = "PLATFORM", "Platform"

class PlatformStatus(models.TextChoices):
    ACTIVE = "ACT", "Active"
    INACTIVE = "INA", "Inactive"


class CounterpartyType(models.TextChoices):
    BANK = "BANK", "Bank"
    BROKER_DEALER = "BROKER_DEALER", "Broker / Dealer"
    CUSTODIAN = "CUSTODIAN", "Custodian"
    OTC_DEALER = "OTC_DEALER", "OTC Dealer"
    OTHER = "OTHER", "Other"


class CounterpartyStatus(models.TextChoices):
    ACTIVE = "ACT", "Active"
    INACTIVE = "INA", "Inactive"


class ExecutionVenueType(models.TextChoices):
    EXCHANGE = "EXCHANGE", "Exchange"
    PLATFORM = "PLATFORM", "Platform"
    COUNTERPARTY = "COUNTERPARTY", "Counterparty"
    OTC = "OTC", "OTC"
    INTERNAL = "INTERNAL", "Internal"


class ExecutionVenueStatus(models.TextChoices):
    ACTIVE = "ACT", "Active"
    INACTIVE = "INA", "Inactive"