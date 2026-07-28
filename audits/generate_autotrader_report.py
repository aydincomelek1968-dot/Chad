# -*- coding: utf-8 -*-
import json, html

SP = "/tmp/claude-0/-home-user-Chad/d7dc6d55-e04f-5614-b610-8f6a0c0ebd12/scratchpad/"
rows = json.load(open(SP + "at_rows.json"))

def money(n):
    return "${:,}".format(n)

# ---------------------------------------------------------------- rank data
RANKS = [
    {
        "model": "Tiguan SE R-Line, FWD",
        "vinpfx": "MSRP $39,496", "units": 21,
        "before": [("Larry H. Miller", 35807, True), ("Camelback", 37378, False),
                   ("VW North Scottsdale", 37544, None), ("Lunde's Peoria", 38011, False),
                   ("Chapman", 40196, False)],
        "after":  [("VW North Scottsdale", 35044, None), ("Larry H. Miller", 35807, True),
                   ("Camelback", 37378, False), ("Lunde's Peoria", 38011, False),
                   ("Chapman", 40196, False)],
        "note": "Our comparable is within $213 of Larry Miller's on MSRP ($39,496 vs $39,709), "
                "so this is a like-for-like pairing. Fixing the feed makes us cheapest outright.",
        "sens": None,
    },
    {
        "model": "Atlas SE w/Technology, FWD",
        "vinpfx": "MSRP $47,834", "units": 13,
        "before": [("Lunde's Peoria", 45333, True), ("Camelback", 45838, False),
                   ("VW North Scottsdale", 45932, None)],
        "after":  [("VW North Scottsdale", 42432, None), ("Lunde's Peoria", 45333, True),
                   ("Camelback", 45838, False)],
        "note": "The strongest comparison in the audit: Lunde's comparable unit carries an "
                "identical $47,834 MSRP to ours, so the $599 we trail them by is purely the "
                "missing bonus. Applying it puts us $2,901 clear of the field.",
        "sens": "Larry Miller and Chapman had no Atlas at this configuration in the returned "
                "result set, so this ranking is three-way rather than five-way.",
    },
]

US = "VW North Scottsdale"


def slope_chart(spec):
    """Bump chart: rank 1 at top, two columns (as listed / if fixed)."""
    n = len(spec["before"])
    top, rowh = 52, 46
    W, H = 720, top + n*rowh + 8
    x1, x2 = 208, 512
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
    for r in range(1, n+1):
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
MODELS = [("Atlas", 42, 147000), ("Tiguan", 41, 90000), ("Atlas Cross Sport", 12, 42000),
          ("ID.4", 7, 42000), ("Jetta", 11, 16500), ("Taos", 10, 15000),
          ("Golf GTI", 6, 9000), ("Jetta GLI", 4, 7000), ("Golf R", 3, 0)]


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
    """Channel comparison: what each platform's convention makes a real gap."""
    W, H = 720, 168
    x0, plotw = 150, 500
    total = 463428
    p=[f'<svg viewBox="0 0 {W} {H}" role="img" class="comp" aria-label="Gap by channel">']
    rows=[("Autotrader", 368500, 0), ("cars.com", 368500, 94928)]
    for i,(name,bonus,fee) in enumerate(rows):
        y = 40 + i*58
        wb = plotw*bonus/total; wf = plotw*fee/total
        p.append(f'<text x="{x0-14}" y="{y+20}" class="blabel" text-anchor="end">{name}</text>')
        p.append(f'<g class="seg"><title>{name}: suppressed bonus ${bonus:,}</title>'
                 f'<rect x="{x0}" y="{y}" width="{wb-2:.1f}" height="28" rx="4" class="r1"/></g>')
        p.append(f'<text x="{x0+8}" y="{y+19}" class="seglab">${bonus:,}</text>')
        if fee:
            p.append(f'<g class="seg"><title>{name}: $698 dealer fee counted as a gap '
                     f'because this platform excludes fees — ${fee:,}</title>'
                     f'<rect x="{x0+wb:.1f}" y="{y}" width="{wf-2:.1f}" height="28" rx="4" class="r2"/></g>')
            p.append(f'<text x="{x0+wb+8:.1f}" y="{y+19}" class="seglab">${fee:,}</text>')
            p.append(f'<text x="{x0+wb+wf+10:.1f}" y="{y+19}" class="bval">${bonus+fee:,}</text>')
        else:
            p.append(f'<text x="{x0+wb+10:.1f}" y="{y+19}" class="bval">${bonus:,}</text>')
        conv = "fees included \u2014 $698 is legitimate here" if fee==0 else "fees excluded \u2014 $698 is a real gap"
        p.append(f'<text x="{x0}" y="{y+43}" class="segsub">{conv}</text>')
    p.append(f'<rect x="{x0}" y="8" width="14" height="10" rx="2" class="r1"/>')
    p.append(f'<text x="{x0+20}" y="17" class="segsub">Suppressed customer bonus</text>')
    p.append(f'<rect x="{x0+230}" y="8" width="14" height="10" rx="2" class="r2"/>')
    p.append(f'<text x="{x0+250}" y="17" class="segsub">$698 dealer fee</text>')
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
    r["model"] = model_of(r["title"])
