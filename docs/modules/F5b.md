# F5b Running the business: operations and control

This module is about day-to-day running: people, vendors, systems, incidents and exits. After reading, you can sketch a target operating model for a digital-asset line. A target operating model is the planned mix of teams, processes, systems and partners that delivers a service. You can also tie each part of it to the official rule that shapes it. The Hong Kong Monetary Authority (HKMA) supervises banks. The Securities and Futures Commission (SFC) sets conduct rules for securities and virtual-asset (VA) business.

## In 60 seconds

Accountability comes first. A registered institution (RI) is a bank the SFC has registered for securities business. It needs at least two executive officers (EOs) for each regulated activity, each with HKMA consent. [S:8934af8cc884, para 2.2.4] At least one must be available at all times. [S:8934af8cc884, para 4.3.9]

Vendors do not take the risk away. As a general principle, a bank may outsource VA custody only to certain regulated firms. [S:ce05e67bcdce, para 14] Ultimate responsibility for outsourced custody stays with the bank. [S:ce05e67bcdce, para 19]

Custody runs around the clock. The HKMA expects security monitoring 24/7, including holidays. [S:ce05e67bcdce, para 23] It also expects drills for emergency and business continuity scenarios. [S:ce05e67bcdce, para 5]

Incidents have reporting duties. An RI should tell the SFC and the HKMA about a material failure of systems and controls. [S:8934af8cc884, para 5.6] The HKMA expects a custody bank to be liable to clients for losses from incidents it causes. [S:ce05e67bcdce, para 11(n)]

Exits need planning. An RI must give at least seven business days' notice before it stops a regulated activity. [S:8934af8cc884, para 5.1]

## Key facts

**Target operating model and accountability**
- A bank offering custody should set written roles, responsibilities and reporting lines. [S:ce05e67bcdce, para 4] It should also manage conflicts of interest across its activities and affiliates. [S:ce05e67bcdce, para 4]
- It should give custody enough people and expertise for governance, operations and risk management. [S:ce05e67bcdce, para 2]
- An RI should name the person principally responsible for its whole business and for each key business or function. [S:17871e6ed4e0, Q1/A1] Changes should reach both regulators within 14 days. [S:17871e6ed4e0, Q14/A14]
- Where a function is outsourced, a member of the RI's own management should be named as responsible for it, not the outside provider. [S:17871e6ed4e0, Q9/A9]
- Under the Banking Ordinance, the people in charge of computer systems, compliance and internal audit count as managers. [S:7e7494d80711, para 2.2.1] A bank must notify the HKMA when it appoints them. [S:17871e6ed4e0, Q1/A1]
- Under the planned custodian regime, staff with direct access to private keys or authority to approve transfers are expected to need a licence, or to be registered as relevant individuals in a bank. [S:f41a543388bc, para 25] Private keys are the secret codes that move digital assets.

**Vendors and outsourcing**
- As a general principle, a bank may outsource VA custody only to three kinds of firm. [S:ce05e67bcdce, para 14] They are another bank or a local bank's subsidiary, an SFC-licensed platform, or an HKMA-licensed stablecoin issuer for its own coins with HKMA consent. [S:ce05e67bcdce, para 14]
- Due diligence on a custody provider includes independent code review and the provider's software release process. [S:ce05e67bcdce, para 15] Ongoing reviews test its security, incident reporting and disaster recovery. [S:ce05e67bcdce, para 15]
- The bank should have the technical skill to judge a provider's solution and spot any single point of failure. [S:ce05e67bcdce, para 16] A single point of failure is one part whose loss stops everything.
- Continuity plans should cover disruption at the custody provider, with regular end-to-end rehearsals. [S:ce05e67bcdce, para 17] The usual controls for traditional outsourcing still apply. [S:ce05e67bcdce, para 18]
- A bank should check that an outsourced provider is competent enough to meet the agreed service levels. [S:6ea96c41cccc, para 2.9] It should monitor the provider using staff with the right expertise. [S:6ea96c41cccc, para 2.9]
- The HKMA has an outsourcing module in its Supervisory Policy Manual (SPM). It expects digital banks to discuss material outsourcing in advance and show they meet that module. [S:5422156398b3, para 23]
- For outsourced distributed ledger technology (DLT) work, an HKMA study suggests vetting vendors at every stage and lining up backup vendors. [S:e0fd558b3dbc, Section 4.2.4, item 1, p.48] The study is research, not a rule.
- A licensed stablecoin issuer should notify the HKMA promptly before starting a material third-party arrangement. [S:240be6833157, para 6.6.11] Examples include reserve custody, coin distribution and critical technology services. [S:240be6833157, para 6.6.11]
- The SFC expects its licensed firms to strengthen oversight of third-party providers against cyberattacks that use artificial intelligence. [S:a4929c8f9f3e, para 13] This affects a bank if its group includes an SFC-licensed firm.

