# Analysis Playbook

The scripts produce arithmetic. This file is the judgment layer — where the numbers
become a pricing decision. This is the part that earns the analysis its keep.

## Contents

1. Competitive position
2. Inventory pressure
3. Reading competitor strategy
4. The three price points
5. Attack / Match / Hold / Clear
6. Gross-profit recovery
7. Ranking market-share opportunities
8. Sanity checks before publishing

---

## 1. Competitive position

Classification uses the **comparable price gap on like trim** — what a
cross-shopper actually sees — with dealer discount % as the cross-dealer
normalizer so trim mix doesn't masquerade as pricing difference.

| Position | Test | Read |
|---|---|---|
| **Market Leader** | at or within $150 of the lowest | Most aggressive in market |
| **Competitive** | within $500 of competitor median | Aligned |
| **Slightly High** | $500–$1,200 above median | Noticeable disadvantage |
| **Uncompetitive** | more than $1,200 above median | Likely losing consideration |

**Why these numbers.** They are anchored to VW front-end gross of roughly
$1,500–2,500 per unit. At $500 — about a quarter of a deal's gross — a shopper
comparing two listings starts to notice. Past $1,200 you are usually not getting
the call at all. They are defaults, not laws: a market with unusually thin or fat
gross should move them, and the reasoning above is what to reason from.

Always report the **sample size** alongside the position. "Uncompetitive on Atlas
(n=2)" is a hypothesis; at n=14 it is a finding.

## 1b. Never infer a discount policy from a listing grid

A search-results page shows a summary price. The itemized ladder lives on the
**vehicle detail page**. Reading the grid and concluding anything about discount
policy is a mistake — one made during this skill's own development, which is why it
gets its own section.

What happened: a markdown-converting fetcher returned our listing cards with a single
price and no pricing breakdown, and returned the listing grid again when pointed at a
detail page. That reads exactly like "this store publishes no discount," and that
conclusion was drawn and was **wrong**. The live page shows a full ladder on every
card:

```
2026 Atlas 2.0T SEL Premium R-Line AWD   (stock W19461)
MSRP                                      $58,030
Discount                                 − $2,600     <- true dealer discount, 4.48%
Dealer Fees                              +   $698
Retail Customer Bonus                    − $3,500     <- factory money
Excl. tax, gov. fees                      $52,628     <- advertised
Military & First Responders Program      −   $500     <- conditional, below the line
```

Note the shape: **$5,402 total off MSRP, of which only $2,600 is ours.** Quoting the
$5,402 as "our discount" overstates what we give by more than double — the same trap
described in `pricing-normalization.md`, and the reason recommendations are always
expressed as dealer discount.

The rules that follow from this:

- **A tool reporting "no discount" is a claim about the tool, not the dealer** —
  until confirmed against a rendered page. Converters drop structured pricing blocks
  silently, returning something that reads like a clean result.
- **Verify a no-discount finding before it reaches a conclusion.** It is the single
  highest-consequence claim this analysis can make about a competitor, and the
  cheapest to get wrong. One screenshot settles it.
- **Discount varies by model within a store.** On the same page, Atlas units carried
  thousands off while a Golf R showed no discount at all. A single model tells you
  nothing about the store — this is Step 6's rule, and it applies to us too.

Where a genuine display gap *does* exist — a dealer discounting in the deal but not
publishing it anywhere a shopper can see — it is worth flagging, because shoppers
filter by price and an unpublished discount wins no consideration. But establish it
from rendered pages across several units and several models.

## 2. Inventory pressure

Price alone is half the picture. The same $1,000 gap means different things at 15
days' supply and at 120.

**Share of market inventory.** With five stores, a neutral share is ~20%. Hold 35%
of the market's Tiguans and you need volume more than you need the next $500 of
gross. Hold 8% and aggressive discounting just sells the few you have cheaper.

**Aging.** Units over 90 days are the strongest argument for discount in this
entire analysis — carrying cost is real and compounding, and a 120-day car costs
more to hold than to discount. Dealer.com's `inventoryDate` yields days in stock
directly.

**Depth of identical competing units.** Fifteen near-identical Tiguan SE FWDs
across the market means price is close to the only differentiator. Three means
availability matters more than price, and discounting is largely wasted.

**Competitor stocking posture.** A competitor with an outsized share of one model
will get aggressive on it — usually before their pricing shows it. Week-over-week
inventory build is a leading indicator of a coming discount push.

## 3. Reading competitor strategy

