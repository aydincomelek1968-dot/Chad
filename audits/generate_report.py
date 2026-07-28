# -*- coding: utf-8 -*-
import json, html

SP = "/tmp/claude-0/-home-user-Chad/d7dc6d55-e04f-5614-b610-8f6a0c0ebd12/scratchpad/"
rows = json.load(open(SP + "joined.json"))

def money(n):
    return "${:,}".format(n)

# ---------------------------------------------------------------- rank data
RANKS = [
    {
        "model": "Tiguan 2.0T SE R-Line Black (FWD)",
        "vinpfx": "3VVHR…", "units": 21,
        "before": [("Larry H. Miller", 34709, True), ("Camelback", 35346, False),
                   ("VW North Scottsdale", 37544, None), ("Lunde's Peoria", 38610, False)],
        "after":  [("VW North Scottsdale", 34346, None), ("Larry H. Miller", 34709, True),
                   ("Camelback", 35346, False), ("Lunde's Peoria", 38610, False)],
        "note": "Fixing the feed makes us outright cheapest on our single highest-volume trim.",
        "sens": "If Larry Miller's unverified $1,082 accessories addendum is also unwound "
                "($33,627), we would land 2nd rather than 1st — still a two-place gain.",
    },
    {
        "model": "Atlas 2.0T SE w/Technology (FWD)",
        "vinpfx": "1V2JN…", "units": 13,
        "before": [("Camelback", 40791, False), ("Larry H. Miller", 40918, True),
                   ("Lunde's Peoria", 45792, False), ("VW North Scottsdale", 45932, None)],
        "after":  [("Camelback", 40791, False), ("Larry H. Miller", 40918, True),
                   ("VW North Scottsdale", 41734, None), ("Lunde's Peoria", 45792, False)],
        "note": "We currently list as the most expensive Atlas SE w/Tech in the market, "
                "$4,141 above Camelback. Fixing the feed closes that to $943.",
        "sens": None,
    },
    {
        "model": "Atlas Cross Sport 2.0T SE w/Technology (FWD)",
        "vinpfx": "1V2WC…", "units": 2,
        "before": [("Larry H. Miller", 39696, True), ("Camelback", 39775, False),
                   ("Lunde's Peoria", 44050, False), ("VW North Scottsdale", 45968, None)],
        "after":  [("Larry H. Miller", 39696, True), ("Camelback", 39775, False),
                   ("VW North Scottsdale", 41770, None), ("Lunde's Peoria", 44050, False)],
        "note": "Thin comparable set — only 2 of our 12 flagged Cross Sports are FWD SE w/Tech. "
                "The weakest of the three stories; do not lead with it.",
        "sens": None,
    },
]

US = "VW North Scottsdale"


