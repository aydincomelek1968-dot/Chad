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
| **VW N Scottsdale (US)** | `vwnorthscottsdale.com/new-vehicles/` | **403** | Dealer Inspire | ❌ blocked |
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

**What was verified:** every path on `vwnorthscottsdale.com` returns HTTP 403 to
scripted requests — `/new-vehicles/`, `/new-inventory/`, `/inventory/new/`, even
`/sitemap.xml` and the site root. Response headers show `server: cloudflare` with a
`__cf_bm` cookie and a Cloudflare "Attention Required" interstitial. The
`x-cars-signature-v1` header identifies the platform as Cars Commerce / Dealer
Inspire, and the Dealer.com-style path `/new-inventory/index.htm` 301-redirects to
`/new-vehicles/`, confirming it is not a Dealer.com store.

A markdown-converting fetcher gets *past* Cloudflare but only retrieves the
navigation shell — the vehicle cards are rendered client-side. It does return the
page title, which reported **127 new units**. Useful as a validation target, not as
data.

**So: a real browser is required.** Use the `cloakbrowser` skill, then parse the
saved HTML:

```bash
python3 scripts/extract_inventory.py --html saved_vwns.html \
  --dealer vwnorthscottsdale > data/raw/vwnorthscottsdale.json
```

**Not yet verified:** browser-based collection of this site has *not* been proven
end-to-end. The attempt was made in a sandbox whose egress proxy the stealth browser
could not traverse — it failed to reach any site, including `example.com`, so the
failure says nothing about Cloudflare or about this dealer. On a normal machine with
direct network access this is the expected-to-work path, but treat the first run as a
test rather than an assumption.

Fallbacks if the browser route does not pan out:

1. **Our own DMS or inventory feed.** We are the dealer — we have authoritative
   access to our own stock, pricing, MSRP, and true days-in-stock without scraping
   anything. This is strictly better data than our website exposes, and it sidesteps
   the problem entirely. Prefer it if a feed or export is available.
2. **Save the SRP by hand.** Open `/new-vehicles/`, scroll until all units load,
   save the page, and point `--html` at it.
3. **Per-model pages** at `/new-vehicles/{model}/` (jetta, tiguan, atlas, taos, id-4,
   id-buzz, …) — smaller pages, easier to render fully, and they naturally chunk the
   collection by model line.

**Dealer Inspire field mappings are unconfirmed.** The extractor will detect the
platform and fall back to schema.org JSON-LD, which yields identity and one price but
usually no discount breakdown. Before trusting any discount component from this
platform, confirm the mapping against a real rendered page and record it in
`references/pricing-normalization.md`. Comparing our JSON-LD-only price against
competitors' fully itemized ladders is an apples-to-oranges trap: their advertised
price may include conditional rebates that ours does not.

## Extraction paths, best to worst

**1. Inline JSON in the SRP.** Dealer.com and Fox both ship the full inventory
payload inside the search-results HTML. No API needed, and it carries the itemized
price ladder. This is what `extract_inventory.py` targets first.

Dealer.com vehicle records contain `vin`, `stockNumber`, `year`, `make`, `model`,
`trim`, `bodyStyle`, `condition`, `inventoryDate` (which yields days in stock), and
a `pricing.dprice[]` ladder. Fox records expose `msrp`, `discountsTotal`,
`markupsTotal`, `rebatesEveryoneTotal`, `rebatesAppliedTotal`, `docFee`, and an
`isCourtesy` flag for service loaners.

**2. schema.org JSON-LD.** Most dealer platforms emit `Vehicle`/`Car` nodes with
`vehicleIdentificationNumber`, `sku`, and an `offers.price`. Useful as a
cross-platform fallback for identity and one price, but it rarely carries the
discount breakdown — which is the part that matters. Treat a JSON-LD-only dealer as
having *price* data but not *discount* data, and say so in the report.

**3. Vehicle detail pages.** Slow, but authoritative. Use for spot-verifying any
result that looks anomalous, and for reading the fine print that changes the real
advertised price.

## When a site blocks you (403 / 429)

Two of five stores do this today, including Berge — which claims to be the largest
VW dealer in the Phoenix market. Dropping it silently would distort every market
average in the report.

Escalate in this order:

1. **Use the `cloakbrowser` skill.** It is available in this environment and exists
   precisely for sites that reject scripted traffic. Drive the SRP, let it render,
   save the HTML, then parse the saved file:
   ```bash
   python3 scripts/extract_inventory.py --html saved_berge.html --dealer berge \
     > data/raw/berge.json
   ```
2. **Use cars.com syndication** — verified to reach every blocked store. See
   "Syndication fallback" below for what it does and does not give you.
3. **Collect manually.** A human can open the SRP and save the page.
4. **Declare the gap.** If none of the above works, the dealer is excluded from
   every average and the report says so explicitly, by name, in the data-quality
   section and next to any conclusion it would have affected.

Never substitute "typical market pricing" or a prior week's numbers for a dealer
you could not reach this run. Stale data presented as current is the same failure
as invented data, just slower-acting.

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
