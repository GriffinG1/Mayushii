import discord
import json
from discord.ext import commands
import asyncio
import os

class Vote:
    vote_list = {}
    def __init__(self, bot):
        self.bot = bot
        if os.path.isfile("votes.json"):
            with open("votes.json", "r") as votefile:
                self.vote_list = json.load(votefile)
        self.queue = asyncio.Queue()

    async def process_vote(self):
        choice, ctx = await self.queue.get()
        self.vote_list[ctx.author.id] = choice
        with open("votes.json", "w") as votefile:
            json.dump(self.vote_list, votefile)
        await ctx.author.send(f"Your vote for {choice} has been succesfully registered!")

    @commands.command()
    async def vote(self, ctx, choice):
        await self.queue.put((choice, ctx)) # tuple -> immutable plus easy get
        await self.process_vote()

def setup(bot):
    bot.add_cog(Vote(bot))