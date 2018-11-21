from discord.ext import commands
import config

'''A simple bot framework. Based on https://gist.github.com/noirscape/cc8e65c1c42f26af0a9b3780e161817d'''

bot = commands.Bot(command_prefix='$', description='Voting bot for Nintendo Homebrew icon contests') 

addons = [
    'addons.vote',
]

for module in addons:
    try:
        bot.load_extension(module)
    except Exception as e:
        print('Could not load module ' + module)
        print(e)

@bot.event
async def on_ready():
    bot.guild = bot.get_guild(config.guild)
    print('Initialized on ' + bot.guild.name)
    
@bot.command()
async def reload(ctx):
    for module in addons:
        try:
            bot.unload_extension(module)
            bot.load_extension(module)
        except Exception as e:
            await ctx.send('Could not reload module ' + module)
            print('Could not load module ' + module)
            print(e)

bot.run(config.token)