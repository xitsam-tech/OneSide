
# OneSide – Python Full Setup

This project moves *all* dynamic pieces to Python serverless functions.

## API Endpoints
- `GET /api/top_coins?vs=EUR&limit=10` – top coins (CG → CoinLore → Binance + FX)
- `GET /api/metrics` – BTC dominance, ETH/BTC, funding (BTC/ETH), Fear & Greed, mempool fees
- `GET /api/geo_feed` – English finance/crypto headlines
- `POST /api/summary` – compact EN/DE bullets

## Deploy
1. Put `api/` and `index.html` at the project root.
2. Vercel → Project → Settings → **Environment Variables**: `OPENAI_API_KEY` *or* `AI_GATEWAY_API_KEY`.
3. (Optional) `AI_API_URL`, `AI_MODEL`, `AI_AUTH_HEADER`, `AI_AUTH_VALUE`.
4. Push → enjoy.

## Notes
- Trend colors are handled on the client, data from Python.
- Translator toggle re-writes external links through Google Translate if enabled.
