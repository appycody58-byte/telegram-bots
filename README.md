# Beast Telegram Bot

Production bot for [appycody58-byte/telegram-bots](https://github.com/appycody58-byte/telegram-bots).

## What you get
- `/start` `/help` `/ping` `/status` `/id` `/echo` `/quote` `/whoami`
- Inline menu
- Railway health endpoint on `/` and `/health`
- Webhook mode when `WEBHOOK_URL` is set, otherwise long-polling + health server

## Railway deploy (2 minutes)
1. Open [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Select `appycody58-byte/telegram-bots` (branch **Master**)
3. Variables:
   - `TELEGRAM_TOKEN` = token from [@BotFather](https://t.me/BotFather)
   - `ADMIN_IDS` = your numeric Telegram user id (optional, comma-separated)
   - After first deploy, copy the public URL (e.g. `https://xxxx.up.railway.app`) and set:
     - `WEBHOOK_URL=https://xxxx.up.railway.app`
4. Redeploy once so webhook mode locks in.
5. Message the bot `/start`.

Polling also works if you leave `WEBHOOK_URL` empty. Railway still gets a health server on `$PORT`.

## Local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_TOKEN=your_token
python bot.py
```
