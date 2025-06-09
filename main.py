import asyncio
import logging
import os
from dotenv import load_dotenv, find_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN  # Make sure this is in your config.py
from utils.database import Database  # Assuming you have a database helper
from handlers.main_menu import router as main_menu_router
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router
from handlers.bin_handlers import router as bin_router
from handlers.cards_handlers import router as cards_router
from handlers.guide_handlers import router as guide_router
from handlers.membership_handler import router as membership_router
from handlers.ticket_handlers import router as ticket_router
import nest_asyncio

# Load environment variables
load_dotenv(find_dotenv())
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set. Please check your environment variables.")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and database
db = Database('bot_database.db')
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Send startup message to all users in batches
async def send_startup_message(bot: Bot):
    if not db.get_startup_message_status():
        logger.info("Startup message is disabled. Skipping...")
        return

    # Get user counts for stats
    user_count = db.get_user_count()
    premium_count = db.get_premium_user_count()
    guide_count = db.get_guide_count()

    # Get all users from the database
    users = db.get_all_users()

    # Send messages in batches of 10 users
    batch_size = 10
    for idx, user in enumerate(users):
        user_id = user['user_id']
        user_data = db.get_user(user_id)

        if user_data:
            membership_level = user_data[2]
            membership_emoji = "🌟" if membership_level.lower() == "premium" else "👤"

            # Construct the startup message
            startup_message = """
🎉 <b>Carding Empire Bot is Online!</b> 🎉

📊 <b>Current Stats:</b>
• <b>Total Users</b>: <code>{user_count}</code>
• <b>Premium Members</b>: <code>{premium_count}</code>
• <b>Available Guides</b>: <code>{guide_count}</code>

<b>Welcome to the Carding Empire Bot!</b> {membership_emoji} We are excited to have you onboard!

Feel free to explore the bot, and remember, premium members have special privileges!
"""

            try:
                await bot.send_message(user_id, startup_message)
                logger.info(f"Sent startup message to user {user_id}")
            except Exception as e:
                if 'Unauthorized' in str(e):
                    logger.info(f"User {user_id} hasn't started the bot yet. Skipping...")
                else:
                    logger.error(f"Failed to send startup message to user {user_id}: {e}")

        # Batch processing: sleep every 10 users to avoid rate-limiting
        if (idx + 1) % batch_size == 0:
            await asyncio.sleep(1)  # Adjust delay to comply with Telegram's rate limit

    # Update the database to prevent sending the message again
    db.set_startup_message_status(True)
    logger.info("Startup message sent to all users.")

# Register your handlers (routers)
async def on_startup():
    logger.info("Starting the bot...")
    await send_startup_message(bot)

# Set bot commands
async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Start the bot"),
        BotCommand(command="/help", description="Get help"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set.")

# Main function to run the bot
async def main():
    # Setup routers for the bot's different sections
    router = Router()
    router.include_router(main_menu_router)
    router.include_router(user_router)
    router.include_router(admin_router)
    router.include_router(bin_router)
    router.include_router(cards_router)
    router.include_router(guide_router)
    router.include_router(membership_router)
    router.include_router(ticket_router)

    # Set bot commands
    await set_bot_commands()

    # Send startup message to all users
    await send_startup_message(bot)

nest_asyncio.apply()
asyncio.run(main())
