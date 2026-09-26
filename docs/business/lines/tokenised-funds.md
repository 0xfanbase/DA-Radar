# Tokenised funds and money market fund settlement

In this line a bank sells, trades, settles or holds fund units kept as tokens on a shared ledger, such as a tokenised money market fund (MMF) (concept).

## At a glance

| Item | Detail |
|---|---|
| Bank role | Distributor; connecting broker; settlement bank; custodian |
| Client segments | Retail, private banking, corporate, institutional |
| Value chain | Distribute, Trade, Hold, Settle and pay |
| Regulatory gate | Sellers should be firms that the Securities and Futures Commission (SFC) has licensed or registered, applying normal suitability checks [S:58ea8520974d, para 18]. A bank should tell both the SFC and the Hong Kong Monetary Authority (HKMA) in advance [S:a9aa06fbcc12, para 35 and fn 8] |
| Status as of 25 Sep 2026 | In force [S:58ea8520974d, para 5] |
| Related modules | C5, C2, C7, E2 |
| Related cases | 5-board-strategic-plan |

## What the bank does

- Sells tokenised funds. The SFC expects sellers of tokenised SFC-authorised products to be licensed or registered firms [S:58ea8520974d, para 18]. They apply the usual client checks and suitability tests [S:58ea8520974d, para 18].
- Passes client orders to a licensed trading platform, as a "Connecting Broker" [S:a64e364fd912, para 13 and fn 4]. It should show a warning when the trade price strays far from the fund's value per unit, its net asset value (NAV) [S:a64e364fd912, para 13]. It should also tell those clients they can subscribe or redeem directly with the fund at NAV instead [S:a64e364fd912, paras 12(b) and 13].
- Settles fund trades with tokenised deposits (bank deposits recorded as tokens). The first focus of EnsembleTX (the HKMA's live tokenisation pilot) is tokenised deposits used in tokenised MMF trades [S:8b67e8dc510f, para 2].
- Accepts virtual assets (VAs) as payment for fund units. The SFC and HKMA do not treat this as a virtual-asset dealing service [S:b79266f3da51, para 7]. The bank should notify the SFC and the HKMA in advance [S:b79266f3da51, para 7(a)].
- Lends against the units. The HKMA says the rule barring client financing for virtual-asset (VA) purchases does not apply to buying tokenised products [S:e64b7b0267b2, fn 4, p.2].

## Revenue levers

- Distribution fees: the fund manager often shares part of its yearly management fee with the selling bank (concept).
- Brokerage: the bank can charge a commission on each secondary trade it passes to a platform (concept).
- Market making: the SFC expects product providers to try to have at least one market maker per product [S:a64e364fd912, para 15(a)]. A market maker earns the gap between its buying and selling prices (concept).
- Settlement balances: cash held as tokenised deposits for fund trades can add to the bank's deposit base (concept).
- Custody: a bank can charge a yearly fee for holding tokens for clients (concept).

## Cost and capital drivers

- Price data: platforms and Connecting Brokers should show an indicative NAV, typically updated at least every 15 seconds in trading hours [S:a64e364fd912, para 20(b)].
- Risk disclosure: they should explain liquidity and price-gap risks and get client confirmation [S:a64e364fd912, para 20(c)].
- Notifications: a bank planning over-the-counter (off-platform) secondary trading should notify and discuss its plan with the SFC before it starts [S:a64e364fd912, para 27]. It should also notify the HKMA [S:a64e364fd912, fn 13].
- Product oversight: the fund manager stays responsible for the token set-up, even if it outsources parts [S:58ea8520974d, para 10]. It should not use public blockchains that anyone can join without extra controls [S:58ea8520974d, para 13].
- Systems: linking token wallets to fund records, payment systems and client reports is a fixed build cost (concept).

## Official signals

- SFC-authorised tokenised retail money market funds (MMFs) held HK$8.66 billion at end-2025, up 14% on the quarter [S:c28638fc5ccc, para 4 and Note 3].
- In March 2026 the public in Hong Kong could buy 13 tokenised products [S:bbd10edd41cf, para 3]. Their tokenised classes held about HK$10.7 billion [S:bbd10edd41cf, para 3]. That was about seven times the level a year earlier [S:bbd10edd41cf, para 3].
- The SFC authorised three retail tokenised MMFs in early 2025 [S:16feb657aaec, Reply (2), para 3]. The Government called them the first in Asia-Pacific [S:16feb657aaec, Reply (2), para 3].
- The SFC stated that the first products under its April 2026 trading framework are expected to be tokenised MMFs [S:bbd10edd41cf, para 6]. It will review how they operate before it considers a wider product range [S:bbd10edd41cf, para 6].
- The 2026 Policy Address says the SFC will promote regulated stablecoins for settling tokenised MMFs [S:ef3648ff1610, para 49(iii)].
- The same Policy Address says the HKMA plans central bank digital currency settlement and round-the-clock operation under EnsembleTX by around end-2026 [S:ef3648ff1610, para 50].

## Industry benchmarks

- The Bank for International Settlements (BIS), 2025 staff bulletin (global, reported): tokenised MMFs on public blockchains held almost US$9 billion by end-October 2025 [I:c1c1a36b00a2, PDF p.6]. That was up from about US$770 million at end-2023 [I:c1c1a36b00a2, PDF p.6].
- The same BIS bulletin notes that some institutional-only funds set a minimum investment of US$5 million [I:c1c1a36b00a2, PDF p.6].
- RWA.xyz, a data provider for real-world assets (RWA), showed about US$14.94 billion of tokenised US Treasury products on 26 September 2026 (global, reported, live data) [I:e258a28e08eb, Dashboard header, 'Distributed Value']. This covers tokenised Treasury bills, notes and bonds as well as MMFs.

## Analysis

> **Analysis — not official**
> **Question:** Is tokenised MMF work a distribution business, or a way to win settlement cash and deposits?
> **How to think about it:**
> - Distribution view: the bank gets a share of the fund's fees, as with ordinary units, plus brokerage on platform trades.
> - Settlement view: each subscription and redemption moves cash; tokenised deposits can keep that cash inside the bank.
> - Cost view: NAV price feeds, price-gap warnings and client confirmations are fixed costs spread over trading volume.
> - Example (illustrative): if the same client moves HK$10 million a month through the fund, the settlement cash can matter more than the fee share.
> **What it depends on:** growth of tokenised fund assets; whether stablecoins or tokenised deposits settle the trades; secondary trading volumes; fee sharing with fund managers.
> **Official signposts:** the SFC's review before widening the product range [S:bbd10edd41cf, para 6]; stablecoin settlement of tokenised MMFs [S:ef3648ff1610, para 49(iii)]; EnsembleTX round-the-clock operation [S:ef3648ff1610, para 50].
> **What this is not:** Not a forecast, not advice, and not the regulator's view.

## Read next

- Module [C5 Tokenisation: tokenised products, deposits and bonds](#m-C5)
- Module [C2 VA funds and ETFs](#m-C2) (ETFs: exchange-traded funds)
- Module [C7 VATP counterparties and the SFC platform regime](#m-C7) (VATP: virtual asset trading platform)
- Module [E2 Wholesale money, CBDC and cross-border projects](#m-E2) (CBDC: central bank digital currency)
- Project profile: [Project Ensemble](#p-ensemble)
- [Case 5: The board's strategic plan](#case-5-board-strategic-plan)
