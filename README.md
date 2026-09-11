# Beast Telegram Bot — Vercel

Serverless webhook bot on Vercel.

## Endpoints
- `GET /` — health
- `POST /api/webhook` — Telegram updates

## Env vars (Vercel dashboard)
- `TELEGRAM_TOKEN` — required (from @BotFather)
- `ADMIN_IDS` — optional comma-separated numeric IDs

## After deploy — set webhook
Replace TOKEN and DOMAIN:

```bash
curl "https://api.telegram.org/botTOKEN/setWebhook?url=https://YOUR-PROJECT.vercel.app/api/webhook"
```

Then message the bot `/start`.

## Commands
/start /help /ping /status /id /echo /quote /whoami