rows.sort(key=lambda r: (order.index(r["model"]), -r["delta"], r["vin"]))

trs = []
for i, r in enumerate(rows, 1):
    bl = f"${r['bonus']:,}" if r["bonus"] else "\u2014"
    trs.append(
        "<tr><td class=n>{i}</td><td class=vin>{vin}</td><td>{stock}</td><td>{desc}</td>"
        "<td class=num>{at}</td><td class=num>{msrp}</td><td class=num>{disc}</td>"
        "<td class=num>{adv}</td><td class=bon>{bl}</td><td class=num>{cmp}</td>"
        "<td class='num dl'>{d}</td></tr>".format(
            i=i, vin=r["vin"], stock=r["stock"] or "\u2014",
            desc=html.escape(r["title"].replace("New 2026 Volkswagen ", "")),
            at=money(r["at"]), msrp=money(r["msrp"]),
            disc=money(r["disc"]) if r["disc"] else "\u2014",
            adv=money(r["adv"]), bl=bl, cmp=money(r["cmp"]),
            d=money(r["delta"]) if r["delta"] else "\u2014"))
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
      <p class="sub">comparable at <code>{s['vinpfx']}</code> · {s['units']} of our units</p>
    </div>
    <div class="rankmove">
      <span class="rk before">#{rb}</span>
      <span class="arrow">→</span>
      <span class="rk after">#{ra}</span>
      <span class="ofn">of {len(s["before"])}</span>
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
<title>Autotrader Syndication Gap — VW North Scottsdale</title>
<style>{CSS}</style></head>
<body><div class="wrap">

<header class="top">
  <p class="eyebrow">Syndication Audit · Autotrader · Penske #182</p>
  <h1>Autotrader hides $368,500 &mdash;<br>the same defect, a second marketplace</h1>
  <p class="meta">Volkswagen North Scottsdale · Autotrader dealer 46562864 ·
     All prices read live on 27 July 2026</p>
  <div class="verdict"><span class="dot"></span>VERDICT: CONFIRMED — 128 of 136 units affected</div>
  <div class="repl"><strong>Companion audit.</strong> This is the Autotrader channel. The
  cars.com channel was audited separately and found the identical defect on the identical
  units. The dollar figures differ for a real reason, explained below — not because the
  two passes disagree.</div>
</header>

<p class="lede">Autotrader publishes our pre-bonus advertised price and never applies the
customer bonus. As on cars.com, this is an exact arithmetic identity rather than a
sampled inference.</p>

<div class="formula">
  <div class="f">Autotrader price = MSRP − Discount + $698 Dealer Fees</div>
  <div class="c">True for <strong>136 of 136</strong> matched units — zero exceptions.
  The customer bonus is applied on <strong>none</strong> of them.</div>
</div>

<div class="tiles">
  <div class="tile hero"><div class="v">$368,500</div><div class="k">Bonus hidden from
    Autotrader shoppers</div></div>
  <div class="tile"><div class="v">128<span style="font-size:15px;color:var(--muted)">/136</span></div>
    <div class="k">Units carrying a suppressed bonus</div></div>
  <div class="tile"><div class="v">$2,879</div><div class="k">Average gap per affected unit</div></div>
  <div class="tile"><div class="v">$6,000</div><div class="k">Worst per-unit gap (ID.4)</div></div>
