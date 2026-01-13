import asyncio
import logging
import os
import random
import re
import string
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from admin import (
    add_hackathon_command,
    add_stage_command,
    broadcast_command,
    close_stage_command,
    deactivate_hackathon_command,
    export_all_command,
    export_submissions_command,
    export_team_members_command,
    export_teams_command,
    export_users_command,
    list_hackathons_command,
    list_stages_command,
    notify_hackathon_command,
)
from config import ADMIN_IDS, BOT_TOKEN
from database import Database
from translations import TRANSLATIONS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


MAIN_MENU = ReplyKeyboardMarkup(
    [["🚀 Hackathons", "⚙️ Settings"], ["📁 My Hackathons", "❓ Help"]],
    resize_keyboard=True,
)


class States:
    (
        REG_OFFER,
        REG_FIRST_NAME,
        REG_LAST_NAME,
        REG_BIRTH_DATE,
        REG_GENDER,
        REG_LOCATION,
        REG_PHONE,
        REG_PINFL,
        TEAM_NAME,
        TEAM_ROLE,
        TEAM_FIELD,
        TEAM_PORTFOLIO,
        JOIN_CODE,
        JOIN_ROLE,
        JOIN_PORTFOLIO,
        SUBMIT_LINK,
        EDIT_FIELD,
        EDIT_VALUE,
    ) = range(18)


@dataclass
class PendingTeam:
    hackathon_id: int
    team_name: Optional[str] = None
    role: Optional[str] = None
    field: Optional[str] = None
    portfolio: Optional[str] = None


@dataclass
class PendingJoin:
    hackathon_id: int
    team_id: Optional[int] = None
    role: Optional[str] = None
    portfolio: Optional[str] = None


def t(language: str, key: str) -> str:
    return TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(key, key)


def parse_language(update: Update, user_data: dict, db_user: Optional[dict]) -> str:
    if db_user and db_user.get("language"):
        return db_user["language"]
    if "language" in user_data:
        return user_data["language"]
    return "en"


def validate_birth_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value.strip()))


def validate_pinfl(value: str) -> bool:
    return bool(re.fullmatch(r"\d{14}", value.strip()))


def validate_link(value: str) -> bool:
    return bool(re.fullmatch(r"https?://\\S+", value.strip()))


def parse_deadline(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    formats = [
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(value.strip(), fmt)
            if "%H:%M" not in fmt:
                return parsed.replace(hour=23, minute=59, tzinfo=timezone.utc)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def generate_team_code() -> str:
    length = random.randint(6, 8)
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


async def ensure_unique_team_code(db: Database) -> str:
    while True:
        code = generate_team_code()
        exists = await asyncio.to_thread(db.get_team_by_code, code)
        if not exists:
            return code


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db = context.application.bot_data["db"]
    telegram_id = update.effective_user.id
    db_user = await asyncio.to_thread(db.get_user, telegram_id)
    language = parse_language(update, context.user_data, db_user)

    if not db_user or not db_user.get("registration_complete"):
        offer_text = t(language, "offer_text")
        if offer_text == "offer_text":
            offer_text = t("uz", "offer_text")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(t(language, "offer_accept"), callback_data="offer_accept"),
                    InlineKeyboardButton(t(language, "offer_decline"), callback_data="offer_decline"),
                ]
            ]
        )
        await update.message.reply_text(offer_text, reply_markup=keyboard)
        return States.REG_OFFER

    await update.message.reply_text(t(language, "welcome_back"), reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def reg_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["first_name"] = update.message.text.strip()
    await update.message.reply_text(t("en", "ask_last_name"))
    return States.REG_LAST_NAME


async def reg_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    language_code = (query.from_user.language_code or "en").lower()
    language = "uz" if language_code.startswith("uz") else "ru" if language_code.startswith("ru") else "en"
    if query.data == "offer_decline":
        await query.message.reply_text(t(language, "offer_required"))
        return States.REG_OFFER
    context.user_data["consent_at"] = datetime.now(timezone.utc)
    await query.message.reply_text(t(language, "ask_first_name"))
    return States.REG_FIRST_NAME


async def reg_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["last_name"] = update.message.text.strip()
    await update.message.reply_text(t("en", "ask_birth_date"))
    return States.REG_BIRTH_DATE


async def reg_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    if not validate_birth_date(value):
        await update.message.reply_text(t("en", "invalid_birth_date"))
        return States.REG_BIRTH_DATE
    context.user_data["birth_date"] = value
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Male", callback_data="gender_male"),
                InlineKeyboardButton("Female", callback_data="gender_female"),
            ]
        ]
    )
    await update.message.reply_text(t("en", "ask_gender"), reply_markup=keyboard)
    return States.REG_GENDER


