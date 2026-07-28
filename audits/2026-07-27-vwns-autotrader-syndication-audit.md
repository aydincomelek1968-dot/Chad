# Autotrader Syndication Gap Audit — VW North Scottsdale (Penske #182)

**Date:** 2026-07-27
**Claim under test:** The same defect found in our cars.com feed — Advertised Price pushed
instead of Lowest Price, hiding the factory Customer Bonus — is also present in our
Autotrader feed.

**Companion document:** `2026-07-27-vwns-carscom-syndication-audit.md` (cars.com channel).

---

## Verdict

**CONFIRMED — the same defect, on the same units, in the same direction.** Autotrader
publishes our pre-bonus advertised price and never applies the customer bonus. As on
cars.com, this is an exact arithmetic identity, not a sampled inference:

> **Autotrader displayed price = MSRP − Discount + $698 Dealer Fees**
> — true for **136 of 136** matched new units, zero exceptions.

**The dollar figure is different from cars.com, and lower — deliberately so.** Autotrader
displays a **"Dealer Fees Included"** badge under every price and its price convention
*includes* dealer fees. cars.com's convention *excludes* them. So the $698 is legitimate
on Autotrader and is **not** counted as a gap here. What remains is the suppressed bonus.

| Measure | Autotrader | cars.com (for contrast) |
|---|---|---|
| New VW units listed | **137** (136 matched + 1 stale) | 136 |
| Units where the identity holds | **136 / 136** | 136 / 136 |
| Units carrying a suppressed bonus | **128** | 128 |
| Units with no bonus (zero gap here) | **8** | 8 (carry $698 each) |
| **Total dollars hidden** | **$368,500** | $463,428 |
| Average gap per affected unit | **$2,879** | $3,407 |
| Price convention on fees | fees **included** (badged) | fees **excluded** |

The $94,928 difference between the two channels is exactly the $698 × 136 dealer-fee
component, which is a defect on cars.com and correct behaviour on Autotrader.

### Dollars hidden by model

| Model | Units | Hidden $ | Avg per unit |
|---|---|---|---|
| Atlas | 42 | $147,000 | $3,500 |
| Tiguan | 41 | $90,000 | $2,195 |
| Atlas Cross Sport | 12 | $42,000 | $3,500 |
| ID.4 | 7 | $42,000 | $6,000 |
| Jetta | 11 | $16,500 | $1,500 |
| Taos | 10 | $15,000 | $1,500 |
| Golf GTI | 6 | $9,000 | $1,500 |
| Jetta GLI | 4 | $7,000 | $1,750 |
| Golf R | 3 | $0 | $0 (no bonus on this model) |
| **Total** | **136** | **$368,500** | **$2,879** |

---

## The Autotrader-specific finding: our stated MSRP is wrong

This channel exposes something cars.com does not. Autotrader prints an **MSRP** next to
the price, and on our listings that number is frequently **not the manufacturer's MSRP**.

- On the **33** units carrying no dealer discount, Autotrader prints
  **MSRP = our real MSRP + $698** — for all 33, exactly. Example: an Atlas 2.0T SE whose
  factory MSRP is **$41,604** is published on Autotrader as **"MSRP $42,302."** The dealer
  fee has been folded into the manufacturer's suggested price.
- On the **64** units that do carry a discount, Autotrader prints the correct MSRP, but
  the **"Savings"** figure is understated by exactly $698, because the fee is netted
  against the discount before display. Verified on all 64:
  `Savings = Discount − $698` and `MSRP = our MSRP`, with no exceptions.

So on 97 of 136 units the published price stack misstates either MSRP or the discount.
Overstating MSRP is the more serious of the two: it is a manufacturer figure, not a
dealer figure, and a shopper cross-checking it against VW's own site will find it wrong.

## Competitors have the same fee behaviour — but not the same bonus behaviour

Two cross-channel checks confirm the fee convention rather than assuming it:

- **Larry H. Miller.** Their lowest comparable Tiguan is **$35,258 on cars.com** and
  **$35,807 on Autotrader** — a difference of exactly **$549**, their documentary fee,
  which they disclose verbatim on their own site. They exclude it on cars.com and include
  it on Autotrader, matching each platform's convention.
- **Chapman.** Their Autotrader price runs exactly **MSRP + $589** on every Tiguan
  observed — the same fee-inclusive structure with their own fee amount.

The distinguishing point is not the fee. It is that **our feed is the one suppressing a
live factory bonus**, on 128 units, inside the program window.

---

## Competitor SRP rank — Autotrader

Comparables matched by **closest MSRP**, because Autotrader collapses trim labels
(our "SE R-Line Black" and the 4MOTION variant both publish as "SE R-Line"), making the
label alone unusable. All prices below are fee-inclusive, per this platform's convention,
so no fee unwinding is applied — unlike the cars.com pass.

### Tiguan SE R-Line, FWD — 21 of our units

| As listed today | | If the feed were fixed | |
|---|---|---|---|
| Larry H. Miller | $35,807 | **VW North Scottsdale** | **$35,044** |
| Camelback | $37,378 | Larry H. Miller | $35,807 |
| **VW North Scottsdale** | **$37,544** | Camelback | $37,378 |
| Lunde's Peoria | $38,011 | Lunde's Peoria | $38,011 |
| Chapman | $40,196 | Chapman | $40,196 |

**Rank change: 3rd of 5 → 1st of 5.** Our comparable unit (MSRP $39,496) is within $213
of Larry Miller's (MSRP $39,709), so this is a like-for-like pairing.

### Atlas SE w/Technology, FWD — 13 of our units

