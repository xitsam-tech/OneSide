
# OneSide – Python Port (APIs + Frontend Snippet)

This bundle moves the dynamic logic to **Python** (serverless-ready). You keep a simple static page that calls:

- `GET /api/top_coins?vs=EUR&limit=10`  → top coins (multi-source, with fallbacks + FX)
- `GET /api/geo_feed`                   → finance/crypto-only English headlines
- `POST /api/summary`                   → compact EN/DE bullets (universal payload)

## Deploy on Vercel

1. Create a new Vercel project or use your existing one.
2. Put the `api/` folder at the project root (so files are `api/top_coins.py`, `api/geo_feed.py`, `api/summary.py`).
3. Add **Environment Variables** (Project → Settings → Environment Variables):
   - `OPENAI_API_KEY` **or** `AI_GATEWAY_API_KEY`
   - optional: `AI_API_URL`, `AI_MODEL`, `AI_AUTH_HEADER`, `AI_AUTH_VALUE`
4. (Optional) Add `vercel.json` from this bundle.
5. Push → Vercel will deploy.

## Frontend integration (minimal)
Use `snippet.html` as a reference (copy the bits into your page). It shows how to:
- load top coins (with target currency)
- render finance-only news with compact bullets (EN/DE)
- apply trend colors to `.coin` cards (±1.5% thresholds)
