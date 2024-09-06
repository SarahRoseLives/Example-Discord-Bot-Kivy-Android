import discord
from discord.ext import commands
import configparser
import os
import asyncio

# Get the current working directory
current_directory = os.path.dirname(os.path.abspath(__file__))


discord_secret = "YOUR_DISCORD_SECRET_TOKEN_HERE"

# Intents (required for some features)
intents = discord.Intents.default()
intents.message_content = True  # Ensure you have this enabled if you want to listen to message content

# Bot setup
bot = commands.Bot(command_prefix='!', intents=intents)

# Load cogs
async def load_cogs():
    cogs_directory = os.path.join(current_directory, 'cogs')
    for filename in os.listdir(cogs_directory):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# On ready event
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Run the bot
async def main():
    await load_cogs()  # Load cogs before starting the bot
    await bot.start(discord_secret)

# Start the bot
asyncio.run(main())
