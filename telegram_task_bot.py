"""
Telegram Task Manager Bot
=========================
A feature-rich Telegram bot for personal task and reminder management.
Built with python-telegram-bot v20+, SQLite for persistence.

Features:
- Add, list, complete, and delete tasks
- Set reminders with due dates
- Task categories and priorities
- Daily summary notifications
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
DB_PATH = "tasks.db"

# ──────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            title     TEXT    NOT NULL,
            category  TEXT    DEFAULT 'General',
            priority  TEXT    DEFAULT 'Medium',
            due_date  TEXT,
            done      INTEGER DEFAULT 0,
            created   TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def db_add_task(user_id: int, title: str, category: str,
                priority: str, due_date: str | None) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (user_id, title, category, priority, due_date, created) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, title, category, priority, due_date,
         datetime.now().isoformat()),
    )
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id


def db_get_tasks(user_id: int, done: int = 0) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT * FROM tasks WHERE user_id = ? AND done = ? ORDER BY due_date, priority",
        (user_id, done),
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def db_complete_task(task_id: int, user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?",
        (task_id, user_id),
    )
    updated = c.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def db_delete_task(task_id: int, user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?",
              (task_id, user_id))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

PRIORITY_EMOJI = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

def format_task(task: dict) -> str:
    emoji = PRIORITY_EMOJI.get(task["priority"], "⚪")
    due = f"  📅 {task['due_date']}" if task["due_date"] else ""
    return (
        f"{emoji} <b>{task['title']}</b>\n"
        f"   📁 {task['category']}{due}\n"
        f"   ID: <code>{task['id']}</code>"
    )


def tasks_keyboard(tasks: list[dict], action: str) -> InlineKeyboardMarkup:
    """Build an inline keyboard with one button per task."""
    buttons = [
        [InlineKeyboardButton(
            f"{'✅' if action == 'done' else '🗑'} {t['title'][:30]}",
            callback_data=f"{action}:{t['id']}",
        )]
        for t in tasks
    ]
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


# ──────────────────────────────────────────────
# COMMAND HANDLERS
# ──────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 <b>Welcome to Task Manager Bot!</b>\n\n"
        "Here's what I can do:\n"
        "/add — Add a new task\n"
        "/list — View your open tasks\n"
        "/done — Mark a task as complete\n"
        "/delete — Delete a task\n"
        "/summary — Today's overview\n"
        "/help — Show this message"
    )
    await update.message.reply_html(text)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage: /add <title> [--cat Category] [--pri High|Medium|Low] [--due YYYY-MM-DD]
    Example: /add Buy groceries --cat Personal --pri High --due 2025-06-15
    """
    if not context.args:
        await update.message.reply_text(
            "Usage: /add <title> [--cat Category] [--pri High|Medium|Low] [--due YYYY-MM-DD]\n"
            "Example: /add Fix login bug --cat Work --pri High --due 2025-06-15"
        )
        return

    raw = " ".join(context.args)

    # Parse optional flags
    def extract_flag(text: str, flag: str, default: str) -> tuple[str, str]:
        if flag in text:
            parts = text.split(flag, 1)
            rest = parts[1].strip()
            value = rest.split("--")[0].strip()
            cleaned = text.replace(flag + " " + value, "").strip()
            return value, cleaned
        return default, text

    category, raw = extract_flag(raw, "--cat", "General")
    priority, raw  = extract_flag(raw, "--pri", "Medium")
    due_date, raw  = extract_flag(raw, "--due", None)
    title = raw.strip()

    if priority not in ("High", "Medium", "Low"):
        priority = "Medium"

    task_id = db_add_task(
        update.effective_user.id, title, category, priority, due_date
    )

    emoji = PRIORITY_EMOJI.get(priority, "⚪")
    due_str = f"\n📅 Due: {due_date}" if due_date else ""
    await update.message.reply_html(
        f"✅ Task added!\n\n"
        f"{emoji} <b>{title}</b>\n"
        f"📁 {category} | Priority: {priority}{due_str}\n"
        f"ID: <code>{task_id}</code>"
    )


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = db_get_tasks(update.effective_user.id)
    if not tasks:
        await update.message.reply_text("🎉 No open tasks! Use /add to create one.")
        return

    lines = [f"📋 <b>Your Tasks ({len(tasks)})</b>\n"]
    lines += [format_task(t) for t in tasks]
    await update.message.reply_html("\n\n".join(lines))


async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = db_get_tasks(update.effective_user.id)
    if not tasks:
        await update.message.reply_text("No open tasks to complete.")
        return
    await update.message.reply_text(
        "Which task did you complete?",
        reply_markup=tasks_keyboard(tasks, "done"),
    )


async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = db_get_tasks(update.effective_user.id)
    if not tasks:
        await update.message.reply_text("No tasks to delete.")
        return
    await update.message.reply_text(
        "Which task do you want to delete?",
        reply_markup=tasks_keyboard(tasks, "del"),
    )


async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = db_get_tasks(update.effective_user.id)
    today = datetime.now().date().isoformat()
    overdue = [t for t in tasks if t["due_date"] and t["due_date"] < today]
    due_today = [t for t in tasks if t["due_date"] == today]
    upcoming = [t for t in tasks if t["due_date"] and t["due_date"] > today]
    no_date = [t for t in tasks if not t["due_date"]]

    lines = ["📊 <b>Daily Summary</b>\n"]
    if overdue:
        lines.append(f"🔴 <b>Overdue ({len(overdue)})</b>")
        lines += [format_task(t) for t in overdue]
    if due_today:
        lines.append(f"\n📅 <b>Due Today ({len(due_today)})</b>")
        lines += [format_task(t) for t in due_today]
    if upcoming:
        lines.append(f"\n⏳ <b>Upcoming ({len(upcoming)})</b>")
        lines += [format_task(t) for t in upcoming[:5]]
    if no_date:
        lines.append(f"\n📌 <b>No Due Date ({len(no_date)})</b>")

    if len(lines) == 1:
        lines.append("All clear! No tasks scheduled.")

    await update.message.reply_html("\n\n".join(lines))


# ──────────────────────────────────────────────
# CALLBACK HANDLER
# ──────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "cancel":
        await query.edit_message_text("Cancelled.")
        return

    action, task_id_str = data.split(":", 1)
    task_id = int(task_id_str)

    if action == "done":
        if db_complete_task(task_id, user_id):
            await query.edit_message_text(f"✅ Task #{task_id} marked as complete!")
        else:
            await query.edit_message_text("Task not found.")

    elif action == "del":
        if db_delete_task(task_id, user_id):
            await query.edit_message_text(f"🗑 Task #{task_id} deleted.")
        else:
            await query.edit_message_text("Task not found.")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("done", cmd_done))
    app.add_handler(CommandHandler("delete", cmd_delete))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
