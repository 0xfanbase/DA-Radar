# Case 1: Virtual-asset custody for private banking

*Fictional case. All people and firms are invented. Facts about Hong Kong rules are real and cited.*

## The situation

Harbourlight Bank is a fictional Hong Kong bank with a private bank for wealthy clients. Several clients already hold bitcoin and ether, two kinds of virtual asset (VA), with outside firms. They ask Harbourlight to hold these assets for them, next to their other investments. The head of private banking wants to launch a custody service within a year.

You lead digital-asset compliance. The chief executive asks you to bring three decisions to the executive committee: how to run the service, how to price it, and how to cover losses. Harbourlight is also a registered institution (RI), a bank registered with the Securities and Futures Commission (SFC) for securities business.

## Cast

- **You**: head of compliance, digital assets.
- **Ines Quaymark**: chief executive (CEO). She wants a clear yes or no by year end.
- **Tobias Lanternwick**: chief financial officer (CFO). He owns the profit and loss account (P&L), the record of income and costs.
- **Priya Harbourfen**: chief risk officer (CRO). She owns the bank's risk appetite.
- **Declan Tidemere**: head of private banking. His clients are asking for the service.
- **Kestrel Custody Tech**: a fictional vendor selling key-management systems.
- **The supervisor**: the bank's Hong Kong Monetary Authority (HKMA) case team. It acts only as the HKMA's published expectations describe.

## Exhibit A: the rules that apply

- A bank that plans to offer digital-asset custody should discuss it with the HKMA first. It should show the HKMA that it meets the expected standards [S:ed61d7c335e7, Implementation, p.2].
- The bank should keep client assets, and the wallet addresses that hold them, apart from its own. This protects them from the bank's creditors [S:ce05e67bcdce, para 6 and fn 6].
- For client virtual assets, the HKMA expects 98% to sit in cold storage, meaning with keys kept offline [S:ce05e67bcdce, para 11(l) and fn 8].
- The bank should generate, store and back up private keys (the secret codes that move assets) in Hong Kong [S:ce05e67bcdce, para 11(b)].
- The bank is expected to be liable for client losses from incidents it causes. It should hold adequate financial resources, which may include insurance [S:ce05e67bcdce, para 11(n)].
- The bank should disclose its fees, and any insurance or compensation cover, clearly to clients [S:ce05e67bcdce, para 20].
- The bank may delegate VA custody only to another bank, an SFC-licensed platform, or a licensed stablecoin issuer for its own coins [S:ce05e67bcdce, para 14]. Final responsibility stays with the bank [S:ce05e67bcdce, para 19].
- Under a planned law, banks that safekeep client VA keys would need a custody licence or registration [S:f41a543388bc, para 35(b)]. Existing providers would get no automatic right to keep operating. The regime would apply in full from its start date [S:f41a543388bc, para 48].

## Act 1: Build, delegate or wait?

Kestrel offers a full key-management system with hardware in Hong Kong. Declan prefers speed and suggests using a licensed trading platform as custodian. Priya asks whether the bank is ready for either.

### Decision 1: How does Harbourlight run custody?

- **A.** Build: run its own key systems and cold storage, using Kestrel's technology.
- **B.** Delegate: appoint an SFC-licensed platform or another bank to hold the assets, with Harbourlight as the client-facing custodian.
- **C.** Wait: offer VA exposure only through exchange-traded funds (ETFs) for now, and revisit custody once the new licensing law is clearer.

### Discussion notes

- **Trade-offs.** Option A gives control of the client experience and the key controls, at a high fixed cost. Option B is faster and uses less capital spending, but adds a dependency on another firm. Option C avoids new custody risk and leaves client demand unmet.
- **What the rules require.** Delegation of VA custody is limited to three kinds of firm [S:ce05e67bcdce, para 14]. The bank keeps ultimate responsibility for anything it delegates [S:ce05e67bcdce, para 19]. Before choosing a delegate, the bank is expected to check its finances, skills, technology and ability to meet the standards [S:ce05e67bcdce, para 15]. Under the planned licence, faster approval is to go to banks that the HKMA has already assessed for custody and that already provide it [S:f41a543388bc, para 51].
- **What a strong answer covers.** It compares the fixed cost of Option A with the fee paid to a delegate in Option B. It asks who holds the keys in each option, since the planned licence turns on key safekeeping. It sets out the timing risk for Option C if the licence starts before the bank is ready.
- **Traps.** Treating delegation as handing over the risk. Assuming existing providers get an automatic right to carry on once the regime starts. The conclusions rule out such automatic permission [S:f41a543388bc, para 48]. Forgetting that providers who skip the pre-application step may face business disruption [S:f41a543388bc, para 52].

## Act 2: What to charge

Tobias asks for a pricing model before any spending. Declan fears that a visible fee may send clients back to outside firms. Kestrel's pricing is a yearly licence plus a charge per wallet.

### Decision 2: How does Harbourlight price custody?

- **A.** A yearly fee as a percentage of assets held, with a monthly minimum per client.
- **B.** No custody fee. The bank earns from dealing, lending and other services to the same clients.
- **C.** A lower percentage fee, plus separate charges for each withdrawal or transfer out.

### Discussion notes

