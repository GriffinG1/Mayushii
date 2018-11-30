import discord
import json
from discord.ext import commands
import asyncio
import os

class Vote:
    pollcfg = {}
    vote_list = {}
    poll_ongoing = False

    def __init__(self, bot):
        self.bot = bot
        if os.path.isfile("poll.json"):
            with open("poll.json", "r") as pollfile:
                self.pollcfg = json.load(pollfile)
                if len(self.pollcfg):
                    self.poll_ongoing = True
                    vote_name = "{}_votes.json".format(self.pollcfg["name"])
                    if os.path.isfile(vote_name):
                        with open(vote_name, "r") as votefile:
                            self.vote_list = json.load(votefile)
        else:
            with open("poll.json", "w") as pollfile:
                json.dump(self.pollcfg, pollfile)
        self.queue = asyncio.Queue()

    async def is_poll_ongoing(ctx):
        if ctx.cog.poll_ongoing:
            print("h")
            return True
        else:
            print("f")
            raise PollException("This thing is a pain")

    async def process_vote(self):
        choice, ctx = await self.queue.get()
        if choice == "cancel":
            popped = self.vote_list.pop(ctx.author.id, None) # default param means nothing goes wrong if someone cancels again
            if popped is not None:
                await ctx.send("Your vote has been cancelled!")
        else:
            self.vote_list[ctx.author.id] = choice
            await ctx.send(f"Your vote for {choice} has been succesfully registered!")
        with open("{}.json".format(self.pollcfg["name"]), "w") as votefile:
            json.dump(self.vote_list, votefile)
        self.queue.task_done()

    @commands.guild_only()
    @commands.group()
    async def poll(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("I don't know what you want me to do. If you would like to create a poll, please do `$help poll create`. If you would like to close an ongoing poll, please do `$poll close`.")

    @poll.command(name='create', alias='start')
    # prob add evi final tally before finishing poll
    async def create_cmd(self, ctx, link="", name="", *, options=""):
        """To create a poll, you  must provide the link to the imgur gallery, the name for the current poll, and a list of available options split by vertical bars. Ex:\n$poll create https://imgur.com/testing testingpoll2018 A | B | C | D"""
        if self.poll_ongoing:
            return await ctx.send("There's already a poll running. You must stop that one first.")
        elif not link or not name or not options:
            return await ctx.send(
                f"You didn't provide an argument. You should fix that.")
        elif not link.startswith("https://"):
            return await ctx.send(f"Your inputted link, `{link}`, is not a valid link.")
        vote_options = []
        for option in options.split(" | "):
            vote_options.append(option)
        if len(vote_options) < 2:
            return await ctx.send("You can't have a poll with only one option.")
        self.pollcfg["name"] = name
        self.pollcfg["link"] = link
        self.pollcfg["options"] = vote_options
        with open("poll.json", "w") as pollfile:
            json.dump(self.pollcfg, pollfile)
        with open(f"{name}_votes.json", "w") as votefile:
            json.dump(self.vote_list, votefile)
        self.poll_ongoing = True
        await ctx.send("Poll successfully created!")

    @commands.check(is_poll_ongoing)
    @poll.command(name='close', alias='end')
    async def close_cmd(self,ctx):
        #maybe add it as a method named count votes
        votes = dict.fromkeys(self.pollcfg["options"], 0)
        for vote in self.vote_list.values():
            if vote in votes:
                votes[vote] += 1
        for v in votes.items():
            self.pollcfg[v[0]] = v[1]
        os.makedirs("Polls", exist_ok=True)
        with open("Polls/{}.json".format(self.pollcfg["name"]), "w") as pollbackup:
            json.dump(self.pollcfg, pollbackup)
        with open("Polls/{}_votes.json".format(self.pollcfg["name"]), "w") as votesbackup:
            json.dump(self.vote_list, votesbackup)
        self.pollcfg = {}
        self.vote_list = {}
        with open("poll.json", "w") as pollfile:
            json.dump(self.pollcfg, pollfile)
        self.poll_ongoing = False
        await ctx.send("Poll successfully closed!")

    @poll.command()
    @commands.check(is_poll_ongoing)
    async def info(self, ctx):
        embed = discord.Embed(title="Current poll")
        embed.add_field(name="Poll name", value=self.pollcfg["name"])
        embed.add_field(name="Link to gallery", value=self.pollcfg["link"])
        embed.add_field(name="Options", value=" | ".join(self.pollcfg["options"]))
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command()
    @commands.check(is_poll_ongoing)
    async def vote(self, ctx, choice):
        await self.queue.put((choice, ctx)) # tuple -> immutable plus easy get
        await self.process_vote()

    @commands.guild_only()
    @commands.command()
    @commands.check(is_poll_ongoing)
    async def tally(self, ctx):
        await self.queue.join()
        embed = discord.Embed(title="Current tally of votes")
        votes = dict.fromkeys(self.pollcfg["options"], 0)
        for vote in self.vote_list.values():
            if vote in votes:
                votes[vote] += 1
        for v in votes.items():
            embed.add_field(name=f"{v[0]}", value=f"{v[1]}")
        await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(Vote(bot))
    
class PollException(commands.errors.CommandError):
    pass