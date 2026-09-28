# VW Competitor Pricing — Phoenix / Scottsdale

**Collected:** 2026-09-27 · **Analyst basis:** live dealer websites + cars.com syndication
**Your store (VW North Scottsdale) is NOT in this data** — its site blocks collection.
This is the competitive field you are priced against, not your position in it.

---

## Headline

**Camelback is the only genuinely aggressive discounter in this market — and their
headline overstates it three separate ways.** Chapman, Berge and Lunde's are all
protecting gross. The market is softer than Camelback's advertising suggests.

---

## 1. What a shopper sees — total off MSRP

Dealer money and factory money combined, which is how a price comparison reads online.

| Model | Camelback | Chapman | Berge | Lunde's |
|---|---:|---:|---:|---:|
| Jetta | **5.88%** (n=19) | 2.88% (61) | 2.86% (4) | 2.78% (1) |
| Taos | **9.02%** (n=12) | 3.48% (20) | 5.05% (2) | 2.71% (1) |
| Tiguan | **13.50%** (n=40) | 4.68% (19) | 2.86% (4) | 0.87% (1) |

Berge and Lunde's samples are small (cars.com), so treat them as indicative.

## 2. What it actually costs them — dealer-only discount

The lever each store controls. Available only where the site itemizes.

| Model | Camelback | Chapman |
|---|---:|---:|
| Jetta | 4.35% (n=19) | **0.77%** (n=61) |
| Taos | 3.71% (n=12) | **1.44%** (n=20) |
| Tiguan | 5.39% (n=40) | **2.90%** (n=19) |

**Chapman shows zero dealer discount on 56 of their 100 units.** Their Jetta line
averages 0.77% — effectively priced at sticker less factory money.

---

## 3. Camelback's headline is inflated three ways

Verified on a live VDP (2026 Jetta, stock 839c8ac5) — the ladder reconciles exactly:

```
MSRP                      $25,685
Dealer Discount          − $1,319   <- the only line costing them gross
Customer Cash (Jetta)    − $2,000   <- VW's money, not theirs
Doc Fee                  +   $599
Advertised Price          $22,965   (25,685 − 1,319 − 2,000 + 599 ✓)
Military Offer               $500   <- conditional
College Grad Offer         $1,000   <- conditional
Dealer Added Accessories   $1,538   <- listed AFTER the price
```

**(a) Factory money bundled in.** Of $2,720 off MSRP, only $1,319 is Camelback's.

**(b) Conditional offers advertised.** 78 of 96 units, averaging $1,128 —
about **22% of their apparent discount** is money most buyers never receive.
Chapman advertises none.

**(c) A uniform $1,538 accessory pack — on 96 of 96 units.** Identical on every
car: door edge guards $116, wheel caps $299, window tint $499, Zaktek $624. That
is a pack, not per-vehicle options, and it is listed *after* the advertised price.

### The pack changes who is actually cheaper

| Comparable trim | As advertised | With the $1,538 pack |
|---|---|---|
| Jetta S | Camelback −$711 | **Chapman cheaper by $827** |
| Jetta SE | Camelback −$646 | **Chapman cheaper by $892** |
| Jetta Sport | Camelback −$756 | **Chapman cheaper by $782** |
| Taos SE | Camelback −$958 | **Chapman cheaper by $580** |
| Taos S | Camelback −$2,808 | Camelback still cheaper by $1,270 |
| Tiguan S | Camelback −$3,236 | Camelback still cheaper by $1,698 |

**Four of six flip.** Camelback's real advantage is concentrated in Taos S and
Tiguan S, where the gap survives the pack.

> **Verify before acting:** the site does not state explicitly whether the pack is
> mandatory. The disclaimer only points to the VDP. A phone call settles it, and it
> is worth making — it decides whether Camelback is beating you by $3,000 or by $700.

---

## 4. Why Camelback is discounting: aging

| | Camelback |
|---|---|
| Median days in stock | 42 |
| Average | 71 |
| Units over 60 days | 40 of 96 |
| Units over 90 days | **24 of 96 (25%)** |

A quarter of their inventory is over 90 days old. Their aggression is
inventory-driven, not a strategic land-grab — which means it is likely to persist
only until that stock clears. Chapman exposes no days-in-stock.

---

## 5. Strategy read, by store

| Store | Posture | Evidence |
|---|---|---|
| **Camelback** | Aggressive headline, protected reality | Deepest advertised discount; $1,538 pack on 100% of units; conditional offers on 81%; 25% of stock >90 days |
| **Chapman** | Gross protection, clean pricing | Zero dealer discount on 56%; no pack; no conditional advertising; the most transparent listings in the market |
| **Berge** | Conservative | $470–$1,830 off MSRP incl. factory money; smallest inventory (78) |
| **Lunde's** | Most conservative | $400–$900 off; largest floorplan (207) yet least aggressive |

## 6. Inventory depth

| Store | Units |
|---|---:|
| Chapman | ~218 |
| Lunde's | 207 |
| Camelback | ~140 |
| **VW N Scottsdale** | **127** |
| Berge | 78 |

You are fourth of five on depth. Chapman and Lunde's carry meaningfully more,
but neither is using it to buy share — both price conservatively.

---

## What this means for you

1. **The market is not a price war.** Three of four competitors discount modestly.
   Only Camelback is aggressive, and only genuinely so on Taos S and Tiguan S.
2. **Do not price against Camelback's headline.** It carries $2,000 of factory
   money, ~$1,128 of conditional offers, and a $1,538 pack. Matching it with real
   dealer money would give away gross to beat a number that does not exist.
3. **Chapman is the store to watch, and they are wide open.** Your closest
   geographic rival shows zero dealer discount on over half their inventory. A
   modest, clearly-published discount wins that comparison outright.
4. **Camelback's aggression has a shelf life** tied to their 90-day stock. Worth
   re-measuring in two weeks to see whether it persists.

## Data quality

- 196 units parsed from live sites; **0 reconciliation failures, 0 missing discounts**
- Camelback 96 of ~140 (site throttles); Chapman 100 of ~218 (client-side paging)
- Berge (78) and Lunde's (207) from cars.com — MSRP and price only, **no dealer/factory
  split**, small samples
- **VW North Scottsdale: not collected** — Cloudflare-blocked to every available method
- Model-level figures mix trims; the trim table in §3 is the like-for-like comparison
