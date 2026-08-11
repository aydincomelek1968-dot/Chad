# Data Collection

Everything in the final report rests on this step. A pricing recommendation built
on inventory that was never actually retrieved is not a weaker analysis — it is a
fabrication with tables. Treat collection as a gate: it either produced real data
or it did not, and the report states which.

## Platform landscape (verified 2026-08-11)

The stores run on at least four different website platforms, and three of six
endpoints block scripted requests outright. There is no single scraping approach.

| Dealer | URL | Status | Platform | Extraction |
|---|---|---|---|---|
| **VW N Scottsdale (US)** | `vwnorthscottsdale.com/new-vehicles/` | **403** | Dealer Inspire | ⚠️ browser only — full ladder on SRP |
| Camelback VW | `camelbackvw.com/new-inventory/index.htm` | 200 | Dealer.com (DDC v9) | ✅ 24/page verified |
| Chapman VW Scottsdale | `chapmanvw.com/search/new` | 200 | Fox Dealer (Nuxt/devalue) | ✅ 100 units verified |
| Lunde's Peoria VW | `peoriavw.com/searchnew.aspx` | 200 | Sincro/DealerOn family | ⚠️ **0 records** |
| Chapman VW (alt domain) | `chapman-vw.com/new-inventory/index.htm` | **403** | Dealer.com | ❌ blocked |
| Berge VW | `bergevw.com/search/?tp=new` | **403** | unknown | ❌ blocked |

**Lunde's is an open gap.** The page returns HTTP 200 and ~20 VINs are visible in
the raw HTML, but neither the platform parsers nor the JSON-LD fallback recover
them — its JSON-LD blocks contain no vehicle nodes and no pricing keys appear in
the markup. It currently extracts **0 records** and is silently absent from any
market average unless someone reads the run summary. Resolving it means inspecting
a saved SRP for the inline payload and adding a parser. Until then, treat every
Lunde's figure as missing, not as zero.

Chapman runs two live domains on different platforms. Confirm which is the current
retail site before collecting, or the same cars get counted twice.

## Collecting our own store

This is the one that cannot be skipped, and it is also the most defended.

**Scripted access is blocked.** Every path on `vwnorthscottsdale.com` returns HTTP
403 — `/new-vehicles/`, `/new-inventory/`, `/inventory/new/`, even `/sitemap.xml`
and the site root. Headers show `server: cloudflare` with a `__cf_bm` cookie and a
Cloudflare interstitial. The `x-cars-signature-v1` header identifies the platform as
Cars Commerce / Dealer Inspire, and `/new-inventory/index.htm` 301-redirects to
`/new-vehicles/`, confirming it is not a Dealer.com store.

**The site publishes a full itemized ladder — on every search-results card.** MSRP,
Discount, Dealer Fees, Retail Customer Bonus, "Excl. tax, gov. fees", conditional
programs, stock number and VIN, across all 127 units. The mapping and a worked
example are in `references/pricing-normalization.md`.

### WARNING: this site defeats markdown-converting fetchers

A markdown fetcher gets past Cloudflare, but returns those same cards stripped down
to a single price with no ladder — **silently, with no error**, on pages that show
the full breakdown to any human viewer. Pointed at a vehicle detail page, it serves
the listing grid instead, which reads as "detail page has no pricing."

During this skill's development that combination produced a confident, completely
wrong conclusion: that the store published no discounts at all, followed by a
merchandising recommendation built on nothing. A single screenshot overturned it.

The rule: **absence of pricing in a converted document is evidence about the
converter, not about the dealer.** Treat any "no discount found" result as unproven
until confirmed against a rendered page or a screenshot.

### What to use instead

1. **The DMS or inventory feed — preferred.** We are the dealer. The feed carries
   MSRP, actual selling price, cost, true days-in-stock and gross, which is more than
   the website exposes and moots the access problem entirely.
2. **Claude in Chrome.** The account has the extension enabled. It runs in the user's
   own logged-in browser, so it renders JavaScript, carries real session cookies, and
   is subject to neither Cloudflare nor sandbox egress limits. It is driven by the
   user from claude.ai rather than callable from a Claude Code session, so the
   workflow is: they run it, then hand back the output. It reads the public SRP ladder
   directly, and it is the only practical route to authenticated systems — the DMS
   inventory screen, the Dealer Inspire admin (pricing rules), and the VW dealer
   portal (program money, universal vs conditional terms).
3. **Save the SRP by hand.** Open `/new-vehicles/`, scroll until all units load, save
   the page, and point the extractor at it with `--html`. Per-model pages at
   `/new-vehicles/{model}/` (jetta, jetta-gli, taos, tiguan, atlas, atlas-cross-sport,
   id-4, id-buzz, golf-gti, golf-r) are smaller and chunk the work by model line.

A prompt that produces a directly loadable export from the DMS:

> Export the current new-vehicle inventory list. For every unit give me: VIN, stock
> number, year, model, trim, drivetrain, MSRP, any dealer addendum/accessories,
> current asking/internet price, dealer discount applied, factory rebate applied,
> days in stock, and whether it's in-transit or a courtesy loaner. Output as CSV.

Normalize to the field names the extractor emits (`vin`, `msrp`, `dealer_discount`,
`universal_incentive`, `universal_applied`, `advertised_price`, `doc_fee`,
`dealer_addons`, `days_in_stock`) so `analyze_pricing.py` consumes it alongside the
scraped competitor files.

