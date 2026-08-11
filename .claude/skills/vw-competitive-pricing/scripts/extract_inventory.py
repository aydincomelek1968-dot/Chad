#!/usr/bin/env python3
"""
Extract new-vehicle inventory + itemized pricing from VW dealer websites.

Design principle that matters more than any other here: this script either
returns real data or reports that it failed. It never guesses, never
interpolates a missing MSRP, and never returns a partial page as if it were
complete inventory. A silent partial extraction is worse than a loud failure,
because the analysis downstream looks identical either way.

Supported platforms (auto-detected):
  dealercom  - Dealer.com / DDC v9. Inventory is inline JSON in the SRP HTML.
               Itemized pricing lives in pricing.dprice[] with type codes that
               distinguish dealer discount from universal vs conditional rebates.
  fox        - Fox Dealer. Nuxt-style index-compressed JSON payload with an
               explicit pricing block (msrp / discountsTotal / markupsTotal /
               rebatesEveryoneTotal / rebatesAppliedTotal).
  jsonld     - Generic schema.org Vehicle/Car + Offer fallback. Gives identity
               and one price, but usually no discount breakdown.

Usage:
  extract_inventory.py --url URL --dealer KEY [--out FILE] [--html FILE]
  extract_inventory.py --config config/dealerships.json --out-dir data/raw/

Exit codes: 0 ok, 2 blocked (needs a real browser), 3 nothing extracted.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

MONEY = re.compile(r"-?[\d,]+(?:\.\d+)?")


def money(v):
    """'$1,362' -> 1362.0. Returns None for anything that isn't a number."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = MONEY.search(str(v).replace("$", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def fetch(url, timeout=60):
    """Returns (html, status). status 403/429 means bot-blocked, not absent."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace"), r.status
    except urllib.error.HTTPError as e:
        return "", e.code
    except Exception as e:
        print(f"  ! fetch error: {e}", file=sys.stderr)
        return "", 0


# ---------------------------------------------------------------- JSON walking

def enclosing_json(s, i, max_levels=6):
    """Return the smallest parseable JSON object containing index i.

    Brace-matching on raw HTML is imperfect (braces can appear inside string
    values), so on a parse failure we widen to the next enclosing object rather
    than dropping the record.
    """
    pos = i
    for _ in range(max_levels):
        depth, start = 0, None
        j = pos
        while j >= 0:
            c = s[j]
            if c == "}":
                depth += 1
            elif c == "{":
                if depth == 0:
                    start = j
                    break
                depth -= 1
            j -= 1
        if start is None:
            return None
        depth, k = 0, start
        end = None
        while k < len(s):
            c = s[k]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = k
                    break
            k += 1
        if end is None:
            return None
        try:
            return json.loads(s[start:end + 1])
        except Exception:
            pos = start - 1
            if pos < 0:
                return None
    return None


# ------------------------------------------------------------- dealer.com (DDC)

# Verified against a live DDC v9 SRP. The `type` code is the load-bearing field:
# it is what separates a discount every buyer gets from one most buyers do not.
DDC_UNIVERSAL = {"SICI"}          # "Offers" - applied above the advertised price
DDC_CONDITIONAL = {"SICCI"}       # "Conditional Offers" - military/grad/loyalty/finance


def parse_ddc_pricing(pricing):
    """Split a DDC dprice ladder into components that mean different things."""
    out = {
        "msrp": None, "dealer_discount": None, "universal_incentive": 0.0,
        "conditional_incentive": 0.0, "advertised_price": None,
        "doc_fee": None, "dealer_addons": None,
        "conditional_detail": [], "universal_detail": [],
    }
    for row in (pricing or {}).get("dprice", []) or []:
        tc = row.get("typeClass") or ""
        rtype = row.get("type") or ""
        label = re.sub(r"<[^>]+>", "", str(row.get("label") or "")).strip()
        val = money(row.get("value"))
        if val is None:
            continue
        if tc == "msrp":
            out["msrp"] = val
        elif row.get("isDiscount") or tc == "ABCRule":
            out["dealer_discount"] = (out["dealer_discount"] or 0.0) + val
        elif tc == "totalFees" or "doc" in label.lower():
            out["doc_fee"] = val
        elif rtype in DDC_CONDITIONAL or tc == "SICCRule":
            out["conditional_incentive"] += val
            out["conditional_detail"].append({"label": label, "amount": val})
        elif rtype in DDC_UNIVERSAL or tc == "SICRule":
            out["universal_incentive"] += val
            out["universal_detail"].append({"label": label, "amount": val})
        elif row.get("isFinalPrice") or tc == "SIFRule":
            out["advertised_price"] = val
        elif tc == "askingPrice":
            # Dealer-added accessories / addendum sitting on top of MSRP.
            out["dealer_addons"] = val
    if not out["advertised_price"]:
        out["advertised_price"] = money((pricing or {}).get("retailPrice"))
    return out


def extract_dealercom(html):
    seen, rows = set(), []
    for m in re.finditer(r'"vin"\s*:\s*"([A-HJ-NPR-Z0-9]{17})"', html):
        vin = m.group(1)
        if vin in seen:
            continue
        obj = enclosing_json(html, m.start())
        if not isinstance(obj, dict) or obj.get("vin") != vin:
            continue
        if "pricing" not in obj:
            continue
        seen.add(vin)
        p = parse_ddc_pricing(obj.get("pricing"))
        rows.append({
            "vin": vin,
            "stock_number": obj.get("stockNumber"),
            "year": obj.get("year"),
            "make": obj.get("make"),
            "model": obj.get("model"),
            "trim": obj.get("trim"),
            "body_style": obj.get("bodyStyle"),
            "condition": obj.get("condition"),
            "type": obj.get("type"),
            "certified": obj.get("certified"),
            "inventory_date": obj.get("inventoryDate"),
            "url_path": obj.get("link"),
            **p,
        })
    return rows


# ------------------------------------------------------------------ fox dealer

def extract_fox(html):
    """Fox Dealer ships a Nuxt `__NUXT_DATA__` payload using devalue encoding: one
    flat array where every integer is an index back into that same array. Values
    must be resolved through the pool -- reading them raw yields array offsets that
    look exactly like small dollar amounts (an MSRP of "294"), which is the most
    dangerous possible failure because it flows silently into the analysis.
    """
    m = re.search(r'id="__NUXT_DATA__"[^>]*>(\[.*?\])</script>', html, re.S)
    if not m:
        return []
    try:
        pool = json.loads(m.group(1))
    except Exception:
        return []

    def res(i, depth=0):
        if depth > 8 or not isinstance(i, int) or not (0 <= i < len(pool)):
            return i
        v = pool[i]
        if isinstance(v, dict):
            return {k: res(x, depth + 1) for k, x in v.items()}
        if isinstance(v, list):
            return [res(x, depth + 1) for x in v]
        return v

    rows, seen = [], set()
    for idx, node in enumerate(pool):
        if not (isinstance(node, dict) and "vin" in node and "pricing" in node):
            continue
        o = res(idx)
        vin = o.get("vin")
        if not isinstance(vin, str) or len(vin) != 17 or vin in seen:
            continue
        seen.add(vin)
        p = o.get("pricing") or {}
        msrp = money(p.get("msrp"))
        disc = money(p.get("discountsTotal")) or 0.0
        markup = money(p.get("markupsTotal")) or 0.0
        reb_applied = money(p.get("rebatesAppliedTotal")) or 0.0
        reb_everyone = money(p.get("rebatesEveryoneTotal")) or 0.0
        if msrp is None:
            continue

        # Only rebates actually *applied* are inside the displayed price. Observed
        # live: this store shows $1,500 of universal VW cash as available but does
        # NOT deduct it, while a Dealer.com competitor deducts the same money up
        # front. Subtracting it here would understate this dealer's price by $1,500
        # and paint them as far more aggressive than they are.
        advertised = msrp + markup - disc - reb_applied
        rows.append({
            "vin": vin,
            "stock_number": o.get("stockNumber"),
            "year": o.get("year"),
            "make": o.get("make"),
            "model": o.get("model"),
            "trim": o.get("trim"),
            "drivetrain": o.get("drive"),
            "body_style": o.get("body"),
            "type": o.get("type"),
            "certified": o.get("isCertified"),
            "is_courtesy": o.get("isCourtesy"),
            "in_transit": o.get("isInTransit"),
            "msrp": msrp,
            "dealer_discount": disc or None,
            "dealer_addons": markup or None,
            "universal_incentive": reb_everyone,
            "universal_applied": bool(reb_applied),
            "conditional_incentive": 0.0,
            "advertised_price": advertised,
            "doc_fee": money(p.get("docFee")),
            "conditional_detail": [], "universal_detail": [],
        })
    return rows


# --------------------------------------------------------------------- JSON-LD

def extract_jsonld(html):
    rows = []
    for blk in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            data = json.loads(blk)
        except Exception:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
                vin = node.get("vehicleIdentificationNumber")
                if not vin:
                    continue
                offers = node.get("offers") or {}
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                rows.append({
                    "vin": vin,
                    "stock_number": node.get("sku"),
                    "year": node.get("vehicleModelDate"),
                    "make": (node.get("manufacturer") or {}).get("name")
                            if isinstance(node.get("manufacturer"), dict) else node.get("manufacturer"),
                    "model": node.get("model") if isinstance(node.get("model"), str) else None,
                    "trim": node.get("name"),
                    "condition": node.get("itemCondition"),
                    "advertised_price": money(offers.get("price")),
                    "msrp": None, "dealer_discount": None,
                    "universal_incentive": 0.0, "conditional_incentive": 0.0,
                    "conditional_detail": [], "universal_detail": [],
                })
    return rows


# ----------------------------------------------------------------- orchestration

def detect_platform(html):
    if "ws-inv-data" in html or "ddc-data-layer" in html:
        return "dealercom"
    if re.search(r'"(markupsTotal|rebatesEveryoneTotal)"', html):
        return "fox"
    # Dealer Inspire / Cars Commerce (our own store). Named explicitly so the run
    # summary reports what it actually hit rather than silently degrading to the
    # JSON-LD fallback, which carries price but no discount breakdown.
    if re.search(r'dealerinspire|x-cars-signature|cars-commerce', html, re.I):
        return "dealerinspire"
    if "application/ld+json" in html:
        return "jsonld"
    return "unknown"


# A real new VW sits roughly $20k-75k. Anything outside this is not a price we
# mis-read the currency on -- it is a parser reading the wrong field. Bounds are
# generous on purpose: the job is to catch structural failure, not to second-guess
# an unusual deal.
MSRP_MIN, MSRP_MAX = 18000, 90000


def plausible(rec):
    """Reject records that cannot be real, and say why.

    This exists because of a live failure: a mis-resolved payload produced 96
    records reading MSRP $294 / discount $295 / price -$11. Every one looked like
    a valid row to the analyzer, which would have averaged them into a market
    price. A parser that emits nonsense is worse than one that emits nothing,
    because nothing is visible and nonsense is not.
    """
    msrp, adv = rec.get("msrp"), rec.get("advertised_price")
    disc = rec.get("dealer_discount")
    if msrp is not None and not (MSRP_MIN <= msrp <= MSRP_MAX):
        return False, f"MSRP {msrp:,.0f} outside ${MSRP_MIN:,}-${MSRP_MAX:,}"
    if adv is not None and adv <= 0:
        return False, f"advertised price {adv:,.0f} is not positive"
    if adv is not None and not (MSRP_MIN * 0.6 <= adv <= MSRP_MAX):
        return False, f"advertised price {adv:,.0f} implausible"
    if disc is not None and msrp and disc > msrp * 0.45:
        return False, f"discount {disc:,.0f} exceeds 45% of MSRP"
    if disc is not None and disc < 0:
        return False, f"negative discount {disc:,.0f}"
    return True, None


def is_new(rec):
    """New retail only. Courtesy/loaner, demo, in-transit and CPO units carry
    different pricing logic and must not be averaged into new retail stock."""
    cond = str(rec.get("condition") or "").lower()
    typ = str(rec.get("type") or "").lower()
    if rec.get("certified") is True or rec.get("is_courtesy") is True:
        return False
    if "used" in cond or "used" in typ or "certified" in cond:
        return False
    if typ in ("u", "c"):            # Fox: U=used, C=certified
        return False
    if typ == "n" or "new" in cond or "new" in typ:
        return True
    return cond == "" and typ == ""


# Platforms name the same car differently -- "Jetta Sedan" on one site, "Jetta" on
# another. Left alone they become separate model lines and never get compared,
# which quietly removes the largest competitor from a model's market average.
MODEL_ALIASES = {
    "jetta sedan": "Jetta", "jetta gli sedan": "Jetta GLI",
    "golf gti": "Golf GTI", "gti": "Golf GTI", "golf r": "Golf R",
    "tiguan": "Tiguan", "taos": "Taos", "atlas": "Atlas",
    "atlas cross sport": "Atlas Cross Sport",
    "id.4": "ID.4", "id4": "ID.4", "id. buzz": "ID. Buzz", "id.buzz": "ID. Buzz",
}


def normalize_model(name):
    if not name:
        return name
    key = re.sub(r"\s+", " ", str(name).strip().lower())
    if key in MODEL_ALIASES:
        return MODEL_ALIASES[key]
    for suffix in (" sedan", " suv", " hatchback", " wagon"):
        if key.endswith(suffix):
            base = key[: -len(suffix)]
            return MODEL_ALIASES.get(base, base.title())
    return str(name).strip()


def days_in_stock(rec, today=None):
    d = rec.get("inventory_date")
    if not d:
        return None
    today = today or date.today()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return (today - datetime.strptime(str(d), fmt).date()).days
        except ValueError:
            continue
    return None


def extract(html, dealer, url):
    plat = detect_platform(html)
    rows = {"dealercom": extract_dealercom, "fox": extract_fox,
            "jsonld": extract_jsonld}.get(plat, lambda h: [])(html)
    if not rows and plat != "jsonld":
        rows = extract_jsonld(html)  # last-resort fallback
        if rows:
            # Worth saying out loud: a dealer collected this way has price data but
            # no discount breakdown, so its "discount" cannot be compared against a
            # dealer whose itemized ladder we parsed in full.
            print(f"  NOTE: {dealer} fell back to JSON-LD ({plat} mapping "
                  f"unverified) - price only, NO discount components",
                  file=sys.stderr)
    out, rejected = [], []
    for r in rows:
        if not is_new(r):
            continue
        ok, why = plausible(r)
        if not ok:
            rejected.append((r.get("vin"), why))
            continue
        r["dealer"] = dealer
        r["source_url"] = url
        r["platform"] = plat
        r["model"] = normalize_model(r.get("model"))
        r["days_in_stock"] = days_in_stock(r)
        r["captured_at"] = datetime.now().isoformat(timespec="seconds")
        # Dealer.com applies universal incentives above the advertised price;
        # some platforms disclose them without deducting. Record which, so the
        # analyzer can put both on one basis instead of comparing a net price
        # against a gross one.
        r.setdefault("universal_applied", True)
        # Derived, never invented: only compute when both inputs are real.
        if r.get("msrp") and r.get("dealer_discount") is not None:
            r["dealer_discount_pct"] = round(r["dealer_discount"] / r["msrp"] * 100, 2)
        else:
            r["dealer_discount_pct"] = None
        out.append(r)

    if rejected:
        print(f"  REJECTED {len(rejected)} implausible record(s) - likely a parser "
              f"or platform change, not real pricing:", file=sys.stderr)
        for vin, why in rejected[:3]:
            print(f"    {vin}: {why}", file=sys.stderr)
        if len(rejected) > 3:
            print(f"    ... and {len(rejected) - 3} more", file=sys.stderr)
    return out, plat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--dealer")
    ap.add_argument("--html", help="parse a local HTML file instead of fetching")
    ap.add_argument("--config")
    ap.add_argument("--out")
    ap.add_argument("--out-dir")
    ap.add_argument("--max-pages", type=int, default=25)
    args = ap.parse_args()

    targets = []
    if args.config:
        cfg = json.load(open(args.config))
        for d in cfg.get("dealerships", []):
            if d.get("srp_url"):
                targets.append((d["key"], d["srp_url"], d.get("page_param", "start"),
                                d.get("page_size", 24)))
    elif args.url:
        targets.append((args.dealer or "unknown", args.url, "start", 24))
    elif args.html:
        html = open(args.html, encoding="utf-8", errors="replace").read()
        recs, plat = extract(html, args.dealer or "unknown", args.html)
        print(json.dumps(recs, indent=1))
        print(f"platform={plat} records={len(recs)}", file=sys.stderr)
        return 0 if recs else 3
    else:
        ap.error("need --url, --html or --config")

    all_recs, blocked, empty = [], [], []
    for key, url, page_param, page_size in targets:
        print(f"[{key}] {url}", file=sys.stderr)
        recs, page, seen = [], 0, set()
        while page < args.max_pages:
            sep = "&" if "?" in url else "?"
            purl = url if page == 0 else f"{url}{sep}{page_param}={page * page_size}"
            html, status = fetch(purl)
            if status in (403, 429) or (status == 0 and page == 0):
                blocked.append((key, purl, status))
                print(f"  BLOCKED http={status} -> needs a real browser "
                      f"(see references/data-collection.md)", file=sys.stderr)
                break
            got, plat = extract(html, key, purl)
            fresh = [r for r in got if r["vin"] not in seen]
            for r in fresh:
                seen.add(r["vin"])
            recs.extend(fresh)
            print(f"  page {page}: +{len(fresh)} (platform={plat})", file=sys.stderr)
            if not fresh:
                break
            page += 1
        if not recs and not any(b[0] == key for b in blocked):
            empty.append(key)
        all_recs.extend(recs)
        if args.out_dir and recs:
            os.makedirs(args.out_dir, exist_ok=True)
            p = os.path.join(args.out_dir, f"{key}.json")
            json.dump(recs, open(p, "w"), indent=1)
            print(f"  wrote {len(recs)} -> {p}", file=sys.stderr)

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        json.dump(all_recs, open(args.out, "w"), indent=1)
        print(f"wrote {len(all_recs)} records -> {args.out}", file=sys.stderr)
    elif not args.out_dir:
        print(json.dumps(all_recs, indent=1))

    # The summary is deliberately loud. An analyst who does not know a dealer
    # was missed will report a market average that quietly excludes a competitor.
    print("\n=== EXTRACTION SUMMARY ===", file=sys.stderr)
    by = {}
    for r in all_recs:
        by[r["dealer"]] = by.get(r["dealer"], 0) + 1
    for k, v in sorted(by.items()):
        print(f"  {k}: {v} new units", file=sys.stderr)
    for k, u, s in blocked:
        print(f"  {k}: BLOCKED (http {s}) - NOT in dataset", file=sys.stderr)
    for k in empty:
        print(f"  {k}: 0 records - selector/platform change? - NOT in dataset", file=sys.stderr)
    if blocked:
        return 2
    return 0 if all_recs else 3


if __name__ == "__main__":
    sys.exit(main())