def slope_chart(spec):
    """Bump chart: rank 1 at top, two columns (as listed / if fixed)."""
    W, H = 720, 228
    x1, x2 = 208, 512
    top, rowh = 52, 46
    def y(rank):
        return top + (rank - 1) * rowh

    before = {n: (i + 1, p) for i, (n, p, _) in enumerate(spec["before"])}
    after = {n: (i + 1, p) for i, (n, p, _) in enumerate(spec["after"])}

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {W} {H}" role="img" class="slope" '
        f'aria-label="Rank change for {html.escape(spec["model"])}">')
    # column headers
    parts.append(f'<text x="{x1}" y="26" class="colhead" text-anchor="middle">As listed today</text>')
    parts.append(f'<text x="{x2}" y="26" class="colhead" text-anchor="middle">If the feed were fixed</text>')
    parts.append(f'<line x1="60" y1="36" x2="{W-60}" y2="36" class="rule"/>')

    # rank guides
    for r in range(1, 5):
        parts.append(f'<text x="{x1-152}" y="{y(r)+4}" class="rankno">#{r}</text>')
        parts.append(f'<line x1="{x1-134}" y1="{y(r)}" x2="{x1-16}" y2="{y(r)}" class="guide"/>')
        parts.append(f'<text x="{x2+150}" y="{y(r)+4}" class="rankno" text-anchor="end">#{r}</text>')
        parts.append(f'<line x1="{x2+16}" y1="{y(r)}" x2="{x2+132}" y2="{y(r)}" class="guide"/>')

    for name, (rb, pb) in before.items():
        ra, pa = after[name]
        us = (name == US)
        cls = "us" if us else "other"
        moved = " moved" if rb != ra else ""
        parts.append(
            f'<g class="ln {cls}{moved}"><title>{html.escape(name)}: rank #{rb} '
            f'{money(pb)} → rank #{ra} {money(pa)}</title>')
        parts.append(f'<line x1="{x1}" y1="{y(rb)}" x2="{x2}" y2="{y(ra)}" class="slopeline"/>')
        parts.append(f'<circle cx="{x1}" cy="{y(rb)}" r="6" class="dot"/>')
        parts.append(f'<circle cx="{x2}" cy="{y(ra)}" r="6" class="dot"/>')
        lbl = name + (" — us" if us else "")
        parts.append(
            f'<text x="{x1-18}" y="{y(rb)-9}" class="dlabel" text-anchor="end">{html.escape(lbl)}</text>')
        parts.append(
            f'<text x="{x1-18}" y="{y(rb)+13}" class="dprice" text-anchor="end">{money(pb)}</text>')
        parts.append(
            f'<text x="{x2+18}" y="{y(ra)-9}" class="dlabel">{html.escape(lbl)}</text>')
        parts.append(f'<text x="{x2+18}" y="{y(ra)+13}" class="dprice">{money(pa)}</text>')
        parts.append('</g>')
    parts.append('</svg>')
    return "".join(parts)


# ---------------------------------------------------------------- bar chart
MODELS = [("Atlas", 42, 176316), ("Tiguan", 41, 118618), ("Atlas Cross Sport", 12, 50376),
          ("ID.4", 7, 46886), ("Jetta", 11, 24178), ("Taos", 10, 21980),
          ("Golf GTI", 6, 13188), ("Jetta GLI", 4, 9792), ("Golf R", 3, 2094)]


def bar_chart():
    W = 720
    rowh, top, labw, barx = 34, 34, 150, 172
    maxv = max(m[2] for m in MODELS)
    plotw = W - barx - 116
    H = top + len(MODELS) * rowh + 16
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" class="bars" '
         f'aria-label="Dollars hidden from cars.com shoppers by model">']
    for gx in range(0, 5):
        v = maxv * gx / 4
        x = barx + plotw * gx / 4
        p.append(f'<line x1="{x:.1f}" y1="{top-12}" x2="{x:.1f}" y2="{H-18}" class="grid"/>')
        p.append(f'<text x="{x:.1f}" y="{top-20}" class="tick" text-anchor="middle">'
                 f'${v/1000:.0f}k</text>')
    for i, (name, units, val) in enumerate(MODELS):
        y = top + i * rowh
        w = plotw * val / maxv
        p.append(f'<g class="bar"><title>{name}: {money(val)} across {units} units</title>')
        p.append(f'<text x="{labw}" y="{y+15}" class="blabel" text-anchor="end">{name}</text>')
        p.append(f'<rect x="{barx}" y="{y+2}" width="{max(w,3):.1f}" height="18" rx="4" class="brect"/>')
        p.append(f'<text x="{barx+w+10:.1f}" y="{y+16}" class="bval">{money(val)} '
                 f'<tspan class="bunits">· {units}u</tspan></text>')
        p.append('</g>')
    p.append(f'<line x1="{barx}" y1="{top-12}" x2="{barx}" y2="{H-18}" class="axis"/>')
    p.append('</svg>')
    return "".join(p)