async def reg_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    gender = "Male" if query.data == "gender_male" else "Female"
    context.user_data["gender"] = gender
    await query.message.reply_text(t("en", "ask_location"))
    return States.REG_LOCATION


async def reg_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["location"] = update.message.text.strip()
    button = KeyboardButton(text=t("en", "share_phone"), request_contact=True)
    reply = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(t("en", "ask_phone"), reply_markup=reply)
    return States.REG_PHONE


async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()
    context.user_data["phone"] = phone
    await update.message.reply_text(t("en", "ask_pinfl"), reply_markup=ReplyKeyboardRemove())
    return States.REG_PINFL


async def reg_pinfl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = update.message.text.strip()
    if not validate_pinfl(value):
        await update.message.reply_text(t("en", "invalid_pinfl"))
        return States.REG_PINFL
    context.user_data["pinfl"] = value

    db = context.application.bot_data["db"]
    user = update.effective_user
    payload = {
        "telegram_id": user.id,
        "username": user.username,
        "first_name": context.user_data["first_name"],
        "last_name": context.user_data["last_name"],
        "birth_date": context.user_data["birth_date"],
        "gender": context.user_data["gender"],
        "location": context.user_data["location"],
        "phone": context.user_data["phone"],
        "pinfl": context.user_data["pinfl"],
        "consent_at": context.user_data.get("consent_at"),
    }
    await asyncio.to_thread(db.create_user, payload)
    await update.message.reply_text(t("en", "registration_complete"), reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def show_hackathons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.application.bot_data["db"]
    hackathons = await asyncio.to_thread(db.get_active_hackathons)
    if not hackathons:
        await update.message.reply_text(t("en", "no_hackathons"))
        return
    keyboard = [
        [InlineKeyboardButton(hackathon["name"], callback_data=f"hackathon_{hackathon['id']}")]
        for hackathon in hackathons
    ]
    await update.message.reply_text(
        t("en", "choose_hackathon"), reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_hackathon_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    hackathon_id = int(query.data.split("_")[1])
    db = context.application.bot_data["db"]
    hackathon = await asyncio.to_thread(db.get_hackathon, hackathon_id)
    if not hackathon:
        await query.message.reply_text(t("en", "hackathon_not_found"))
        return

    user_id = query.from_user.id
    team = await asyncio.to_thread(db.get_user_team_for_hackathon, user_id, hackathon_id)

    text = (
        f"*{hackathon['name']}*\n"
        f"{hackathon.get('description') or ''}\n"
        f"Deadline: {hackathon.get('deadline') or 'TBA'}\n"
        f"Prize pool: {hackathon.get('prize_pool') or 'TBA'}"
    )
    if team:
        members = await asyncio.to_thread(db.get_team_members, team["id"])
        member_lines = [
            f"- {member['user_name']} ({member['role'] or 'Member'})"
            for member in members
        ]
        text += "\n\n*Your Team:*\n"
        text += f"{team['name']} (Code: {team['code']})\n"
        text += "\n".join(member_lines)
        keyboard = [
            [InlineKeyboardButton(t("en", "see_details"), callback_data=f"details_{hackathon_id}")],
            [InlineKeyboardButton(t("en", "stages"), callback_data=f"stages_{hackathon_id}")],
            [InlineKeyboardButton(t("en", "leave_team"), callback_data=f"leave_{team['id']}")],
        ]
        if team["leader_id"] == user_id or user_id in ADMIN_IDS:
            keyboard.append(
                [InlineKeyboardButton(t("en", "remove_member"), callback_data=f"remove_member_{team['id']}")]
            )
        keyboard.append([InlineKeyboardButton(t("en", "back"), callback_data="back_hackathons")])
        await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard = [
        [InlineKeyboardButton(t("en", "register"), callback_data=f"register_{hackathon_id}")],
        [InlineKeyboardButton(t("en", "join_team"), callback_data=f"join_{hackathon_id}")],
        [InlineKeyboardButton(t("en", "stages"), callback_data=f"stages_{hackathon_id}")],
        [InlineKeyboardButton(t("en", "back"), callback_data="back_hackathons")],
    ]
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_stages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    hackathon_id = int(query.data.split("_")[1])
    db = context.application.bot_data["db"]
    stages = await asyncio.to_thread(db.list_stages_for_hackathon, hackathon_id)
    if not stages:
        await query.message.reply_text(t("en", "no_stages"))
        return
    keyboard = [
        [InlineKeyboardButton(stage["name"], callback_data=f"stage_{stage['id']}")]
        for stage in stages
    ]
    keyboard.append([InlineKeyboardButton(t("en", "back"), callback_data="back_hackathons")])
    await query.message.reply_text(t("en", "choose_stage"), reply_markup=InlineKeyboardMarkup(keyboard))


async def show_stage_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    stage_id = int(query.data.split("_")[1])
    db = context.application.bot_data["db"]
    stage = await asyncio.to_thread(db.get_stage, stage_id)
    if not stage:
        await query.message.reply_text(t("en", "stage_not_found"))
        return
    deadline = parse_deadline(stage.get("deadline"))
    status = t("en", "open") if stage.get("is_active") else t("en", "closed")
    text = (
        f"*{stage['name']}*\n"
        f"{stage.get('description') or ''}\n"
        f"Deadline: {stage.get('deadline') or 'TBA'}\n"
        f"Status: {status}"
    )
    user_id = query.from_user.id
    team = await asyncio.to_thread(db.get_user_team_for_hackathon, user_id, stage["hackathon_id"])
    keyboard = []
    if team:
        submission = await asyncio.to_thread(db.get_team_submission_for_stage, stage_id, team["id"])
        if submission:
            text += f"\n\n{t('en', 'submission_received')}: {submission['link']}"
        else:
            is_open = stage.get("is_active")
            if deadline and datetime.now(timezone.utc) > deadline:
                is_open = False
            if is_open:
                keyboard.append([InlineKeyboardButton(t("en", "submit_demo"), callback_data=f"submit_{stage_id}")])
            else:
                text += f"\n\n{t('en', 'submission_closed')}"
    keyboard.append([InlineKeyboardButton(t("en", "back"), callback_data="back_hackathons")])
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))


