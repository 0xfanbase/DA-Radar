# Collateral and tokenised financing

In this line a bank lends against digital or tokenised assets, or helps clients use such assets as collateral (security for a loan or trade). (concept)

## At a glance

| Item | Detail |
|---|---|
| Bank role | Lender; repo counterparty; collateral agent; custodian of pledged assets |
| Client segments | Private banking, corporate, institutional |
| Value chain | Finance, Hold, Settle and pay |
| Regulatory gate | A bank registered with the Securities and Futures Commission (SFC) for virtual-asset (VA) dealing may offer VA financing. It is expected to meet the standards in a Hong Kong Monetary Authority (HKMA) circular [S:e64b7b0267b2, p.2] |
| Status as of 25 Sep 2026 | In force [S:e64b7b0267b2, p.2] |
| Related modules | C6, D1, C5, C3, E2 |
| Related cases | none |

## What the bank does

- Lends to its securities margin clients for VA trading [S:e64b7b0267b2, items (1)-(2), p.2]. If it relies on VA collateral, the HKMA says it should accept only bitcoin, ether and stablecoins from HKMA-licensed issuers [S:e64b7b0267b2, item (4), pp.3-4].
- Applies a haircut (a cut to the collateral's value before lending against it). The HKMA says the haircut on bitcoin and ether should be 60% or more [S:e64b7b0267b2, fn 5, p.4].
- Values VA collateral at prices on the platform that executes the client's orders, as the HKMA generally expects [S:e64b7b0267b2, item (6), p.4].
- Keeps pledged virtual assets (VAs) untouched. The bank should not reuse or repledge VA collateral, except to enforce it on default [S:e64b7b0267b2, item (7)(c), p.5].
- Holds or lends against tokenised traditional assets, such as tokenised bonds. (concept) In the banking book, these Group 1a (tokenised traditional) exposures generally follow the capital rules for the underlying asset [S:5d0c13e09312, para 8.7.1].
- Meets tokens used as margin in the market. The SFC's February 2026 high-level framework covers perpetual contracts (futures with no expiry date) on trading platforms. It says their margin should be fiat money, or stablecoins or tokenised deposits regulated by the HKMA [S:49f642bdee28, Margin arrangements section].

## Revenue levers

- A lender earns interest on the loan above its own funding cost. This gap is called the net interest margin. (concept)
- A repo (a sale and agreed buy-back of securities that works like a secured loan) earns a small spread for the cash lender. (concept)
- A collateral agent earns fees for holding, valuing and moving pledged assets between parties. (concept)

## Cost and capital drivers

- Capital: the Banking (Capital) Rules do not recognise VA collateral. So a loan secured only by VAs must be treated as a clean (unsecured) loan [S:e64b7b0267b2, item (9), p.5].
- Capital: Group 2b cryptoassets get the HKMA's conservative treatment, a 1,250% risk weight [S:5d845665ba83, para 4.3.2]. In effect, the bank holds capital equal to the whole exposure. (concept)
- Classification: a bank taking on a new type of cryptoasset must notify the HKMA [S:b7d630146e6c, para 2.1.2]. It must treat the asset as Group 2b until the HKMA agrees its class [S:b7d630146e6c, para 2.1.2].
- Liquidity: the HKMA says fiat loans secured on cryptoassets should be treated like similar deals under the liquidity rules [S:69600121310a, Annex 3, para 10].
- Liquidity: a category 1 bank must keep a minimum liquidity coverage ratio, a short-term liquidity test [S:69600121310a, para 3.1.2]. It may count a tokenised asset as a high-quality liquid asset only if it is an eligible Group 1a token [S:69600121310a, Annex 3, para 1].
- Controls: the bank should monitor VA collateral volatility in real time and act promptly [S:e64b7b0267b2, item (5)(b), p.4].

## Official signals

- The 2026 Policy Address states that the HKMA will test tokenised Exchange Fund Bills by the end of 2026 [S:ef3648ff1610, para 35(ii)]. These are short-term debt papers the HKMA issues. The stated aim is to help banks use more than HK$1.3 trillion of these bills efficiently, round the clock [S:ef3648ff1610, para 35(ii)].
- The Central Moneymarkets Unit (CMU), the Hong Kong system where bonds are held and settled, held about HK$5 trillion at end-September 2025 [S:9c8855ec55a1, About CMU OmniClear]. Its operator is CMU OmniClear (set up in October 2024). CMU OmniClear offers collateral management among its services [S:9c8855ec55a1, About CMU OmniClear].
- The Project Ensemble Sandbox listed repo and treasury management under its liquidity theme [S:5f8362ecd97f, p.1].
- In April 2026 the HKMA licensed two stablecoin issuers. Its summary of their plans lists collateral management in tokenised asset trading as one use of their coins [S:193316443831, Use cases section].
- Hong Kong Exchanges and Clearing (HKEX) aims to pilot tokenised warehouse-receipt financing with chosen banks in 2027 [S:ef3648ff1610, para 46(iv)].
- In June 2026 the HKMA clarified a Group 1 condition for tokenised traditional assets on public blockchains. The condition can now also be met where a financial market regulator supervises the tokenisation business [S:dca53ff0a62c, p.1].

## Industry benchmarks

- A 2025 report by the Global Financial Markets Association (GFMA) and other trade bodies (global, modelled) cites a study by Boston Consulting Group (BCG) and Ripple [I:7f93581e44fe, PDF p.10]. That modelled estimate says a bank running about US$100 billion of daily repo could save US$150–300 million a year [I:7f93581e44fe, PDF p.10].
- The GFMA's 2025 case studies (global, operator-reported) put one ledger-based repo platform at about US$1.5 trillion a month in late 2024 [I:04d8f959d7a3, p.14].
- The International Organization of Securities Commissions (IOSCO) published a report in 2025 (global, survey). In its 2024 survey of members, 91% of respondents reported nil or very limited commercial tokenisation use in their markets [I:5f69773bc91f, p.13, section 3.B.1].

## Analysis

> **Analysis — not official**
> **Question:** Where does tokenised collateral create value for a bank: in new lending, or in cheaper use of assets it already holds?
> **How to think about it:**
> - Lending view: VA-backed loans carry no capital relief for the collateral [S:e64b7b0267b2, item (9), p.5]. The income then has to cover the full capital charge on an unsecured loan.
> - Balance-sheet view: tokenised high-quality assets could move faster between desks and counterparties. In this view, value would come from smaller idle buffers, not from new fees.
> - Service view: holding and valuing collateral for others earns fees without the bank lending its own money.
> **What it depends on:** test design; counterparty acceptance of tokens; legal certainty on pledges; capital treatment.
> **Official signposts:** tokenised Exchange Fund Bill tests [S:ef3648ff1610, para 35(ii)]; the HKEX warehouse-receipt pilot [S:ef3648ff1610, para 46(iv)]; the April 2026 capital-rule proposal on cryptoassets and cash items [S:1e9b351e81e7, Item 45].
> **What this is not:** Not a forecast, not advice, and not the regulator's view.

## Read next

- Module C6: Financing, shared order books and client withdrawals.
- Module D1: Capital and prudential treatment of cryptoassets.
- Module C5: Tokenisation: tokenised products, deposits and bonds.
- Module C3: Custody of digital assets and key management.
- Module E2: Wholesale money, CBDC (central bank digital currency) and cross-border projects.
- Project profile: CMU OmniClear digital asset platform and tokenised Exchange Fund Bills.
- Project profile: Project Ensemble.
- Business line: Virtual-asset financing and margin.

*For general information only. Not legal or regulatory advice. Always check the official source.*