</div>

<h2>Why this number is lower than cars.com's <span class="kicker">and why that is correct</span></h2>

<p>The cars.com audit reported <strong>$463,428</strong>. This one reports
<strong>$368,500</strong>. The $94,928 difference is exactly the $698 dealer fee across 136
units — and it is <em>deliberately excluded here</em>. Autotrader displays a
<strong>“Dealer Fees Included”</strong> badge under every price and its price convention
<em>includes</em> dealer fees. cars.com's convention <em>excludes</em> them. So the same
$698 is a genuine defect on one platform and correct behaviour on the other.</p>

<figure>{comp_chart()}
<figcaption>The suppressed bonus is common to both channels. The dealer-fee component
counts as a gap only on cars.com, whose price convention excludes fees.</figcaption></figure>

<div class="callout"><strong>Confirmed, not assumed.</strong> Larry H. Miller's comparable
Tiguan lists at <strong>$35,258 on cars.com</strong> and <strong>$35,807 on Autotrader</strong>
— a difference of exactly <strong>$549</strong>, the documentary fee they disclose on their
own site. They exclude it on one platform and include it on the other, matching each
platform's convention. Chapman's Autotrader price runs exactly MSRP + $589, their own fee.
The fee behaviour is industry-wide; the suppressed bonus is ours.</div>

<h2 class="pagebreak">The Autotrader-only finding <span class="kicker">our published MSRP is wrong</span></h2>

<p>This channel exposes something cars.com does not. Autotrader prints an <strong>MSRP</strong>
beside the price, and on our listings that number is frequently not the manufacturer's MSRP.</p>

<div class="callout"><strong>On 33 units carrying no discount, Autotrader prints
MSRP = our real MSRP + $698</strong> — for all 33, exactly. An Atlas 2.0T SE whose factory
MSRP is <strong>$41,604</strong> is published as <strong>“MSRP $42,302.”</strong> The dealer
fee has been folded into the manufacturer's suggested price.<br><br>
<strong>On the 64 units that do carry a discount</strong>, the MSRP is correct but the
published <strong>“Savings”</strong> is understated by exactly $698, because the fee is
netted against the discount before display. Verified on all 64:
<code>Savings = Discount − $698</code>.</div>

<p>So on <strong>97 of 136</strong> units the published price stack misstates either MSRP or
the discount. Overstating MSRP is the more serious of the two — it is a manufacturer figure,
and a shopper who cross-checks it against VW's own site will find it wrong.</p>

<h2>Rank impact</h2>

<p>Comparables are matched by <strong>closest MSRP</strong>, because Autotrader collapses trim
labels — our “SE R-Line Black” and the 4MOTION variant both publish as “SE R-Line”, making the
label alone unusable. All prices below are fee-inclusive per this platform's convention, so
no fee unwinding is applied, unlike the cars.com pass.</p>

{''.join(rank_blocks)}

<div class="callout"><strong>Atlas Cross Sport is missing on purpose.</strong> Autotrader has no
<code>atlas-cross-sport</code> model slug and the filter fallback returned unfiltered inventory,
so competitor prices could not be read at audit quality. Our own 12 Cross Sport units are fully
counted in the $368,500; only the competitive comparison is absent. The cars.com pass ranked this
model 4th → 3rd, but those are cars.com prices and do not transfer.</div>

<h2>Where the money is <span class="kicker">bonus hidden by model</span></h2>

<figure>{bar_chart()}
<figcaption>Suppressed customer bonus summed across each model's affected units. Golf R carries
no bonus on any of its 3 units, so it shows no gap.</figcaption></figure>

<p>Priority follows the dollars: <strong>Atlas</strong> (42 units, $147,000) and
<strong>Tiguan</strong> (41 units, $90,000) are 64% of the total. <strong>ID.4</strong> is the
highest-value fix per unit — 7 cars at $6,000 of hidden bonus each.</p>

<h2>Evidence, and one material limitation</h2>

<div class="callout"><strong>Autotrader publishes no VIN anywhere</strong> — not on the search
results page and not on the vehicle detail page; both were checked directly. This is the one
respect in which this audit is weaker than the cars.com pass, and it cannot be fixed from this
access path. The join is by <strong>advertised price</strong>, corroborated by <strong>MSRP and
Savings</strong> — not by VIN.</div>

