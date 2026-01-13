import asyncio
import io
import logging
from typing import Iterable, List

from telegram import InputFile, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import ADMIN_IDS

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def _send_csv(update: Update, filename: str, content: str) -> None:
    data = io.BytesIO(content.encode("utf-8"))
    data.seek(0)
    await update.effective_message.reply_document(InputFile(data, filename=filename))


def _csv_escape(value: str) -> str:
    if value is None:
        return ""
    text = str(value)
    if any(ch in text for ch in [",", "\"", "\n"]):
        return "\"" + text.replace("\"", "\"\"") + "\""
    return text


def _csv_rows(headers: List[str], rows: Iterable[Iterable]) -> str:
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(_csv_escape(value) for value in row))
    return "\n".join(lines)


async def add_hackathon_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /add_hackathon <name> | <description> | <deadline> | <prize_pool>"
        )
        return
    payload = " ".join(context.args)
    parts = [part.strip() for part in payload.split("|")]
    if not parts or not parts[0]:
        await update.effective_message.reply_text("Hackathon name is required.")
        return
    name = parts[0]
    description = parts[1] if len(parts) > 1 and parts[1] else None
    deadline = parts[2] if len(parts) > 2 and parts[2] else None
    prize_pool = parts[3] if len(parts) > 3 and parts[3] else None
    db = context.application.bot_data["db"]
    hackathon_id = await asyncio.to_thread(
        db.create_hackathon, name, description, deadline, prize_pool, True
    )
    await update.effective_message.reply_text(
        f"Hackathon created with ID {hackathon_id}."
    )


async def list_hackathons_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    db = context.application.bot_data["db"]
    hackathons = await asyncio.to_thread(db.list_hackathons)
    if not hackathons:
        await update.effective_message.reply_text("No hackathons found.")
        return
    lines = []
    for hackathon in hackathons:
        status = "active" if hackathon.get("is_active") else "inactive"
        lines.append(f"{hackathon['id']}. {hackathon['name']} ({status})")
    await update.effective_message.reply_text("\n".join(lines))


async def deactivate_hackathon_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /deactivate_hackathon <id>")
        return
    try:
        hackathon_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Hackathon id must be a number.")
        return
    db = context.application.bot_data["db"]
    await asyncio.to_thread(db.set_hackathon_active, hackathon_id, False)
    await update.effective_message.reply_text(f"Hackathon {hackathon_id} deactivated.")