- **Trade-offs.** Option A matches income to the value held and to the cost of safekeeping. Option B makes custody a feature, not a profit line, and depends on other income from the same clients. Option C keeps the headline fee low and charges for the costliest actions.
- **What the rules require.** Fees and costs of custody belong in the client disclosure [S:ce05e67bcdce, para 20]. Before a client buys VA-related products, such as VA funds, the bank should check the client's knowledge of virtual assets [S:8a016a912528, para 6.2]. Institutional and qualified corporate professional investors are exempt from this test [S:8a016a912528, para 6.2]. Each regulated activity needs at least two executive officers approved in writing by the HKMA [S:8934af8cc884, para 2.2.4].
- **What a strong answer covers.** It sets the fee against a full cost base: keys, monitoring, audit and insurance. It tests Option B by listing the other income that custody makes possible. It checks whether charges in Option C are clear enough for clients to compare.
- **Traps.** Pricing only against fund fees. China Asset Management (Hong Kong) published a key facts statement in April 2026 for its Hong Kong ether fund [I:ee50e4efff6f, PDF p.11]. It reported that the fund pays up to 1% of fund value a year for custody and administration together [I:ee50e4efff6f, PDF p.11]. That fee covers fund services as well, so it is not a private-bank price [I:ee50e4efff6f, PDF p.11]. Another trap is ignoring the round-the-clock security monitoring the HKMA expects [S:ce05e67bcdce, para 23].

## Act 3: Covering losses

Priya asks what happens if a hacker drains a wallet. Tobias asks how much capital the service uses. Kestrel says insurers will quote only after a security review.

### Decision 3: How does Harbourlight cover potential losses?

- **A.** Buy insurance to cover a set share of client assets, higher for online (hot) wallets than for cold storage.
- **B.** Self-insure: set aside the bank's own financial resources to cover losses, with no outside policy.
- **C.** Mix: insurance for hot wallets, and the bank's own resources for cold storage.

### Discussion notes

- **Trade-offs.** Option A moves part of the loss to an insurer, for a yearly premium. Option B avoids premiums but keeps the whole loss with the bank. Option C spends premiums where the risk of theft is higher.
- **What the rules require.** The bank is expected to be liable for losses it causes and to have adequate financial resources, which may include insurance [S:ce05e67bcdce, para 11(n)]. That paragraph sets no fixed share of cover [S:ce05e67bcdce, para 11(n)]. Planned capital floors for new custodians leave banks out, because HKMA capital rules already apply [S:f41a543388bc, paras 41-42]. Rules applying the Basel standard for banks' cryptoasset exposures have been in force in Hong Kong since 1 January 2026 [S:100b982aadca, p.90]. They amended the banking capital, disclosure and exposure-limits rules [S:100b982aadca, p.90].
- **What a strong answer covers.** It separates client assets from the bank's own positions, because custody standards cover assets held for clients, not the bank's own [S:ed61d7c335e7, fn 1, p.1]. It checks whether any bank-owned VA position arises, such as for settlement. It explains the cover levels to clients, as the disclosure standard expects [S:ce05e67bcdce, para 20].
- **Traps.** Copying a fund's cover level without checking the source. A Bosera Asset Management (International) prospectus for two Hong Kong funds, from March 2026, reported the cover its sub-custodian must keep [I:d81073907a14, PDF p.118]. The cover is 50% of client virtual assets kept offline (cold) and 100% of those held online or elsewhere [I:d81073907a14, PDF p.118]. That is one firm's contract, not an HKMA standard.

## Exhibit B: illustrative P&L

Year-three view of Harbourlight's custody service under each Act 1 option, in HK$ millions. The numbers are invented to show the shape of each P&L. They are not estimates of any market or firm.

| Line (HK$ million, year 3) | A: Build | B: Delegate | C: Wait (ETFs only) |
|---|---|---|---|
| Custody fees from clients | 10 | 10 | 0 |
| Other income from the same clients | 5 | 5 | 2 |
| Fee paid to delegate custodian | 0 | -5 | 0 |
| Technology, keys and monitoring | -6 | -1 | 0 |
| Insurance and loss provisions | -2 | -1 | 0 |
| Compliance and control staff | -3 | -2 | -1 |
| Net contribution | 4 | 6 | 1 |

*(illustrative)*

## What this case teaches

- Custody is a control business first. In Exhibit B, most costs come from key safety, monitoring and loss cover.
- Delegation changes costs, not responsibility. The bank still answers for the delegate [S:ce05e67bcdce, para 19].
- Pricing either covers the full cost base or rests on other income from the same clients.
- Loss cover is a choice about who bears a hack: the insurer, the bank or both.
- The planned custody licence shapes timing for every option [S:f41a543388bc, paras 35(b), 48].

## Modules to revisit

- Business line: Virtual-asset custody.
- Business line: Virtual-asset distribution and brokerage.
- Module C3: Custody of digital assets and key management.
- Module C1: Selling, dealing and advising on virtual assets.
- Module D1: Capital and prudential treatment of cryptoassets.
- Module F2: How regulation writes the P&L.
- Module F5b: Running the business: operations and control.

*For general information only. Not legal or regulatory advice. Always check the official source.*
