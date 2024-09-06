import discord
from discord.ext import commands

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello')
    async def hello(self, ctx):
        """Says hello"""
        await ctx.send('Hello!')

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Replies with pong"""
        await ctx.send('Pong!')

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