async def submit_demo_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    stage_id = int(query.data.split("_")[1])
    context.user_data["submit_stage_id"] = stage_id
    await query.message.reply_text(t("en", "ask_demo_link"))
    return States.SUBMIT_LINK


async def submit_demo_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    link = update.message.text.strip()
    if not validate_link(link):
        await update.message.reply_text(t("en", "invalid_link"))
        return States.SUBMIT_LINK
    db = context.application.bot_data["db"]
    stage_id = context.user_data.get("submit_stage_id")
    stage = await asyncio.to_thread(db.get_stage, stage_id)
    if not stage:
        await update.message.reply_text(t("en", "stage_not_found"))
        return ConversationHandler.END
    deadline = parse_deadline(stage.get("deadline"))
    if deadline and datetime.now(timezone.utc) > deadline:
        await update.message.reply_text(t("en", "submission_closed"))
        return ConversationHandler.END
    team = await asyncio.to_thread(
        db.get_user_team_for_hackathon, update.effective_user.id, stage["hackathon_id"]
    )
    if not team:
        await update.message.reply_text(t("en", "team_required"))
        return ConversationHandler.END
    await asyncio.to_thread(db.create_submission, stage_id, team["id"], update.effective_user.id, link)
    await update.message.reply_text(t("en", "submission_saved"), reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def back_to_hackathons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await show_hackathons(update, context)


async def create_team_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    hackathon_id = int(query.data.split("_")[1])
    context.user_data["pending_team"] = PendingTeam(hackathon_id=hackathon_id)
    await query.message.reply_text(t("en", "ask_team_name"))
    return States.TEAM_NAME


async def create_team_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pending: PendingTeam = context.user_data["pending_team"]
    pending.team_name = update.message.text.strip()
    await update.message.reply_text(t("en", "ask_team_role"))
    return States.TEAM_ROLE


async def create_team_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pending: PendingTeam = context.user_data["pending_team"]
    pending.role = update.message.text.strip()
    await update.message.reply_text(t("en", "ask_team_field"))
    return States.TEAM_FIELD


async def create_team_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pending: PendingTeam = context.user_data["pending_team"]
    pending.field = update.message.text.strip()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(t("en", "no_portfolio"), callback_data="no_portfolio")]]
    )
    await update.message.reply_text(t("en", "ask_portfolio"), reply_markup=keyboard)
    return States.TEAM_PORTFOLIO