def comp_chart():
    W, H = 720, 116
    x0, plotw = 26, 668
    total = 463428
    bonus, fee = 368500, 94928
    wb = plotw * bonus / total
    wf = plotw * fee / total
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" class="comp" '
         f'aria-label="Composition of the total gap">']
    p.append(f'<g class="seg s1"><title>Suppressed customer bonus: {money(bonus)} '
             f'(79.5% of the gap)</title>'
             f'<rect x="{x0}" y="30" width="{wb-2:.1f}" height="30" rx="4" class="r1"/></g>')
    p.append(f'<g class="seg s2"><title>Dealer fee baked into the price field: {money(fee)} '
             f'(20.5% of the gap)</title>'
             f'<rect x="{x0+wb:.1f}" y="30" width="{wf-2:.1f}" height="30" rx="4" class="r2"/></g>')
    p.append(f'<text x="{x0+8}" y="50" class="seglab">{money(bonus)}</text>')
    p.append(f'<text x="{x0+wb+8:.1f}" y="50" class="seglab">{money(fee)}</text>')
    p.append(f'<text x="{x0}" y="82" class="segsub">Suppressed customer bonus · 79.5%</text>')
    p.append(f'<text x="{x0+wb:.1f}" y="82" class="segsub">$698 dealer fee · 20.5%</text>')
    p.append('</svg>')
    return "".join(p)


# ---------------------------------------------------------------- appendix
def model_of(t):
    if "Cross Sport" in t: return "Atlas Cross Sport"
    if "Atlas" in t: return "Atlas"
    if "Tiguan" in t: return "Tiguan"
    if "GLI" in t: return "Jetta GLI"
    if "Jetta" in t: return "Jetta"
    if "Taos" in t: return "Taos"
    if "Golf R" in t: return "Golf R"
    if "GTI" in t: return "Golf GTI"
    if "ID.4" in t: return "ID.4"
    return "other"

order = ["Atlas", "Tiguan", "Atlas Cross Sport", "ID.4", "Jetta", "Taos",
         "Golf GTI", "Jetta GLI", "Golf R"]
for r in rows:
    r["model"] = model_of(r["desc"])
rows.sort(key=lambda r: (order.index(r["model"]), -r["delta"], r["vin"]))

trs = []
for i, r in enumerate(rows, 1):
    TAG = {"Retail Customer Bonus": "Retail", "Customer Bonus": "Cust."}
    bl = " + ".join(f"${v:,} {TAG.get(k, k)}" for k, v in r["bonus_labels"]) or "—"
    trs.append(
        "<tr><td class=n>{i}</td><td class=vin>{vin}</td><td>{stock}</td><td>{desc}</td>"
        "<td class=num>{cars}</td><td class=num>{msrp}</td><td class=num>{disc}</td>"
        "<td class=num>{sale}</td><td class=bon>{bl}</td><td class=num>{low}</td>"
        "<td class='num dl'>{d}</td></tr>".format(
            i=i, vin=r["vin"], stock=r["stock"] or "—", desc=html.escape(r["desc"]),
            cars=money(r["cars"]), msrp=money(r["msrp"]),
            disc=money(r["disc"]) if r["disc"] else "—",
            sale=money(r["sale"]), bl=html.escape(bl), low=money(r["lowest"]),
            d=money(r["delta"])))
appendix = "\n".join(trs)

rank_blocks = []
for s in RANKS:
    rb = {n: i + 1 for i, (n, _, _) in enumerate(s["before"])}[US]
    ra = {n: i + 1 for i, (n, _, _) in enumerate(s["after"])}[US]
    sens = (f'<p class="sens"><strong>Sensitivity.</strong> {s["sens"]}</p>' if s["sens"] else "")
    rank_blocks.append(f"""
<div class="rankcard">
  <div class="rankhead">
    <div>
      <h3>{html.escape(s['model'])}</h3>
      <p class="sub">VIN config <code>{s['vinpfx']}</code> · {s['units']} of our units</p>
    </div>
    <div class="rankmove">
      <span class="rk before">#{rb}</span>
      <span class="arrow">→</span>
      <span class="rk after">#{ra}</span>
      <span class="ofn">of 4</span>
    </div>
  </div>
  {slope_chart(s)}
  <p class="note">{html.escape(s['note'])}</p>
  {sens}
</div>""")

