# Case 4: The night the hot wallet emptied

*Fictional case. All people and firms are invented. Facts about Hong Kong rules are real and cited.*

## The situation

Lanternway Exchange Limited is a fictional virtual asset trading platform (VATP) licensed by the Securities and Futures Commission (SFC). A virtual asset is a digital token, such as a cryptocurrency. You joined Lanternway as chief operating officer (COO) a year ago.

At 3am on a Saturday, monitoring flags large transfers out of one hot wallet (a wallet whose keys are online). Within 40 minutes the wallet is empty. The loss is tokens worth about HK$80 million (illustrative). Early signs point to malicious code in wallet software supplied by a vendor. The cold wallets (keys kept offline) look untouched. Clients wake up to the news in a few hours.

## Cast

- **Silas Emberquay, chief executive (CEO).** Wants to protect clients and the licence, in that order.
- **Oriel Saltmarch, chief financial officer (CFO).** Holds the cash, the insurance policy and the set-aside funds.
- **Kit Larkquay, Manager-in-Charge of information technology.** The senior manager in charge of technology. Leads the technical response.
- **Rhona Kelpwick, head of compliance.** Owns contact with the SFC case team.
- **Quillgate Wallet Systems.** The fictional vendor whose software was compromised.
- **Seawhistle Bank.** The fictional Hong Kong bank that holds Lanternway's client money.
- **The supervisor.** The SFC case team. It acts only as its published guidelines and circulars say.
- **You.** COO, running the response.

## Exhibit A: the rules that apply

As of 25 Sep 2026. "The Guidelines" means the SFC's Guidelines for VATP operators.

- A platform should hold 98% of clients' virtual assets offline, to limit losses from hacking. [S:f1bbafccd556, para 10.6(c)] The SFC may allow limited exceptions case by case. [S:f1bbafccd556, para 10.6(c)]
- A platform should hold an SFC-approved compensation arrangement. [S:f1bbafccd556, para 10.22] It should cover potential loss of 50% of client assets in cold storage and 100% of those in hot and other storage. [S:f1bbafccd556, para 10.22] The cover can be insurance, set-aside funds or assets, or a bank guarantee. [S:f1bbafccd556, para 10.22]
- A platform should tell clients how it will compensate them if assets are lost through hacking. [S:f1bbafccd556, para 10.19(c)]
- If a material system failure occurs, a platform should fix it promptly. [S:f1bbafccd556, para 12.20] It should also tell clients, as soon as it can, what happens to their open orders, deposits and withdrawals. [S:f1bbafccd556, para 12.20]
- A platform should notify the SFC immediately of material failures in its custody and other core systems. [S:f1bbafccd556, para 16.7(b)-(c)] It should send an incident report without undue delay. [S:f1bbafccd556, para 16.7, Note]
- Licensed firms should promptly tell the SFC about material cybersecurity incidents. [S:a4929c8f9f3e, para 18]
- The Manager-in-Charge of information technology and other senior managers bear ultimate responsibility for cyber risk. [S:a4929c8f9f3e, para 3]
- A platform should have controls and resources that can reasonably protect clients and assets from losses through theft, fraud and other dishonesty. [S:f1bbafccd556, para 11.10]
- Client money should sit in segregated accounts at a Hong Kong authorized institution (a bank) or an approved overseas bank. [S:f1bbafccd556, para 10.11(a)]

## Act 1: The first three hours

Kit has isolated the affected wallet. He is not yet sure whether other hot wallets are safe. Silas asks whether to keep the platform open while the facts come in.

### Decision 1: What does Lanternway do with its services before markets open?

- **A.** Suspend all deposits and withdrawals for every token, but keep trading open.
- **B.** Suspend only the affected blockchain's wallet and keep everything else running.
- **C.** Suspend trading, deposits and withdrawals until the root cause is known.

### Discussion notes

- Trade-offs. Option A limits outflows but traps client assets on the platform. Option B keeps the business running if the attack is truly contained. Option C is the most cautious and the most costly to clients who need to trade.
- What the rules require. The SFC says firms should consider pre-planned ways to block malicious activity, isolate systems and restrict access fast [S:a4929c8f9f3e, para 15]. The Guidelines expect immediate notice to the SFC of material custody system failures [S:f1bbafccd556, para 16.7(b)-(c)].
- The Guidelines expect clients to hear what happens to their open orders, deposits and withdrawals [S:f1bbafccd556, para 12.20]. The contingency plan is to include trained staff to answer clients and regulators [S:f1bbafccd556, para 12.18(c)].
- A strong answer separates what is known from what is not. It names who approves each step and when the next update goes out (concept).
- A strong answer also calls Seawhistle Bank early. A withdrawal wave hits the client money accounts first (concept).
- Trap: waiting for full facts before telling the supervisor. The SFC expects prompt notice of material cyber incidents [S:a4929c8f9f3e, para 18].
- Trap: a client message that promises an outcome the firm cannot yet confirm (concept).

## Act 2: Making clients whole

By Sunday the loss is confirmed at one hot wallet. The cold wallets are intact. Oriel has three funding sources: the insurance policy, funds set aside on trust, and Lanternway's own liquid assets. The insurer says its assessment will take weeks.

