# Case 7: The single admin key

*Fictional case. All people and firms are invented. Facts about Hong Kong rules are real and cited.*

## The situation

Wrenhaven Bank is a fictional Hong Kong bank. It is a registered institution (RI), meaning a bank registered with the Securities and Futures Commission (SFC) for securities business. Moonvetch Money Limited is a fictional stablecoin issuer licensed by the Hong Kong Monetary Authority (HKMA). A stablecoin is a token meant to keep a steady value against a currency.

Moonvetch wants Wrenhaven to hold part of its reserves as deposits and to sell its coin to clients. You are head of compliance (digital assets). The chief executive (CEO) wants your sign-off within a month.

During due diligence, Wrenhaven pays an outside firm to review Moonvetch's token contract. A token contract is the program on the blockchain that creates and controls the coin. The review finds that one key can mint (create) coins, burn (destroy) them, freeze a holder's coins and pause all transfers. No timelock applies. A timelock is a built-in delay before an action takes effect.

## Cast

- **You.** Head of compliance (digital assets).
- **Hesper Wrenfold, chief executive (CEO).** Wants the deal signed this quarter.
- **Otto Brambleway, chief financial officer (CFO).** Owns the profit and loss (P&L) account, the record of income and costs.
- **Linnea Stoatmere, chief risk officer (CRO).** Owns operational and third-party risk.
- **Casimir Fernhollow, head of wealth.** Plans to sell the coin to wealth clients.
- **Moonvetch Money Limited.** The fictional licensed issuer.
- **Coppergill Code Review.** A fictional firm that reviews blockchain programs. It wrote the finding.
- **The supervisor.** The bank's HKMA case team. It acts only as the HKMA's published expectations describe.

## Exhibit A: the rules that apply

As of 25 Sep 2026. "Licensee" below means the licensed issuer.

- A licensee should document the design of all its coin's smart contracts, including token, proxy and multi-signature contracts, and whether they can be upgraded [S:240be6833157, para 6.5.2]. A smart contract is a program that runs on a blockchain.
- It should list every lifecycle operation. The list includes deploy, mint, burn, upgrade, pause, blacklist and freeze [S:240be6833157, para 6.5.3].
- High-risk operations should be built so no single party can carry them out alone, for example through multi-signature approval [S:240be6833157, para 6.5.3]. Multi-signature means several keys must approve one action.
- Where relevant, extra safeguards include velocity limits, minting only to whitelisted addresses, and timelocks on some operations [S:240be6833157, para 6.5.3]. A velocity limit caps how much can move in a set time.
- Duties should be split between authorised staff. No one person should have full control over role management, such as assigning roles or changing approval rules [S:240be6833157, para 6.5.4].
- A qualified outside firm should audit the smart contracts at least once a year. It should also audit them at each deployment, redeployment or upgrade [S:240be6833157, para 6.5.5].
- Keys used for deployment, upgrades, role management or large-scale minting and burning generally count as significant keys. They should meet higher security standards [S:240be6833157, para 6.5.7].
- Significant keys should be generated offline in an air-gapped setting, meaning one with no network link. The key ceremony should involve a minimal number of authorised staff [S:240be6833157, para 6.5.7(ii)].
- An issuer may freeze coins promptly when regulators or law enforcement ask, or a court orders it. The HKMA lists this as one possible measure [S:4d98c6a80b4d, para 5.10(c)]. After filing a suspicious transaction report, an issuer should review the client relationship and take suitable steps. Examples include freezing or burning coins when law enforcement asks [S:4d98c6a80b4d, para 8.6].
- An issuer should have procedures to tell the HKMA in good time when its incident response is, or is likely to be, triggered [S:240be6833157, para 6.8.20].
- Before launching virtual asset services, banks should discuss them with the HKMA and get its feedback on their controls [S:642680fa4467, AIs' VA-related proposals section, p.5].

## Act 1: The finding lands

Hesper wants to sign now and fix the contract later. Otto points out that the reserve deposits are a large new balance. Linnea asks who holds the single key today.

### Decision 1: What does Wrenhaven do with the finding before signing?

- **A.** Sign now, and record the finding as a follow-up for Moonvetch.
- **B.** Share the finding with Moonvetch and make a fix a condition before signing.
- **C.** Sign the deposit side only, and hold back distribution until the fix is verified.

### Discussion notes

- Trade-offs. Option A keeps the timetable but leaves a known gap open. Option B protects the bank but may cost the deal. Option C splits the risk, yet the deposits still depend on the same coin.
- What the rules say. The HKMA expects Moonvetch to design high-risk operations so no single party acts alone [S:240be6833157, para 6.5.3]. A strong answer asks how a single key that can mint, burn, freeze and pause fits that expectation (concept).
- The bank's own duty. The HKMA expects banks to assess risks before any virtual asset activity [S:642680fa4467, HKMA's Regulatory Approach section, pp.2-3]. A virtual asset service provider (VASP) is a firm offering virtual asset services, such as an issuer of virtual assets. A bank dealing with a VASP may need extra checks. These include understanding its business and assessing its anti-money laundering controls [S:642680fa4467, AML/CFT section (b), p.4].
- The issuer checks the bank too. Moonvetch should confirm its distributors are permitted offerors and should assess their controls [S:240be6833157, para 3.4.2]. Due diligence runs both ways (concept).
- A strong answer asks whether the design is already documented. The HKMA expects that record to exist [S:240be6833157, para 6.5.2].
- A strong answer keeps the finding in writing and routes it to the board (concept).
- Trap: reading a licence as proof that every control is in place (concept).

## Act 2: What to require