CSS = """
:root{color-scheme:light dark;
 --surface-1:#fcfcfb;--plane:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;
 --grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);
 --s1:#2a78d6;--s2:#eb6834;--good:#006300;--crit:#d03b3b;--wash:#eef4fd;}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme=light])){
 --surface-1:#1a1a19;--plane:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;
 --grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
 --s1:#3987e5;--s2:#d95926;--good:#0ca30c;--crit:#d03b3b;--wash:#15233a;}}
:root[data-theme=dark]{--surface-1:#1a1a19;--plane:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;
 --muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
 --s1:#3987e5;--s2:#d95926;--good:#0ca30c;--crit:#d03b3b;--wash:#15233a;}
*{box-sizing:border-box}
body{margin:0;background:var(--plane);color:var(--ink);
 font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;}
.wrap{max-width:880px;margin:0 auto;padding:44px 30px 72px}
header.top{border-bottom:2px solid var(--ink);padding-bottom:20px;margin-bottom:28px}
.eyebrow{font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);
 font-weight:600;margin:0 0 8px}
h1{font-size:29px;line-height:1.22;margin:0 0 10px;letter-spacing:-.015em}
.meta{color:var(--ink2);font-size:13.5px;margin:0}
.verdict{display:inline-flex;align-items:center;gap:9px;margin-top:16px;
 background:var(--crit);color:#fff;padding:7px 15px;border-radius:999px;
 font-weight:700;font-size:13px;letter-spacing:.03em}
.verdict .dot{width:8px;height:8px;border-radius:50%;background:#fff;opacity:.9}
.repl{margin-top:13px;font-size:12.5px;color:var(--ink2);background:var(--wash);
 border-radius:8px;padding:10px 13px;line-height:1.5}
.repl strong{color:var(--good)}
.urgent{border-left:3px solid var(--crit);background:var(--surface-1);
 border:1px solid var(--border);border-left:3px solid var(--crit);
 border-radius:8px;padding:14px 17px;margin:20px 0;font-size:14px}
h2{font-size:19px;margin:44px 0 6px;letter-spacing:-.01em;
 padding-bottom:8px;border-bottom:1px solid var(--border)}
h2 .kicker{color:var(--muted);font-weight:400;font-size:13px;margin-left:8px}
h3{font-size:15.5px;margin:0 0 3px}
p{margin:11px 0}
.lede{font-size:16px;color:var(--ink2)}
code{font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--wash);
 padding:1px 5px;border-radius:4px}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0 8px}
.tile{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:14px}
.tile .v{font-size:25px;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.tile .k{font-size:11.5px;color:var(--muted);margin-top:5px;line-height:1.35}
.tile.hero .v{color:var(--crit)}
.formula{background:var(--surface-1);border:1px solid var(--border);
 border-left:3px solid var(--s1);border-radius:8px;padding:16px 18px;margin:18px 0}
.formula .f{font:15px ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:600}
.formula .c{font-size:13px;color:var(--ink2);margin-top:7px}
figure{margin:20px 0 8px;background:var(--surface-1);border:1px solid var(--border);
 border-radius:10px;padding:18px 16px 12px}
figcaption{font-size:12.5px;color:var(--muted);margin-top:10px;padding:0 4px}
svg{width:100%;height:auto;display:block;overflow:visible}
.colhead{font-size:12px;fill:var(--muted);font-weight:600;letter-spacing:.05em;
 text-transform:uppercase}
.rule{stroke:var(--border);stroke-width:1}
.guide{stroke:var(--grid);stroke-width:1;stroke-dasharray:2 3}
.rankno{font-size:12px;fill:var(--muted);font-weight:700}
.axis{stroke:var(--axis);stroke-width:1}
.grid{stroke:var(--grid);stroke-width:1}
.tick{font-size:11px;fill:var(--muted)}
.slopeline{stroke:var(--muted);stroke-width:2;fill:none;opacity:.42}
.dot{fill:var(--muted);stroke:var(--surface-1);stroke-width:2}
.dlabel{font-size:12px;fill:var(--ink2)}
.dprice{font-size:12px;fill:var(--muted);font-variant-numeric:tabular-nums}
.ln.us .slopeline{stroke:var(--s1);stroke-width:3;opacity:1}
.ln.us .dot{fill:var(--s1);r:7}
.ln.us .dlabel{fill:var(--ink);font-weight:700}
.ln.us .dprice{fill:var(--ink);font-weight:600}
.ln:hover .slopeline{opacity:1;stroke-width:3.5}
.ln:hover .dlabel{fill:var(--ink)}
.brect{fill:var(--s1)}
.blabel{font-size:12.5px;fill:var(--ink2)}
.bval{font-size:12.5px;fill:var(--ink);font-weight:650;font-variant-numeric:tabular-nums}
.bunits{fill:var(--muted);font-weight:400}
.bar:hover .brect{fill:var(--s2)}
.r1{fill:var(--s1)}.r2{fill:var(--s2)}
.seglab{font-size:13.5px;fill:#fff;font-weight:700;font-variant-numeric:tabular-nums}
.segsub{font-size:12px;fill:var(--ink2)}
.rankcard{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;
 padding:18px 18px 14px;margin:18px 0}
.rankhead{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;
 margin-bottom:6px}
.sub{margin:0;font-size:12.5px;color:var(--muted)}
.rankmove{display:flex;align-items:center;gap:7px;white-space:nowrap}
.rk{font-size:17px;font-weight:800;padding:3px 10px;border-radius:7px}
.rk.before{background:var(--wash);color:var(--ink2)}
.rk.after{background:var(--good);color:#fff}
.arrow{color:var(--muted);font-size:15px}
.ofn{font-size:11.5px;color:var(--muted)}
.note{font-size:13px;color:var(--ink2);margin:6px 0 0}
.sens{font-size:12.5px;color:var(--muted);margin:7px 0 0;padding-left:11px;
 border-left:2px solid var(--grid)}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:13px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--border);vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);
 font-weight:700;border-bottom:1.5px solid var(--axis)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tbody tr:hover{background:var(--wash)}
.dl{font-weight:700;color:var(--crit)}
tfoot td{font-weight:700;border-top:1.5px solid var(--axis);border-bottom:none}
.callout{background:var(--wash);border-radius:9px;padding:15px 18px;margin:18px 0;
 font-size:14px}
.callout strong{color:var(--ink)}
ul{margin:11px 0;padding-left:20px}li{margin:5px 0}
.appx table{font-size:10.5px}
.appx td,.appx th{padding:2.5px 5px;white-space:nowrap}
.appx th{white-space:normal}
.appx .vin{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10px}
.appx .bon{font-size:10px;color:var(--ink2)}
.appx .n{color:var(--muted)}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--border);
 font-size:12px;color:var(--muted)}
@media print{
 @page{size:letter;margin:14mm 12mm}
 body{background:#fff}
 .wrap{max-width:none;padding:0}
 .rankcard,figure,.tile,.callout,.formula{break-inside:avoid}
 h2{break-after:avoid}
 .pagebreak{break-before:page}
 tbody tr:hover{background:none}
 .appx table{font-size:9px}
 thead{display:table-header-group}
 tfoot{display:table-row-group}
}
@media (max-width:720px){.tiles{grid-template-columns:repeat(2,1fr)}}
"""

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>cars.com Syndication Gap — VW North Scottsdale</title>
<style>{CSS}</style></head>
<body><div class="wrap">

