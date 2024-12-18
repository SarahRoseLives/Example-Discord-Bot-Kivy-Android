import configparser
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import Clock, mainthread
from threading import Thread
from discord.ext import commands
import discord
import asyncio
import queue
import os
import ssl
import certifi
import aiohttp

# Set up SSL context using the bundled cert file
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Load KV file
KV = """
MDScreen:
    MDBoxLayout:
        orientation: "vertical"

        MDLabel:
            text: "Discord Bot Logs"
            halign: "center"
            font_style: "H6"
            size_hint_y: None
            height: self.texture_size[1]

        ScrollView:
            MDList:
                id: log_list
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

@bot.event
async def on_connect():
    log_queue.put("Connecting to Discord...")

@bot.event
async def on_disconnect():
    log_queue.put("Disconnected from Discord!")

async def load_cogs():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    cogs_directory = os.path.join(current_dir, 'cogs')
    for filename in os.listdir(cogs_directory):
        if filename.endswith('.pyc'):
            await bot.load_extension(f'cogs.{filename[:-4]}')


async def bot_start():
    """Start the Discord bot using a custom SSL context."""
    try:
        # Create a custom connector with the SSL context
        connector = aiohttp.TCPConnector(ssl=ssl_context)

        # Patch the bot's HTTP session with the custom connector
        bot.http.connector = connector

        # Load cogs before starting the bot
        await load_cogs()

        # Start the bot
        await bot.start(discord_token)
    except discord.LoginFailure:
        log_queue.put("Failed to login. Check your Discord token.")
    except Exception as e:
        log_queue.put(f"Unexpected error: {str(e)}")

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
        """Safely add log messages to the ScrollView's MDList."""
        from kivymd.uix.list import OneLineListItem

        log_item = OneLineListItem(text=text)
        self.root.ids.log_list.add_widget(log_item)

        # Auto-scroll to the bottom
        scroll_view = self.root.ids.log_list.parent
        scroll_view.scroll_y = 0  # Scroll to bottom

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