| As listed today | | If the feed were fixed | |
|---|---|---|---|
| Lunde's Peoria | $45,333 | **VW North Scottsdale** | **$42,432** |
| Camelback | $45,838 | Lunde's Peoria | $45,333 |
| **VW North Scottsdale** | **$45,932** | Camelback | $45,838 |

**Rank change: 3rd of 3 (last) → 1st of 3.** The strongest comparison in the audit:
Lunde's comparable unit carries an **identical $47,834 MSRP** to ours, so the $599 we
currently trail them by is purely a function of the missing bonus. Applying it would put
us $2,901 clear of the field.

Larry H. Miller and Chapman had no Atlas at this configuration in the returned result
set, so this ranking is three-way rather than five-way.

### Atlas Cross Sport — not obtained

Autotrader has no `atlas-cross-sport` model slug and the model-filter fallback returned
unfiltered inventory, so competitor Cross Sport prices could not be read at audit
quality in this pass. **No Cross Sport ranking is reported for Autotrader.** Our own 12
Cross Sport units are fully covered in the dollar figures above ($42,000 hidden); only
the competitive comparison is missing. The cars.com pass ranked this model 4th → 3rd,
but those are cars.com prices and do not transfer.

---

## Evidence standard, and one material limitation

**Autotrader publishes no VIN anywhere.** Not on the search results page, and not on the
vehicle detail page — both were checked directly. This is the one respect in which this
audit is weaker than the cars.com audit, and it cannot be fixed from this access path.

The join is therefore **not by VIN**. It is by **advertised price**, corroborated by
**MSRP and Savings**, against the 161 live price stacks captured from our own site:

- **136 of 137** Autotrader listings match a computed advertised price
  (`MSRP − Discount + $698`) from our own site data. The match is exact, to the dollar.
- **97 of those 136** carry a second, independent confirmation: Autotrader's own MSRP
  and Savings values reconcile against the same site unit (64 via true MSRP + savings,
  33 via the MSRP + $698 overstatement).
- The **price multiset is identical to cars.com's** 136 prices — same units, same
  numbers, two independent channels.

Because MSRP is shared across same-configuration units, this establishes a
**unit-level correspondence, not a VIN-level one**. For a defect that is uniform across
the whole inventory the distinction does not change the totals, but it should be stated
rather than glossed.

### The one unmatched listing

One Autotrader listing — a **Tiguan SE R-Line at $38,073** (Autotrader MSRP $40,025,
savings $1,952, Deep Black Pearl, listing 781071327) — matches **no** current price on our
site. Its price implies a **$2,650 discount** on a $40,025-MSRP car; all four units at
that MSRP on our site now show a **$0 discount** and advertise at $40,723. The most
likely reading is a **stale Autotrader listing** carrying a discount that has since been
pulled. It is excluded from every figure above. Note this is a *second, separate*
syndication defect — a stale price — and it happens to run in the shopper's favour.

### Other checks

- Every price was read off a live page on 2026-07-27.
- The dealer-fee inclusion was confirmed from Autotrader's own **"Dealer Fees Included"**
  badge, observed on our listings and on Chapman's, Larry Miller's and Lunde's.
- Competitor rows were required to satisfy `PRICE = MSRP − SAVINGS` internally; rows that
  failed were re-read rather than used. Chapman's first read returned transposed
  price/MSRP columns and was re-queried before use.
- Our own site's price stacks reconcile 136/136 (`MSRP − Discount + Fees − Bonus =
  displayed bottom line`), as established in the cars.com audit.

## How the data was obtained

| Path | Target | Result |
|---|---|---|
| **WebFetch (server-side)** | autotrader.com dealer 46562864, all pages; 4 competitor dealers | **Worked.** The only viable path. Source of every Autotrader figure. |
| Stealth browser → mitmproxy → agent egress | autotrader.com | **502 at the egress gateway** — autotrader.com is not in this session's egress allowlist, so no browser path exists regardless of fingerprint quality. |
| Stealth browser | vwnorthscottsdale.com | **Worked** — source of our own price stacks (reused from the cars.com pass, same day). |
| WebFetch | Autotrader VDP (`/cars-for-sale/vehicle/<id>`) | Renders, but **exposes no VIN**. Confirms price, MSRP, savings and the "Dealer Fees Included" note. |

**Known read-path fragility.** Autotrader's `modelCodeList` parameter did not filter for
competitor dealers, and the markdown conversion transposed price/MSRP columns on one
dealer. Both were caught by the `PRICE = MSRP − SAVINGS` self-consistency check and
re-queried. Any future pass should keep that check as a gate.

## Recommended fix

**The same one-line remap fixes both channels, but they need different fee handling.**

1. **Map the Autotrader `price` field to the bonus-inclusive lowest price.** Recovers
   the full **$368,500**. This is the same field-mapping change already recommended for
   cars.com.
2. **Keep the $698 in the price for Autotrader — but stop folding it into MSRP.** The
   fee belongs in the price under Autotrader's convention; it does **not** belong in the
   MSRP field. Publishing MSRP + $698 as "MSRP" misstates a manufacturer figure on 33
   units today and understates disclosed savings on 64 more.
3. **Do not apply the cars.com fee fix here.** On cars.com the $698 must come *out* of
   the price field; on Autotrader it must stay *in*. A single global change would fix one
   channel and break the other.
4. **Investigate the stale $38,073 listing** as a separate feed-freshness issue.

**Verify after the next push** by re-reading the dealer inventory and confirming that
non-SEL Tiguans land $2,500 below `MSRP − Discount + $698`, and that the 33 no-discount
units publish MSRP without the $698 added.

**Time sensitivity.** The Tiguan Customer Bonus runs **Jul 1 – Aug 31, 2026**. Combined
with the cars.com channel, the same 128 units are being advertised above their real price
on both major third-party marketplaces simultaneously.
