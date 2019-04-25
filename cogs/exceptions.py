from discord.ext import commands

class PollException(commands.errors.CommandError):
    pass


class ChannelException(commands.errors.CommandError):
    pass


class NotOldEnough(commands.errors.CommandError):
    pass


class BlackListed(commands.errors.CommandError):
    pass

class IDNotFound(commands.errors.CommandError):
    pass