<ul>
<li><strong>136 of 137</strong> Autotrader listings match a computed advertised price
(<code>MSRP − Discount + $698</code>) from our own live site data, exact to the dollar.</li>
<li><strong>97 of those 136</strong> carry a second independent confirmation from Autotrader's
own MSRP and Savings values (64 via true MSRP + savings, 33 via the $698 MSRP overstatement).</li>
<li>The <strong>price multiset is identical to cars.com's</strong> 136 prices — same units, same
numbers, two independent channels and two independent read paths.</li>
<li>Because MSRP is shared across same-configuration units, this is a <strong>unit-level</strong>
correspondence, not a VIN-level one. For a defect uniform across the whole inventory that does
not change the totals, but it is stated rather than glossed.</li>
<li><strong>One unmatched listing:</strong> a Tiguan SE R-Line at <strong>$38,073</strong>
(listing 781071327) matches no current price on our site. Its price implies a $2,650 discount
that no current unit carries — most likely a <strong>stale listing</strong>. Excluded from every
figure here. It is a separate feed-freshness defect, and it runs in the shopper's favour.</li>
<li><strong>Read-path fragility, controlled:</strong> Autotrader's model filter did not apply for
competitor dealers, and the page conversion transposed price/MSRP columns on one dealer. Both
were caught by requiring <code>PRICE = MSRP − SAVINGS</code> on every competitor row, and
re-queried before use.</li>
</ul>

<h2>Recommended fix</h2>

<p>The same one-line remap fixes both channels — but they need <strong>different</strong> fee
handling, and a single global change would fix one and break the other.</p>

<ol>
<li><strong>Map the Autotrader <code>price</code> field to the bonus-inclusive lowest price.</strong>
Recovers the full $368,500.</li>
<li><strong>Keep the $698 in the price for Autotrader — but stop folding it into MSRP.</strong>
The fee belongs in the price under this platform's convention; it does not belong in the MSRP
field.</li>
<li><strong>Do not apply the cars.com fee fix here.</strong> On cars.com the $698 must come
<em>out</em> of the price field; on Autotrader it must stay <em>in</em>.</li>
<li><strong>Investigate the stale $38,073 listing</strong> as a separate feed-freshness issue.</li>
</ol>

<div class="urgent"><strong>Time sensitivity.</strong> The Tiguan Customer Bonus runs
<strong>1 July – 31 August 2026</strong>. Combined with the cars.com channel, the same 128 units
are being advertised above their real price on both major third-party marketplaces
simultaneously, inside the window the factory funded the bonus to move them.</div>

<h2 class="pagebreak">Appendix — all 136 matched units</h2>

<p style="font-size:13px;color:var(--ink2)">Comparable = (MSRP − Discount − bonus) + $698,
retaining the dealer fee per Autotrader's fee-inclusive convention. Gap = Autotrader price −
comparable, which equals the suppressed bonus. VINs and stock numbers come from our own site;
Autotrader publishes neither.</p>

<div class="appx">
<table>
<thead><tr><th>#</th><th>VIN (our site)</th><th>Stock</th><th>Model / trim</th>
<th class="num">Autotrader</th><th class="num">Our MSRP</th><th class="num">Disc.</th>
<th class="num">Advertised</th><th>Bonus</th><th class="num">Comparable</th>
<th class="num">Gap</th></tr></thead>
<tbody>
{appendix}
</tbody>
<tfoot><tr><td colspan="10">Total bonus hidden across 136 units</td>
<td class="num dl">$368,500</td></tr></tfoot>
</table>
</div>

<footer>Volkswagen North Scottsdale (Penske #182) · Autotrader syndication gap audit ·
Data captured live 27 July 2026 · Full methodology in
<code>audits/2026-07-27-vwns-autotrader-syndication-audit.md</code> · Companion cars.com audit in
<code>audits/2026-07-27-vwns-carscom-syndication-audit.md</code></footer>

</div></body></html>"""

open("/home/user/Chad/audits/vwns-autotrader-syndication-report.html", "w").write(HTML)
print("html written:", len(HTML), "bytes ·", len(rows), "appendix rows")
