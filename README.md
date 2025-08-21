# Crypto Pulse – Vercel Starter

Quell-HTML: OneSide.html

## Quick Deploy (ohne CLI)
1. Repo bei GitHub/GitLab/Bitbucket erstellen und diesen Ordner hochladen.
2. Auf vercel.com -> **Add New... → Project** -> Repo wählen -> Deploy.
3. Seite läuft unter `https://<projekt>.vercel.app`.
4. APIs erreichbar unter `/api/funding` und `/api/fees`.

## Deploy mit CLI (wenn du kein Git nutzt)
```bash
npm i -g vercel
vercel login
vercel           # Preview-Deploy
vercel --prod    # Live-Deploy
```

## Optional: CORS enger setzen
Im Vercel-Projekt unter *Settings → Environment Variables*:
- `ALLOWED_ORIGINS` = `https://<deine-domain>.vercel.app, https://<custom-domain.tld>`

## Dateien
- `index.html` – fertige Onefile-Seite
- `api/funding.py` – Binance Funding (BTC/ETH)
- `api/fees.py` – BTC Mempool Fees
- `vercel.json` – Clean URLs
- `requirements.txt` – leer (keine Abhängigkeiten notwendig)