"""
Kod va G'oyalar Hackathons Bot - Complete Telegram Bot for Hackathon Management
Features:
- User registration with PINFL verification
- Multi-language support (Uzbek, Russian, English)
- Hackathon discovery and registration  
- Team creation and management
- Stage-based task system with deadlines
- Admin panel for managing hackathons
- Broadcast announcements to participants
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Optional
from enum import Enum

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

from database import Database
from config import BOT_TOKEN, ADMIN_IDS, SUPPORT_EMAIL
from translations import get_text, LANGUAGES

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
class State(Enum):
    FIRST_NAME = 1
    LAST_NAME = 2
    BIRTH_DATE = 3
    PHONE = 4
    PINFL = 5
    TEAM_NAME = 6
    TEAM_CODE = 7
    SUBMIT_LINK = 8
    CHANGE_FIRST_NAME = 9
    CHANGE_LAST_NAME = 10
    CHANGE_BIRTH_DATE = 11
    CHANGE_GENDER = 12
    CHANGE_LOCATION = 13
    ADMIN_HACKATHON_NAME = 14
    ADMIN_HACKATHON_DESC = 15
    ADMIN_HACKATHON_DATES = 16
    ADMIN_STAGE_NAME = 17
    ADMIN_STAGE_DATES = 18
    ADMIN_BROADCAST = 19
    ADMIN_TASK_TEXT = 20


# Initialize database
db = Database()


def get_main_menu_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    """Generate main menu keyboard"""
    keyboard = [
        [KeyboardButton(f"🚀 {get_text('hackathons', lang)}"), 
         KeyboardButton(f"⚙️ {get_text('settings', lang)}")],
        [KeyboardButton(f"📁 {get_text('my_hackathons', lang)}"),
         KeyboardButton(f"❓ {get_text('help', lang)}")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Generate language selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 Uz", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Ru", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 En", callback_data="lang_en")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command - begin registration or welcome back"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    
    if user:
        # Existing user - welcome back
        lang = user.get('language', 'en')
        await update.message.reply_text(
            f"👋 {get_text('welcome_back', lang)}",
            reply_markup=get_main_menu_keyboard(lang)
        )
        return ConversationHandler.END
    
    # New user - show welcome message and start registration
    welcome_text = """What can this bot do?

👋 Welcome to the IT Community Hackathons Bot!

This bot helps you participate in our hackathons effectively 💡

Here you can:
• Register for upcoming hackathons 📝
• Receive and submit tasks ⚙️
• Track your progress and results 📊
• Stay updated with announcements 📬


Good luck and build something amazing with our hackathons 💚"""
    
    await update.message.reply_text(welcome_text)
    await asyncio.sleep(0.5)
    
    await update.message.reply_text(
        "Enter your first name (e.g. Robiya)",
        reply_markup=ReplyKeyboardRemove()
    )
    return State.FIRST_NAME.value


async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle first name input"""
    context.user_data['first_name'] = update.message.text.strip()
    await update.message.reply_text("Enter your last name (e.g. Obidjonova)")
    return State.LAST_NAME.value


