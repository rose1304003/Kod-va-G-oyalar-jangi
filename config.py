"""
Configuration for ITCom Hackathons Bot
Set environment variables for production deployment
"""

import os

# Bot Token - Get from @BotFather on Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Database URL - PostgreSQL connection string
# For Railway: postgres://user:password@host:port/database
# For local development: leave empty to use SQLite
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Admin IDs - Telegram user IDs who have admin access
# Add your Telegram user ID here (get it from @userinfobot)
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(',') if x.strip()]

# Super Admin IDs - Full system control
SUPER_ADMIN_IDS_STR = os.getenv('SUPER_ADMIN_IDS', '')
SUPER_ADMIN_IDS = [int(x.strip()) for x in SUPER_ADMIN_IDS_STR.split(',') if x.strip()]

# Support email
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'ai500@itcommunity.uz')

# Alternative support email
ALT_SUPPORT_EMAIL = os.getenv('ALT_SUPPORT_EMAIL', 'itcommunityuzbekistan@gmail.com')

# FAQ URL
FAQ_URL = os.getenv('FAQ_URL', 'https://drive.google.com/file/d/1rhwoJX6gzIdoQTaohc5l7TdRASmAO7-F')

# Bot timezone (for deadline calculations)
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Tashkent')

# Webhook settings (for production)
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8443'))

# Logging level
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Maximum team size
MAX_TEAM_SIZE = int(os.getenv('MAX_TEAM_SIZE', '5'))

# File upload settings
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))

# Allowed file extensions for submissions
ALLOWED_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.pptx', '.ppt',
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.mp4', '.mov', '.avi', '.mkv',
    '.mp3', '.wav', '.ogg',
    '.zip', '.rar', '.7z',
    '.txt', '.md', '.html', '.css', '.js', '.py'
]