<header class="top">
  <p class="eyebrow">Syndication Audit · Penske #182</p>
  <h1>cars.com is hiding $463,428 of price<br>across every new car we list</h1>
  <p class="meta">Volkswagen North Scottsdale · cars.com dealer 109556 ·
     All prices read live on 27 July 2026</p>
  <div class="verdict"><span class="dot"></span>VERDICT: CONFIRMED — 136 of 136 units affected</div>
  <div class="repl"><strong>Independently replicated.</strong> Two sessions ran this audit in
  parallel, sharing no intermediate data and using different collection paths. Both produced
  identical figures — 136 units, $463,428, the $368,500/$94,928 split, and the same identity
  on 136 of 136 units.</div>
</header>

<p class="lede">Our cars.com feed publishes the pre-bonus advertised price with the dealer
fee baked in, and never applies the customer bonus. This is not a sampling inference:
it is an exact arithmetic identity that holds on every single unit in the store.</p>

<div class="formula">
  <div class="f">cars.com price = MSRP − Discount + $698 Dealer Fees</div>
  <div class="c">True for <strong>136 of 136</strong> new units — zero exceptions.
  The customer bonus appears on our own price stack for 128 of them and is never
  reflected on cars.com.</div>
</div>

<div class="tiles">
  <div class="tile hero"><div class="v">$463,428</div><div class="k">Total price hidden from
    cars.com shoppers</div></div>
  <div class="tile"><div class="v">136<span style="font-size:15px;color:var(--muted)">/136</span></div>
    <div class="k">Units flagged — the entire new inventory</div></div>
  <div class="tile"><div class="v">$3,407</div><div class="k">Average gap per unit</div></div>
  <div class="tile"><div class="v">$6,698</div><div class="k">Worst per-unit gap (ID.4)</div></div>