**Parser status:** no Dealer Inspire parser exists yet. Once a rendered SRP is saved,
add one using the ladder mapping in `pricing-normalization.md` — the labels are
stable and the arithmetic reconciles, so it is a straightforward addition.

**Browser automation inside this sandbox does not work at all** — port-level egress
refusal, failing even on `example.com`, for both CloakBrowser and stock Playwright.
That is environmental and says nothing about Cloudflare or this dealer.

## Syndication fallback (cars.com) — verified 2026-08-11

Every dealer syndicates inventory to cars.com, and it reaches all three stores that
block us directly. This is the most reliable route to full market coverage.

| Dealer | cars.com dealer ID | New units |
|---|---|---|
| VW North Scottsdale (us) | `109556` | 126 |
| Lunde's Peoria VW | `176673` | 188 |
| Camelback VW | `5393241` | 140 |
| Berge VW | `6000291` | 72 |
| Chapman VW Scottsdale | *not yet located* | — |

```
https://www.cars.com/dealers/<id>/<slug>/inventory/?stock_type=new
```

cars.com returns 403 to plain scripted requests, but a markdown-converting fetcher
retrieves it fine. A rendering browser is the route to bulk parsing.

**Accuracy — cross-validated, not assumed.** Camelback is the one store with both a
verified itemized ladder and a cars.com listing, so it serves as the control:

| Vehicle | cars.com MSRP / price | Direct MSRP / advertised |
|---|---|---|
| Taos S | $28,271 / $26,120 | $28,271 / $26,120 |
| Tiguan 2.0T S | $32,919 / $29,177 | — / $29,177 |

Exact agreement. Syndicated MSRP and listed price mirror the dealer's own
advertised price, so this is real data, not an approximation.

**What it cannot do, and this is the important part.** cars.com publishes MSRP and a
final price — nothing else. There is **no breakdown of dealer discount, universal
rebate, or conditional incentive**. All you can derive is:

```
total_off_msrp = MSRP − listed price      (dealer money + factory money, merged)
```

That is not the lever management controls, and separating those components is the
analytical core of this whole skill (Steps 2, 6, 7 and rules 4–5). A store showing
$3,000 off via syndication might be giving $800 of its own money with $2,200 of VW
cash, or the reverse — and the pricing decision is completely different in each
case. **Never derive a dealer-discount recommendation from syndicated data alone.**

Two further limits:

- **Trim labels differ.** Camelback's own site lists a "1.5T Sport" Jetta that
  cars.com renders as 1.4T/2.0T variants. Trim-level like-for-like matching needs
  care, and VIN is the only reliable join key across the two sources.
- **No days-in-stock**, so aging analysis (Step 5) is unavailable from syndication.

**Where it fits.** Use syndication for what it is genuinely good at: full-market
**unit counts, inventory depth, model mix, MSRP, and advertised price** — which
covers Step 1 identity/price, Step 3 model comparison, and most of Step 5. Then get
itemized ladders from the dealer sites that allow it (Camelback, Chapman) and treat
the blocked stores' discount *composition* as unknown rather than inferred.

The best combination is syndication for market-wide coverage plus our own DMS for
our side, since we need our own discount composition exactly and already have it.

**One observation worth verifying before acting on it:** several VW North Scottsdale
units list *above* MSRP (a Tiguan at $47,005 against $46,307 MSRP; a Golf R at
$57,142 against $56,444). Camelback carries $1,538 of dealer-added accessories on
every unit, so an addendum above MSRP is entirely plausible and would mean we are
advertising above sticker on some stock — a significant competitive finding. It
could equally be a fee artifact in the syndicated feed. Confirm against a vehicle
detail page before it reaches a recommendation.

## Inclusion rules

**New retail units only.** Exclude used, CPO, demo, and service loaners — they
carry different pricing logic and drag averages down in ways that have nothing to
do with competitive strategy. Fox exposes `isCourtesy`; Dealer.com exposes
`condition` / `type` / `certified`. Where a site advertises loaners *as* new, note
it rather than silently including them.

**In-transit vs on-ground.** Some sites list in-transit units in the same results.
They compete for the same customer but cannot be delivered today, and they distort
days-supply math. Capture the distinction where the site exposes it.

**Pagination.** Page until a request returns no new VINs. Partial collection is the
most likely silent failure here: it under-counts inventory, which flows straight
into inventory-pressure conclusions and out into a recommendation. Cross-check the
total against the site's own displayed result count where one exists.

## Verifying a collection run

Before analyzing, confirm:

- Every configured dealer appears in the summary with a plausible unit count
  (a mid-size VW store carries roughly 80–250 new units).
- The model mix looks like a VW store — Jetta, Taos, Tiguan, Atlas, Atlas Cross
  Sport, ID.4, ID. Buzz, GTI, Golf R. A store with zero Tiguans has an extraction
  problem, not an inventory problem.
- `failed_reconciliation` is 0 or near it. The analyzer independently checks that
  `MSRP + fee − dealer discount − universal incentive = advertised price`; records
  that fail were probably mis-parsed and should not be trusted.
- Record the date and time of collection. Pricing is perishable and every figure
  in the report is only true as of that timestamp.

## When a platform changes

Dealer sites get replatformed without notice. A dealer that returns 0 units when it
returned 140 last week has almost certainly changed its site — that is the first
hypothesis, not "they sold out." Re-inspect the SRP HTML for the inline JSON
pattern, update the extractor, and note the change in the run log.
