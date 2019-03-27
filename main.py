from discord.ext import commands
import subprocess
import discord
import config
from traceback import format_exception, print_exc

from cogs.exceptions import PollException, ChannelException, NotOldEnough, BlackListed

"""A simple bot framework. Based on https://gist.github.com/noirscape/cc8e65c1c42f26af0a9b3780e161817d"""

bot = commands.Bot(command_prefix="$", description="Voting bot for Nintendo Homebrew icon contests")

modules = [
    "cogs.vote",
    "cogs.gallery",
]

for module in modules:
    try:
        bot.load_extension(module)
        print(f'Loaded {module}')
    except Exception as e:
        print_exc()
        print("Could not load module " + module)


@bot.event
async def on_ready():
    bot.guild = bot.get_guild(config.guild)
    bot.creator_griffing1 = await bot.fetch_user(177939404243992578)
    bot.creator_noirscape = await bot.fetch_user(126747960972279808)
    bot.creator_frozenchen = await bot.fetch_user(159824269411352576)
    bot.creator_architdate = await bot.fetch_user(135204578986557440)
    print(f"Initialized on {bot.guild.name}")


@bot.event
async def on_command_error(ctx, e):
    if isinstance(e, commands.errors.CommandNotFound):
        pass # Don't need you in console
    elif isinstance(e, PollException):
        await ctx.send("There's no poll ongoing!")
    elif isinstance(e, ChannelException):
        try:
            await ctx.message.delete()
        except commands.MissingPermissions:
            pass
        try:
            await ctx.author.send("All voting commands must be done in {}".format(
                ' or '.join(f"<#{c}>" for c in config.channel)))
        except discord.Forbidden:
            await ctx.send("All voting commands must be done in {}".format(
                ' or '.join(f"<#{c}>" for c in config.channel)))
    elif isinstance(e, commands.CheckFailure):
        await ctx.send("You don't have permission to use this command!")
    elif isinstance(e, NotOldEnough):
        try:
            await ctx.message.delete()
        except commands.MissingPermissions:
            pass
        try:
            await ctx.author.send(
                "You must have been a member of this server for longer than {} days".format(config.min_time_since_join))
        except discord.Forbidden:
            await ctx.send(
                "You must have been a member of this server for longer than {} days".format(config.min_time_since_join))
    elif isinstance(e, BlackListed):
        try:
            await ctx.message.delete()
        except commands.MissingPermissions:
            pass
        try:
            await ctx.author.send(
                "You are blacklisted from voting, if you think there is a mistake please contact staff in <#270890866820775946>")
        except discord.Forbidden:
            await ctx.send(
                "You are blacklisted from voting, if you think there is a mistake please contact staff in <#270890866820775946>")
    elif isinstance(e, commands.errors.MissingRequiredArgument):
        await ctx.send(f"You're missing required arguments.\n")
        await ctx.send_help(ctx.command)
    else:
        print_exc()


@bot.event
async def on_error(event, *args, **kwargs):
    if isinstance(args[0], commands.errors.CommandNotFound):
        return


@bot.command()
async def about(ctx):
    embed = discord.Embed(title="Written by {}, {}, {}, and {}".format(bot.creator_griffing1, bot.creator_noirscape, bot.creator_frozenchen, bot.creator_architdate))
    embed.description = "This is a bot written in Python 3.7 and discord.py 1.0.0 for use in votes on Nintendo Homebrew. Source can be found [here](https://github.com/FrozenChen/Mayushii)."
    embed.set_thumbnail(url="https://i.catgirlsin.space/52/62b643b128796ca5de11d1a4a9a8d3438caca9.png")
    await ctx.send(embed=embed)

@bot.command()
async def pull(ctx):
    await ctx.send("Pulling changes")
    subprocess.run(["git", "pull"])
    await bot.close()


bot.run(config.token)