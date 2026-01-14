"""
Scheduler module for ITCom Hackathons Bot
Handles automatic notifications and deadline reminders
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from database import Database
from translations import get_text
from config import TIMEZONE

logger = logging.getLogger(__name__)

# Timezone
tz = pytz.timezone(TIMEZONE)


class NotificationScheduler:
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler(timezone=tz)
    
    def start(self):
        """Start the scheduler"""
        # Check deadlines every hour
        self.scheduler.add_job(
            self.check_deadlines,
            CronTrigger(hour='*'),  # Every hour
            id='check_deadlines',
            replace_existing=True
        )
        
        # Send daily reminders at 10:00 AM
        self.scheduler.add_job(
            self.send_daily_reminders,
            CronTrigger(hour=10, minute=0),
            id='daily_reminders',
            replace_existing=True
        )
        
        # Check for new stages at 9:00 AM
        self.scheduler.add_job(
            self.notify_new_stages,
            CronTrigger(hour=9, minute=0),
            id='new_stages',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Notification scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Notification scheduler stopped")
    
    async def check_deadlines(self):
        """Check for approaching deadlines and send notifications"""
        try:
            now = datetime.now(tz)
            today = now.date()
            
            # Get all active stages
            hackathons = await self.db.get_active_hackathons()
            
            for hackathon in hackathons:
                stages = await self.db.get_hackathon_stages(hackathon['id'])
                
                for stage in stages:
                    if not stage.get('is_active'):
                        continue
                    
                    end_date = datetime.fromisoformat(stage['end_date']).date() if stage.get('end_date') else None
                    if not end_date:
                        continue
                    
                    days_left = (end_date - today).days
                    
                    # Notify based on days left
                    if days_left == 0 and now.hour == 9:
                        await self.send_deadline_notification(
                            hackathon['id'],
                            f"⏳ Deadline approaching!\n\n"
                            f"Today until 23:59 — the final chance to submit your Stage {stage['number']} answers.\n"
                            f"The Selection Team will review submissions tomorrow.\n\n"
                            f"Good luck! ✨"
                        )
                    elif days_left == 0 and now.hour == 21:
                        await self.send_deadline_notification(
                            hackathon['id'],
                            f"⚠️ LAST 3 HOURS!\n\n"
                            f"Stage {stage['number']} deadline is at 23:59 tonight.\n"
                            f"Don't forget to submit your work!"
                        )
        
        except Exception as e:
            logger.error(f"Error checking deadlines: {e}")
    
    async def send_daily_reminders(self):
        """Send daily reminders about upcoming tasks"""
        try:
            now = datetime.now(tz)
            today = now.date()
            
            hackathons = await self.db.get_active_hackathons()
            
            for hackathon in hackathons:
                stages = await self.db.get_hackathon_stages(hackathon['id'])
                
                for stage in stages:
                    start_date = datetime.fromisoformat(stage['start_date']).date() if stage.get('start_date') else None
                    if not start_date:
                        continue
                    
                    days_until_start = (start_date - today).days
                    
                    # 3 days before first task
                    if days_until_start == 3:
                        await self.send_hackathon_notification(
                            hackathon['id'],
                            f"⏳ 3 days left until the first task!\n\n"
                            f"Your first task is coming up soon, so now is a good time to settle on your project idea.\n\n"
                            f"If you don't yet have a clear direction, you may consider exploring agriculture 🌱 — "
                            f"our partners have a special interest in this area.\n\n"
                            f"If you already have your idea, just keep going.\n\n"
                            f"🏆 At {hackathon['name']}, the strongest project wins — regardless of the track.\n\n"
                            f"Questions? Contact support at ai500@itcommunity.uz 📧"
                        )
                    
                    # 2 days before
                    elif days_until_start == 2:
                        await self.send_hackathon_notification(
                            hackathon['id'],
                            f"🕐 In just two days you will receive your first task!\n\n"
                            f"To help you prepare, we've put together an FAQ with all the key information about the hackathon.\n\n"
                            f"📋 Check the FAQ if you have any questions.\n\n"
                            f"If you still have questions, feel free to contact us at ai500@itcommunity.uz 📧"
                        )
        
        except Exception as e:
            logger.error(f"Error sending daily reminders: {e}")
    
    async def notify_new_stages(self):
        """Notify participants about new active stages"""
        try:
            now = datetime.now(tz)
            today = now.date()
            
            hackathons = await self.db.get_active_hackathons()
            
            for hackathon in hackathons:
                stages = await self.db.get_hackathon_stages(hackathon['id'])
                
                for stage in stages:
                    if not stage.get('is_active'):
                        continue
                    
                    start_date = datetime.fromisoformat(stage['start_date']).date() if stage.get('start_date') else None
                    
                    # If stage starts today, send notification
                    if start_date == today:
                        await self.send_hackathon_notification(
                            hackathon['id'],
                            f"🎉 {hackathon['name']} — Stage {stage['number']}\n"
                            f"📅 {stage['start_date']} — {stage['end_date']}\n\n"
                            f"🎊 Congratulations on making it to Stage {stage['number']}!\n\n"
                            f"Your task: {stage.get('task_description', 'Check the bot for details')}\n\n"
                            f"❗ Deadline: {stage['end_date']} 23:59 (GMT +5)\n"
                            f"❗ Submission: Send the link to your live demo website in this bot\n\n"
                            f"💡 Tip: Make your content clear and complete, don't miss any section, "
                            f"and highlight AI tools or technologies you plan to use."
                        )
        
        except Exception as e:
            logger.error(f"Error notifying new stages: {e}")
    
    async def send_hackathon_notification(self, hackathon_id: int, message: str):
        """Send notification to all participants of a hackathon"""
        try:
            participants = await self.db.get_hackathon_participants(hackathon_id)
            
            sent = 0
            failed = 0
            
            for participant in participants:
                try:
                    await self.bot.send_message(
                        chat_id=participant['user_id'],
                        text=message
                    )
                    sent += 1
                except Exception as e:
                    logger.warning(f"Failed to send to {participant['user_id']}: {e}")
                    failed += 1
                
                # Rate limiting
                await asyncio.sleep(0.05)
            
            logger.info(f"Notification sent to hackathon {hackathon_id}: {sent} sent, {failed} failed")
        
        except Exception as e:
            logger.error(f"Error sending hackathon notification: {e}")
    
    async def send_deadline_notification(self, hackathon_id: int, message: str):
        """Send deadline notification to participants without submissions"""
        try:
            participants = await self.db.get_hackathon_participants(hackathon_id)
            hackathon = await self.db.get_hackathon(hackathon_id)
            stages = await self.db.get_hackathon_stages(hackathon_id)
            
            # Find active stage
            active_stage = None
            for stage in stages:
                if stage.get('is_active'):
                    active_stage = stage
                    break
            
            if not active_stage:
                return
            
            sent = 0
            for participant in participants:
                # Check if they have submitted
                submission = await self.db.get_submission(participant['user_id'], active_stage['id'])
                
                if not submission:
                    try:
                        await self.bot.send_message(
                            chat_id=participant['user_id'],
                            text=message
                        )
                        sent += 1
                    except Exception as e:
                        logger.warning(f"Failed to send to {participant['user_id']}: {e}")
                
                await asyncio.sleep(0.05)
            
            logger.info(f"Deadline notification sent: {sent} participants")
        
        except Exception as e:
            logger.error(f"Error sending deadline notification: {e}")
    
    async def send_stage_results(self, hackathon_id: int, stage_number: int, 
                                  advanced_teams: list, message: str = None):
        """Send stage results and advancement notifications"""
        try:
            hackathon = await self.db.get_hackathon(hackathon_id)
            participants = await self.db.get_hackathon_participants(hackathon_id)
            
            for participant in participants:
                # Check if participant's team advanced
                registration = await self.db.get_user_hackathon_registration(
                    participant['user_id'], hackathon_id
                )
                
                if registration and registration.get('team_id') in advanced_teams:
                    text = f"🎉 Congratulations!\n\n" \
                           f"Your team has advanced to Stage {stage_number + 1} of {hackathon['name']}!\n\n" \
                           f"Stay tuned for the next task. ✨"
                else:
                    text = f"Thank you for participating in {hackathon['name']}!\n\n" \
                           f"Unfortunately, your team didn't advance to the next stage this time.\n\n" \
                           f"Keep building and improving — we hope to see you in future hackathons! 💪"
                
                try:
                    await self.bot.send_message(chat_id=participant['user_id'], text=text)
                except Exception as e:
                    logger.warning(f"Failed to send results to {participant['user_id']}: {e}")
                
                await asyncio.sleep(0.05)
        
        except Exception as e:
            logger.error(f"Error sending stage results: {e}")