async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle last name input"""
    context.user_data['last_name'] = update.message.text.strip()
    await update.message.reply_text("Enter your birth date (e.g. 23.10.2007)")
    return State.BIRTH_DATE.value


async def get_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle birth date input"""
    text = update.message.text.strip()
    
    # Parse date
    try:
        birth_date = datetime.strptime(text, "%d.%m.%Y").date()
        context.user_data['birth_date'] = birth_date.isoformat()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid date format. Please use DD.MM.YYYY format (e.g. 23.10.2007)"
        )
        return State.BIRTH_DATE.value
    
    # Request phone number with button
    keyboard = [[KeyboardButton("📱 Send phone number", request_contact=True)]]
    await update.message.reply_text(
        "Send your phone number (📱 via button)",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return State.PHONE.value


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle phone number input"""
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()
    
    context.user_data['phone'] = phone
    
    pinfl_text = """Please enter your Personal Identification Number (PINFL) - 14 digits.

Why we require your PINFL:
- to verify your age
- to organize your participation in the final event if needed (booking accommodation and purchasing tickets)"""
    
    await update.message.reply_text(pinfl_text, reply_markup=ReplyKeyboardRemove())
    return State.PINFL.value


async def get_pinfl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle PINFL input and complete registration"""
    pinfl = update.message.text.strip()
    
    # Validate PINFL (14 digits)
    if not pinfl.isdigit() or len(pinfl) != 14:
        await update.message.reply_text(
            "❌ PINFL must be exactly 14 digits. Please try again."
        )
        return State.PINFL.value
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Save user to database
    await db.create_user(
        user_id=user_id,
        username=username,
        first_name=context.user_data['first_name'],
        last_name=context.user_data['last_name'],
        birth_date=context.user_data['birth_date'],
        phone=context.user_data['phone'],
        pinfl=pinfl
    )
    
    completion_text = """You're almost done 🔄

To confirm your participation, please choose your hackathon:
Menu → 🚀 Hackathons → AI500! → Register ✅

⚠️ Registration without selecting a hackathon is not valid"""
    
    await update.message.reply_text(completion_text)
    
    # Show hackathons button
    keyboard = [[InlineKeyboardButton("🚀 Hackathons", callback_data="show_hackathons")]]
    await update.message.reply_text(
        "Click below to view available hackathons:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await asyncio.sleep(0.5)
    await update.message.reply_text(
        "You can now use the menu:",
        reply_markup=get_main_menu_keyboard('en')
    )
    
    return ConversationHandler.END


async def show_hackathons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available hackathons"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    hackathons = await db.get_active_hackathons()
    
    if not hackathons:
        message = f"❌ {get_text('no_hackathons', lang)}"
        if query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    # Show each hackathon
    for hackathon in hackathons:
        keyboard = [
            [InlineKeyboardButton(
                f"🏆 {hackathon['name']}", 
                callback_data=f"hackathon_{hackathon['id']}"
            )]
        ]
        
        text = f"""🏆 {hackathon['name']}
        
{hackathon.get('description', '')}

📅 {hackathon.get('start_date', '')} — {hackathon.get('end_date', '')}
💰 Prize pool: {hackathon.get('prize_pool', 'TBA')}"""
        
        if query:
            await query.message.reply_photo(
                photo=hackathon.get('image_url', 'https://via.placeholder.com/400x200'),
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            ) if hackathon.get('image_url') else await query.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_hackathon_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show hackathon details and registration options"""
    query = update.callback_query
    await query.answer()
    
    hackathon_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    hackathon = await db.get_hackathon(hackathon_id)
    if not hackathon:
        await query.edit_message_text("Hackathon not found")
        return
    
    # Check if user is already registered
    registration = await db.get_user_hackathon_registration(user_id, hackathon_id)
    
    keyboard = []
    if registration:
        # Show team options
        team = await db.get_team(registration.get('team_id'))
        if team:
            keyboard.append([InlineKeyboardButton(
                f"👥 Team: {team['name']}", callback_data=f"team_{team['id']}"
            )])
        keyboard.append([InlineKeyboardButton(
            "ℹ️ See details", callback_data=f"details_{hackathon_id}"
        )])
        keyboard.append([InlineKeyboardButton(
            "🚪 Leave team", callback_data=f"leave_team_{hackathon_id}"
        )])
    else:
        keyboard.append([InlineKeyboardButton(
            "✅ Register", callback_data=f"register_{hackathon_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="show_hackathons")])
    
    await query.edit_message_text(
        f"""🏆 {hackathon['name']}

{hackathon.get('description', '')}

📅 {hackathon.get('start_date', '')} — {hackathon.get('end_date', '')}
💰 Prize pool: {hackathon.get('prize_pool', 'TBA')}
👥 Registered teams: {await db.count_teams(hackathon_id)}""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def register_hackathon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Register for a hackathon - create or join team"""
    query = update.callback_query
    await query.answer()
    
    hackathon_id = int(query.data.split('_')[1])
    context.user_data['current_hackathon'] = hackathon_id
    
    keyboard = [
        [InlineKeyboardButton("🆕 Create new team", callback_data=f"create_team_{hackathon_id}")],
        [InlineKeyboardButton("🔗 Join existing team", callback_data=f"join_team_{hackathon_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"hackathon_{hackathon_id}")]
    ]
    
    await query.edit_message_text(
        "How would you like to participate?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


async def create_team_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start team creation"""
    query = update.callback_query
    await query.answer()
    
    hackathon_id = int(query.data.split('_')[2])
    context.user_data['current_hackathon'] = hackathon_id
    
    await query.edit_message_text("📝 Enter your team name:")
    return State.TEAM_NAME.value


async def create_team_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle team name and create team"""
    team_name = update.message.text.strip()
    user_id = update.effective_user.id
    hackathon_id = context.user_data.get('current_hackathon')
    
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    # Create team
    team = await db.create_team(
        hackathon_id=hackathon_id,
        name=team_name,
        leader_id=user_id
    )
    
    # Register user for hackathon with this team
    await db.register_user_for_hackathon(user_id, hackathon_id, team['id'])
    
    text = f"""✅ Team created!

📁 Name: {team_name}
🔑 Code: {team['code']}

Share this code with your teammates so they can join the team.

ℹ️ Soon you will receive updates about the next stages of this hackathon.
Please do not block the bot!"""
    
    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard(lang))
    return ConversationHandler.END


async def join_team_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start joining a team"""
    query = update.callback_query
    await query.answer()
    
    hackathon_id = int(query.data.split('_')[2])
    context.user_data['current_hackathon'] = hackathon_id
    
    await query.edit_message_text("🔑 Enter the team code:")
    return State.TEAM_CODE.value


async def join_team_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle team code and join team"""
    code = update.message.text.strip()
    user_id = update.effective_user.id
    hackathon_id = context.user_data.get('current_hackathon')
    
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    # Find team by code
    team = await db.get_team_by_code(code)
    
    if not team or team['hackathon_id'] != hackathon_id:
        await update.message.reply_text(
            "❌ Invalid team code. Please check and try again.",
            reply_markup=get_main_menu_keyboard(lang)
        )
        return ConversationHandler.END
    
    # Join team
    await db.add_team_member(team['id'], user_id)
    await db.register_user_for_hackathon(user_id, hackathon_id, team['id'])
    
    await update.message.reply_text(
        f"✅ You have joined team '{team['name']}'!",
        reply_markup=get_main_menu_keyboard(lang)
    )
    return ConversationHandler.END


async def show_my_hackathons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's registered hackathons"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    registrations = await db.get_user_registrations(user_id)
    
    if not registrations:
        await update.message.reply_text(
            f"📁 {get_text('your_hackathons', lang)}:\n\n"
            f"You haven't registered for any hackathons yet."
        )
        return
    
    text = f"📁 {get_text('your_hackathons', lang)}:\n\n"
    keyboard = []
    
    for reg in registrations:
        hackathon = await db.get_hackathon(reg['hackathon_id'])
        if hackathon:
            keyboard.append([InlineKeyboardButton(
                hackathon['name'],
                callback_data=f"my_hackathon_{hackathon['id']}"
            )])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )


async def show_my_hackathon_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show details of user's hackathon participation"""
    query = update.callback_query
    await query.answer()
    
    hackathon_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    
    hackathon = await db.get_hackathon(hackathon_id)
    registration = await db.get_user_hackathon_registration(user_id, hackathon_id)
    team = await db.get_team(registration['team_id']) if registration else None
    
    if not team:
        await query.edit_message_text("Team not found")
        return
    
    members = await db.get_team_members(team['id'])
    members_text = ""
    for i, member in enumerate(members, 1):
        member_user = await db.get_user(member['user_id'])
        if member_user:
            role = "(TeamLead)" if member['user_id'] == team['leader_id'] else ""
            members_text += f"{i}. {member_user['first_name']} {member_user['last_name']} - {member.get('role', 'Member')} {role}\n"
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ See details", callback_data=f"details_{hackathon_id}")],
        [InlineKeyboardButton("🚪 Leave team", callback_data=f"leave_team_{hackathon_id}")],
        [InlineKeyboardButton("❌ Remove member", callback_data=f"remove_member_{team['id']}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_my_hackathons")]
    ]
    
    await query.edit_message_text(
        f"""📁 Name: {team['name']}
🔑 Code: {team['code']}

👥 Members:
{members_text}

To see more about this hackathon, use the button below 👇""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show settings menu"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    await update.message.reply_text(
        f"🌐 {get_text('choose_language', lang)}:",
        reply_markup=get_language_keyboard()
    )


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language change"""
    query = update.callback_query
    await query.answer()
    
    new_lang = query.data.split('_')[1]
    user_id = update.effective_user.id
    
    await db.update_user_language(user_id, new_lang)
    user = await db.get_user(user_id)
    
    # Show user data
    keyboard = [
        [InlineKeyboardButton(f"✏️ {get_text('change_first_name', new_lang)}", callback_data="edit_first_name")],
        [InlineKeyboardButton(f"✏️ {get_text('change_last_name', new_lang)}", callback_data="edit_last_name")],
        [InlineKeyboardButton(f"✏️ {get_text('birth_date', new_lang)}", callback_data="edit_birth_date")],
        [InlineKeyboardButton(f"✏️ {get_text('gender', new_lang)}", callback_data="edit_gender")],
        [InlineKeyboardButton(f"✏️ {get_text('location', new_lang)}", callback_data="edit_location")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
    ]
    
    text = f"""👤 {get_text('your_data', new_lang)}:

• {get_text('first_name', new_lang)}: {user.get('first_name', '')}
• {get_text('last_name', new_lang)}: {user.get('last_name', '')}
• {get_text('birth_date', new_lang)}: {user.get('birth_date', '')}
• {get_text('gender', new_lang)}: {user.get('gender', 'Not set')}
• {get_text('location', new_lang)}: {user.get('location', 'Not set')}"""
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user data after settings"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    keyboard = [
        [InlineKeyboardButton(f"✏️ {get_text('change_first_name', lang)}", callback_data="edit_first_name")],
        [InlineKeyboardButton(f"✏️ {get_text('change_last_name', lang)}", callback_data="edit_last_name")],
        [InlineKeyboardButton(f"✏️ {get_text('birth_date', lang)}", callback_data="edit_birth_date")],
        [InlineKeyboardButton(f"✏️ {get_text('gender', lang)}", callback_data="edit_gender")],
        [InlineKeyboardButton(f"✏️ {get_text('location', lang)}", callback_data="edit_location")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
    ]
    
    text = f"""👤 {get_text('your_data', lang)}:

• {get_text('first_name', lang)}: {user.get('first_name', '')}
• {get_text('last_name', lang)}: {user.get('last_name', '')}
• {get_text('birth_date', lang)}: {user.get('birth_date', '')}
• {get_text('gender', lang)}: {user.get('gender', 'Not set')}
• {get_text('location', lang)}: {user.get('location', 'Not set')}"""
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    help_text = f"""💡 {get_text('need_help', lang)}

{get_text('help_text', lang)}
📧 {SUPPORT_EMAIL}

{get_text('describe_problem', lang)} ✅"""
    
    await update.message.reply_text(help_text)


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu button presses"""
    text = update.message.text.lower()
    
    if "hackathon" in text and "my" not in text:
        await show_hackathons_menu(update, context)
    elif "my hackathon" in text or "mening" in text:
        await show_my_hackathons(update, context)
    elif "setting" in text or "sozlamalar" in text or "настройки" in text:
        await show_settings(update, context)
    elif "help" in text or "yordam" in text or "помощь" in text:
        await show_help(update, context)


async def show_hackathons_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show hackathons from menu button"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    hackathons = await db.get_active_hackathons()
    
    if not hackathons:
        await update.message.reply_text(f"❌ {get_text('no_hackathons', lang)}")
        return
    
    keyboard = []
    for hackathon in hackathons:
        keyboard.append([InlineKeyboardButton(
            f"🏆 {hackathon['name']}",
            callback_data=f"hackathon_{hackathon['id']}"
        )])
    
    await update.message.reply_text(
        f"🚀 {get_text('available_hackathons', lang)}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============== ADMIN FUNCTIONS ==============

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Access denied")
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Create Hackathon", callback_data="admin_create_hackathon")],
        [InlineKeyboardButton("📋 Manage Hackathons", callback_data="admin_manage_hackathons")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("🏆 Manage Stages", callback_data="admin_stages")],
    ]
    
    await update.message.reply_text(
        "🔐 Admin Panel",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_create_hackathon_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start hackathon creation"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id not in ADMIN_IDS:
        return ConversationHandler.END
    
    await query.edit_message_text("📝 Enter hackathon name:")
    return State.ADMIN_HACKATHON_NAME.value


async def admin_hackathon_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle hackathon name"""
    context.user_data['admin_hackathon_name'] = update.message.text.strip()
    await update.message.reply_text("📝 Enter hackathon description:")
    return State.ADMIN_HACKATHON_DESC.value


async def admin_hackathon_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle hackathon description"""
    context.user_data['admin_hackathon_desc'] = update.message.text.strip()
    await update.message.reply_text(
        "📅 Enter dates (format: DD.MM.YYYY - DD.MM.YYYY)\n"
        "Example: 01.12.2024 - 15.12.2024"
    )
    return State.ADMIN_HACKATHON_DATES.value


async def admin_hackathon_dates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle hackathon dates and create"""
    dates_text = update.message.text.strip()
    
    try:
        start_str, end_str = dates_text.split(' - ')
        start_date = datetime.strptime(start_str.strip(), "%d.%m.%Y").date()
        end_date = datetime.strptime(end_str.strip(), "%d.%m.%Y").date()
    except:
        await update.message.reply_text("❌ Invalid date format. Use: DD.MM.YYYY - DD.MM.YYYY")
        return State.ADMIN_HACKATHON_DATES.value
    
    # Create hackathon
    hackathon = await db.create_hackathon(
        name=context.user_data['admin_hackathon_name'],
        description=context.user_data['admin_hackathon_desc'],
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    await update.message.reply_text(
        f"✅ Hackathon '{hackathon['name']}' created!\n"
        f"ID: {hackathon['id']}"
    )
    return ConversationHandler.END


async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start broadcast message"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id not in ADMIN_IDS:
        return ConversationHandler.END
    
    # Get hackathons for selection
    hackathons = await db.get_all_hackathons()
    
    if not hackathons:
        await query.edit_message_text("No hackathons available")
        return ConversationHandler.END
    
    keyboard = []
    for h in hackathons:
        keyboard.append([InlineKeyboardButton(
            h['name'], 
            callback_data=f"broadcast_to_{h['id']}"
        )])
    keyboard.append([InlineKeyboardButton("📢 All users", callback_data="broadcast_to_all")])
    
    await query.edit_message_text(
        "Select target audience:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


async def admin_broadcast_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle broadcast target selection"""
    query = update.callback_query
    await query.answer()
    
    target = query.data.split('_')[2]
    context.user_data['broadcast_target'] = target
    
    await query.edit_message_text("📝 Enter the message to broadcast:")
    return State.ADMIN_BROADCAST.value


async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send broadcast message"""
    message = update.message.text
    target = context.user_data.get('broadcast_target', 'all')
    
    if target == 'all':
        users = await db.get_all_users()
    else:
        users = await db.get_hackathon_participants(int(target))
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(chat_id=user['user_id'], text=message)
            sent += 1
        except Exception as e:
            logger.error(f"Failed to send to {user['user_id']}: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"✅ Broadcast completed!\n"
        f"Sent: {sent}\n"
        f"Failed: {failed}"
    )
    return ConversationHandler.END


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics"""
    query = update.callback_query
    await query.answer()
    
    total_users = await db.count_users()
    total_teams = await db.count_all_teams()
    active_hackathons = len(await db.get_active_hackathons())
    
    await query.edit_message_text(
        f"📊 Statistics\n\n"
        f"👥 Total users: {total_users}\n"
        f"👥 Total teams: {total_teams}\n"
        f"🏆 Active hackathons: {active_hackathons}"
    )


# ============== STAGE MANAGEMENT ==============

async def show_stages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show hackathon stages (for participants)"""
    query = update.callback_query
    await query.answer()
    
    hackathon_id = int(query.data.split('_')[1])
    stages = await db.get_hackathon_stages(hackathon_id)
    
    if not stages:
        await query.edit_message_text("No stages defined yet.")
        return
    
    keyboard = []
    for stage in stages:
        status = "✅" if stage.get('is_active') else "⏳"
        keyboard.append([InlineKeyboardButton(
            f"{status} Stage {stage['number']}: {stage['name']}",
            callback_data=f"stage_{stage['id']}"
        )])
    
    await query.edit_message_text(
        "📋 Hackathon Stages:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_stage_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show stage details and submission option"""
    query = update.callback_query
    await query.answer()
    
    stage_id = int(query.data.split('_')[1])
    stage = await db.get_stage(stage_id)
    
    if not stage:
        await query.edit_message_text("Stage not found")
        return
    
    user_id = update.effective_user.id
    submission = await db.get_submission(user_id, stage_id)
    
    keyboard = []
    if stage.get('is_active') and not submission:
        keyboard.append([InlineKeyboardButton(
            "📤 Submit", callback_data=f"submit_{stage_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"details_{stage['hackathon_id']}")])
    
    status_text = ""
    if submission:
        status_text = f"\n\n✅ Your submission: {submission.get('link', 'Submitted')}"
    elif not stage.get('is_active'):
        status_text = "\n\n⏰ Stage deadline has already passed :("
    
    await query.edit_message_text(
        f"""🏁 Stage {stage['number']}: {stage['name']}

📅 {stage.get('start_date', '')} — {stage.get('end_date', '')}

📝 Task: {stage.get('task_description', 'Check the task document')}

❗ Deadline: {stage.get('end_date', '')} 23:59 (GMT +5)
❗ Submission: Send the link to your live demo website in this bot{status_text}""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def submit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start submission process"""
    query = update.callback_query
    await query.answer()
    
    stage_id = int(query.data.split('_')[1])
    context.user_data['submit_stage'] = stage_id
    
    await query.edit_message_text(
        "📤 Submit your work\n\n"
        "Send the link to your live demo website:"
    )
    return State.SUBMIT_LINK.value


async def submit_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle submission link"""
    link = update.message.text.strip()
    stage_id = context.user_data.get('submit_stage')
    user_id = update.effective_user.id
    
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    # Save submission
    await db.create_submission(user_id, stage_id, link)
    
    await update.message.reply_text(
        f"✅ Submission received!\n\n"
        f"Link: {link}\n\n"
        "Good luck! 🍀",
        reply_markup=get_main_menu_keyboard(lang)
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation"""
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.get('language', 'en') if user else 'en'
    
    await update.message.reply_text(
        "Operation cancelled.",
        reply_markup=get_main_menu_keyboard(lang)
    )
    return ConversationHandler.END


def main() -> None:
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Registration conversation
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.FIRST_NAME.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_first_name)],
            State.LAST_NAME.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_last_name)],
            State.BIRTH_DATE.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birth_date)],
            State.PHONE.value: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)
            ],
            State.PINFL.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pinfl)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Team creation conversation
    team_creation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_team_start, pattern=r"^create_team_\d+$")],
        states={
            State.TEAM_NAME.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_team_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Team join conversation
    team_join_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(join_team_start, pattern=r"^join_team_\d+$")],
        states={
            State.TEAM_CODE.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_team_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Submission conversation
    submission_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(submit_start, pattern=r"^submit_\d+$")],
        states={
            State.SUBMIT_LINK.value: [
                MessageHandler(filters.Document.ALL, handle_submission),
                MessageHandler(filters.PHOTO, handle_submission),
                MessageHandler(filters.VIDEO, handle_submission),
                MessageHandler(filters.AUDIO, handle_submission),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_submission),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Admin hackathon creation conversation
    admin_hackathon_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_create_hackathon_start, pattern=r"^admin_create_hackathon$")],
        states={
            State.ADMIN_HACKATHON_NAME.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_hackathon_name)],
            State.ADMIN_HACKATHON_DESC.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_hackathon_desc)],
            State.ADMIN_HACKATHON_DATES.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_hackathon_dates)],
            State.ADMIN_HACKATHON_PRIZE.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_hackathon_prize)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Admin stage creation conversation
    admin_stage_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_stage_start, pattern=r"^admin_add_stage_\d+$")],
        states={
            State.ADMIN_STAGE_NAME.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_stage_name)],
            State.ADMIN_STAGE_DATES.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_stage_dates)],
            State.ADMIN_STAGE_TASK.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_stage_task)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Admin broadcast conversation
    admin_broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_select, pattern=r"^broadcast_to_")],
        states={
            State.ADMIN_BROADCAST.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers in order
    application.add_handler(registration_handler)
    application.add_handler(team_creation_handler)
    application.add_handler(team_join_handler)
    application.add_handler(submission_handler)
    application.add_handler(admin_hackathon_handler)
    application.add_handler(admin_stage_handler)
    application.add_handler(admin_broadcast_handler)
    
    # Command handlers
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("help", show_help))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(show_hackathons, pattern=r"^show_hackathons$"))
    application.add_handler(CallbackQueryHandler(show_hackathon_details, pattern=r"^hackathon_\d+$"))
    application.add_handler(CallbackQueryHandler(register_hackathon, pattern=r"^register_\d+$"))
    application.add_handler(CallbackQueryHandler(show_my_hackathon_details, pattern=r"^my_hackathon_\d+$"))
    application.add_handler(CallbackQueryHandler(leave_team, pattern=r"^leave_team_\d+$"))
    application.add_handler(CallbackQueryHandler(show_stages, pattern=r"^stages_\d+$"))
    application.add_handler(CallbackQueryHandler(show_stage_details, pattern=r"^stage_\d+$"))
    application.add_handler(CallbackQueryHandler(change_language, pattern=r"^lang_"))
    application.add_handler(CallbackQueryHandler(edit_gender, pattern=r"^edit_gender$"))
    application.add_handler(CallbackQueryHandler(set_gender, pattern=r"^set_gender_"))
    application.add_handler(CallbackQueryHandler(change_language, pattern=r"^settings$"))
    
    # Admin callbacks
    application.add_handler(CallbackQueryHandler(admin_back, pattern=r"^admin_back$"))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern=r"^admin_stats$"))
    application.add_handler(CallbackQueryHandler(admin_broadcast_start, pattern=r"^admin_broadcast$"))
    application.add_handler(CallbackQueryHandler(admin_export_submissions, pattern=r"^admin_export$"))
    application.add_handler(CallbackQueryHandler(export_hackathon_submissions, pattern=r"^export_hackathon_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_manage_stages, pattern=r"^admin_stages_list$"))
    application.add_handler(CallbackQueryHandler(admin_hackathon_stages, pattern=r"^admin_stages_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_stage_details, pattern=r"^admin_stage_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_toggle_stage, pattern=r"^toggle_stage_\d+$"))
    
    # Menu button handler (should be last)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_menu_buttons
    ))
    
    # Run the bot
    print("🚀 Kod va G'oyalar Hackathons Bot is starting...")
    print("Press Ctrl+C to stop")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()points=[CallbackQueryHandler(join_team_start, pattern=r"^join_team_\d+$")],
        states={
            State.TEAM_CODE.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_team_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Submission conversation
    submission_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(submit_start, pattern=r"^submit_\d+$")],
        states={
            State.SUBMIT_LINK.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, submit_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Admin hackathon creation conversation
    admin_hackathon_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_create_hackathon_start, pattern=r"^admin_create_hackathon$")],
        states={
            State.ADMIN_HACKATHON_NAME.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_hackathon_name)],
            State.ADMIN_HACKATHON_DESC.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_hackathon_desc)],
            State.ADMIN_HACKATHON_DATES.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_hackathon_dates)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Admin broadcast conversation
    admin_broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_select, pattern=r"^broadcast_to_")],
        states={
            State.ADMIN_BROADCAST.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers
    application.add_handler(registration_handler)
    application.add_handler(team_creation_handler)
    application.add_handler(team_join_handler)
    application.add_handler(submission_handler)
    application.add_handler(admin_hackathon_handler)
    application.add_handler(admin_broadcast_handler)
    
    # Command handlers
    application.add_handler(CommandHandler("admin", admin_panel))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(show_hackathons, pattern=r"^show_hackathons$"))
    application.add_handler(CallbackQueryHandler(show_hackathon_details, pattern=r"^hackathon_\d+$"))
    application.add_handler(CallbackQueryHandler(register_hackathon, pattern=r"^register_\d+$"))
    application.add_handler(CallbackQueryHandler(show_my_hackathon_details, pattern=r"^my_hackathon_\d+$"))
    application.add_handler(CallbackQueryHandler(change_language, pattern=r"^lang_"))
    application.add_handler(CallbackQueryHandler(show_user_data, pattern=r"^settings$"))
    application.add_handler(CallbackQueryHandler(show_stages, pattern=r"^stages_\d+$"))
    application.add_handler(CallbackQueryHandler(show_stage_details, pattern=r"^stage_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_broadcast_start, pattern=r"^admin_broadcast$"))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern=r"^admin_stats$"))
    
    # Menu button handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_menu_buttons
    ))
    
    # Run the bot
    print("🚀 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