async def create_team_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pending: PendingTeam = context.user_data["pending_team"]
    if update.callback_query:
        await update.callback_query.answer()
        pending.portfolio = None
        message = update.callback_query.message
    else:
        pending.portfolio = update.message.text.strip()
        message = update.message

    db = context.application.bot_data["db"]
    code = await ensure_unique_team_code(db)
    leader_id = message.from_user.id
    team_id = await asyncio.to_thread(
        db.create_team,
        pending.hackathon_id,
        pending.team_name,
        code,
        leader_id,
        pending.field,
    )
    await asyncio.to_thread(
        db.add_team_member,
        team_id,
        leader_id,
        pending.role,
        pending.portfolio,
        True,
    )
    await message.reply_text(
        t("en", "team_created").format(name=pending.team_name, code=code),
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END


async def join_team_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    hackathon_id = int(query.data.split("_")[1])
    context.user_data["pending_join"] = PendingJoin(hackathon_id=hackathon_id)
    await query.message.reply_text(t("en", "ask_team_code"))
    return States.JOIN_CODE


async def join_team_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    code = update.message.text.strip().upper()
    db = context.application.bot_data["db"]
    team = await asyncio.to_thread(db.get_team_by_code, code)
    pending: PendingJoin = context.user_data["pending_join"]
    if not team or team["hackathon_id"] != pending.hackathon_id:
        await update.message.reply_text(t("en", "invalid_team_code"))
        return States.JOIN_CODE
    pending.team_id = team["id"]
    await update.message.reply_text(t("en", "ask_team_role"))
    return States.JOIN_ROLE


async def join_team_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pending: PendingJoin = context.user_data["pending_join"]
    pending.role = update.message.text.strip()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(t("en", "no_portfolio"), callback_data="no_portfolio_join")]]
    )
    await update.message.reply_text(t("en", "ask_portfolio"), reply_markup=keyboard)
    return States.JOIN_PORTFOLIO


