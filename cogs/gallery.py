import os

import discord
from discord.ext import commands
from sqlalchemy import Column, String, Integer, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from cogs import exceptions

Base = declarative_base()


class Artist(Base):
    __tablename__ = "artist"
    userid = Column(Integer, primary_key=True)
    likes = Column(Integer, default=0)
    gallery = relationship("Art", back_populates='user', cascade="all, delete, delete-orphan")

    def __repr__(self):
        return f"<Artist userid='{self.userid}', likes={self.likes}>"


class Art(Base):
    __tablename__ = "gallery"
    id = Column(Integer, primary_key=True)
    artist = Column(Integer, ForeignKey('artist.userid'))
    link = Column(String)
    user = relationship("Artist", back_populates="gallery")

    def __repr__(self):
        return f"<Art id={self.id}, artist={self.artist}, link='{self.link}'>"


class BlackList(Base):
    __tablename__ = "blacklist"
    userid = Column(Integer, primary_key=True)


class Gallery(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        engine = create_engine('sqlite:///gallery.db')
        session = sessionmaker(bind=engine)
        self.s = session()
        if not os.path.isfile("gallery.db"):
            Base.metadata.create_all(engine)
            self.s.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.attachments and message.attachments[0].height and "addgallery" in message.attachments[0].filename:
            try:
                self.add_art(message.author, message.attachments[0].url)
            except exceptions.BlackListed:
                await message.author.send("You are blacklisted from creating a gallery!")

    def add_art(self, author, url):
        if self.s.query(BlackList).filter(BlackList.userid == author.id).scalar():
            raise exceptions.BlackListed("You are blacklisted")
        if not self.s.query(Artist).filter(Artist.userid == author.id).all():
            self.s.add(Artist(userid=author.id))
        self.s.add(Art(artist=author.id, link=url))
        self.s.commit()

    @commands.command()
    async def printdb(self, ctx):
        print("Printing DB")
        for a in self.s.query(Artist).all():
            print(a)

        for a in self.s.query(Art).all():
            print(a)

    async def delete_art(self, id):
        self.s.query(Art).filter(Art.id == id).delete()
        self.s.commit()

    @commands.guild_only()
    @commands.command()
    async def addart(self, ctx):
        """Add image to user gallery. Requires a image to be uploaded along with the command"""
        if not ctx.message.attachments:
            await ctx.send("No image attached")
        print(ctx.message.attachments[0])
        self.add_art(ctx.author, ctx.message.attachments[0].url)
        await ctx.send("Art added succesfullly")

    @commands.command()
    async def delart(self, ctx, id: int):
        """Removes image from user gallery"""
        art = self.s.query(Art).get(id)
        if art is None:
            await ctx.send("Art ID not found")
            return
        elif not ctx.author.id == art.artist or not ctx.author.permissions_in(ctx.channel).manage_nicknames:
            await ctx.send("You cant delete other people art scum!")
            return
        await self.s.delete(art)
        await ctx.send("Art deleted succesfully!")

    @commands.command()
    async def gallery(self, ctx, member: discord.Member = None):
        """Show user gallery in DMs"""
        await ctx.message.delete()
        if not member:
            member = ctx.author
        artist = self.s.query(Artist).get(member.id)
        if artist is not None:
            for idx, art in enumerate(artist.gallery):
                embed = discord.Embed(color=discord.Color.dark_red())
                embed.set_author(name=f"{member.display_name}'s Gallery Image {idx + 1}", icon_url=member.avatar_url)
                embed.set_image(url=art.link)
                embed.set_footer(text=f"Image id: {art.id}")
                await ctx.author.send(embed=embed)
        else:
            await ctx.author.send("This user doesnt have a gallery")

    @commands.guild_only()
    @commands.command()
    async def delartist(self, ctx, member: discord.Member):
        """Deletes artist along with gallery"""
        artist = self.s.query(Artist).get(member.id)
        if artist is None:
            await ctx.send(f"{member} doesnt have a gallery")
            return
        self.s.delete(artist)
        self.s.commit()
        await ctx.send("Artist deleted")

    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    @commands.command()
    async def blackart(self, ctx, member: discord.Member):
        """Blacklist user"""
        if self.s.query(BlackList).get(member.id):
            await ctx.send(f"{member} is already in the blacklist")
            return
        self.s.add(BlackList(userid=member.id))
        self.s.commit()
        await ctx.send(f"Added {member} to the blacklist")


    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    @commands.command()
    async def whiteart(self, ctx, member: discord.Member):
        """Blacklist user"""
        user = self.s.query(BlackList).get(member.id)
        if user is None:
            await ctx.send(f"{member} is not in the blacklist")
        self.s.delete(user)
        await ctx.send(f"Removed {member} from the blacklist")

def setup(bot):
    bot.add_cog(Gallery(bot))