Characterize each competitor **per model**, never as a whole store. A dealer can be
brutal on Atlas and conservative on Taos, and averaging those into "aggressive
dealer" throws away the actionable part.

Patterns worth naming:

- **Protecting gross** — discounts well below market, thin inventory
- **Matching** — clustered near median, low variance
- **Volume play** — consistently deepest discount across a model line with depth
  to support it
- **Loss leaders** — one or two deeply cut units against otherwise normal pricing.
  The analyzer flags units more than 2 SD above the dealer's own mean discount and
  excludes them from competitor price pools. Report them separately: they are
  advertising, not a price position.
- **Conditional-rebate advertising** — low headline prices built on stacked
  conditional offers. Check `conditional_share_of_discount`. A store where
  conditionals are a large share of the apparent discount is not underpricing you
  as much as the listing suggests. **Do not chase this with real dealer money.**
- **Aging-inventory clearance** — deep discounts concentrated on older units
- **Model-line dominance** — depth plus aggression on one nameplate, signalling an
  intent to own it

## 4. The three price points

Derived from the competitor distribution, expressed as **dealer discount** because
that is the lever management controls:

- **Target** — competitor median − $200. Solidly competitive without buying the
  bottom of the market.
- **Aggressive** — the more aggressive of the 10th percentile or median − $750.
  For when share matters more than per-unit gross.
- **Defensive** — the most we can hold and still sit inside the competitive band
  (median + $400). For thin inventory or strong demand.

Inventory pressure shifts the whole ladder ±$250: overstocked moves down,
understocked moves up.

Always state both figures and keep them distinct:

```
Target:      $2,300 dealer discount (7.2% of MSRP)
             → $24,850 advertised, assuming $1,500 VW cash
```

Every recommendation must trace to collected data. If you cannot name the
competitor and the units creating the pressure, the recommendation is not ready.

## 5. Attack / Match / Hold / Clear

| Call | When | Watch for |
|---|---|---|
| **ATTACK** | Real gap, we have depth, model has demand, gap is closable for modest money | Competitor matching back — check next week |
| **MATCH** | Roughly aligned; small moves won't change consideration | Drifting without noticing |
| **HOLD** | Thin inventory, strong demand, or already at/near lowest | Discounting from habit |
| **CLEAR** | Aging or excess units regardless of position | Cutting the whole line when only the old units need it |

CLEAR is unit-specific, not model-wide. Discounting the entire Tiguan line to move
four 120-day cars gives away gross on fresh inventory that would have sold anyway.

## 6. Gross-profit recovery

Symmetry matters: the analysis must be as willing to find over-discounting as
under-pricing, or it becomes a one-way ratchet toward zero gross.

Flag a **GROSS-PROFIT RECOVERY OPPORTUNITY** where any hold:

- We are already lowest and the next competitor is more than $500 above — that gap
  is money on the table
- We hold materially less inventory than competitors (no volume pressure)
- Competitors are protecting gross and no one is chasing
- The model is in short supply market-wide
- Additional discount would not change our position band

Quantify how much can come out while staying inside the competitive band, and
recommend moving in steps — $300–500 at a time, re-measured weekly — rather than
in one jump. Raising price is a testable hypothesis, not a one-way door.

## 7. Ranking market-share opportunities

Rank the top five by expected share gain per dollar of gross invested:

1. **Gap size** — how far below market are we, on like trim
2. **Closability** — can a modest move change the position band
3. **Inventory depth** — do we have units to sell if demand arrives
4. **Model demand** — volume nameplates move share; niche trims move little
5. **Competitive density** — how many near-identical units compete
6. **Gross cost** — total dollars at risk across the affected units
7. **Durability** — will competitors immediately match

The best opportunity is rarely the largest gap. It is usually a mid-size gap on a
high-volume model where we have depth and a $400 move flips the position band.

## 8. Sanity checks before publishing

- Does every cited number trace to a collected record?
- Is any conclusion resting on n=1 or n=2? Label it a hypothesis.
- Any competitor looking implausibly cheap? Check for stacked conditionals, an
  add-on-inflated MSRP, or a mis-parsed ladder before calling it a price war.
- Are dealer discount and total-off-MSRP kept distinct everywhere?
- Are the excluded dealers named next to the conclusions they would have affected?
- Does every recommended $500 have a stated reason and expected return?
- Is there at least one HOLD or RAISE? An analysis that recommends cutting
  everywhere has stopped analyzing and started capitulating.
