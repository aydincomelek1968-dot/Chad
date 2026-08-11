#!/usr/bin/env python3
"""
Normalize extracted VW inventory and compute competitive position by model line.

The arithmetic here is deliberately boring and fully auditable. Every number the
final report cites should be traceable to a record that actually exists. The one
piece of judgment baked in is the position-classification thresholds, which are
tunable and explained in references/analysis-playbook.md.

Usage:
  analyze_pricing.py --in data/raw/ --us KEY [--prior data/snapshots/PRIOR.json]
                     [--out analysis.json] [--md report_tables.md]
"""

import argparse
import glob
import json
import os
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime

# --- Tunable thresholds -------------------------------------------------------
# Anchored to VW front-end gross, roughly $1.5-2.5k/unit. A $500 gap is about a
# quarter of a deal's gross and is where shoppers start noticing; $1,200+ is
# where a cross-shopper stops calling you. Adjust in config if your market moves.
GAP_LEADER = 150      # within this of the lowest -> effectively the price leader
GAP_COMPETITIVE = 500   # within this of competitor median -> competitive
GAP_SLIGHTLY_HIGH = 1200  # beyond this above median -> uncompetitive

MIN_UNITS_DEALER_CELL = 3   # below this, a dealer's average is anecdote
MIN_DEALERS_MARKET = 2      # below this, there is no "market" to average
LOSS_LEADER_SD = 2.0        # discount this many SD above the dealer's own mean


def pct(n, d):
    return round(n / d * 100, 2) if (n is not None and d) else None


def load(indir):
    recs = []
    for p in sorted(glob.glob(os.path.join(indir, "*.json"))):
        try:
            data = json.load(open(p))
        except Exception as e:
            print(f"! skip {p}: {e}", file=sys.stderr)
            continue
        if isinstance(data, list):
            recs.extend(data)
    return recs


def normalize(recs, include_fees=False):
    """Put every dealer on one comparable basis.

    Two traps this guards against:
      1. Conditional incentives (military/grad/loyalty/finance) are stripped out
         of the comparable price. They are real money to *some* buyers but they
         are not a discount every shopper receives, and treating them as one
         makes an ordinary store look like a price leader.
      2. Doc fees. Some sites fold the doc fee into the advertised price and
         some do not, which is a several-hundred-dollar phantom gap. We compare
         on a fee-excluded basis by default and record the fee separately.
    """
    out = []
    for r in recs:
        msrp = r.get("msrp")
        adv = r.get("advertised_price")
        fee = r.get("doc_fee") or 0.0
        disc = r.get("dealer_discount")
        uni = r.get("universal_incentive") or 0.0
        cond = r.get("conditional_incentive") or 0.0

        comparable = adv
        # Put every dealer on one basis for universal factory money. Observed live:
        # one store deducts $1,500 of VW cash from its shown price and another
        # discloses the same $1,500 without deducting it. Comparing those raw makes
        # the first look $1,500 cheaper on identical economics. Universal money is
        # available to every buyer, so net it out everywhere.
        if comparable is not None and not r.get("universal_applied", True):
            comparable = comparable - (r.get("universal_incentive") or 0.0)
        if comparable is not None and not include_fees:
            comparable = comparable - fee

        # Reconciliation is our independent check that we parsed the ladder
        # correctly. A record that does not reconcile is reported, not silently
        # trusted, because a mis-parsed ladder looks exactly like a real price.
        reconciles = None
        if None not in (msrp, adv) and disc is not None:
            addons = r.get("dealer_addons") or 0.0
            applied = uni if r.get("universal_applied", True) else 0.0
            # Sites differ on whether the doc fee and the factory rebate sit inside
            # the advertised number, so accept any of the conventions actually
            # observed rather than forcing one and crying wolf on the rest.
            candidates = [
                msrp + fee - disc - applied,
                msrp - disc - applied,
                msrp + addons + fee - disc - applied,
                msrp + addons - disc - applied,
            ]
            reconciles = min(abs(c - adv) for c in candidates) < 1.0

        rec = dict(r)
        rec.update({
            "comparable_price": comparable,
            "total_customer_discount": (msrp - adv) if None not in (msrp, adv) else None,
            "true_dealer_discount": disc,
            "true_dealer_discount_pct": pct(disc, msrp),
            "conditional_incentive": cond,
            "conditional_share_of_discount": pct(cond, (msrp - adv)) if (
                None not in (msrp, adv) and (msrp - adv)) else None,
            "reconciles": reconciles,
        })
        out.append(rec)
    return out


