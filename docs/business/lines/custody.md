# Virtual-asset custody

In this line a bank safekeeps clients' digital assets, such as virtual assets (VAs) and tokenised securities [S:ed61d7c335e7, fn 1, p.1]. It also guards the private keys (secret codes) that move them [S:ed61d7c335e7, fn 1, p.1].

## At a glance

| Item | Detail |
|---|---|
| Bank role | Custodian; custody delegate for funds and other firms |
| Client segments | Retail, private banking, institutional, fintechs |
| Value chain | Hold, Settle and pay |
| Regulatory gate | The Hong Kong Monetary Authority (HKMA) expects the bank to discuss plans with it first and show it meets the HKMA custody standards [S:ed61d7c335e7, Implementation, p.2] |
| Status as of 25 Sep 2026 | In force [S:ed61d7c335e7, Implementation, p.2] |
| Related modules | C3, C2, C1, D1, D4 |
| Related cases | 1-va-custody-private-banking |

## What the bank does

- Keeps client assets and wallet addresses apart from its own, as the HKMA expects, out of reach of the bank's creditors [S:ce05e67bcdce, para 6 and fn 6].
- Keeps 98% of client virtual assets (VA) in cold storage (keys held offline), as the HKMA expects [S:ce05e67bcdce, para 11(l) and fn 8].
- Creates, stores and backs up private keys for client VAs in Hong Kong, a control the HKMA generally requires [S:ce05e67bcdce, para 11(b)].
- Holds assets for funds. The Securities and Futures Commission (SFC) lets the trustee of a VA fund it authorises delegate VA custody to a bank that meets HKMA standards [S:c79c4686c5e0, para 20].
- Serves the clients of other banks, SFC-licensed firms and licensed platforms that keep assets in an account with it [S:ce05e67bcdce, fn 9].
- Sends assets to third parties for payments or client settlement, if effective controls are in place [S:ce05e67bcdce, para 11(m)].

## Revenue levers

- A custody fee is usually a yearly percentage of the value held, sometimes with a monthly minimum. (concept)
- Fund custody fees may be bundled with administration fees. The sub-custodian (a second custodian holding the assets for the main one) is then paid from that bundle. (concept)
- Staking (locking client VAs so they help run a blockchain, for a reward) is a further lever. The HKMA has issued separate guidance on staking from custody [S:ce05e67bcdce, para 26].
- Custody also anchors other income from the same client, such as dealing, fund servicing and lending. (concept)

## Cost and capital drivers

- Liability: the HKMA expects the bank to be liable for losses from incidents it causes [S:ce05e67bcdce, para 11(n)]. It should hold adequate financial resources, which may include insurance [S:ce05e67bcdce, para 11(n)].
- Operations: security monitoring should run around the clock [S:ce05e67bcdce, para 23]. Holdings should be checked client by client against records on the blockchain and in the bank's own books [S:ce05e67bcdce, para 21].
- Outsourcing: as a general principle, a bank may delegate VA custody only to three kinds of firm [S:ce05e67bcdce, para 14]. They are another bank or a local bank's subsidiary, an SFC-licensed platform, or an HKMA-licensed stablecoin issuer for its own coins with HKMA consent [S:ce05e67bcdce, para 14]. Final responsibility stays with the bank [S:ce05e67bcdce, para 19].
- New licence: banks that safekeep client VA keys would need a licence or registration under the planned regime [S:f41a543388bc, para 35(b)]. The Government and the SFC do not plan to treat existing VA custodians as licensed while they apply [S:f41a543388bc, para 48]. The regime takes full effect on its start date [S:f41a543388bc, para 48].
- Capital: banks are left out of the planned HK$10 million paid-up capital baseline, because HKMA capital rules already apply [S:f41a543388bc, paras 41-42].
- Technology: the SFC says its August 2025 platform custody standards will be core expectations for future custodians [S:562c0f8addce, p.2].

## Official signals

- The SFC listed 13 licensed VA trading platforms at its 29 May 2026 update [S:b14be2203d39, Licensed platforms table; Last update line].
- Hong Kong had 11 VA spot exchange-traded funds (ETFs) at end-2025, with a total market value of over HK$5.4 billion [S:c28638fc5ccc, para 4].
- The SFC and the Financial Services and the Treasury Bureau aim to put a custodian bill to the Legislative Council in 2026 [S:f41a543388bc, para 65].
- Banks the HKMA has already assessed, and that already provide VA custody, are to get faster approval [S:f41a543388bc, para 51].
- Under the planned dealing regime, the SFC will require VA dealers to use SFC-regulated custodians [S:6186c01c6649, para 26].
- The SFC plans to begin running a system to watch digital-asset custody in the second half of 2026 [S:ef3648ff1610, para 51(iii)].

## Industry benchmarks

- China Asset Management (Hong Kong) reported a fee in its April 2026 key facts statement (Hong Kong scope) [I:ee50e4efff6f, PDF p.11]. Its ether fund pays up to 1% a year for custody and admin [I:ee50e4efff6f, PDF p.11]. That fee includes the sub-custodian [I:ee50e4efff6f, PDF p.11].
- Bosera Asset Management (International) reported in a March 2026 Hong Kong fund prospectus the sub-custodian's loss cover [I:d81073907a14, PDF p.118]. Compensation or insurance covers 50% of client VAs in cold storage [I:d81073907a14, PDF p.118]. It is 100% for hot (online) and other storage [I:d81073907a14, PDF p.118].
- OSL Group Limited (OSL) reported custody income in its 2025 annual report (Hong Kong and global scope) [I:e2df03a8c8a6, PDF p.126, Note 5]. It was about HK$16.1 million in 2025, up from about HK$9.6 million in 2024 [I:e2df03a8c8a6, PDF p.126, Note 5].

## Analysis

> **Analysis — not official**
> **Question:** Is VA custody a fee business on its own, or mainly the base that lets other lines run?
> **How to think about it:**
> - Standalone view: income equals assets held times the fee rate. Costs for keys, monitoring, audit and insurance come first and are largely fixed.
> - Enabler view: count the dealing, fund, staking and settlement income that needs a custodian in place.
> - Build or delegate: own key systems differ from delegating to a licensed platform, where responsibility stays with the bank [S:ce05e67bcdce, para 19].
> **What it depends on:** client asset levels; fee pressure from fund issuers; insurance cost; the final custodian rules and their start date.
> **Official signposts:** the custodian bill target [S:f41a543388bc, para 65]; SFC work on flexible custody technology and storage ratios [S:f41a543388bc, para 38]; custodian use under the dealing regime [S:6186c01c6649, para 26].
> **What this is not:** Not a forecast, not advice, and not the regulator's view.

## Read next

- Module [C3 Custody of digital assets and key management](#m-C3)
- Module [C2 VA funds and ETFs](#m-C2)
- Module [D1 Capital and prudential treatment of cryptoassets](#m-D1)
- Project profile: [New VA licensing regimes: dealing, custody, advisory and management](#p-va-licensing-regimes)
- [Case 1: Virtual-asset custody for private banking](#case-1-va-custody-private-banking)
