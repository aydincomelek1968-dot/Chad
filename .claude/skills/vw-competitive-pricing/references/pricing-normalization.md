# Pricing Normalization

Dealer websites display pricing in whatever ladder makes their number look best.
Normalization is what turns five incomparable advertised prices into one honest
comparison. Get this wrong and every downstream conclusion inherits the error.

## The components, and why they are not interchangeable

| Component | What it is | Who gets it | Costs us gross? |
|---|---|---|---|
| **MSRP** | Factory sticker | — | — |
| **Dealer add-ons** | Accessories / addendum above MSRP | — | No (adds gross) |
| **Dealer discount** | Money the store gives up | Everyone | **Yes** |
| **Universal incentive** | VW cash available to all | Everyone | No |
| **Conditional incentive** | Military, grad, loyalty, conquest, finance | **A minority** | No |
| **Doc / dealer fees** | Added to the deal | Everyone | No |
| **Advertised price** | The headline number | — | — |

Two distinctions carry the whole analysis:

**Dealer discount vs. manufacturer money.** Only the dealer discount costs the
store gross profit. It is the only lever management controls. A competitor whose
advertised price is $1,500 lower purely because they display VW's cash more
prominently is not out-discounting anyone. Recommendations are therefore expressed
in *dealer discount*, not total off MSRP — otherwise a store congratulates itself
for "giving" $4,000 when $1,500 was VW's and $600 was a fee.

**Universal vs. conditional.** A conditional rebate is real money to the buyer who
qualifies and zero to everyone else. Stacking three of them produces an advertised
price almost no one can actually transact at. Matching that number with real dealer
discount hands away gross to beat a price that was never truly available.

## The comparable price

The figure every cross-dealer comparison uses:

```
comparable_price = advertised_price − doc_fee          (conditional rebates excluded)
```

Conditional incentives are excluded because they are not available to the shopper
you are competing for. Fees are excluded because sites disagree on whether to
include them, and that disagreement alone creates a several-hundred-dollar phantom
gap. Flip with `--include-fees` if the market convention shifts.

And the reconciliation check, which is how we know the ladder was parsed correctly
rather than merely parsed:

```
MSRP + doc_fee − dealer_discount − universal_incentive = advertised_price
```

Verified against 24/24 live Camelback units. A record that fails this is reported,
not trusted — a mis-parsed ladder produces a number that looks exactly like a real
price.

## Verified site field mappings

### Dealer.com (Camelback, Chapman alt domain)

Pricing arrives as `pricing.dprice[]`, an ordered ladder. The `type` / `typeClass`
codes are the discriminator — labels alone are unreliable:

| `typeClass` | `type` | Meaning | Bucket |
|---|---|---|---|
| `msrp` | `MIDDLE` | MSRP | MSRP |
| `ABCRule` | `-` | "Dealer Discount" (`isDiscount: true`) | **Dealer discount** |
| `totalFees` | `MIDDLE` | Doc fee | Fees |
| `SICRule` | `SICI` | "Offers" | **Universal incentive** |
| `SIFRule` | `SIF` | "Price" (`isFinalPrice: true`) | Advertised price |
| `SICCRule` | `SICCI` | "Conditional Offers" | **Conditional incentive** |
| `askingPrice` | `TOTAL` | "Dealer Added Optional Accessories" | Add-ons |

Conditional rows sit *below* the final price in the ladder — the site is disclosing
them correctly. The analytical error is ours if we roll them up.

Observed live example (2026 Jetta 1.5T Sport, stock 26V438):

```
MSRP                      $26,876
Dealer Discount          − $1,362      <- the only line that costs gross
Doc Fee                  +   $599
Offers (universal)       − $1,500
Price                     $24,613      <- includes the doc fee
Conditional Offers         $1,500      (2 rows, below the line)
Dealer Added Accessories   $1,538
```

True dealer discount is **$1,362 / 5.07%**. A naive read of "up to $4,400 off"
overstates the store's actual aggression by more than 3×.

### Fox Dealer (Chapman)

The pricing block names its components explicitly:

| Field | Bucket |
|---|---|
| `msrp` | MSRP |
| `markupsTotal` | Dealer add-ons / addendum |
| `discountsTotal` | Dealer discount |
| `rebatesEveryoneTotal` | Universal incentive |
| `rebatesAppliedTotal` | All rebates applied |
| `docFee` | Fees |

Conditional incentive is `rebatesAppliedTotal − rebatesEveryoneTotal` — this
platform helpfully draws the universal/conditional line for us. `isCourtesy` flags
service loaners, which must be excluded from new retail comparisons.

### JSON-LD fallback

Gives identity and `offers.price` only. A dealer collected this way has price data
but **no discount breakdown** — say so rather than inferring a discount by
subtracting a guessed MSRP.

## Dealer add-ons

Accessories above MSRP inflate the base a discount is measured against, so a store
can show a bigger discount % off a number the factory never set. Every Camelback
unit observed carried $1,538 in add-ons. Where present:

- Compute discount % off **factory MSRP**, not MSRP + addendum.
- Note the add-on load per dealer — a store with heavy add-ons and a large headline
  discount may be net *more* expensive than a store with neither.

## Fine print worth reading

- Prices "including all applicable rebates" that assume every conditional stacks.
- Finance-contingent pricing (must finance through VW Credit).
- Trade-assist cash requiring a qualifying trade.
- Prices excluding destination — a ~$1,300 swing on its own.
- Expired or about-to-expire incentive windows.
- In-transit units advertised alongside on-ground stock.