Moonvetch agrees to change its setup. Its team argues that freeze and burn powers serve lawful purposes. The HKMA's anti-money laundering (AML) guideline for issuers lists prompt freezing on law enforcement requests as one possible measure an issuer may use [S:4d98c6a80b4d, para 5.10(c)]. After a suspicious transaction report, it gives freezing or burning coins at law enforcement request as an example step [S:4d98c6a80b4d, para 8.6]. So the discussion turns to how the powers are controlled.

### Decision 2: Which controls does Wrenhaven require, and how does it verify them?

- **A.** Accept Moonvetch's written statement that controls now meet the guideline.
- **B.** Require multi-signature approval, role separation and timelocks, and verify with a new outside audit.
- **C.** Do option B, and also ask to observe evidence of the key ceremony and to test the pause procedure.

### Discussion notes

- Trade-offs. Option A is quick but gives little assurance. Option B adds cost and time. Option C gives the most comfort but asks more of Moonvetch.
- What the rules expect. High-risk operations should need more than one party [S:240be6833157, para 6.5.3]. Staff duties should be split, and no one person should have full control over role management [S:240be6833157, para 6.5.4].
- Timelocks and limits. The HKMA lists timelocks, velocity limits and whitelisted minting addresses as safeguards where relevant [S:240be6833157, para 6.5.3]. A strong answer asks which apply to which operation.
- A timelock can clash with urgency. The AML guideline for issuers speaks of freezing promptly on requests from regulators, law enforcement or courts [S:4d98c6a80b4d, para 5.10(c)]. A strong answer asks how Moonvetch balances a delay against that need (concept).
- Audits. Moonvetch should use a qualified firm at least yearly and at every upgrade [S:240be6833157, para 6.5.5]. Factors in judging that firm include size, expertise, track record and presence in Hong Kong [S:240be6833157, para 6.5.5].
- Keys. Upgrade and role keys generally count as significant keys [S:240be6833157, para 6.5.7]. They should be generated offline in an air-gapped setting [S:240be6833157, para 6.5.7(ii)].
- A strong answer turns each control into a contract term and a yearly evidence request (concept).
- Trap: checking the contract once and not after upgrades (concept).

## Act 3: The pause

Six months after launch, on a busy payment day, all transfers of the coin stop. Moonvetch confirms a pause was triggered. It does not yet know why. Casimir's clients are calling. Some need to pay suppliers today.

### Decision 3: How does Wrenhaven respond?

- **A.** Tell clients it is Moonvetch's issue and wait for news.
- **B.** Tell clients what is known and not known, log each request, and offer redemption through Moonvetch.
- **C.** Do option B, and also brief the supervisor on the bank's own exposure the same day.

### Discussion notes

- Trade-offs. Option A limits what the bank says but may harm trust. Option B takes staff time. Option C adds a supervisory contact while facts are still thin.
- The issuer's duties. Moonvetch should keep issuance, redemption and distribution orderly when normal operations break [S:240be6833157, para 6.8.5]. It should have procedures to tell the HKMA in good time when its incident response is, or is likely to be, triggered [S:240be6833157, para 6.8.20].
- Redemption timing. Valid redemption requests should be processed within one business day unless the HKMA approves otherwise [S:240be6833157, para 3.3.3]. Any delay beyond that should first have the HKMA's written consent [S:240be6833157, para 6.8.21].
- Evidence. Moonvetch should preserve forensic evidence and later find the root cause [S:240be6833157, para 6.8.8].
- The bank's side. Banks should manage and reduce the risks they identify [S:642680fa4467, HKMA's Regulatory Approach section, pp.2-3]. A strong answer checks the bank's own HKMA reporting duties rather than assuming the issuer's notice covers them (concept).
- Clients. When dealing in the coin, an RI should disclose how it keeps its value and how redemption works [S:a0bd48559762, para (5), p.5]. A strong answer checks that earlier disclosures match what clients now face (concept).
- Trap: promising clients a restart time the bank cannot control (concept).

## Exhibit B: illustrative P&L

Figures in HK$ million a year. All numbers are invented to show the shape, not real prices. (illustrative)

| Line | Sign now, fix later | Conditions and verification first |
|---|---|---|
| Net interest on reserve deposits | 20 | 16 |
| Distribution fees | 5 | 4 |
| Outside audit and technical review | -1 | -3 |
| Compliance and monitoring | -4 | -5 |
| Incident handling and client redress | -6 | -2 |
| Profit before tax | 14 | 10 |

*(illustrative) Round numbers only. Net interest means interest earned minus interest paid. The incident line shows the cost of one event, not a prediction.*

## What this case teaches

- A token contract's control design is part of partner due diligence (concept).
- The HKMA expects high-risk token operations to need more than one party [S:240be6833157, para 6.5.3].
- After a suspicious transaction report, the HKMA gives freezing or burning coins at law enforcement request as an example step [S:4d98c6a80b4d, para 8.6]. The design question is who can use such powers and how (concept).
- Contract audits are expected yearly and at every upgrade [S:240be6833157, para 6.5.5].
- In an incident, the bank's duties and the issuer's duties run side by side (concept).

## Modules to revisit

Module D3 covers anti-money laundering (AML) and counter-financing of terrorism (CFT) rules.

- Module [C4 Stablecoins](#m-C4)
- Module [C3 Custody of digital assets and key management](#m-C3)
- Module [D4 Cyber, fraud and technology risk](#m-D4)
- Module [B3 Governance, risk and technology expectations](#m-B3)
- Module [D3 AML/CFT for digital assets at a bank](#m-D3)
- Business line: [Stablecoin roles for banks](#b-stablecoin-roles)

*For general information only. Not legal or regulatory advice. Always check the official source.*