async def join_team_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pending: PendingJoin = context.user_data["pending_join"]
    if update.callback_query:
        await update.callback_query.answer()
        pending.portfolio = None
        message = update.callback_query.message
    else:
        pending.portfolio = update.message.text.strip()
        message = update.message

    db = context.application.bot_data["db"]
    try:
        await asyncio.to_thread(
            db.add_team_member,
            pending.team_id,
            message.from_user.id,
            pending.role,
            pending.portfolio,
            False,
        )
    except ValueError:
        await message.reply_text(t("en", "already_in_team"))
        return ConversationHandler.END
    team = await asyncio.to_thread(db.get_team, pending.team_id)
    await message.reply_text(
        t("en", "joined_team").format(name=team["name"], code=team["code"]),
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END


async def leave_team(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    team_id = int(query.data.split("_")[1])
    db = context.application.bot_data["db"]
    user_id = query.from_user.id
    team = await asyncio.to_thread(db.get_team, team_id)
    if not team:
        await query.message.reply_text(t("en", "team_not_found"))
        return
    members = await asyncio.to_thread(db.get_team_members, team_id)
    if team["leader_id"] == user_id:
        remaining = [member for member in members if member["user_id"] != user_id]
        if remaining:
            new_leader = remaining[0]["user_id"]
            await asyncio.to_thread(db.update_team_leader, team_id, new_leader)
        else:
            await asyncio.to_thread(db.remove_team, team_id)
            await query.message.reply_text(t("en", "left_team"), reply_markup=MAIN_MENU)
            return
    await asyncio.to_thread(db.remove_team_member, team_id, user_id)
    await query.message.reply_text(t("en", "left_team"), reply_markup=MAIN_MENU)


async def remove_member_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    team_id = int(query.data.split("_")[2])
    db = context.application.bot_data["db"]
    members = await asyncio.to_thread(db.get_team_members, team_id)
    keyboard = []
    for member in members:
        if member["is_lead"]:
            continue
        keyboard.append(
            [InlineKeyboardButton(member["user_name"], callback_data=f"remove_{team_id}_{member['user_id']}")]
        )
    if not keyboard:
        await query.message.reply_text(t("en", "no_members_to_remove"))
        return
    keyboard.append([InlineKeyboardButton(t("en", "back"), callback_data="back_hackathons")])
    await query.message.reply_text(t("en", "choose_member"), reply_markup=InlineKeyboardMarkup(keyboard))


async def remove_member_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, team_id, user_id = query.data.split("_")
    db = context.application.bot_data["db"]
    await asyncio.to_thread(db.remove_team_member, int(team_id), int(user_id))
    await query.message.reply_text(t("en", "member_removed"))


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t("en", "change_language"), callback_data="change_language")],
            [InlineKeyboardButton(t("en", "edit_personal"), callback_data="edit_personal")],
        ]
    )
    await update.message.reply_text(t("en", "settings"), reply_markup=keyboard)


async def language_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Uz", callback_data="lang_uz"),
                InlineKeyboardButton("Ru", callback_data="lang_ru"),
                InlineKeyboardButton("En", callback_data="lang_en"),
            ]
        ]
    )
    await query.message.reply_text(t("en", "choose_language"), reply_markup=keyboard)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    language = query.data.split("_")[1]
    db = context.application.bot_data["db"]
    await asyncio.to_thread(db.update_user_language, query.from_user.id, language)
    context.user_data["language"] = language
    await query.message.reply_text(t(language, "language_updated"), reply_markup=MAIN_MENU)


async def edit_personal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db = context.application.bot_data["db"]
    user = await asyncio.to_thread(db.get_user, query.from_user.id)
    if not user:
        await query.message.reply_text(t("en", "user_not_found"))
        return
    profile = (
        f"First name: {user['first_name']}\n"
        f"Last name: {user['last_name']}\n"
        f"Birth date: {user['birth_date']}\n"
        f"Gender: {user['gender']}\n"
        f"Location: {user['location']}"
    )
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("First name", callback_data="edit_first_name")],
            [InlineKeyboardButton("Last name", callback_data="edit_last_name")],
            [InlineKeyboardButton("Birth date", callback_data="edit_birth_date")],
            [InlineKeyboardButton("Gender", callback_data="edit_gender")],
            [InlineKeyboardButton("Location", callback_data="edit_location")],
        ]
    )
    await query.message.reply_text(profile, reply_markup=keyboard)


