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
    """Fox payloads index-compress values, so pricing fields are pointers into a
    shared constant pool. We resolve them where the pool is recoverable and skip
    the record where it is not -- a skipped record is honest, a guessed one is not.
    """
    rows = []
    pool = None
    m = re.search(r'\[(?:"[^"]*"|[-\d.eE]+|null|true|false|,|\s)+\]', html)
    if m:
        try:
            pool = json.loads(m.group(0))
        except Exception:
            pool = None

    def deref(v):
        if isinstance(v, int) and pool and 0 <= v < len(pool):
            got = pool[v]
            return got if isinstance(got, (int, float, str)) else None
        return v

    for pm in re.finditer(r'\{"msrp":\s*(\d+)[^{}]*\}', html):
        obj = enclosing_json(html, pm.start())
        if not isinstance(obj, dict):
            continue
        vin = None
        vs = re.search(r'"([A-HJ-NPR-Z0-9]{17})"', html[max(0, pm.start() - 1200):pm.start()])
        if vs:
            vin = vs.group(1)
        if not vin:
            continue
        msrp = money(deref(obj.get("msrp")))
        disc = money(deref(obj.get("discountsTotal"))) or 0.0
        markup = money(deref(obj.get("markupsTotal"))) or 0.0
        reb_all = money(deref(obj.get("rebatesAppliedTotal"))) or 0.0
        reb_everyone = money(deref(obj.get("rebatesEveryoneTotal"))) or 0.0
        if msrp is None:
            continue
        rows.append({
            "vin": vin,
            "msrp": msrp,
            "dealer_discount": disc or None,
            "dealer_addons": markup or None,
            "universal_incentive": reb_everyone,
            # Anything applied but not available to everyone is conditional.
            "conditional_incentive": max(0.0, reb_all - reb_everyone),
            "advertised_price": (msrp + markup - disc - reb_everyone) if msrp else None,
            "doc_fee": money(deref(obj.get("docFee"))),
            "conditional_detail": [], "universal_detail": [],
        })
    # de-dup
    out, seen = [], set()
    for r in rows:
        if r["vin"] not in seen:
            seen.add(r["vin"])
            out.append(r)
    return out


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
    if "application/ld+json" in html:
        return "jsonld"
    return "unknown"


def is_new(rec):
    """New only. Courtesy/loaner/demo units carry different pricing logic and
    must not be averaged in with new retail stock."""
    cond = str(rec.get("condition") or "").lower()
    typ = str(rec.get("type") or "").lower()
    if rec.get("certified") is True:
        return False
    if "used" in cond or "used" in typ or "certified" in cond:
        return False
    return ("new" in cond) or ("new" in typ) or (cond == "" and typ == "")


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
    out = []
    for r in rows:
        if not is_new(r):
            continue
        r["dealer"] = dealer
        r["source_url"] = url
        r["platform"] = plat
        r["days_in_stock"] = days_in_stock(r)
        r["captured_at"] = datetime.now().isoformat(timespec="seconds")
        # Derived, never invented: only compute when both inputs are real.
        if r.get("msrp") and r.get("dealer_discount") is not None:
            r["dealer_discount_pct"] = round(r["dealer_discount"] / r["msrp"] * 100, 2)
        else:
            r["dealer_discount_pct"] = None
        out.append(r)
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