def _agg(units):
    ds = [u["true_dealer_discount"] for u in units if u.get("true_dealer_discount") is not None]
    dp = [u["true_dealer_discount_pct"] for u in units if u.get("true_dealer_discount_pct") is not None]
    ms = [u["msrp"] for u in units if u.get("msrp")]
    cp = [u["comparable_price"] for u in units if u.get("comparable_price")]
    age = [u["days_in_stock"] for u in units if u.get("days_in_stock") is not None]
    return {
        "units": len(units),
        "avg_msrp": round(st.mean(ms), 0) if ms else None,
        "avg_discount": round(st.mean(ds), 0) if ds else None,
        "avg_discount_pct": round(st.mean(dp), 2) if dp else None,
        "min_price": round(min(cp), 0) if cp else None,
        "median_price": round(st.median(cp), 0) if cp else None,
        "avg_days_in_stock": round(st.mean(age), 0) if age else None,
        "units_over_90_days": sum(1 for a in age if a > 90) if age else 0,
        "addon_units": sum(1 for u in units if u.get("dealer_addons")),
        "conditional_units": sum(1 for u in units if u.get("conditional_incentive")),
        "thin_sample": len(units) < MIN_UNITS_DEALER_CELL,
    }


def flag_loss_leaders(units):
    """A single deeply-cut car is a tactic, not a pricing strategy. Averaging it
    in makes a competitor look broadly aggressive when they cut one roof-line."""
    ds = [u["true_dealer_discount"] for u in units if u.get("true_dealer_discount") is not None]
    if len(ds) < 4:
        return []
    mean, sd = st.mean(ds), (st.pstdev(ds) or 0)
    if sd == 0:
        return []
    return [u["vin"] for u in units
            if u.get("true_dealer_discount") is not None
            and (u["true_dealer_discount"] - mean) / sd > LOSS_LEADER_SD]


def classify(our_price, comp_prices):
    if our_price is None or not comp_prices:
        return "Insufficient Data", None
    low, med = min(comp_prices), st.median(comp_prices)
    gap = our_price - med
    if our_price <= low + GAP_LEADER:
        return "Market Leader", round(gap, 0)
    if gap <= GAP_COMPETITIVE:
        return "Competitive", round(gap, 0)
    if gap <= GAP_SLIGHTLY_HIGH:
        return "Slightly High", round(gap, 0)
    return "Uncompetitive", round(gap, 0)


