import discord
import json
from discord.ext import commands
import asyncio
import os

class Vote:
    pollcfg = {}
    vote_list = {}
    ongoing = False
    cleanup_msgs_after = 30

    def __init__(self, bot):
        self.bot = bot
        if os.path.isfile("poll.json"):
            with open("poll.json", "r") as pollfile:
                self.pollcfg = json.load(pollfile)
                if len(self.pollcfg):
                    self.ongoing = True
                    vote_name = self.pollcfg["name"] + "_votes.json"
                    if os.path.isfile(vote_name):
                        with open(vote_name, "r") as votefile:
                            self.vote_list = json.load(votefile)
        else:
            with open("poll.json", "w") as pollfile:
                json.dump(self.pollcfg, pollfile)
        self.queue = asyncio.Queue()

    async def process_vote(self):
        choice, ctx = await self.queue.get()
        if choice == "cancel":
            popped = self.vote_list.pop(ctx.author.id, None) # default param means nothing goes wrong if someone cancels again
            if popped is not None:
                await ctx.send("Your vote has been cancelled!", delete_after=self.cleanup_msgs_after)
        else:
            self.vote_list[ctx.author.id] = choice
            await ctx.send(f"Your vote for {choice} has been succesfully registered!", delete_after=self.cleanup_msgs_after)
        with open("votes.json", "w") as votefile:
            json.dump(self.vote_list, votefile)
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.guild_only()
    @commands.command()
    async def poll(self, ctx, command, link="", name="",*,options=""):
        if command == "create":
            if not self.ongoing:
                vote_options = []
                self.pollcfg["name"] = name
                self.pollcfg["link"] = link
                for op in options.split(" | "):
                    vote_options.append(op)
                self.pollcfg["options"] = vote_options
                with open("poll.json", "w") as pollfile:
                    json.dump(self.pollcfg, pollfile)
                with open(name+"_votes.json","w") as votefile:
                    json.dump(self.vote_list, votefile)
                self.ongoing = True
                await ctx.send("Poll successfully created!", delete_after=self.cleanup_msgs_after)
            else:
                await ctx.send("There is poll ongoing already!", delete_after=self.cleanup_msgs_after)
        if command == "close":
            if self.ongoing:
                # prob add evi final tally before finishing poll
                if not os.path.isdir("Polls/"):
                    os.mkdir("Polls")
                with open("Polls/"+ self.pollcfg["name"]+".json", "w") as pollbackup:
                    json.dump(self.pollcfg, pollbackup)
                with open("Polls/"+ self.pollcfg["name"]+"_votes.json", "w") as votesbackup:
                    json.dump(self.vote_list, votesbackup)
                self.pollcfg = {}
                self.vote_list = {}
                with open("poll.json", "w") as pollfile:
                    json.dump(self.pollcfg, pollfile)
                self.ongoing = False
                await ctx.send("Poll successfully closed!", delete_after=self.cleanup_msgs_after)
            else:
                await ctx.send("There is no ongoing poll!", delete_after=self.cleanup_msgs_after)

    @commands.guild_only()
    @commands.command()
    async def vote(self, ctx, choice):
        await self.queue.put((choice, ctx)) # tuple -> immutable plus easy get
        await self.process_vote()

    @commands.guild_only()
    @commands.command()
    async def tally(self, ctx):
        votes = dict.fromkeys(self.pollcfg["options"],0)
        msg = ""
        for vote in self.vote_list.values():
            if vote in votes:
                votes[vote] += 1
        for k in votes.items():
            print(votes.items())
            msg += "{} = {}\n".format(k[0],k[1])
            print(msg)
        await ctx.send("Current Tally:\n"+msg, delete_after=self.cleanup_msgs_after)



def setup(bot):
    bot.add_cog(Vote(bot))