# Data Collection

Everything in the final report rests on this step. A pricing recommendation built
on inventory that was never actually retrieved is not a weaker analysis — it is a
fabrication with tables. Treat collection as a gate: it either produced real data
or it did not, and the report states which.

## Platform landscape (verified 2026-08-11)

The five stores run on at least three different website platforms, and two of the
five block scripted requests outright. There is no single scraping approach.

| Dealer | URL | Status | Platform |
|---|---|---|---|
| Camelback VW | `camelbackvw.com/new-inventory/index.htm` | 200 | Dealer.com (DDC v9) |
| Lunde's Peoria VW | `peoriavw.com/searchnew.aspx` | 200 | Sincro/DealerOn family |
| Chapman VW Scottsdale | `chapmanvw.com/search/new` | 200 | Fox Dealer |
| Chapman VW (alt domain) | `chapman-vw.com/new-inventory/index.htm` | **403** | Dealer.com |
| Berge VW | `bergevw.com/search/?tp=new` | **403** | unknown (blocked) |

Chapman runs two live domains on different platforms. Confirm which is the current
retail site before collecting, or the same cars get counted twice.

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
2. **Try the alternate domain or a syndication source.** Some stores mirror
   inventory to a second domain. Syndicators (Cars.com et al.) can confirm unit
   counts and rough pricing, but their price fields are often stale or
   normalized differently — acceptable for inventory *depth*, not for discount math.
3. **Collect manually.** A human can open the SRP and save the page.
4. **Declare the gap.** If none of the above works, the dealer is excluded from
   every average and the report says so explicitly, by name, in the data-quality
   section and next to any conclusion it would have affected.

Never substitute "typical market pricing" or a prior week's numbers for a dealer
you could not reach this run. Stale data presented as current is the same failure
as invented data, just slower-acting.

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
