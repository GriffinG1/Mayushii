import discord
import json
from discord.ext import commands
import asyncio
import os
import shutil
from config import channel, min_time_since_join
from datetime import datetime

class Vote:
    pollcfg = {}
    vote_list = {}
    white_list = []
    black_list = []
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
        if not os.path.isdir("data/"):
            os.makedirs("Data", exist_ok=True)
        else:
            if os.path.isfile("Data/whitelist.json"):
                with open("Data/whitelist.json", "r") as whitefile:
                    self.white_list = json.load(whitefile)
            if os.path.isfile("Data/blacklist.json"):
                with open("Data/blacklist.json", "r") as blackfile:
                    self.black_list = json.load(blackfile)
        self.queue = asyncio.Queue()

    async def is_poll_ongoing(ctx):
        if ctx.cog.poll_ongoing:
            return True
        else:
            raise PollException("This thing is a pain")
            
    async def is_poll_channel(ctx):
        if ctx.message.channel.id in channel:
            return True
        else:
            raise ChannelException("I ~~love~~ hate error handling")
            
    async def is_old_enough(ctx):
        if (datetime.now() - ctx.author.joined_at).days < min_time_since_join and ctx.author.id not in ctx.cog.white_list:
            raise NotOldEnough("Little child")
        elif ctx.author.id in ctx.cog.black_list:
            raise BlackListed("You scum")
        else:
            return True

    async def process_vote(self):
        lower = [c.lower() for c in self.pollcfg["options"]]
        choice, ctx = await self.queue.get()
        if choice == "cancel" or choice == "clear":
            popped = self.vote_list.pop(str(ctx.author.id), None) # default param means nothing goes wrong if someone cancels again
            if popped is not None:
                await ctx.send("Your vote has been cancelled!")
        elif choice.lower() not in lower:
            await ctx.send("This is not a valid voting option.")
        else:
            choice = self.pollcfg["options"][lower.index(choice.lower())]
            self.vote_list[str(ctx.author.id)] = choice
            await ctx.send(f"Your vote for {choice} has been successfully registered!")
        with open("{}.json".format("{}_votes".format(self.pollcfg["name"])), "w") as votefile:
            json.dump(self.vote_list, votefile)
        self.queue.task_done()

    @commands.guild_only()
    @commands.has_permissions(change_nickname=True)
    @commands.group()
    async def poll(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("I don't know what you want me to do. If you would like to create a poll, please do `$help poll create`. If you would like to close an ongoing poll, please do `$poll close`.")

    @commands.has_permissions(manage_guild=True)
    @poll.command(alias='start')
    async def create(self, ctx, link, name, *, options):
        """To create a poll, you must provide the link to the imgur gallery, the name for the current poll, and a list of available options split by vertical bars. Ex:\n$poll create https://imgur.com/testing testingpoll2018 A | B | C | D"""
        if self.poll_ongoing:
            return await ctx.send("There's already a poll running. You must stop that one first.")
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

    @commands.has_permissions(manage_guild=True)
    @commands.check(is_poll_ongoing)
    @poll.command(alias='end')
    async def close(self, ctx):
        await ctx.invoke(self.bot.get_command("tally"))
        self.poll_ongoing = False # Should be _much_ earlier

        votes = dict.fromkeys(self.pollcfg["options"], 0)

        for vote in self.vote_list.values():
            if vote in votes:
                votes[vote] += 1

        for v in votes.items():
            self.pollcfg[v[0]] = v[1]

        os.makedirs("Polls", exist_ok=True)
        shutil.move("poll.json", "Polls/{}.json".format(self.pollcfg["name"]))
        shutil.move("{}_votes.json".format(self.pollcfg["name"]), "Polls/{}_votes.json".format(self.pollcfg["name"]))

        self.pollcfg = {}
        self.vote_list = {}

        os.remove("poll.json")

        await ctx.send("Poll successfully closed!")

    @commands.has_permissions(change_nickname=True)
    @poll.command()
    @commands.check(is_poll_ongoing)
    @commands.check(is_poll_channel)
    async def info(self, ctx):
        embed = discord.Embed(title="Current poll")
        embed.add_field(name="Poll name", value=self.pollcfg["name"])
        embed.add_field(name="Link to gallery", value=self.pollcfg["link"])
        embed.add_field(name="Options", value=" | ".join(self.pollcfg["options"]))
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command()
    @commands.check(is_poll_ongoing)
    @commands.check(is_poll_channel)
    @commands.check(is_old_enough)
    async def vote(self, ctx, choice):
        await self.queue.put((choice, ctx)) # tuple -> immutable plus easy get
        await self.process_vote()

    @commands.guild_only()
    @commands.has_permissions(change_nickname=True)
    @commands.command()
    @commands.check(is_poll_ongoing)
    @commands.check(is_poll_channel)
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

    @commands.has_permissions(manage_guild=True)
    @commands.group()
    async def whitelist(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("No option provided.")

    @whitelist.command(name='add')
    async def white_add(self, ctx, user: discord.User):
        """Adds user to whitelist"""
        if user.id in self.white_list:
            return await ctx.send(f"{user} is already in the whitelist.")
        if user.id in self.black_list:
            return await ctx.send(f"{user} is blacklisted, remove them before whitelisting them.")
        self.white_list.append(user.id)
        with open("Data/whitelist.json", "w") as whitefile:
            json.dump(self.white_list, whitefile)
        await ctx.send(f"Added {user} to whitelist.")

    @whitelist.command(name='remove')
    async def white_remove(self, ctx, user: discord.User):
        """Removes user to whitelist"""
        if user.id not in self.white_list:
            return await ctx.send(f"{user} is not in the whitelist.")
        self.white_list.remove(user.id)
        with open("Data/whitelist.json", "w") as whitefile:
            json.dump(self.white_list, whitefile)
        await ctx.send(f"Removed {user} from whitelist.")

    @whitelist.command(name='clear')
    async def white_clear(self, ctx):
        """Clears the whitelist"""
        self.white_list = []
        with open("Data/whitelist.json", "w") as whitefile:
            json.dump(self.white_list, whitefile)

    @commands.has_permissions(manage_guild=True)
    @commands.group()
    async def blacklist(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("No option provided.")

    @blacklist.command(name='add')
    async def black_add(self, ctx, user: discord.User):
        """Adds user to blacklist"""
        if user.id in self.black_list:
            return await ctx.send(f"{user} is already in the blacklist.")
        if user.id in self.white_list:
            return await ctx.send(f"{user} is whitelisted, remove them before whitelisting them.")
        self.black_list.append(user.id)
        with open("Data/blacklist.json", "w") as blackfile:
            json.dump(self.black_list, blackfile)
        await ctx.send(f"Added {user} to blacklist.")

    @blacklist.command(name='remove')
    async def black_remove(self, ctx, user: discord.User):
        """Removes user to blacklist"""
        if user.id not in self.black_list:
            return await ctx.send(f"{user} is not in the blacklist.")
        self.black_list.remove(user.id)
        with open("Data/blacklist.json", "w") as blackfile:
            json.dump(self.black_list, blackfile)
        await ctx.send(f"Removed {user} from blacklist.")

    @blacklist.command(name='clear')
    async def black_clear(self, ctx):
        """Clears the blacklist"""
        self.black_list = []
        with open("Data/blacklist.json", "w") as blackfile:
            json.dump(self.black_list, blackfile)


def setup(bot):
    bot.add_cog(Vote(bot))
    
class PollException(commands.errors.CommandError):
    pass
    
class ChannelException(commands.errors.CommandError):
    pass

class NotOldEnough(commands.errors.CommandError):
    pass

class BlackListed(commands.errors.CommandError):
    pass