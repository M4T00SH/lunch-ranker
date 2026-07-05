"""Render the ranked dish table into a single static HTML page."""
from __future__ import annotations

import html
import json


def render_page(data: dict) -> str:
    rows = []
    for i, d in enumerate(data["dishes"], 1):
        name = html.escape(d["name"])
        extra = " · ".join(x for x in (d.get("weight"), d.get("category")) if x)
        extra_html = f'<div class="sub">{html.escape(extra)}</div>' if extra else ""
        reason = html.escape(d.get("reason", ""))
        rows.append(
            f'<tr onclick="this.nextElementSibling.classList.toggle(\'open\')">'
            f'<td class="rank">{i}</td>'
            f'<td class="dish"><div>{name}</div>{extra_html}'
            f'<div class="rest">{html.escape(d["restaurant"])}</div></td>'
            f'<td class="num prot">{d["protein_g"]}</td>'
            f'<td class="num">{d["kcal"]}</td></tr>'
            f'<tr class="detail"><td></td><td colspan="3">{reason}</td></tr>'
        )

    warnings_html = ""
    if data["warnings"]:
        items = "".join(f"<li>{html.escape(w)}</li>" for w in data["warnings"])
        warnings_html = f'<div class="warn"><ul>{items}</ul></div>'

    body_note = ""
    if not data["dishes"]:
        body_note = '<p class="empty">No lunch menus found today (weekend or nothing published yet).</p>'

    return f"""<!DOCTYPE html>
<html lang="sk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Protein Lunch Ranker</title>
<style>
:root {{ --bg:#fff; --fg:#1a1a1a; --sub:#777; --line:#eee; --accent:#0a7d38; --chip:#f2f2f2; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#121212; --fg:#eee; --sub:#999; --line:#2a2a2a; --accent:#4cc477; --chip:#222; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:12px; background:var(--bg); color:var(--fg);
  font:16px/1.45 -apple-system, "SF Pro Text", Segoe UI, Roboto, sans-serif; }}
h1 {{ font-size:22px; margin:6px 0 2px; }}
.meta {{ color:var(--sub); font-size:13px; margin-bottom:10px; }}
.warn {{ background:#8a6d0022; border:1px solid #8a6d0055; border-radius:10px;
  padding:6px 10px; font-size:13px; margin-bottom:10px; }}
.warn ul {{ margin:4px 0; padding-left:18px; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ text-align:left; font-size:12px; color:var(--sub); text-transform:uppercase;
  letter-spacing:.04em; padding:6px 4px; border-bottom:2px solid var(--line); }}
td {{ padding:9px 4px; border-bottom:1px solid var(--line); vertical-align:top; }}
.rank {{ color:var(--sub); width:26px; font-size:14px; padding-top:11px; }}
.dish {{ padding-right:6px; }}
.sub {{ color:var(--sub); font-size:13px; }}
.rest {{ display:inline-block; background:var(--chip); border-radius:20px;
  font-size:12px; padding:1px 9px; margin-top:4px; color:var(--sub); }}
.num {{ text-align:right; width:58px; font-variant-numeric:tabular-nums; }}
.prot {{ color:var(--accent); font-weight:700; font-size:18px; }}
tr.detail {{ display:none; }}
tr.detail.open {{ display:table-row; }}
tr.detail td {{ color:var(--sub); font-size:13px; border-bottom:1px solid var(--line); padding-top:0; }}
.empty {{ color:var(--sub); }}
footer {{ color:var(--sub); font-size:12px; margin-top:14px; }}
</style>
</head>
<body>
<h1>🥩 Protein Lunch Ranker</h1>
<div class="meta">{html.escape(data["day_label"])} · generated {html.escape(data["generated_at"])} ·
estimates: {html.escape(data["method"])} · tap a row for reasoning</div>
{warnings_html}
{body_note}
<table>
<thead><tr><th>#</th><th>Dish</th><th>Prot.</th><th>kcal</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
<footer>Estimates are approximate. Sources: restaurant websites, fetched at generation time.</footer>
<script type="application/json" id="data">{json.dumps({"date": data["date"]})}</script>
</body>
</html>
"""
