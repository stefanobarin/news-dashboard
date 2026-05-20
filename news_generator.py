#!/usr/bin/env python3
"""
news_generator.py
Fetches RSS (6 categories) + BTC price, generates index.html, pushes to GitHub Pages.
"""

import json
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from html import escape

REPO_DIR = Path(__file__).parent
OUT_FILE = REPO_DIR / "index.html"
LOG_FILE = REPO_DIR / "news-dash.log"

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
)

GN = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

FEEDS = {
    "de": [GN.format(q="data+engineering+airflow+dbt+spark+pipeline")],
    "ai": [GN.format(q="AI+LLM+GPT+Claude+model+2026")],
    "btc": [
        "https://cointelegraph.com/rss",
        GN.format(q="bitcoin+crypto+2026"),
    ],
    "fin": [
        "https://www.marketwatch.com/rss/realtimeheadlines",
        GN.format(q="federal+reserve+bonds+macro+finance+2026"),
    ],
    "cars": [
        "https://www.motor1.com/rss/news/all/",
        GN.format(q="new+cars+EV+electric+vehicle+2026"),
    ],
    "copa": [GN.format(q="Copa+do+Mundo+2026+Brasil+sele%C3%A7%C3%A3o")],
}

META = {
    "de":   {"label": "Data Engineering",   "bg": "oklch(23% 0.08 145)", "fg": "oklch(74% 0.16 145)", "num": "oklch(58% 0.12 145)"},
    "ai":   {"label": "AI / LLM",           "bg": "oklch(20% 0.07 260)", "fg": "oklch(74% 0.14 260)", "num": "oklch(58% 0.10 260)"},
    "btc":  {"label": "BTC / Crypto",       "bg": "oklch(23% 0.08 55)",  "fg": "oklch(76% 0.15 55)",  "num": "oklch(60% 0.12 55)"},
    "fin":  {"label": "Financeiro",         "bg": "oklch(20% 0.07 195)", "fg": "oklch(72% 0.14 195)", "num": "oklch(56% 0.10 195)"},
    "cars": {"label": "Carros",             "bg": "oklch(22% 0.09 25)",  "fg": "oklch(72% 0.17 25)",  "num": "oklch(56% 0.13 25)"},
    "copa": {"label": "Copa do Mundo 2026", "bg": "oklch(22% 0.09 142)", "fg": "oklch(72% 0.17 142)", "num": "oklch(56% 0.13 142)"},
}

COPA_SCHEDULE = [
    {"date": "13 Jun", "teams": "Brasil vs Marrocos", "venue": "Los Angeles", "next": True},
    {"date": "17 Jun", "teams": "Brasil vs Haiti",    "venue": "Dallas",      "next": False},
    {"date": "21 Jun", "teams": "Brasil vs Escócia",  "venue": "Atlanta",     "next": False},
]

CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:         oklch(9% 0.008 240);
    --surface:    oklch(13% 0.007 240);
    --border:     oklch(20% 0.007 240);
    --border-h:   oklch(30% 0.007 240);
    --divider:    oklch(18% 0.006 240);
    --text:       oklch(92% 0.006 240);
    --text-2:     oklch(72% 0.007 240);
    --text-3:     oklch(50% 0.007 240);
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 28px 28px 48px;
    font-size: 14px;
    line-height: 1.5;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding-bottom: 20px;
    margin-bottom: 28px;
    border-bottom: 1px solid var(--divider);
  }
  .header-title { font-size: 15px; font-weight: 600; color: var(--text); letter-spacing: -0.2px; }
  .header-meta  { font-size: 12px; color: var(--text-2); display: flex; align-items: baseline; gap: 10px; }
  .btc-price    { color: oklch(73% 0.14 55); font-weight: 600; font-size: 13px; }
  .btc-change   { font-size: 11px; color: oklch(60% 0.18 25); }

  .section-heading {
    font-size: 10px; font-weight: 700; letter-spacing: 1.8px;
    text-transform: uppercase; color: var(--text-3); margin-bottom: 14px;
  }

  .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin-bottom: 14px; }
  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }

  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px 18px 18px;
    transition: border-color 180ms ease-out;
  }
  .card:hover { border-color: var(--border-h); }

  .card-label {
    display: inline-block; font-size: 9px; font-weight: 700;
    letter-spacing: 1.4px; text-transform: uppercase;
    padding: 2px 7px; border-radius: 3px; margin-bottom: 14px;
  }

  .item { display: flex; gap: 10px; padding: 9px 0; border-top: 1px solid var(--divider); }
  .item:first-of-type { border-top: none; }
  .item-n { font-size: 11px; font-weight: 700; min-width: 18px; padding-top: 1px; }
  .item-body { flex: 1; min-width: 0; }
  .item-body h3 { font-size: 12.5px; font-weight: 500; line-height: 1.45; margin-bottom: 3px; }
  .item-body h3 a { color: var(--text); text-decoration: none; }
  .item-body h3 a:hover { color: oklch(85% 0.08 240); }
  .item-body p { font-size: 11.5px; color: var(--text-2); line-height: 1.4; margin-bottom: 3px;
                 display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .item-src { font-size: 10.5px; color: var(--text-3); }

  .schedule { margin-bottom: 12px; display: flex; flex-direction: column; gap: 6px; }
  .match { display: flex; align-items: center; gap: 8px; font-size: 11.5px; color: var(--text-2); }
  .match.next { color: var(--text); }
  .match-date-badge { font-size: 10px; font-weight: 700; color: var(--text-3); min-width: 38px; }
  .match-teams { flex: 1; display: flex; align-items: center; gap: 6px; }
  .match-venue { font-size: 10px; color: var(--text-3); }
  .next-pill { font-size: 9px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase;
               background: oklch(22% 0.09 142); color: oklch(72% 0.17 142);
               padding: 1px 5px; border-radius: 3px; }

  .world-section { margin-top: 28px; }

  @media (max-width: 900px) { .grid-4 { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 560px) { .grid-2, .grid-4 { grid-template-columns: 1fr; } }
"""


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def fetch(url: str, timeout: int = 15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NewsDash/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        log(f"fetch error {url}: {e}")
        return None


def fetch_btc() -> dict:
    data = fetch(COINGECKO_URL)
    if not data:
        return {}
    try:
        j = json.loads(data)["bitcoin"]
        price  = j.get("usd")
        change = j.get("usd_24h_change")
        if price:
            log(f"BTC: ${price:,.0f} {change:+.2f}%")
        return {"price": price, "change": change}
    except Exception as e:
        log(f"BTC parse error: {e}")
        return {}


def fetch_items(key: str, n: int = 3) -> list[dict]:
    log(f"Buscando {key}...")
    items = []
    for url in FEEDS[key]:
        if len(items) >= n:
            break
        raw = fetch(url)
        if not raw:
            continue
        try:
            root = ET.fromstring(raw)
            ns = {"media": "http://search.yahoo.com/mrss/"}
            for item in root.iter("item"):
                if len(items) >= n:
                    break
                title = item.findtext("title", "").strip()
                link  = item.findtext("link", "").strip()
                desc  = item.findtext("description", "").strip()
                src_el = item.find("source")
                src = src_el.text.strip() if src_el is not None else ""
                if title and link:
                    items.append({"title": title, "link": link, "desc": desc, "src": src})
        except Exception as e:
            log(f"  parse error {url}: {e}")
    return items[:n]


def render_item(item: dict, idx: int, num_color: str) -> str:
    title = escape(item["title"])
    link  = escape(item["link"])
    src   = escape(item["src"])
    desc_html = f'<p>{escape(item["desc"])}</p>' if item.get("desc") else ""
    return (
        f'    <div class="item">\n'
        f'      <span class="item-n" style="color:{num_color}">{idx:02d}</span>\n'
        f'      <div class="item-body">\n'
        f'        <h3><a href="{link}" target="_blank">{title}</a></h3>\n'
        f'        {desc_html}\n'
        f'        <span class="item-src">{src}</span>\n'
        f'      </div>\n'
        f'    </div>\n'
    )


def render_schedule() -> str:
    parts = ['<div class="schedule">']
    for m in COPA_SCHEDULE:
        cls = 'match next' if m["next"] else 'match'
        next_pill = '<span class="next-pill">Próximo</span>' if m["next"] else ""
        parts.append(
            f'<div class="{cls}">'
            f'<span class="match-date-badge">{m["date"]}</span>'
            f'<span class="match-teams">{escape(m["teams"])}{next_pill}</span>'
            f'<span class="match-venue">{escape(m["venue"])}</span>'
            f'</div>'
        )
    parts.append("</div>")
    return "".join(parts)


def render_card(key: str, items: list[dict]) -> str:
    m = META[key]
    label_html = f'<div class="card-label" style="background:{m["bg"]};color:{m["fg"]}">{m["label"]}</div>'
    schedule_html = render_schedule() if key == "copa" else ""
    items_html = "".join(render_item(it, i + 1, m["num"]) for i, it in enumerate(items))
    return f'<div class="card">\n  {label_html}\n  {schedule_html}\n{items_html}</div>'


def build_html(btc: dict, cards: dict[str, list]) -> str:
    now_str = datetime.now().strftime("%-d %b %Y, %H:%M")

    btc_price  = f'${btc["price"]:,.0f}' if btc.get("price") else "—"
    btc_change = f'{btc["change"]:+.2f}%' if btc.get("change") else ""
    btc_color  = "oklch(60% 0.18 25)" if btc.get("change", 0) < 0 else "oklch(65% 0.18 145)"

    header = (
        f'<header>\n'
        f'  <span class="header-title">News Dashboard</span>\n'
        f'  <div class="header-meta">\n'
        f'    <span>{now_str}</span>\n'
        f'    <span>BTC <span class="btc-price">{btc_price}</span>'
        f' <span class="btc-change" style="color:{btc_color}">{btc_change}</span></span>\n'
        f'  </div>\n'
        f'</header>\n'
    )

    top_section = (
        '<div class="section-heading">Tech &amp; Carreira</div>\n'
        '<div class="grid-2">\n'
        + render_card("de", cards["de"])
        + render_card("ai", cards["ai"])
        + '\n</div>\n'
    )

    world_section = (
        '<div class="world-section">\n'
        '  <div class="section-heading">Mundo</div>\n'
        '  <div class="grid-4">\n'
        + render_card("btc",  cards["btc"])
        + render_card("fin",  cards["fin"])
        + render_card("cars", cards["cars"])
        + render_card("copa", cards["copa"])
        + '\n  </div>\n</div>\n'
    )

    return (
        '<!DOCTYPE html>\n'
        '<html lang="pt-BR">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>News Dashboard</title>\n'
        f'<style>{CSS}</style>\n'
        '</head>\n'
        '<body>\n\n'
        + header
        + '\n'
        + top_section
        + '\n'
        + world_section
        + '\n</body>\n</html>'
    )


def git_push() -> bool:
    try:
        subprocess.run(["git", "add", "index.html"], cwd=REPO_DIR, check=True)
        msg = f"update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
        log("Push GitHub OK")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Push falhou: {e}")
        return False


def main() -> None:
    log("Iniciando geracao do dashboard...")

    btc   = fetch_btc()
    cards = {key: fetch_items(key) for key in FEEDS}

    html = build_html(btc, cards)
    OUT_FILE.write_text(html, encoding="utf-8")
    log(f"Dashboard salvo em {OUT_FILE}")

    git_push()


if __name__ == "__main__":
    main()
