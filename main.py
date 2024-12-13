import configparser
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import Clock, mainthread
from threading import Thread

from requests import session

from discord.ext import commands
import discord
import asyncio
import queue
import os
import ssl
import certifi
import aiohttp

# Path to the certificate in the assets folder
cert_path = 'discord-cert.pem'


# Set up SSL context using the bundled cert file
ssl_context = ssl.create_default_context(cafile=cert_path)
#ssl_context = ssl.create_default_context(cafile=certifi.where())


# Load KV file
KV = """
MDScreen:
    MDLabel:
        id: log_label
        text: "Starting Discord bot..."
        halign: "center"
        valign: "middle"
        font_style: "H6"
"""

# Configuration Setup
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), "config.ini")

if not os.path.exists(config_path):
    # Create a default config.ini file if it doesn't exist
    config["BOT"] = {"token": "YOUR_DISCORD_BOT_TOKEN_HERE"}
    with open(config_path, "w") as configfile:
        config.write(configfile)
    print(f"Config file created at {config_path}. Please fill in your Discord bot token.")
    raise SystemExit("Exiting... Add your Discord bot token in the config.ini file.")

# Load token from config.ini
config.read(config_path)
discord_token = config["BOT"].get("token")

if not discord_token or discord_token == "YOUR_DISCORD_BOT_TOKEN_HERE":
    raise ValueError("No valid Discord token found in the config.ini file. Update it with your bot token.")

# Start Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# A thread-safe queue to send logs to the Kivy UI
log_queue = queue.Queue()

# Async bot events
@bot.event
async def on_ready():
    log_queue.put(f"Logged in as {bot.user}")
    log_queue.put("Bot is ready and session initialized.")

@bot.event
async def on_connect():
    log_queue.put("Connecting to Discord...")

@bot.event
async def on_disconnect():
    log_queue.put("Disconnected from Discord!")

async def load_cogs():
    """Load all cogs from the 'cogs' folder."""
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            cog_name = f"cogs.{filename[:-3]}"  # Remove '.py' and add folder name
            try:
                await bot.load_extension(cog_name)
                log_queue.put(f"Loaded cog: {cog_name}")
            except Exception as e:
                log_queue.put(f"Failed to load cog {cog_name}: {str(e)}")

async def bot_start():
    """Start the Discord bot with an aiohttp session."""
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            bot.session = session  # Attach aiohttp session to the bot
            await load_cogs()  # Load cogs before starting the bot
            await bot.start(discord_token)  # Use token from config.ini
    except discord.LoginFailure:
        log_queue.put("Failed to login. Check your Discord token.")

def start_discord_bot():
    """Run the bot start coroutine."""
    asyncio.run(bot_start())

# Main App
class BotLogApp(MDApp):
    def build(self):
        # Load KV content
        self.root = Builder.load_string(KV)
        return self.root

    @mainthread
    def update_log_label(self, text):
        """Safely update the log_label text on the UI thread."""
        self.root.ids.log_label.text = text

    def check_logs(self, dt):
        """Check the log queue and update the Kivy UI."""
        while not log_queue.empty():
            log_message = log_queue.get()
            self.update_log_label(log_message)

    def on_start(self):
        """Start Discord bot and schedule log updates."""
        # Schedule checking the log queue
        Clock.schedule_interval(self.check_logs, 0.5)

        # Start Discord bot in a separate thread
        bot_thread = Thread(target=start_discord_bot, daemon=True)
        bot_thread.start()

# Run the App
if __name__ == "__main__":
    BotLogApp().run()
