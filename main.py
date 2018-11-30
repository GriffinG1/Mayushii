from discord.ext import commands
import config
from addons.vote import PollException, ChannelException

"""A simple bot framework. Based on https://gist.github.com/noirscape/cc8e65c1c42f26af0a9b3780e161817d"""

bot = commands.Bot(command_prefix="$", description="Voting bot for Nintendo Homebrew icon contests")

modules = [
    "addons.vote",
]

for module in modules:
    try:
        bot.load_extension(module)
    except Exception as e:
        print("Could not load module " + module)
        print(e)

@bot.event
async def on_ready():
    bot.guild = bot.get_guild(config.guild)
    print("Initialized on " + bot.guild.name)
    
@bot.event
async def on_command_error(ctx, e):
    if isinstance(e, commands.errors.CommandNotFound):
        pass # Don't need you in console
    elif isinstance(e, commands.errors.CheckFailure) and not isinstance(e, PollException) and not isinstance(e, ChannelException):
        await ctx.send("You don't have permission to use this command!")
    elif isinstance(e, PollException):
        await ctx.send("There's no poll ongoing!")
    elif isinstance(e, ChannelException):
        try:
            await ctx.message.delete()
        except commands.BotMissingPermissions:
            pass
        try:
            await ctx.author.send("All voting commands must be done in <#{}>".format(config.channel))
        except discord.Forbidden:
            await ctx.send("All voting commands must be done in <#{}>".format(config.channel))
    elif isinstance(e, commands.errors.MissingRequiredArgument):
        formatted_help = await commands.formatter.HelpFormatter().format_help_for(ctx, ctx.command)
        await ctx.send(f"You're missing required arguments.\n{formatted_help[0]}")

@bot.event
async def on_error(event, *args, **kwargs):
    if isinstance(args[0], commands.errors.CommandNotFound):
        return

    
@bot.command()
async def reload(ctx):
    for module in modules:
        try:
            bot.unload_extension(module)
            bot.load_extension(module)
        except Exception as e:
            await ctx.send("Could not reload module " + module)
            print("Could not load module " + module)
            print(e)
        await ctx.send("Reloading of modules finished!")

bot.run(config.token)