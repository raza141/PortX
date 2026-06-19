# users/choices.py
# ─────────────────────────────────────────────────────
# All TextChoices for the users app.
# Import from here in models, forms, serializers, views.
# ─────────────────────────────────────────────────────

from django.db import models


class UserRole(models.TextChoices):
    CLIENT          = "client",          "Client / Investor"
    RM              = "rm",              "Relationship Manager"
    COMPLIANCE_L1   = "compliance_l1",   "Compliance Officer L1"
    SENIOR_MGMT     = "senior_mgmt",     "Senior Management"
    COMPLIANCE_FINAL= "compliance_final","Compliance Final Sign-off"
    ADMIN           = "admin",           "System Administrator"


class UserMarket(models.TextChoices):
    PSX   = "PSX",   "Pakistan Stock Exchange"
    US    = "US",    "US Equities"
    GCC   = "GCC",   "GCC Region"
    SARWA = "SARWA", "SARWA Platform"
    ALL   = "ALL",   "All Markets"

class DepartmentChoices(models.TextChoices):
    ASSET_MANAGEMENT = "asset_mgmt", "Asset Management"
    WEALTH_MANAGEMENT = "wealth_mgmt", "Wealth Management & RMs"
    COMPLIANCE_LEGAL = "compliance_legal", "Compliance & Legal"
    RISK_MANAGEMENT = "risk_mgmt", "Risk Management"
    OPERATIONS = "operations", "Operations & Settlements"
    FINANCE_ACCOUNTS = "finance_acc", "Finance & Accounts"
    RESEARCH_ANALYTICS = "research", "Investment Research & Analytics"
    TECHNOLOGY = "tech", "Technology & Systems"

class DesignationChoices(models.TextChoices):
    # Executive Management
    CEO = "ceo", "Chief Executive Officer"
    CIO = "cio", "Chief Investment Officer"
    CCO = "cco", "Chief Compliance Officer"

    # Investment & Portfolio Management
    PORTFOLIO_MANAGER = "portfolio_mgr", "Portfolio Manager"
    INVESTMENT_ANALYST = "analyst", "Investment Analyst"
    RESEARCH_HEAD = "research_head", "Head of Research"

    # Wealth, Client Relations & RMs
    WEALTH_MANAGER = "wealth_mgr", "Wealth Manager"
    SENIOR_RM = "senior_rm", "Senior Relationship Manager"
    RM = "rm", "Relationship Manager"

    # Control & Operations
    COMPLIANCE_OFFICER = "compliance_off", "Compliance Officer"
    RISK_OFFICER = "risk_off", "Risk Officer"
    OPERATIONS_ASSOC = "ops_assoc", "Operations Associate"