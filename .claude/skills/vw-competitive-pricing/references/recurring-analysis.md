# Recurring Analysis

A single snapshot answers "who is cheapest today." A weekly series answers "who is
**getting** more aggressive, on which models, and how fast" — which is the more
actionable question, because it lets you respond to a competitor's push while it is
still forming rather than after you have lost a month of share.

## Cadence

**Weekly is the right default.** Dealer pricing moves on incentive cycles (VW
programs typically turn at month start), month-end volume pushes, and aging
inventory crossing internal thresholds. Weekly catches all three. Daily is noise —
you will chase listing churn that reverses in 48 hours.

Useful additions:

- **Month-end** (last 3 days) — the most aggressive pricing of the cycle
- **Month-start** (first 2 days) — new incentive programs land
- **Ad-hoc** when a competitor is suspected of a push

Run at a consistent time of day. Sites update on their own schedules and a
Monday-morning run compared against a Friday-evening run mixes real movement with
time-of-week effects.

## Layout

```
data/
  raw/                      # current run, one JSON per dealer
  snapshots/
    2026-08-04.json         # analysis output, kept
    2026-08-11.json
  reports/
    2026-08-11-report.md
```

```bash
python3 scripts/extract_inventory.py --config config/dealerships.json --out-dir data/raw/
python3 scripts/analyze_pricing.py --in data/raw/ --us <our_key> \
  --out data/snapshots/$(date +%F).json \
  --md data/reports/$(date +%F)-tables.md \
  --prior data/snapshots/<previous-date>.json
```

Keep snapshots indefinitely — they are small, and a season of history is what makes
seasonality and competitor behavior patterns visible.

## What week-over-week surfaces

`--prior` produces per-dealer, per-model movement: discount change in dollars and
percentage points, and unit-count change. Movers of $250 or more are flagged.

Read them together, because the combination is the signal:

| Discount | Inventory | Likely meaning |
|---|---|---|
| Up | Up | Overstocked, pushing volume — expect sustained pressure |
| Up | Down | Clearing aging units — likely temporary |
| Down | Down | Selling through, protecting gross — room for us to hold |
| Down | Up | Confident on demand, or new stock at fresh pricing |
| Flat | Up sharply | Build-up before a push — **leading indicator** |

The last row is the most valuable thing a weekly series gives you: inventory builds
before discounts follow, so a competitor stocking up on Atlas is telling you what
their pricing will do in two weeks.

## Reading trends honestly

**Distinguish movement from noise.** A $200 change on a handful of units is mix
shift, not strategy. Look for changes that are large (>$250), sustained (two-plus
weeks), or broad (across a model line).

**Watch our own drift.** Competitors moving while we sit still changes our position
without any decision being made. That is the most common way a store becomes
uncompetitive — not by choosing to, but by not noticing.

**Mix changes masquerade as pricing changes.** A dealer whose average discount
"rose" may simply have sold their base trims and be left with loaded ones. Confirm
at trim level before calling it a strategy shift.

**Inventory counts move for boring reasons too.** A drop can mean sales, or a
website glitch, or a platform change. Check the extraction summary before building
a narrative on it.

## Automating

The `loop` skill can schedule recurring runs. Weekly, mid-morning, consistent day.

Keep a human in the loop for the *interpretation*. Collection and normalization
automate cleanly; the attack/hold/raise call should not, because it depends on
floor-plan cost, factory objectives, and stair-step targets that never appear on a
competitor's website.

## Report continuity

Each weekly report should open with what changed since last week — movers, position
changes, and whether last week's recommended actions were taken and what happened.
A recommendation that was never executed is not evidence the strategy failed, and a
series that never checks back cannot tell the difference.