</div>

<div class="callout"><strong>What a shopper actually sees.</strong> Atlas SEL, VIN
1V2BN2CA6TC539279, stock W19342. cars.com shows <strong>$50,224</strong>. The same car
on our own site shows <strong>$46,724</strong> after its $3,500 Retail Customer Bonus.
A cars.com shopper never sees a number below $50,224 — the car is sorted, filtered
and price-compared against rivals at a figure $4,198 above its true comparable price.</div>

<h2>Rank impact <span class="kicker">the three highest-volume flagged models</span></h2>

<p>Comparable trims are matched by <strong>VIN configuration prefix</strong>, not by dealer
trim label — labels are inconsistent across stores, with several rivals listing 4MOTION
units as “SE R-Line Black” with no drivetrain qualifier. Larry H. Miller's listed
price <strong>includes a $549 documentary fee</strong> (verified verbatim on their own site);
that $549 is unwound below to match cars.com convention.
<strong>Chapman Volkswagen lists zero new vehicles on cars.com</strong> — 14 listings, all
pre-owned — so they are absent from these rankings, a notable competitive fact in itself.</p>

{''.join(rank_blocks)}

<div class="callout"><strong>The pattern.</strong> On every one of the three models the feed
costs us at least one rank position, and on the two we stock most deeply it drops us to the
bottom or near-bottom of a four-dealer market we would otherwise lead or sit mid-pack in.
The prices are already competitive — only the number we publish is not.</div>

<h2>Where the money is <span class="kicker">hidden dollars by model</span></h2>

<figure>{bar_chart()}
<figcaption>Total gap between the cars.com price and our comparable lowest price, summed
across each model's flagged units. Hover a bar for its unit count.</figcaption></figure>

<p>Priority follows the dollars: <strong>Atlas</strong> (42 units, $176,316) and
<strong>Tiguan</strong> (41 units, $118,618) together account for 64% of the total.
<strong>ID.4</strong> is the highest-value fix per unit — only 7 cars, but $6,698 of
suppressed price on each.</p>

<h2>What the gap is made of</h2>

