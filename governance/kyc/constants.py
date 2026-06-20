"""
governance/kyc/constants.py

Non-enum constants for the KYC app. Magic numbers/strings live here, never
scattered through services or views.
"""

# Application-number format: {MARKET}-KYC-{YEAR}-{SEQUENCE:06d}
APPLICATION_NUMBER_TEMPLATE = "{market}-KYC-{year}-{sequence:06d}"
APPLICATION_NUMBER_SEQUENCE_WIDTH = 6
APPLICATION_NUMBER_INFIX = "KYC"

# Joint holders — Phase 1 business cap: principal + up to 4 additional = 5 total.
# The child-table design imposes no structural cap; raising this needs no migration.
MAX_TOTAL_HOLDERS = 5
MAX_ADDITIONAL_JOINT_HOLDERS = MAX_TOTAL_HOLDERS - 1

# Share-percentage validation tolerance (principal + joint holders must total 100).
SHARE_TOTAL = 100
SHARE_TOLERANCE = 0.01

# Wizard sections (used by section_completion + the AJAX progress indicator).
SECTION_PERSONAL = "personal"
SECTION_RESIDENCE = "residence"
SECTION_SOURCE_OF_WEALTH = "source_of_wealth"
SECTION_REQUIREMENTS = "requirements"

WIZARD_SECTIONS = (
    SECTION_PERSONAL,
    SECTION_RESIDENCE,
    SECTION_SOURCE_OF_WEALTH,
    SECTION_REQUIREMENTS,
)