import os
import asyncio
import logging
from datetime import datetime, timedelta

from mcstatus import JavaServer
from telegram.ext import Application

# === SETTINGS ===
SERVER_IP = os.environ.get("SERVER_IP", "127.0.0.1:25565")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "10")) # seconds
COOLDOWN_HOURS = int(os.environ.get("COOLDOWN_HOURS", "1"))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "-1"))
TELEGRAM_CHAT_THREAD_ID = int(os.environ.get("TELEGRAM_CHAT_THREAD_ID", "1"))

# === INITIALIZATION ===
application = Application.builder().token(TELEGRAM_TOKEN).build()
server = JavaServer.lookup(SERVER_IP)

player_status = {}  # {nickname: (online: bool, last_notification: datetime)}
initial_check_done = False  # Last check completion flag

logging.basicConfig(level=logging.INFO)

async def send_telegram_message(text: str):
    """Helper function to send messages to Telegram"""
    try:
        # Checking if the application is initialized
        if hasattr(application, 'bot') and application.bot:
            await application.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                message_thread_id=TELEGRAM_CHAT_THREAD_ID,
                text=text  # Using message_thread_id instead of reply_to_message_id
            )
            logging.info(f"Telegram message sent: {text}")
        else:
            # Creating a temporary bot to send a message
            from telegram import Bot as TelegramBot
            temp_bot = TelegramBot(token=TELEGRAM_TOKEN)
            await temp_bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                message_thread_id=TELEGRAM_CHAT_THREAD_ID,
                text=text
            )
            await temp_bot.close()
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")

async def check_server():
    global initial_check_done
    
    # Initializing the bot inside the app
    await application.initialize()
    await application.start()
    
    try:
        while True:
            try:
                status = server.status()
                now = datetime.now()
                current_players = {p.name for p in status.players.sample} if status.players.sample else set()

                # First check - only save status
                if not initial_check_done:
                    for name in current_players:
                        player_status[name] = (True, None)  # Save online-status with no notification
                    logging.info(f"Initial check: {len(current_players)} players online")
                    initial_check_done = True
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue
                
                # Next checks - regular procedure
                all_players = set(player_status.keys()).union(current_players)
                
                for name in all_players:
                    is_online = name in current_players
                    last_data = player_status.get(name, (False, None))
                    was_online, last_notification = last_data
                    
                    if is_online and not was_online:  # Player joined
                        if last_notification is None or (now - last_notification) > timedelta(hours=COOLDOWN_HOURS):
                            message = f"🎮 Игрок {name} зашёл на сервер"
                            await send_telegram_message(message)
                            
                            player_status[name] = (True, now)
                        else:
                            player_status[name] = (True, last_notification)
                    elif not is_online:  # Player left
                        player_status[name] = (False, last_notification)

                logging.info(f"Check complete. Online: {len(current_players)} players.")

            except Exception as e:
                logging.warning(f"Error parsing the server: {e}")

            await asyncio.sleep(CHECK_INTERVAL)
            
    finally:
        # Stopping the app correctly
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(check_server())