<figure>{comp_chart()}
<figcaption>Two independent defects in one field. Both are corrected by the same
remapping.</figcaption></figure>

<p>Roughly four-fifths of the gap is the suppressed customer bonus. The remaining fifth is
the $698 dealer fee being carried <em>inside</em> the price field — which is why even the
8 units with no bonus at all still list $698 above their comparable price.</p>

<h2>Spot-checked arithmetic <span class="kicker">read off live pages</span></h2>

<table>
<thead><tr><th>VIN / unit</th><th class="num">cars.com</th><th>Our live price stack</th>
<th class="num">Delta</th></tr></thead>
<tbody>
<tr><td>3VW5W7BUXTM049475<br><span style="color:var(--muted)">Jetta 1.5T S · WT4149</span></td>
 <td class="num">$26,383</td>
 <td>25,685 + 698 − 1,500 = <strong>$24,883</strong><br>
 <span style="color:var(--muted)">25,685 + 698 = 26,383 = cars.com ✓ · lowest 24,185</span></td>
 <td class="num dl">$2,198</td></tr>
<tr><td>1V2BN2CA6TC539279<br><span style="color:var(--muted)">Atlas 2.0T SEL · W19342</span></td>
 <td class="num">$50,224</td>
 <td>52,126 − 2,600 + 698 − 3,500 = <strong>$46,724</strong><br>
 <span style="color:var(--muted)">52,126 − 2,600 + 698 = 50,224 = cars.com ✓ · lowest 46,026</span></td>
 <td class="num dl">$4,198</td></tr>
<tr><td>3VVHR7RM0TM132086<br><span style="color:var(--muted)">Tiguan SE R-Line Black · W19519</span></td>
 <td class="num">$41,573</td>
 <td>40,875 + 698 − 2,500 = <strong>$39,073</strong><br>
 <span style="color:var(--muted)">40,875 + 698 = 41,573 = cars.com ✓ · lowest 38,375</span></td>
 <td class="num dl">$3,198</td></tr>
<tr><td>1V2DSPE82TC001428<br><span style="color:var(--muted)">ID.4 Pro AWD · W19289</span></td>
 <td class="num">$47,670</td>
 <td>50,972 − 4,000 + 698 − 6,000 = <strong>$41,670</strong><br>
 <span style="color:var(--muted)">50,972 − 4,000 + 698 = 47,670 = cars.com ✓ · lowest 40,972</span></td>
 <td class="num dl">$6,698</td></tr>
</tbody></table>

<p>Two of these independently reproduce figures captured days earlier by a different method
in an earlier pass ($24,883 Jetta; $39,073 Tiguan) — cross-session, cross-method agreement
on the same units.</p>

<h2>Method, evidence and limits</h2>

<p><strong>The comparable.</strong> Our site's bottom line adds the $698 dealer fee and
subtracts the bonus; cars.com's price convention excludes doc fees. The apples-to-apples
figure is therefore <code>(MSRP − Discount) − bonus</code>, with no +$698. Using our
site's own bottom line instead would understate the gap by $698 per unit.</p>