async def add_stage_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /add_stage <hackathon_id> | <stage_name> | <description> | <deadline>"
        )
        return
    payload = " ".join(context.args)
    parts = [part.strip() for part in payload.split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        await update.effective_message.reply_text("Hackathon id and stage name are required.")
        return
    try:
        hackathon_id = int(parts[0])
    except ValueError:
        await update.effective_message.reply_text("Hackathon id must be a number.")
        return
    name = parts[1]
    description = parts[2] if len(parts) > 2 and parts[2] else None
    deadline = parts[3] if len(parts) > 3 and parts[3] else None
    db = context.application.bot_data["db"]
    stage_id = await asyncio.to_thread(db.create_stage, hackathon_id, name, description, deadline, True)
    await update.effective_message.reply_text(f"Stage created with ID {stage_id}.")


async def list_stages_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /list_stages <hackathon_id>")
        return
    try:
        hackathon_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Hackathon id must be a number.")
        return
    db = context.application.bot_data["db"]
    stages = await asyncio.to_thread(db.list_stages_for_hackathon, hackathon_id)
    if not stages:
        await update.effective_message.reply_text("No stages found.")
        return
    lines = []
    for stage in stages:
        status = "active" if stage.get("is_active") else "inactive"
        lines.append(f"{stage['id']}. {stage['name']} ({status})")
    await update.effective_message.reply_text("\n".join(lines))


async def close_stage_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /close_stage <stage_id>")
        return
    try:
        stage_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Stage id must be a number.")
        return
    db = context.application.bot_data["db"]
    await asyncio.to_thread(db.set_stage_active, stage_id, False)
    await update.effective_message.reply_text(f"Stage {stage_id} closed.")


async def export_submissions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /export_submissions <stage_id>")
        return
    try:
        stage_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Stage id must be a number.")
        return
    db = context.application.bot_data["db"]
    submissions = await asyncio.to_thread(db.list_stage_submissions, stage_id)
    headers = ["stage_id", "team_id", "team_name", "user_id", "link", "created_at"]
    rows = [
        [
            submission.get("stage_id"),
            submission.get("team_id"),
            submission.get("team_name"),
            submission.get("user_id"),
            submission.get("link"),
            submission.get("created_at"),
        ]
        for submission in submissions
    ]
    await _send_csv(update, f"stage_{stage_id}_submissions.csv", _csv_rows(headers, rows))


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    db = context.application.bot_data["db"]
    users = await asyncio.to_thread(db.get_all_users)
    sent = 0
    failed = 0
    for user in users:
        try:
            await context.bot.send_message(chat_id=user["telegram_id"], text=message)
            sent += 1
        except TelegramError:
            failed += 1
            logger.warning("Failed to send broadcast to %s", user["telegram_id"])
    await update.effective_message.reply_text(f"Broadcast complete. Sent: {sent}, failed: {failed}.")


async def notify_hackathon_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.effective_message.reply_text("Usage: /notify_hackathon <hackathon_id> <message>")
        return
    hackathon_id = int(context.args[0])
    message = " ".join(context.args[1:])
    db = context.application.bot_data["db"]
    participants = await asyncio.to_thread(db.get_hackathon_participants, hackathon_id)
    sent = 0
    failed = 0
    for user_id in participants:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            sent += 1
        except TelegramError:
            failed += 1
            logger.warning("Failed to send hackathon notification to %s", user_id)
    await update.effective_message.reply_text(f"Notification complete. Sent: {sent}, failed: {failed}.")


async def export_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    db = context.application.bot_data["db"]
    users = await asyncio.to_thread(db.get_all_users)
    headers = [
        "telegram_id",
        "username",
        "first_name",
        "last_name",
        "birth_date",
        "gender",
        "location",
        "phone",
        "pinfl",
        "language",
        "consent_at",
        "created_at",
    ]
    rows = [
        [
            user.get("telegram_id"),
            user.get("username"),
            user.get("first_name"),
            user.get("last_name"),
            user.get("birth_date"),
            user.get("gender"),
            user.get("location"),
            user.get("phone"),
            user.get("pinfl"),
            user.get("language"),
            user.get("consent_at"),
            user.get("created_at"),
        ]
        for user in users
    ]
    await _send_csv(update, "users.csv", _csv_rows(headers, rows))


async def export_teams_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    db = context.application.bot_data["db"]
    teams = await asyncio.to_thread(db.get_all_teams)
    headers = ["hackathon_name", "team_name", "code", "leader_id", "field", "created_at"]
    rows = [
        [
            team.get("hackathon_name"),
            team.get("name"),
            team.get("code"),
            team.get("leader_id"),
            team.get("field"),
            team.get("created_at"),
        ]
        for team in teams
    ]
    await _send_csv(update, "teams.csv", _csv_rows(headers, rows))


async def export_team_members_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        return
    db = context.application.bot_data["db"]
    members = await asyncio.to_thread(db.get_all_team_members)
    headers = ["team_id", "team_name", "user_id", "user_name", "role", "is_lead"]
    rows = [
        [
            member.get("team_id"),
            member.get("team_name"),
            member.get("user_id"),
            member.get("user_name"),
            member.get("role"),
            member.get("is_lead"),
        ]
        for member in members
    ]
    await _send_csv(update, "team_members.csv", _csv_rows(headers, rows))


async def export_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await export_users_command(update, context)
    await export_teams_command(update, context)
    await export_team_members_command(update, context)