**24/7 resilience**
- A custody bank should test system changes before deployment. [S:ce05e67bcdce, para 23] Its monitoring should cover vendors, blockchain protocols, encryption and common software libraries. [S:ce05e67bcdce, para 24]
- Monitoring should also track major industry incidents and publicly known security weaknesses. [S:ce05e67bcdce, para 25]
- Where DLT supports critical functions, continuity plans should test cyberattacks, key loss or theft, and forks (splits of a blockchain). [S:1884530ff235, Annex, item 10]
- A licensed stablecoin issuer should set the minimum service it must keep during a disruption. [S:240be6833157, para 6.8.12] It should also set a maximum tolerable downtime and recovery targets for systems and data. [S:240be6833157, para 6.8.12]
- The issuer should avoid relying too heavily on third parties for continuity support. [S:240be6833157, para 6.8.16]
- The HKMA plans 24/7 operation for EnsembleTX (its tokenised deposit settlement pilot) by around end-2026. [S:ef3648ff1610, para 50]

**Incidents and crisis**
- A custody bank should have written procedures to handle security alerts and incidents by severity level. [S:ce05e67bcdce, para 10]
- An RI should tell both the SFC and the HKMA about any event caused by a material failure in its systems and controls. [S:8934af8cc884, para 5.6] This applies even if the failure happened at a group entity outside Hong Kong. [S:8934af8cc884, para 5.6]
- Under the SFC Code of Conduct, an RI is expected to report any actual or suspected material breach to both regulators immediately. [S:8934af8cc884, para 5.6]
- SFC-licensed firms should promptly notify the SFC of material cyber incidents and attacks. [S:a4929c8f9f3e, para 18] This matters if the bank's group has such a firm.
- For SFC-licensed internet brokers and VA service providers (not banks directly), the SFC expects hacking incidents to be reported to it immediately, with a root-cause review. [S:724f4d9f786e, para 18] The SFC says it will hold such a firm accountable for client losses if it fails to stop large-scale unauthorised trades after hacking. [S:724f4d9f786e, para 25]
- A licensed stablecoin issuer should keep forensic evidence and review root causes after an incident. [S:240be6833157, para 6.8.8] Delaying redemptions beyond one business day needs the Monetary Authority's written consent. [S:240be6833157, para 6.8.21]
- If staff incompetence causes significant losses or bad publicity, a bank should tell the HKMA in good time. [S:6ea96c41cccc, para 4.1.3]

**Product approval**
- A bank should assess money-laundering and terrorist-financing risks before launching a new product, practice or technology. [S:7bfdad704174, paras 2.10-2.11]
- A bank should not launch a new product unless staff understand it, its market and its rules. [S:6ea96c41cccc, para 3.7.4]
- Before launching custody, a bank should complete a full risk assessment under board and senior management oversight. [S:ce05e67bcdce, para 1]
- Before offering staking, a bank should have policies, systems and controls in place and discuss them with the HKMA. [S:4641e6c404d2, Implementation section] Staking means locking up tokens to help run a blockchain, for rewards.