<ul>
<li><strong>Every price was read off a live page on 27 July 2026.</strong> No crawl cache,
no search snippets, no estimates.</li>
<li><strong>No unverified VINs.</strong> All 136 cars.com units were matched to a live price
stack on our own site. Twelve units missed by the paginated sweep (the results grid re-sorts
between requests) were each recovered individually by VIN search.</li>
<li><strong>Independent transcription check.</strong> The cars.com inventory was re-read
through a differently-composed URL (model-filtered rather than paginated); all 24 overlapping
VIN/price pairs matched the original read exactly.</li>
<li><strong>Full independent replication.</strong> A parallel session repeated the audit end
to end using different collection paths, sharing no intermediate data, and reproduced every
figure in this report exactly. It additionally confirmed that for all 136 units the extracted
price equals the rendered on-screen price, and that the factory program's own trim boundary
falls out of the parsed data unprompted — 36 non-SEL Tiguans at exactly $2,500 and 5 SEL
R-Line units at $0, matching the published “excludes SEL trims” rule.</li>
<li><strong>Conservative bonus treatment.</strong> Conditional offers shown on our site but
not available to every shopper (Military &amp; First Responders, College Graduate) are
excluded. Including them would enlarge the reported gap.</li>
<li><strong>Not verified:</strong> Larry H. Miller's ~$1,082 accessories addendum was not
present on any reachable live page. It is shown only as a sensitivity, never folded into a
primary ranking.</li>
<li><strong>Scope note:</strong> our site lists 161 new VINs against 136 on cars.com. The
25-unit difference is largely units priced off a <code>Market Price</code> line rather than
<code>MSRP</code> (typically demo/courtesy vehicles). Whether those should be syndicated is a
separate question this audit does not answer.</li>
</ul>

<h2>Recommended fix</h2>

<p>The defect is a <strong>feed field mapping</strong>, not a pricing error. The cars.com
export is mapped to the advertised/asking price column instead of the after-incentive lowest
price. Two changes:</p>

<ol>
<li><strong>Map the cars.com <code>price</code> field to the bonus-inclusive lowest price</strong>
— the same figure our site shows as its bottom line, less the $698 dealer fee. Recovers
the full $463,428 of visible price.</li>
<li><strong>Stop pushing the $698 dealer fee inside the price field.</strong> It belongs in the
fee/disclosure field; carrying it in <code>price</code> inflates all 136 units.</li>
</ol>

<p>Sequence by recoverable dollars: Atlas, then Tiguan, then Atlas Cross Sport — with ID.4
worth pulling forward on per-unit impact.</p>

<div class="urgent"><strong>Time sensitivity.</strong> The Tiguan Customer Bonus runs
<strong>1 July – 31 August 2026</strong>. Every day the mapping stays wrong is a day 128
bonus-eligible units are advertised to third-party shoppers above their real price — inside
the very window the factory funded the bonus to move them.</div>

<p><strong>How to verify the fix took.</strong> After the next feed push, re-read the dealer
inventory on cars.com and confirm that non-SEL Tiguans land $2,500 <em>below</em>
MSRP-minus-discount rather than $698 above it. The identity proven here is precise enough to
tell you immediately whether the remap took effect.</p>

<h2 class="pagebreak">Appendix — full delta table <span class="kicker">all 136 units</span></h2>

<p style="font-size:13px;color:var(--ink2)">Our lowest = (MSRP − Discount) − bonus,
excluding the $698 fee per the convention above. Every unit carries $698 in Dealer Fees.
Bonus key: <strong>Retail</strong> = Retail Customer Bonus · <strong>Cust.</strong> = Customer
Bonus (ID.4). Conditional offers (Military &amp; First Responders, College Graduate) are
excluded throughout.</p>

<div class="appx">
<table>
<thead><tr><th>#</th><th>VIN</th><th>Stock</th><th>Model / trim</th><th class="num">cars.com</th>
<th class="num">MSRP</th><th class="num">Disc.</th><th class="num">Sale</th><th>Bonus applied</th>
<th class="num">Our lowest</th><th class="num">Delta</th></tr></thead>
<tbody>
{appendix}
</tbody>
<tfoot><tr><td colspan="10">Total hidden across 136 units</td>
<td class="num dl">$463,428</td></tr></tfoot>
</table>
</div>

<footer>Volkswagen North Scottsdale (Penske #182) · cars.com syndication gap audit ·
Data captured live 27 July 2026 · Full evidence log and methodology in
<code>audits/2026-07-27-vwns-carscom-syndication-audit.md</code></footer>

</div></body></html>"""

open("/home/user/Chad/audits/vwns-carscom-syndication-report.html", "w").write(HTML)
print("html written:", len(HTML), "bytes ·", len(rows), "appendix rows")
