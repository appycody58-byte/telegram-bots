#!/usr/bin/env python3
"""AppyCody Beast Telegram bot — Railway / webhook ready."""

from __future__ import annotations

import hashlib
import html
import logging
import os
import random
import time
from datetime import datetime, timezone

from aiohttp import web
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("beast-bot")

START_TS = time.time()
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or ""
WEBHOOK_URL = (os.getenv("WEBHOOK_URL") or "").rstrip("/")
PORT = int(os.getenv("PORT", "8080"))
SECRET = os.getenv("WEBHOOK_SECRET") or hashlib.sha256(TOKEN.encode() or b"beast").hexdigest()[:32]
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

QUOTES = [
    "Build loud. Ship faster. Sleep never.",
    "Limits are just poorly documented features.",
    "A bot that answers is a tool. A bot that hunts is a beast.",
    "Deploy once. Iterate forever.",
    "If it compiles on Railway, it lives forever.",
]


def uptime() -> str:
    s = int(time.time() - START_TS)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{d}d {h}h {m}m {s}s"


def menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Status", callback_data="status"),
                InlineKeyboardButton("Ping", callback_data="ping"),
            ],
            [
                InlineKeyboardButton("Quote", callback_data="quote"),
                InlineKeyboardButton("Help", callback_data="help"),
            ],
        ]
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = html.escape(user.first_name if user else "hunter")
    await update.effective_message.reply_html(
        f"<b>BEAST MODE ONLINE</b>\n\n"
        f"Hey {name}. I am not a toy /start bot.\n"
        f"Hosted to stay alive. Built to expand.\n\n"
        f"Tap a button or fire a command.",
        reply_markup=menu(),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_html(
        "<b>COMMAND DECK</b>\n"
        "/start — wake the beast\n"
        "/help — this deck\n"
        "/ping — latency check\n"
        "/status — uptime + env\n"
        "/id — your Telegram IDs\n"
        "/echo &lt;text&gt; — bounce text\n"
        "/quote — fuel line\n"
        "/whoami — profile dump",
        reply_markup=menu(),
    )


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    t0 = time.perf_counter()
    msg = await update.effective_message.reply_text("pong…")
    ms = (time.perf_counter() - t0) * 1000
    await msg.edit_text(f"PONG · {ms:.0f} ms · uptime {uptime()}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mode = "webhook" if WEBHOOK_URL else "polling"
    await update.effective_message.reply_html(
        f"<b>SYSTEM</b>\n"
        f"mode: <code>{mode}</code>\n"
        f"uptime: <code>{uptime()}</code>\n"
        f"port: <code>{PORT}</code>\n"
        f"utc: <code>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}Z</code>"
    )


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = update.effective_user
    c = update.effective_chat
    await update.effective_message.reply_html(
        f"user_id: <code>{u.id if u else '?'}</code>\n"
        f"chat_id: <code>{c.id if c else '?'}</code>\n"
        f"username: <code>@{html.escape(u.username) if u and u.username else 'none'}</code>"
    )


async def cmd_echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args).strip() if context.args else ""
    if not text:
        await update.effective_message.reply_text("Usage: /echo your words")
        return
    await update.effective_message.reply_text(text[:4000])


async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(random.choice(QUOTES))


async def cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = update.effective_user
    if not u:
        return
    admin = "yes" if u.id in ADMIN_IDS else "no"
    await update.effective_message.reply_html(
        f"<b>{html.escape(u.full_name)}</b>\n"
        f"id <code>{u.id}</code> · admin {admin} · lang {u.language_code or '?}"
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    data = q.data or ""
    fake = Update(update.update_id, message=q.message)
    # reuse command handlers against the same message
    mapping = {
        "status": cmd_status,
        "ping": cmd_ping,
        "quote": cmd_quote,
        "help": cmd_help,
    }
    handler = mapping.get(data)
    if handler:
        await handler(update, context)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    if not text:
        return
    low = text.lower()
    if low in {"hi", "hello", "hey", "yo"}:
        await update.effective_message.reply_text("Beast hears you. Try /help.")
        return
    await update.effective_message.reply_text(
        f"Got it ({len(text)} chars). Commands live in /help."
    )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("handler exploded: %s", context.error)


def build_app() -> Application:
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_TOKEN (or BOT_TOKEN) in Railway variables.")
    app = (
        Application.builder()
        .token(TOKEN)
        .concurrent_updates(True)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("echo", cmd_echo))
    app.add_handler(CommandHandler("quote", cmd_quote))
    app.add_handler(CommandHandler("whoami", cmd_whoami))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    return app


async def health(_request: web.Request) -> web.Response:
    return web.json_response(
        {"ok": True, "service": "beast-bot", "uptime": uptime(), "mode": "webhook" if WEBHOOK_URL else "polling"}
    )


def main() -> None:
    application = build_app()

    if WEBHOOK_URL:
        log.info("Starting webhook on 0.0.0.0:%s -> %s", PORT, WEBHOOK_URL)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
            secret_token=SECRET,
            drop_pending_updates=True,
        )
    else:
        log.info("WEBHOOK_URL empty — polling + health server on %s", PORT)

        async def post_init(app: Application) -> None:
            runner = web.AppRunner(web.Application())
            # attach health later

        # tiny aiohttp health so Railway thinks the service is alive
        async def on_startup(app: Application) -> None:
            site_app = web.Application()
            site_app.router.add_get("/", health)
            site_app.router.add_get("/health", health)
            runner = web.AppRunner(site_app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", PORT)
            await site.start()
            app.bot_data["health_runner"] = runner
            log.info("Health server listening on %s", PORT)

        application.post_init = on_startup
        application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