**Key performance indicators (KPIs) and board reporting**
- A key performance indicator is a measure used to track results. The HKMA's DLT study suggests metrics such as task completion time, productivity and cost savings. [S:e0fd558b3dbc, Section 4.2.1, pp.44-45]
- The board and senior management should understand firm-wide risks, especially from new or complex activities such as crypto. [S:349a543ae2f0, para 4.2.8]
- Manager appraisals should not give undue weight to profit or market share. [S:7e7494d80711, para 4.1.7] They should also weigh compliance with internal rules. [S:7e7494d80711, para 4.1.7]
- A licensed stablecoin issuer's board should approve its incident, continuity and exit plans. [S:240be6833157, para 6.8.18] Test results should go to the board and senior management. [S:240be6833157, para 6.8.19]
- A custody bank should run independent audits of its systems, controls and compliance. [S:ce05e67bcdce, para 23]
- The HKMA finalised revised banking return templates for cryptoasset exposures in November 2025. [S:30b686db29f9, Banking returns section]

**Wind-down**
- An RI must give the SFC and the HKMA at least seven business days' notice before it stops a regulated activity. [S:8934af8cc884, para 5.1]
- A custody bank should hold client assets in separate accounts, beyond the reach of its creditors in insolvency. [S:ce05e67bcdce, para 6 and fn 6]
- A bank offering staking should keep control of the means to unstake client assets, such as withdrawal keys. [S:4641e6c404d2, p.2, section A]
- A licensed stablecoin issuer's exit plan should cover selling reserve assets, taking redemption claims and paying holders. [S:240be6833157, para 6.8.17] It should also cover arrangements with third parties. [S:240be6833157, para 6.8.17]

**Organisation and talent**
- The board should set the direction for staff development. [S:6ea96c41cccc, para 2.4] Senior management should propose talent plans with measurable targets, which the board reviews at least once a year. [S:6ea96c41cccc, para 2.4]
- Banks should assess how technology changes job roles and keep a long-term reskilling plan. [S:6ea96c41cccc, para 4.2.2]
- Custody staff need training at the start and on an ongoing basis. [S:ce05e67bcdce, para 3] Staff who sign transactions need in-depth training on checks and exceptions. [S:ce05e67bcdce, para 3]
- The HKMA's DLT study says firms may consider a dedicated central DLT team mixing technology and business staff. [S:e0fd558b3dbc, Section 4.2.2, p.45]
- In SFC-licensed firms, cyber risk rests in the end with senior management. That includes the manager in charge of information technology. [S:a4929c8f9f3e, para 3]

## Industry view

- Morgan McKinley (a recruitment firm) publishes a salary survey. Its 2026 Hong Kong guide estimates a median of HK$120,000 a month for a head of middle and back office in banking. [I:fd149f7bf877, 'Banking & Financial Services Salaries in Hong Kong SAR' table, Middle & Back Office rows] The same guide gives a median of HK$35,000 a month for a custody role in operations. It does not say whether this covers digital-asset custody. [I:fd149f7bf877, 'Banking & Financial Services Salaries in Hong Kong SAR' table, Operations rows]
- KPMG (an accounting and advisory firm) published its Hong Kong Banking Report in 2026. Based on the published results of the Hong Kong banks it surveyed, it reported that their total staff costs rose 6.7% in 2025. [I:1dfc7a0205ff, Performance section, p.8]
- In the same report's commentary (opinion, not a measured figure), KPMG lists the risks digital assets add. They include custody, cyber, legal, financial crime and governance risk. [I:1dfc7a0205ff, pp.42-43]
- In a section on artificial intelligence, the same commentary says banks have focused on what they outsource, less on what their vendors outsource in turn. [I:1dfc7a0205ff, p.48] KPMG sells advisory services to banks.

## How it works commercially

