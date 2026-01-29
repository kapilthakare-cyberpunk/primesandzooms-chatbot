# Telegram Bot Integration Guide

## Overview

The Primes and Zooms chatbot includes a Telegram bot integration that allows customers to interact with the rental assistant directly through Telegram.

## Features

- 🤖 Automatic responses using RAG-powered knowledge base
- 📝 Command support (`/start`, `/help`, `/equipment`, `/contact`)
- ⚡ Webhook support for production deployment
- 🔄 Polling mode for local development

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to name your bot
4. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Configure Environment

Add to your `.env` file:

```env
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_WEBHOOK_SECRET=optional-random-secret
```

### 3. Local Development (Polling Mode)

For local development, the bot can use polling mode:

```bash
# Start the server
uvicorn app.main:app --reload

# In another terminal, run the polling script
python scripts/telegram_polling.py
```

### 4. Production Deployment (Webhook Mode)

For production, set up a webhook:

1. Deploy your application to a public URL (e.g., Railway, Render)
2. Set the webhook:

```bash
curl -X POST https://your-domain.com/telegram/webhook/setup \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://your-domain.com/telegram/webhook"}'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/telegram/webhook` | POST | Receives updates from Telegram |
| `/telegram/webhook/setup` | POST | Sets the webhook URL |
| `/telegram/webhook` | DELETE | Removes webhook (for polling) |
| `/telegram/send` | POST | Send a message to a chat |
| `/telegram/health` | GET | Check bot configuration status |

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and introduction |
| `/help` | Show available commands |
| `/equipment` | Browse equipment categories |
| `/contact` | Get shop contact information |

## Message Flow

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐
│Telegram │────▶│  Webhook    │────▶│ RAG Engine  │────▶│Response │
│  User   │     │  Endpoint   │     │   Query     │     │  Sent   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────┘
```

## Testing

1. Start the server
2. Open your bot in Telegram (search for your bot username)
3. Send `/start` to test
4. Try asking questions like:
   - "What cameras do you have for rent?"
   - "How much is the Sony A7S III per day?"
   - "What's your security deposit policy?"

## Troubleshooting

### Bot not responding?

1. Check `TELEGRAM_BOT_TOKEN` is set correctly
2. Verify webhook is set: `GET /telegram/health`
3. Check server logs for errors

### Webhook issues?

1. Ensure your server has a valid SSL certificate
2. Check the webhook URL is publicly accessible
3. Telegram requires HTTPS for webhooks

### Rate limiting?

Telegram has rate limits:
- 30 messages per second to different chats
- 1 message per second to the same chat

The bot handles this automatically with async processing.
