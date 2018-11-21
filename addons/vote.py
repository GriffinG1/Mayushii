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
        if choice == "cancel":
            popped = self.vote_list.pop(ctx.author.id, None) # default param means nothing goes wrong if someone cancels again
            if popped is not None:
                await ctx.author.send("Your vote has been cancelled!")
        else:
            self.vote_list[ctx.author.id] = choice
            await ctx.author.send(f"Your vote for {choice} has been succesfully registered!")
        with open("votes.json", "w") as votefile:
            json.dump(self.vote_list, votefile)
        try:
            await ctx.message.delete()
        except:
            pass # whatevs, user mustve voted through DMs

    @commands.command()
    async def vote(self, ctx, choice):
        await self.queue.put((choice, ctx)) # tuple -> immutable plus easy get
        await self.process_vote()

def setup(bot):
    bot.add_cog(Vote(bot))