### This app dividend into four layers and below apps:
___
#### Project name: **Core**
___
#### Layer Structure
* **refdata**
  * masters
  * taxonomy
  * instruments
* **governance**
  * crm
  * Policies
* **operation**
  * portfolio
  * ibor
  * abor
  * oms
* **reporting**
  * risk 
  * performance

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

#### We have created the below dirs to seed data papulation 
    

    The adventage to having below files, that we can run them directly in termianl like manage.py seed_master

* master/management/commands/seed_master
* instrument/management/commands/seed_instrument
* taxonomy/management/commands/seed_taxonomy
    
    