def _pctile(sorted_vals, q):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    i = q * (len(sorted_vals) - 1)
    lo, hi = int(i), min(int(i) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (i - lo)


def recommend(comp_prices, our_msrp, our_universal, inv_pressure):
    """Derive the three price points from the competitor distribution.

    Target      -> land just inside the competitive band (median - small buffer)
    Aggressive  -> match the most aggressive credible competitor (10th pctile)
    Defensive   -> the most we can hold and still sit inside the competitive band

    Inventory pressure shifts the whole ladder: carrying an outsized share of the
    market's units means we need volume more than we need the next $500 of gross.

    Two discount figures come out of this and they are not interchangeable:

      total_off_msrp  - what the shopper perceives (dealer money + factory money)
      dealer_discount - the only lever management actually controls

    Reporting only the first is how a store talks itself into "giving" $4,000
    when $1,500 of that is VW's money and $600 is a doc fee. The dealer-discount
    figure is the one that costs gross, so it is the one to act on.
    """
    if not comp_prices or not our_msrp:
        return None
    srt = sorted(comp_prices)
    med = st.median(srt)
    p10 = _pctile(srt, 0.10)

    target_price = med - 200
    aggressive_price = min(p10, med - 750)
    defensive_price = med + GAP_COMPETITIVE - 100

    if inv_pressure == "overstocked":
        target_price -= 250
        aggressive_price -= 250
    elif inv_pressure == "understocked":
        target_price += 250
        defensive_price += 250

    uni = our_universal or 0.0

    def as_disc(p):
        # comp prices are fee-excluded, so: price = MSRP - dealer_disc - universal
        dealer_disc = our_msrp - uni - p
        total_off = our_msrp - p
        return {
            "advertised_price": round(p, 0),
            "dealer_discount": round(dealer_disc, 0),
            "dealer_discount_pct": pct(dealer_disc, our_msrp),
            "total_off_msrp": round(total_off, 0),
            "total_off_msrp_pct": pct(total_off, our_msrp),
            "assumed_universal_incentive": round(uni, 0),
        }

    return {"target": as_disc(target_price),
            "aggressive": as_disc(aggressive_price),
            "defensive": as_disc(defensive_price)}


def analyze(recs, us, prior=None):
    by_model = defaultdict(lambda: defaultdict(list))
    by_trim = defaultdict(lambda: defaultdict(list))
    for r in recs:
        model = (r.get("model") or "Unknown").strip()
        by_model[model][r["dealer"]].append(r)
        key = f"{model} | {(r.get('trim') or '?').strip()}"
        by_trim[key][r["dealer"]].append(r)

    total_by_dealer = defaultdict(int)
    for r in recs:
        total_by_dealer[r["dealer"]] += 1

    models = {}
    for model, dealers in sorted(by_model.items()):
        stats = {d: _agg(u) for d, u in dealers.items()}
        leaders = {d: flag_loss_leaders(u) for d, u in dealers.items()}
        ours = dealers.get(us, [])
        comps = {d: u for d, u in dealers.items() if d != us}

        # Competitor price pool excludes flagged loss leaders.
        comp_prices = []
        for d, u in comps.items():
            ll = set(leaders.get(d, []))
            comp_prices += [x["comparable_price"] for x in u
                            if x.get("comparable_price") and x["vin"] not in ll]

        our_prices = [x["comparable_price"] for x in ours if x.get("comparable_price")]
        our_med = st.median(our_prices) if our_prices else None
        our_msrp = st.mean([x["msrp"] for x in ours if x.get("msrp")]) if ours else None

        market_units = sum(s["units"] for s in stats.values())
        our_units = stats.get(us, {}).get("units", 0)
        expected = market_units / len(stats) if stats else 0
        pressure = "balanced"
        if our_units and expected:
            if our_units > expected * 1.4:
                pressure = "overstocked"
            elif our_units < expected * 0.6:
                pressure = "understocked"

        position, gap = classify(our_med, comp_prices)
        thin_market = len(comps) < MIN_DEALERS_MARKET
        if thin_market:
            # One competitor is a data point, not a market. Say so rather than
            # dressing a two-store comparison up as a market position.
            position = "Insufficient Data"

        disc_by_dealer = {d: s["avg_discount_pct"] for d, s in stats.items()
                          if s["avg_discount_pct"] is not None}
        most_agg = max(disc_by_dealer, key=disc_by_dealer.get) if disc_by_dealer else None
        least_agg = min(disc_by_dealer, key=disc_by_dealer.get) if disc_by_dealer else None

        models[model] = {
            "by_dealer": stats,
            "loss_leaders": {d: v for d, v in leaders.items() if v},
            "our_units": our_units,
            "market_units": market_units,
            "our_share_of_market_inventory": pct(our_units, market_units),
            "inventory_pressure": pressure,
            "our_median_price": round(our_med, 0) if our_med else None,
            "competitor_median_price": round(st.median(comp_prices), 0) if comp_prices else None,
            "competitor_min_price": round(min(comp_prices), 0) if comp_prices else None,
            "market_spread": round(max(comp_prices) - min(comp_prices), 0) if comp_prices else None,
            "position": position,
            "gap_vs_competitor_median": gap,
            "most_aggressive": most_agg,
            "least_aggressive": least_agg,
            "thin_market": thin_market,
            "our_avg_universal_incentive": round(
                st.mean([x.get("universal_incentive") or 0 for x in ours]), 0) if ours else None,
            # No recommendation without a market to derive it from. A confident
            # number built on one competitor is the failure this whole skill exists
            # to prevent.
            "recommendation": None if thin_market else recommend(
                comp_prices, our_msrp,
                st.mean([x.get("universal_incentive") or 0 for x in ours]) if ours else 0,
                pressure),
        }

    trims = {}
    for key, dealers in sorted(by_trim.items()):
        if us not in dealers or len(dealers) < 2:
            continue
        stats = {d: _agg(u) for d, u in dealers.items()}
        comp_p = [x["comparable_price"] for d, u in dealers.items() if d != us
                  for x in u if x.get("comparable_price")]
        our_p = [x["comparable_price"] for x in dealers[us] if x.get("comparable_price")]
        if not (comp_p and our_p):
            continue
        pos, gap = classify(st.median(our_p), comp_p)
        trims[key] = {"by_dealer": {d: s["units"] for d, s in stats.items()},
                      "our_median_price": round(st.median(our_p), 0),
                      "competitor_median_price": round(st.median(comp_p), 0),
                      "competitor_min_price": round(min(comp_p), 0),
                      "gap": gap, "position": pos,
                      "thin_sample": len(our_p) < MIN_UNITS_DEALER_CELL}

    # Data-quality panel. This exists so the report can state what it does NOT
    # know, which is the difference between analysis and confident invention.
    dq = {
        "total_records": len(recs),
        "dealers_present": sorted(total_by_dealer.keys()),
        "units_by_dealer": dict(total_by_dealer),
        "missing_msrp": sum(1 for r in recs if not r.get("msrp")),
        "missing_discount": sum(1 for r in recs if r.get("true_dealer_discount") is None),
        "failed_reconciliation": sum(1 for r in recs if r.get("reconciles") is False),
        "units_with_addons": sum(1 for r in recs if r.get("dealer_addons")),
        "units_with_conditional": sum(1 for r in recs if r.get("conditional_incentive")),
    }

    out = {"generated_at": datetime.now().isoformat(timespec="seconds"),
           "our_dealer": us, "data_quality": dq, "models": models, "trims": trims}

    if prior:
        out["week_over_week"] = deltas(prior, out)
    return out


def deltas(prior, current):
    """Movement is the signal a single snapshot cannot give you: who is getting
    more aggressive, on which model, and how fast."""
    res = {}
    pm = prior.get("models", {})
    for model, cur in current["models"].items():
        old = pm.get(model)
        if not old:
            res[model] = {"note": "new model line vs prior snapshot"}
            continue
        row = {}
        for d, s in cur["by_dealer"].items():
            o = old.get("by_dealer", {}).get(d)
            if not o:
                continue
            if s.get("avg_discount") is not None and o.get("avg_discount") is not None:
                row[d] = {
                    "discount_change": round(s["avg_discount"] - o["avg_discount"], 0),
                    "pct_change": round((s.get("avg_discount_pct") or 0)
                                        - (o.get("avg_discount_pct") or 0), 2),
                    "unit_change": s["units"] - o["units"],
                }
        movers = {d: v for d, v in row.items() if abs(v["discount_change"]) >= 250}
        res[model] = {"by_dealer": row, "notable_movers": movers}
    return res


def to_md(a):
    us = a["our_dealer"]
    L = ["# Executive Pricing Table",
         "",
         "Recommended figures are **dealer discount** (the lever you control), not",
         "total off MSRP. Factory money is shown separately so it is never double-counted.",
         "",
         "| Model | Our Avg Dealer Disc | Our Disc % | Mkt Median Price | Lowest Comp | Our Position | "
         "Target Disc | Aggressive | Defensive | Units (ours/mkt) |",
         "|---|---:|---:|---:|---:|---|---:|---:|---:|---:|"]
    for m, d in a["models"].items():
        s = d["by_dealer"].get(us, {})
        r = d.get("recommendation") or {}
        def f(x, p="$"):
            return f"{p}{x:,.0f}" if isinstance(x, (int, float)) else "n/a"
        def rec(k):
            v = (r.get(k) or {})
            if not v:
                return "n/a"
            return f"{f(v.get('dealer_discount'))} / {v.get('dealer_discount_pct')}%"
        L.append(
            f"| {m} | {f(s.get('avg_discount'))} | "
            f"{s.get('avg_discount_pct') if s.get('avg_discount_pct') is not None else 'n/a'}% | "
            f"{f(d.get('competitor_median_price'))} | {f(d.get('competitor_min_price'))} | "
            f"{d['position']} | {rec('target')} | {rec('aggressive')} | {rec('defensive')} | "
            f"{d['our_units']}/{d['market_units']} |")

    L += ["", "# Dealer Scorecard - Avg True Dealer Discount % of MSRP", ""]
    dealers = sorted({d for m in a["models"].values() for d in m["by_dealer"]})
    L.append("| Model | " + " | ".join(dealers) + " | Price Leader |")
    L.append("|---|" + "---:|" * len(dealers) + "---|")
    for m, d in a["models"].items():
        cells = []
        for dl in dealers:
            v = d["by_dealer"].get(dl, {}).get("avg_discount_pct")
            n = d["by_dealer"].get(dl, {}).get("units", 0)
            cells.append(f"{v}% (n={n})" if v is not None else "-")
        L.append(f"| {m} | " + " | ".join(cells) + f" | {d.get('most_aggressive') or '-'} |")

    dq = a["data_quality"]
    L += ["", "# Data Quality", "",
          f"- Records: {dq['total_records']} across {len(dq['dealers_present'])} dealers "
          f"({', '.join(dq['dealers_present'])})",
          f"- Units by dealer: {dq['units_by_dealer']}",
          f"- Missing MSRP: {dq['missing_msrp']} | Missing dealer discount: {dq['missing_discount']}",
          f"- Failed price-ladder reconciliation: {dq['failed_reconciliation']}",
          f"- Units carrying dealer add-ons: {dq['units_with_addons']}",
          f"- Units advertising conditional incentives: {dq['units_with_conditional']}"]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--us", required=True, help="dealer key for our store")
    ap.add_argument("--prior", help="prior snapshot JSON for week-over-week")
    ap.add_argument("--out")
    ap.add_argument("--md")
    ap.add_argument("--include-fees", action="store_true")
    args = ap.parse_args()

    recs = load(args.indir)
    if not recs:
        print("No records found. Run extract_inventory.py first.", file=sys.stderr)
        return 3
    recs = normalize(recs, include_fees=args.include_fees)
    if args.us not in {r["dealer"] for r in recs}:
        print(f"! '{args.us}' not in dataset: {sorted({r['dealer'] for r in recs})}",
              file=sys.stderr)
        return 3
    prior = json.load(open(args.prior)) if args.prior and os.path.exists(args.prior) else None
    a = analyze(recs, args.us, prior)

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        json.dump(a, open(args.out, "w"), indent=1)
        print(f"wrote {args.out}", file=sys.stderr)
    if args.md:
        open(args.md, "w").write(to_md(a))
        print(f"wrote {args.md}", file=sys.stderr)
    if not args.out and not args.md:
        print(to_md(a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
