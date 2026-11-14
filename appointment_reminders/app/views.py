"""HTML for the front desk: server-rendered, a little CSS, no JavaScript."""
from __future__ import annotations

from html import escape

STYLE = """
:root{--ink:#241a35;--page:#f5f3f8;--panel:#fff;--line:#e5e0ee;--muted:#6c6480;--accent:#5a3e9b;--accent-soft:#efeaf8;
--due:#d98e1f;--due-soft:#fdf2df;--bad:#b3261e;--bad-soft:#fbe9e7;
--serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--page);font-variant-numeric:tabular-nums}
header{background:var(--ink);color:#d9d2e6;display:flex;align-items:baseline;gap:24px;padding:14px 36px;flex-wrap:wrap}
header b{font:600 21px var(--serif);color:#fff;letter-spacing:.01em}
header span{margin-left:auto;font-size:14px}
.test{background:repeating-linear-gradient(-45deg,#f6d28f,#f6d28f 12px,#f3c672 12px,#f3c672 24px);color:#3d2600;padding:7px 36px;font-weight:600;font-size:14px}
main{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:40px;padding:30px 36px 48px;max-width:1280px}
h1{font:400 40px/1.1 var(--serif);margin:0;letter-spacing:-.01em}
h2{font:600 20px var(--serif);margin:0 0 14px}
.top{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin-bottom:6px}
.lede{color:var(--muted);margin:6px 0 0}
.note{margin:18px 0 0;padding:8px 14px;border-radius:8px;background:var(--accent-soft);color:var(--accent);font-weight:500;display:inline-block}
button{font:inherit;cursor:pointer;border-radius:999px;border:1px solid var(--accent);background:var(--accent);color:#fff;padding:9px 20px;font-weight:600;white-space:nowrap}
button.quiet{background:transparent;color:var(--accent);border-color:var(--line);padding:3px 12px;font-weight:500;font-size:14px}
button.quiet:hover{border-color:var(--accent)}
button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
form{display:inline}
ol{list-style:none;margin:26px 0 0;padding:0;position:relative}
ol:before{content:"";position:absolute;left:95px;top:6px;bottom:6px;width:2px;background:var(--line)}
li.slot{display:grid;grid-template-columns:80px 30px 1fr;align-items:start;margin-bottom:12px}
.time{font:600 22px/1.2 var(--serif);text-align:right;padding-top:12px}
.time small{display:block;font:13px system-ui,sans-serif;color:var(--muted)}
.dot{width:12px;height:12px;border-radius:50%;background:var(--panel);border:2px solid var(--muted);margin:19px 0 0 10px;position:relative}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 16px;display:grid;grid-template-columns:1fr auto;gap:2px 16px}
.card .who{font-weight:600;font-size:16px} .card .sub{color:var(--muted);font-size:14px}
.card .risk{color:var(--muted);font-size:13px;text-align:right}
.acts{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px}
.acts details[open]{flex-basis:100%}
.tag{display:inline-block;font-size:12px;padding:0 9px;border-radius:9px;background:var(--page);color:var(--muted);margin-left:6px}
li.due .card{background:var(--due-soft);border-color:#f1d4a3}
li.due .dot{background:var(--due);border-color:var(--due)}
li.band{margin:4px 0 10px 125px;color:#9a5f07;font-size:14px;font-weight:600} li.band.later{color:var(--muted);margin-top:18px}
li.now{display:grid;grid-template-columns:80px 30px 1fr;align-items:center;margin:0 0 10px;color:var(--accent);font-weight:600;font-size:14px}
li.now .time{font-size:14px;padding:0;font-family:inherit}
li.now .dot{margin:0 0 0 7px;width:18px;height:18px;background:var(--accent);border-color:var(--accent);box-shadow:0 0 0 5px var(--accent-soft)}
li.now hr{border:0;border-top:2px solid var(--accent);margin:0}
details summary{cursor:pointer;color:var(--accent);font-size:14px;list-style:none} details summary:before{content:"+ "}
details[open] summary:before{content:"\\2212  "}
details form{display:inline-flex;gap:6px;margin:8px 8px 0 0}
input,select{font:inherit;font-size:14px;padding:3px 9px;border:1px solid var(--line);border-radius:8px;background:#fff}
.earlier{margin:22px 0 0 125px;color:var(--muted)} .earlier summary{color:var(--muted)} .earlier p{margin:6px 0}
aside{border-left:1px solid var(--line);padding-left:32px}
aside p.empty{color:var(--muted)}
.msgs{list-style:none;margin:0;padding:0}
.msgs li{margin-bottom:16px} .msgs .to{font-size:13px;color:var(--muted);margin-bottom:4px}
.bubble{background:var(--accent-soft);border-radius:16px 16px 16px 4px;padding:9px 14px}
.notice .bubble{background:var(--due-soft)}
.twice .bubble{background:var(--bad-soft);box-shadow:inset 0 0 0 1px #f0b4ae}
.twice .flag{color:var(--bad);font-weight:600;font-size:13px;margin-top:4px}
@media (max-width:900px){main{grid-template-columns:1fr;padding:22px 16px} header,.test{padding-left:16px;padding-right:16px}
aside{border:0;padding:0} .top{flex-direction:column;align-items:flex-start} h1{font-size:32px}
li.slot,li.now{grid-template-columns:52px 24px 1fr} ol:before{left:67px} li.band,.earlier{margin-left:91px} .card{grid-template-columns:1fr}
.card .risk{text-align:left}}
"""


def page(title: str, header_note: str, trouble: list, body: str) -> str:
    banner = "".join(f"<div class='test'>Test environment: {escape(t)}.</div>" for t in trouble)
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{escape(title)} - Reminders desk</title><style>{STYLE}</style></head><body>"
            f"<header><b>Reminders desk</b><span>{header_note}</span></header>{banner}{body}</body></html>")


def button(action: str, label: str, fields: dict = None, cls: str = "") -> str:
    hidden = "".join(f'<input type="hidden" name="{k}" value="{escape(str(v))}">' for k, v in (fields or {}).items())
    return f'<form method="post" action="{action}">{hidden}<button class="{cls}">{escape(label)}</button></form>'


def select(name: str, options: list, current: str) -> str:
    return f'<select name="{name}">' + "".join(f"<option{' selected' if o == current else ''}>{escape(o)}</option>" for o in options) + "</select>"
