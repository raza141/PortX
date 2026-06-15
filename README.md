### This app dividend into four layers and below apps:
___
#### Project name: **Core**
___
#### Layer Structure
* **refdata**
  * masters
  * taxonomy
  * instruments
___
* **governance**: (what is allowed & why)
  * crm
  * Policies
___
* **operation**: (what happened & booking)
  * portfolio
  * IBOR (Investment-focused (Market price, intraday, broader/granular views for performance/risk))
    * Trade blotter
    * Cash Ledger
    * lot (FIFO)
    * Valuation
    * Position (Snapshots)
  * ABOR (official accounting truth)
    * ABOR is accounting-focused (Market price, NAV, chart of acc, period close, reconciliations)
  * PBOR: IBOR plus more (Performance results + risk exposures + refernce/adjusted data)
  * CBOR
  * MBOR = IBOR + ABOR + CBOR + PBOR
  * OMS
___
* **reporting**: (official accounting truth)
  * risk (VaR, Exposures, ES)
  * performance (TWM/MWR, GIPS)
  * Statements
  * TAX (CGT Report, Withholding Summary)
___
#### Admin control: 

**Superuser** has access to all apps and their models using below credential 
* username: raza....
* password: Ahmed....11..22...33...@@
___
#### App Structure and details: 

**Masters App:**

    Masters = reference data that everything else depends on.
        1.Benchmark
        2. FeeSchedule
___
**CRM App:**

    CRM = Investor onboarding file
        1. Investor
    
    Why it matters
    This is our client record + compliance gate.

    Banks treat CRM as a separate domain because:
        it has workflow
        it has regulatory requirements
        it drives eligibility (“can trade or not”)
___

**Portfolio App:** Mandates, Accounts, Ownership structure
    
    This is where investment structure lives.
    1. Portfolio
    2. Accounts
    3. OwnershipStructure

    Why it matters
        This is the “investment book” part:
        a client can have multiple portfolios
        a portfolio can have multiple accounts
        an account can be linked to multiple portfolios (if you allow)
        So portfolio is about how holdings and trades are organized.

___

**Instruments App**: 
    
    This Table is used to map the securities
    1. Asset_class, Asset_sub_Class, Security_identifier, Security_lisiting, issuer and so on.. 
___

**Taxonomy App**: 
    
    This Table is used to map the local sector to GICS classification system.

* GICS edition 
* GICS SECTOR
* GICS INDUSTRY GROUP
* GICS INSUSTRIES
* GICS SUB INDUSTRY
* LOCAL SECTOR 
* LOCAL SECTOR TO GICS
____
##### Under Operation layer Ibor layer:
###### IBOR = Investment Book of Record
It answers (near real-time):
* What do I own? (positions, lots)
* What cash do I have? (settled vs pending)
* What’s my PnL? (realized/unrealized)
* What changed today? (blotter + cash movements + lot movements)

IBOR is driven by events: trades, corporate actions, fees, FX, cash movements.
___
#### We have created the below dirs to seed data papulation 
    

    The adventage to having below files, that we can run them directly in termianl like manage.py seed_master

* master/management/commands/seed_master
* instrument/management/commands/seed_instrument
* taxonomy/management/commands/seed_taxonomy
    
    ____
### How App flow will work:
Business flow (real world)

1. Investor onboarding → RM assigned
2. Create Mandate (contract container)
3. Create IPSVersion (policy snapshot; effective-dated)
4. Create Portfolio(s) (reporting books)
5. Create Account(s) at broker/custodian
6. Map Portfolio ↔ Account (which account funds/trades which portfolio)
___
### Then investing starts:

7. Funding / withdrawals hit cash ledger
8. Trades are booked (buy/sell)
9. IBOR booking engine creates/updates:
10. Position lots (for FIFO cost)
11. Cash ledger postings (settlement cash)
12. Position aggregates (optional table or computed)
13. Pricing/FX (later) → valuation, unrealized PnL 
14. Performance reporting (ABOR/GIPS layer) consumes IBOR outputs
___
### DB flow (DB language)

- Trades and cash events are fact tables 
- Lots and cash ledger are derived posting tables (booked results)
- Mapping tables resolve “what account belongs to what book”
- ***Use one schedule per broker + market + asset class + currency + side conte***