### Decision 2: How does Lanternway restore affected client balances?

- **A.** Restore every affected balance now from set-aside funds and own assets, then claim from the insurer.
- **B.** Restore balances in stages as the insurer pays each part of the claim.
- **C.** Restore balances now, and refill hot wallets from cold storage so withdrawals can restart the same day.

### Discussion notes

- Trade-offs. Option A settles clients fast but drains the company's liquid assets. Option B protects cash but leaves clients waiting. Option C restores service fastest but moves more assets out of cold storage.
- What the rules require. The compensation arrangement should cover potential loss of 100% of client assets in hot storage [S:f1bbafccd556, para 10.22]. The Guidelines expect a platform to have told clients how it will compensate them for hacking losses [S:f1bbafccd556, para 10.19(c)].
- Cash matters too. A platform should keep liquid assets in Hong Kong equal to at least 12 months of operating costs [S:f1bbafccd556, para 6.1]. Paying out from own funds reduces that buffer (concept).
- Cover after the payout. The Guidelines expect a platform to check daily that its cover still matches client assets [S:f1bbafccd556, para 10.23]. If a shortfall looks set to persist, the Guidelines expect it to notify the SFC and fix it promptly [S:f1bbafccd556, para 10.24].
- Cold storage. The Guidelines expect a platform to keep moves out of the main cold wallet to a minimum [S:f1bbafccd556, para 10.6(d)].
- A strong answer ties the choice to the Guidelines' expectation that controls protect clients from losses caused by theft and fraud [S:f1bbafccd556, para 11.10].
- Trap: counting the insurance claim as cash before the insurer agrees to pay (concept).

## Act 3: Rebuilding with the supervisor

Two weeks on, the root cause is clear. An attacker placed malicious code in Quillgate's software, which changed what signers saw on screen. The SFC had warned about this pattern at overseas platforms. [S:562c0f8addce, p.1] The supervisor is now reviewing Lanternway's report. Silas asks you to set the path back to normal.

### Decision 3: How does Lanternway rebuild its wallet set-up?

- **A.** Keep Quillgate, with patched code and an independent review.
- **B.** Replace Quillgate with a new vendor.
- **C.** Build transaction signing in-house.

### Discussion notes

- Trade-offs. Option A is quickest but keeps the same supplier risk. Option B brings new integration risk. Option C gives the most control but needs scarce staff and time.
- What the rules require. The Guidelines expect a strict independent cyber assessment before any platform change goes live [S:f1bbafccd556, para 12.13]. It covers wallet security and a source code review of the custody system [S:f1bbafccd556, para 12.13].
- Change notice. The Guidelines expect a platform to tell the SFC before making technology changes that might affect operations [S:f1bbafccd556, para 16.7(a)].
- Supplier risk. The SFC asks firms to strengthen reviews of the third parties that support critical systems [S:a4929c8f9f3e, para 13].
- The incident report. The Guidelines list what it covers, including root cause, clients affected and steps to prevent a repeat [S:f1bbafccd556, Schedule 3, section 2].
- Ownership. The Guidelines expect senior management to take full responsibility for the platform's controls [S:f1bbafccd556, para 11.1].
- A strong answer shows the supervisor a dated plan, named owners and evidence of testing (concept).
- Trap: blaming the vendor in public. Responsibility for the controls stays with Lanternway's own senior managers [S:a4929c8f9f3e, para 3].

## Exhibit B: illustrative P&L

Lanternway's year, in HK$ million. All numbers are invented to show the shape. (illustrative)

| Line | Plan before the incident | Year with the incident |
|---|---|---|
| Trading fees | 300 | 240 |
| Custody and other fees | 40 | 35 |
| Staff and technology | -180 | -200 |
| Insurance premium | -20 | -30 |
| Incident costs (forensics, legal, client support) | 0 | -25 |
| Client losses paid, net of insurance recovery | 0 | -10 |
| Profit before tax | 140 | 10 |

*(illustrative) Round numbers only. Profit and loss (P&L) shows income less costs for the year.*

## What this case teaches

- Speed with regulators is part of the response. The SFC expects prompt notice of material cyber incidents. [S:a4929c8f9f3e, para 18]
- The 98% cold storage standard limits the damage, but not to zero. [S:f1bbafccd556, para 10.6(c)]
- Compensation cover is a real funding plan. The order in which each source pays out shapes the response (concept).
- Vendor risk sits with the platform. The SFC listed a compromised third-party wallet solution among the weaknesses behind overseas losses. [S:562c0f8addce, p.1]

## Modules to revisit

- Module [C7 VATP counterparties and the SFC platform regime](#m-C7)
- Module [D4 Cyber, fraud and technology risk](#m-D4)
- Module [C6 Financing, shared order books and client withdrawals](#m-C6)
- Module [C1 Selling, dealing and advising on virtual assets](#m-C1)
- Business line: [Virtual-asset dealing](#b-va-dealing)
- Business line: [Banking the digital-asset industry](#b-banking-da-industry)

*For general information only. Not legal or regulatory advice. Always check the official source.*
