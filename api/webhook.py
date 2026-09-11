"""Vercel serverless Telegram webhook — Beast Mode."""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("beast-bot")

START_TS = time.time()
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN") or ""
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
    "Serverless on Vercel. Alive on every request.",
]

_app: Application | None = None


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
        f"<b>BEAST MODE ONLINE</b>\n"
        f"Platform: <code>Vercel serverless</code>\n\n"
        f"Hey {name}. Webhook locked. Commands armed.",
        reply_markup=menu(),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_html(
        "<b>COMMAND DECK</b>\n"
        "/start — wake the beast\n"
        "/help — this deck\n"
        "/ping — latency check\n"
        "/status — system dump\n"
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
    await update.effective_message.reply_html(
        f"<b>SYSTEM</b>\n"
        f"mode: <code>vercel-webhook</code>\n"
        f"uptime: <code>{uptime()}</code>\n"
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
        f"id <code>{u.id}</code> · admin {admin} · lang {u.language_code or '?'}"
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    data = q.data or ""
    mapping = {
        "status": cmd_status,
        "ping": cmd_ping,
        "quote": cmd_quote,
        "help": cmd_help,
    }
    handler_fn = mapping.get(data)
    if handler_fn:
        await handler_fn(update, context)


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


def get_app() -> Application:
    global _app
    if _app is not None:
        return _app
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN is not set")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("ping", cmd_ping))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("id", cmd_id))
    application.add_handler(CommandHandler("echo", cmd_echo))
    application.add_handler(CommandHandler("quote", cmd_quote))
    application.add_handler(CommandHandler("whoami", cmd_whoami))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    application.add_error_handler(on_error)
    _app = application
    return application


async def process_update(raw: dict) -> None:
    application = get_app()
    await application.initialize()
    try:
        update = Update.de_json(raw, application.bot)
        if update:
            await application.process_update(update)
    finally:
        await application.shutdown()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"ok":true,"endpoint":"webhook","method":"POST only"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            asyncio.run(process_update(data))
            body = b"ok"
            self.send_response(200)
        except Exception as exc:
            log.exception("webhook failed: %s", exc)
            body = b"error"
            self.send_response(500)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
