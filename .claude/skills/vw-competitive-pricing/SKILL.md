---
name: vw-competitive-pricing
description: >
  Volkswagen new-vehicle competitive pricing, discount, and market-share analysis
  against rival VW dealers. Collects live dealer-website inventory, separates true
  dealer discount from manufacturer and conditional incentives, scores our
  competitive position by model line and trim, and recommends target/aggressive/
  defensive discount levels plus where to attack, match, hold, or clear. Use this
  skill whenever the user asks about competitor pricing, dealer discounts, discount
  strategy, price positioning, market share, inventory pressure, days' supply,
  who is cheapest on a model, whether we are leaving gross on the table, or wants a
  recurring/weekly competitive pricing check - even if they don't say "analysis" or
  name the competing stores. Also use for questions like "are we priced right on
  Tiguan", "who's discounting Atlas hardest", "should we cut price on Taos", or
  "what changed in the market this week".
---

# VW Competitive Pricing & Market-Share Analysis

## What this is for

A dealer principal or GM does not need to know who advertises the lowest price.
They need to know **where the next $500 of discount buys market share and where it
just burns gross**. That is the question this skill answers.

The output is a pricing decision, not a price list.

## The two failure modes that ruin this analysis

Everything below is shaped by avoiding these. Internalize them before starting.

**1. Fabricated inventory data.** This analysis has an unusual property: a report
built on invented MSRPs looks *exactly* like a report built on real ones. Same
tables, same confident recommendations. Several of these dealer sites actively
block scripted requests, and a blocked fetch that gets quietly filled in with
plausible numbers produces a document that will move real money in the wrong
direction. **Never write a price, MSRP, VIN, or unit count you did not extract.**
If a dealer cannot be collected, the report says so and that dealer is excluded
from every average. An analysis covering three of five stores, clearly labeled, is
genuinely useful. One covering five stores where two were imagined is worse than
nothing.

**2. Treating conditional rebates as real discounts.** Conditional offers -
military, college grad, loyalty, conquest, finance-through-VCI - are money most
shoppers never receive. A store advertising a low price built on $2,500 of stacked
conditional rebates is not underpricing the market; it is advertising differently.
Chasing that phantom price with real dealer money is the single most expensive
mistake this analysis can cause. Keep the two in separate columns, always.

## Before starting: who are we?

`config/dealerships.json` needs `our_dealer` filled in. There is no "us" to compare
against until it is. If the user has not said which store is theirs, **ask** - this
is the one question worth blocking on, because every number in the report is
relative to it.

Copy `config/dealerships.example.json`, which already carries verified URLs and
per-site notes for the four Phoenix-market competitors.

## Workflow

### 1. Collect

```bash
python3 scripts/extract_inventory.py --config config/dealerships.json --out-dir data/raw/
```

The extractor auto-detects the site platform, walks pagination, keeps new units
only, and prints a loud per-dealer summary including anything blocked or empty.
It exits 2 if any dealer was blocked and 3 if nothing was extracted.

Read that summary before going further. If a dealer shows `BLOCKED (http 403)` or
`0 records`, resolve it via `references/data-collection.md` (the **cloakbrowser**
skill handles the blocking sites) or explicitly carry it as a gap. Do not proceed
quietly.

Sanity-check the yield: a mid-size VW store carries roughly 80-250 new units. If a
dealer returns 12, pagination probably stopped early - that under-count will skew
inventory-pressure conclusions.

### 2. Normalize and analyze

```bash
python3 scripts/analyze_pricing.py --in data/raw/ --us <our_key> \
  --out data/analysis.json --md data/tables.md \
  [--prior data/snapshots/<last-week>.json]
```

This separates MSRP / dealer discount / universal incentive / conditional
incentive / fees / dealer add-ons, computes position by model and by
model+trim, flags loss leaders and thin samples, and derives the three
recommended discount levels. `references/pricing-normalization.md` explains the
component taxonomy and the site-specific field mappings it relies on.

### 3. Interpret

The script produces arithmetic. The judgment is yours, and it is the part worth
the most. Work through `references/analysis-playbook.md`, which covers competitive
position, inventory pressure, reading each competitor's strategy by model, the
attack/match/hold/clear call, and gross-profit recovery opportunities.

### 4. Report

Follow `assets/report-template.md`. Lead with the actions, not the methodology.

## Rules that keep the analysis honest

**Compare like to like.** Tiguan SE FWD against Tiguan SE FWD. Trim and drivetrain
move MSRP by thousands; a model-level average that mixes S with SEL R-Line is
comparing inventory mix, not pricing strategy. Use model-level numbers for the
executive table and trim-level numbers for any recommendation you actually act on.

**Normalize on dealer discount % of MSRP** for cross-dealer scorecards, so
differing trim mix doesn't masquerade as pricing difference. But recommend in
**dollars**, because that is what a desk manager executes.

**Recommend on the lever you control.** Total off MSRP includes VW's money. The
dealer discount is what costs gross. The analyzer reports both and the
recommendation is expressed as dealer discount - keep it that way, or the store
will think it is "giving" $4,000 when $1,500 of it is factory cash.

**Watch the fee basis.** Some sites fold the doc fee into the advertised price and
some don't - a several-hundred-dollar phantom gap. Camelback's advertised price
includes a $599 doc fee (verified). Comparison defaults to a fee-excluded basis.

**Watch dealer add-ons.** Accessories and addendum stickers inflate MSRP, making a
store's discount % look larger against a number the factory never set. Every
Camelback unit observed carried them. Call them out where present.

**Three units minimum** before a dealer-model average means anything, and two
competitors minimum before "the market" exists. The analyzer flags both rather
than quietly averaging noise. One deeply-cut car is a tactic, not a strategy -
loss leaders are flagged and excluded from competitor price pools.

**A surprise is a finding, not an inconvenience.** If a competitor appears $3,000
below market, the first hypothesis is a data error or a stacked conditional
rebate - not a price war. Verify against the actual vehicle detail page before it
reaches a recommendation.

**Never recommend being cheapest for its own sake.** Every $500 of additional
discount needs a stated reason and an expected return. The objective is maximum
sustainable share growth per dollar of gross invested.

## Recurring runs

Competitor pricing moves with month-end pushes, incentive cycles, and aging
inventory. A single snapshot tells you who is cheapest today; a weekly series
tells you **who is changing, on which models, and in which direction** - which is
the more actionable signal. Pass `--prior` to surface week-over-week movers.
See `references/recurring-analysis.md` for the snapshot layout and cadence.

## Reference files

- `references/data-collection.md` - per-site extraction, pagination, handling
  blocked sites, what to do when a platform changes
- `references/pricing-normalization.md` - the discount component taxonomy and
  verified site field mappings
- `references/analysis-playbook.md` - position thresholds and the reasoning behind
  them, inventory pressure, competitor strategy reading, attack/match/hold/clear,
  gross recovery
- `references/recurring-analysis.md` - weekly cadence and trend interpretation
- `assets/report-template.md` - output structure