- **Operating model layers.** A service needs a front office, operations, technology, control functions and partners. Each layer has an owner and a cost. (concept)
- **Fixed cost of round-the-clock service.** A 24/7 service needs shift cover, on-call engineers and weekend controls. Much of this cost stays the same at low and high volume. (concept)
- **Vendor economics.** Outsourcing turns fixed cost into a fee, but it adds oversight cost, exit cost and concentration risk. Concentration risk is the danger of many services relying on one provider. (concept)
- **Cost of incidents.** An incident costs client compensation, staff time, remediation, regulatory attention and lost business. Prevention spending is easier to justify when these costs are counted. (concept)
- **Leading and lagging measures.** Lagging measures show results after the fact, such as revenue or losses. Leading measures warn early, such as open audit issues or failed reconciliations. (concept)

> **Analysis — not official**
> **Question:** For a 24/7 custody service, which parts could a bank run in-house and which could a partner run?
> **How to think about it:**
> - Which functions are critical? Examples: key management, transaction signing, monitoring, reconciliation and client service.
> - For each, who holds the keys and who can move assets? Outsourcing of VA custody is, as a general principle, limited to certain regulated firms [S:ce05e67bcdce, para 14].
> - What does oversight cost? It includes provider reviews, rehearsals and skilled monitoring staff [S:ce05e67bcdce, paras 15, 17].
> - What does exit cost? That covers moving client assets if the provider fails or the contract ends.
> - A round example: if shift cover needs six people per role (illustrative), fixed cost is most of the total at low volume.
> **What it depends on:** client balances; the hours when clients trade; available talent; provider quality and concentration; final custodian rules.
> **Official signposts:** licensing of key staff under the custodian regime [S:f41a543388bc, para 25]; EnsembleTX 24/7 operation [S:ef3648ff1610, para 50]; HKMA expectations for 24/7 security monitoring [S:ce05e67bcdce, para 23].
> **What this is not:** Not a forecast, not advice, and not the regulator's view.

> **Analysis — not official**
> **Question:** What could a one-page board report for a digital-asset line show?
> **How to think about it:**
> - Results: client balances, revenue, contribution and capital used.
> - Risk: incidents by severity [S:ce05e67bcdce, para 10], reconciliation breaks (records that do not match), open audit points, vendor issues.
> - Readiness: continuity drill results [S:ce05e67bcdce, para 5], staff training [S:ce05e67bcdce, para 3], regulatory notices due.
> - Balance: pair each profit measure with a control measure, in line with HKMA views on appraisals [S:7e7494d80711, para 4.1.7].
> **What it depends on:** the line's size; how much risk the board accepts; data quality; how often the board meets.
> **Official signposts:** the board plan circular of 9 March 2026 [S:3ec5b269b5dc, letter body, p.2]; board understanding of crypto risk [S:349a543ae2f0, para 4.2.8].
> **What this is not:** Not a forecast, not advice, and not the regulator's view.

## Talking points

**To the CEO**
- Outsourced custody still leaves ultimate responsibility with us. [S:ce05e67bcdce, para 19]
- The HKMA expects custody security monitoring 24/7, holidays included. [S:ce05e67bcdce, para 23]

**To the CCO**
- A material failure of systems and controls triggers notice to both the SFC and the HKMA. [S:8934af8cc884, para 5.6]
- We need at least two EOs for each regulated activity, with one always available. [S:8934af8cc884, paras 2.2.4, 4.3.9]

**To business heads**
- The HKMA expects us not to launch until staff understand the product, its market and its rules. [S:6ea96c41cccc, para 3.7.4]
- Stopping a regulated activity needs at least seven business days' notice. [S:8934af8cc884, para 5.1]

**To Risk / CRO**
- The HKMA expects us, as custodian, to be liable for client losses from incidents we cause. [S:ce05e67bcdce, para 11(n)]
- Where DLT supports critical functions, continuity plans should test key loss, cyberattacks and forks. [S:1884530ff235, Annex, item 10]

