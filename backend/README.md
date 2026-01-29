# Primes and Zooms Chatbot (Backend)

## Local setup

1) Create and activate a virtualenv
```
python3.12 -m venv venv
source venv/bin/activate
```

2) Install dependencies
```
pip install -U pip
pip install -r requirements.txt
```

3) Configure environment
- Copy `.env.example` to `.env`
- Fill in real values (never commit `.env`)

4) Run server
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Telegram webhook (local demo)

Use a tunnel (Cloudflare Tunnel recommended):
```
cloudflared tunnel --url http://localhost:8000
```

Set webhook:
```
curl -X POST http://127.0.0.1:8000/telegram/webhook/setup \
  -H 'Content-Type: application/json' \
  -d '{"webhook_url":"https://YOUR_PUBLIC_URL/telegram/webhook"}'
```

## Railway deployment

Railway uses the `PORT` environment variable. Start command uses it automatically in `railway.json`.

Steps:
1) Create a new Railway project and connect this repo.
2) Add environment variables (Settings → Variables):
   - `OPENAI_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - (optional) `TELEGRAM_WEBHOOK_SECRET`
3) Deploy.
4) Set webhook to your Railway URL:
```
curl -X POST https://YOUR_RAILWAY_URL/telegram/webhook/setup \
  -H 'Content-Type: application/json' \
  -d '{"webhook_url":"https://YOUR_RAILWAY_URL/telegram/webhook"}'
```

