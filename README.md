# News Dashboard

Personal news dashboard auto-generated twice daily. Covers tech, AI, crypto, finance, cars, and football.
assuntos de interesse. 
**Live:** https://stefanobarin.github.io/news-dashboard/

---

## What it does

A Python script fetches RSS feeds across 6 categories, grabs a live BTC price, and generates a static HTML dashboard. A launchd job pushes the result to GitHub Pages at 07:00 and 19:00 every day.

**Categories**
- Data Engineering — dbt, Airflow, Spark, pipelines
- AI / LLM — model releases, agent frameworks
- BTC / Crypto — Bitcoin price + headlines
- Financial Markets — Fed, bonds, macro
- Cars — new models, EVs
- Copa do Mundo 2026 — Brazil schedule + news

---

## Stack

- Python 3 (stdlib only — no dependencies)
- RSS feeds via Google News + direct sources
- CoinGecko API for BTC price
- GitHub Pages for hosting
- macOS launchd for scheduling

---

## How the update works

```
07:00 / 19:00
    └── launchd triggers news_generator.py
            ├── fetch RSS feeds (6 categories)
            ├── fetch BTC price (CoinGecko)
            ├── generate index.html
            └── git push → GitHub Pages
```

The generator script is just local on mac 