## Common mix-ups

- **Myth:** A vendor can be named as responsible for an outsourced function. **Fact:** The HKMA expects a member of the RI's management to be named instead. [S:17871e6ed4e0, Q9/A9]
- **Myth:** Any reputable custody provider will do. **Fact:** As a general principle, VA custody can go only to three kinds of firm. [S:ce05e67bcdce, para 14] They are another bank or a local bank's subsidiary, an SFC-licensed platform, or an HKMA-licensed stablecoin issuer for its own coins with HKMA consent. [S:ce05e67bcdce, para 14]
- **Myth:** Continuity plans can ignore the provider. **Fact:** The HKMA expects plans to cover provider disruption, with end-to-end rehearsals. [S:ce05e67bcdce, para 17]
- **Myth:** Only cyber incidents need reporting. **Fact:** An RI also notifies regulators of material failures of systems and controls, even at overseas group entities. [S:8934af8cc884, para 5.6]
- **Myth:** Profit is the main test of a good manager. **Fact:** The HKMA says appraisals should also weigh compliance. [S:7e7494d80711, para 4.1.7]

## Read these first

1. **Updated Guidance on Expected Standards on Provision of Custodial Services for Digital Assets** — HKMA, 27 May 2026. Read paras 1-5, 10, 14-19 and 23-25. https://brdr.hkma.gov.hk/eng/doc-ldg/docId/getPdf/20260527-7-EN/20260527-7-EN.pdf
2. **SPM SB-1 Supervision of Regulated Activities of SFC-Registered AIs** (SB = supervision of banks' securities business; AIs = authorized institutions) — HKMA, 12 September 2025. Read paras 2.2.4, 4.3.9, 5.1 and 5.6. https://brdr.hkma.gov.hk/eng/doc-ldg/docId/getPdf/20250909-3-EN/SB-1.PDF
3. **Management Accountability at Registered Institutions – FAQs** — HKMA, 16 October 2017. Read Q1, Q9 and Q14. https://brdr.hkma.gov.hk/eng/doc-ldg/docId/getPdf/20171016-2-EN/20171016-2-EN.pdf
4. **SPM CG-6 Competence and Ethical Behaviour** (CG = corporate governance) — HKMA, 23 May 2024. Read paras 2.4, 2.9, 3.7.4 and 4.1-4.2. https://brdr.hkma.gov.hk/eng/doc-ldg/docId/getPdf/20240523-2-EN/20240523-2-EN.pdf
5. **Guideline on Supervision of Licensed Stablecoin Issuers** — HKMA, 1 August 2025. Read paras 6.6.11 and 6.8.8-6.8.21 as a model for continuity and exit planning. https://www.hkma.gov.hk/media/eng/doc/key-functions/ifc/stablecoin-issuers/Guideline_on_supervision_of_licensed_stablecoin_issuers_eng.pdf

## Open items

- The HKMA's general modules on outsourcing, operational resilience and technology risk are not among the sources reviewed. Only DLT-, custody- and stablecoin-specific text is covered here.
- No HKMA-wide incident reporting timeline for bank digital-asset incidents was found in the sources reviewed.
- No official source gives staffing levels or costs for a 24/7 digital-asset operation.
- The custodian regime's staff licensing rules are conclusions, not yet law. [S:f41a543388bc, para 25]

## Related modules

B2, B3, C3, D2, D4, F2, F5a, F6. Business lines: [Virtual-asset custody](#b-custody); [Infrastructure as a service](#b-infrastructure-service); [Staking services](#b-staking). Project: [Project Ensemble](#p-ensemble). Cases: [Case 1: Virtual-asset custody for private banking](#case-1-va-custody-private-banking); [Case 4: The night the hot wallet emptied](#case-4-vatp-incident); [Case 6: Stopping a product](#case-6-stopping-a-product).

*For general information only. Not legal or regulatory advice. Always check the official source.*