async def edit_field_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    field = query.data.replace("edit_", "")
    context.user_data["edit_field"] = field
    if field == "gender":
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Male", callback_data="gender_edit_male"),
                    InlineKeyboardButton("Female", callback_data="gender_edit_female"),
                ]
            ]
        )
        await query.message.reply_text(t("en", "choose_gender"), reply_markup=keyboard)
        return States.EDIT_FIELD
    await query.message.reply_text(t("en", "enter_new_value"))
    return States.EDIT_VALUE


async def edit_gender_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    gender = "Male" if query.data == "gender_edit_male" else "Female"
    field = context.user_data["edit_field"]
    db = context.application.bot_data["db"]
    await asyncio.to_thread(db.update_user_field, query.from_user.id, field, gender)
    await query.message.reply_text(t("en", "updated"), reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def edit_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    field = context.user_data["edit_field"]
    value = update.message.text.strip()
    if field == "birth_date" and not validate_birth_date(value):
        await update.message.reply_text(t("en", "invalid_birth_date"))
        return States.EDIT_VALUE
    db = context.application.bot_data["db"]
    await asyncio.to_thread(db.update_user_field, update.effective_user.id, field, value)
    await update.message.reply_text(t("en", "updated"), reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def my_hackathons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.application.bot_data["db"]
    teams = await asyncio.to_thread(db.get_user_teams, update.effective_user.id)
    if not teams:
        await update.message.reply_text(t("en", "no_hackathons"))
        return
    lines = []
    for team in teams:
        lines.append(f"{team['hackathon_name']}: {team['team_name']} (Code: {team['code']})")
    await update.message.reply_text("\n".join(lines))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(t("en", "help"))


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Bot stopped. Use /start to begin again.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error", exc_info=context.error)


async def send_stage_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.application.bot_data["db"]
    stages = await asyncio.to_thread(db.get_active_stages)
    now = datetime.now(timezone.utc)
    for stage in stages:
        deadline = parse_deadline(stage.get("deadline"))
        if not deadline:
            continue
        days_left = (deadline.date() - now.date()).days
        if days_left not in (3, 2, 1, 0):
            continue
        participants = await asyncio.to_thread(db.get_hackathon_participants, stage["hackathon_id"])
        for user_id in participants:
            inserted = await asyncio.to_thread(db.record_stage_reminder, stage["id"], user_id, days_left)
            if not inserted:
                continue
            user = await asyncio.to_thread(db.get_user, user_id)
            language = (user.get("language") if user else "en") or "en"
            if days_left == 3:
                message = t(language, "reminder_3days").format(stage=stage["name"])
            elif days_left == 2:
                message = t(language, "reminder_2days").format(stage=stage["name"])
            elif days_left == 1:
                message = t(language, "reminder_deadline").format(stage=stage["name"])
            else:
                message = t(language, "reminder_last_day").format(stage=stage["name"])
            try:
                await context.bot.send_message(chat_id=user_id, text=message)
            except TelegramError:
                logger.warning("Failed to send reminder to %s", user_id)


def build_application(db: Database) -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["db"] = db

    registration = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            States.REG_OFFER: [CallbackQueryHandler(reg_offer, pattern=r"^offer_")],
            States.REG_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_first_name)],
            States.REG_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_last_name)],
            States.REG_BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_birth_date)],
            States.REG_GENDER: [CallbackQueryHandler(reg_gender, pattern=r"^gender_")],
            States.REG_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_location)],
            States.REG_PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), reg_phone)],
            States.REG_PINFL: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_pinfl)],
        },
        fallbacks=[],
    )

    create_team_flow = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_team_start, pattern=r"^register_")],
        states={
            States.TEAM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_team_name)],
            States.TEAM_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_team_role)],
            States.TEAM_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_team_field)],
            States.TEAM_PORTFOLIO: [
                CallbackQueryHandler(create_team_portfolio, pattern=r"^no_portfolio$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_team_portfolio),
            ],
        },
        fallbacks=[],
    )

    join_team_flow = ConversationHandler(
        entry_points=[CallbackQueryHandler(join_team_start, pattern=r"^join_")],
        states={
            States.JOIN_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_team_code)],
            States.JOIN_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_team_role)],
            States.JOIN_PORTFOLIO: [
                CallbackQueryHandler(join_team_portfolio, pattern=r"^no_portfolio_join$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, join_team_portfolio),
            ],
        },
        fallbacks=[],
    )

    edit_flow = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_field_prompt, pattern=r"^edit_")],
        states={
            States.EDIT_FIELD: [CallbackQueryHandler(edit_gender_value, pattern=r"^gender_edit_")],
            States.EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_value)],
        },
        fallbacks=[],
    )

    submit_flow = ConversationHandler(
        entry_points=[CallbackQueryHandler(submit_demo_start, pattern=r"^submit_")],
        states={States.SUBMIT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, submit_demo_link)]},
        fallbacks=[],
    )

    app.add_handler(registration)
    app.add_handler(create_team_flow)
    app.add_handler(join_team_flow)
    app.add_handler(edit_flow)
    app.add_handler(submit_flow)

    app.add_handler(MessageHandler(filters.Regex(r"^🚀 Hackathons$"), show_hackathons))
    app.add_handler(CallbackQueryHandler(show_hackathon_detail, pattern=r"^hackathon_"))
    app.add_handler(CallbackQueryHandler(show_hackathon_detail, pattern=r"^details_"))
    app.add_handler(CallbackQueryHandler(show_stages, pattern=r"^stages_"))
    app.add_handler(CallbackQueryHandler(show_stage_detail, pattern=r"^stage_"))
    app.add_handler(CallbackQueryHandler(back_to_hackathons, pattern=r"^back_hackathons$"))
    app.add_handler(CallbackQueryHandler(leave_team, pattern=r"^leave_"))
    app.add_handler(CallbackQueryHandler(remove_member_prompt, pattern=r"^remove_member_"))
    app.add_handler(CallbackQueryHandler(remove_member_confirm, pattern=r"^remove_\d+_"))

    app.add_handler(MessageHandler(filters.Regex(r"^⚙️ Settings$"), settings_menu))
    app.add_handler(CallbackQueryHandler(language_prompt, pattern=r"^change_language$"))
    app.add_handler(CallbackQueryHandler(set_language, pattern=r"^lang_"))
    app.add_handler(CallbackQueryHandler(edit_personal, pattern=r"^edit_personal$"))

    app.add_handler(MessageHandler(filters.Regex(r"^📁 My Hackathons$"), my_hackathons))
    app.add_handler(MessageHandler(filters.Regex(r"^❓ Help$"), help_command))

    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("notify_hackathon", notify_hackathon_command))
    app.add_handler(CommandHandler("export_users", export_users_command))
    app.add_handler(CommandHandler("export_teams", export_teams_command))
    app.add_handler(CommandHandler("export_team_members", export_team_members_command))
    app.add_handler(CommandHandler("export_all", export_all_command))
    app.add_handler(CommandHandler("add_hackathon", add_hackathon_command))
    app.add_handler(CommandHandler("list_hackathons", list_hackathons_command))
    app.add_handler(CommandHandler("deactivate_hackathon", deactivate_hackathon_command))
    app.add_handler(CommandHandler("add_stage", add_stage_command))
    app.add_handler(CommandHandler("list_stages", list_stages_command))
    app.add_handler(CommandHandler("close_stage", close_stage_command))
    app.add_handler(CommandHandler("export_submissions", export_submissions_command))
    app.add_handler(CommandHandler("stop", stop_command))

    app.add_error_handler(error_handler)
    app.job_queue.run_repeating(send_stage_reminders, interval=21600, first=30)
    return app


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")
    db = Database()
    db.create_tables()
    app = build_application(db)
    logger.info("Starting ITCom Hackathons Bot")
    app.run_polling()


if __name__ == "__main__":
    main()
