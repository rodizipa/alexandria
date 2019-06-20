from discord.ext import commands
import discord
import asyncio
from utils import formatter
import pendulum


def is_admin():
    async def predicate(ctx):
        if ctx.author.id == ctx.bot.owner_id or ctx.author.id == 224522663626801152:
            return True
        else:
            await ctx.author.send("You have no permissions.")
            await asyncio.sleep(1)
            await ctx.message.delete()
            return False

    return commands.check(predicate)


class AdminCog(commands.Cog):
    """Owner and Admin Stuff"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='role')
    @is_admin()
    async def role(self, ctx, action, user: discord.Member, result_role: discord.Role):
        """Assign/remove roles to user."""
        if action == 'add':
            await user.add_roles(result_role)
            await asyncio.sleep(1)
            await ctx.message.delete()

        elif action == 'remove':
            await user.remove_roles(result_role)
            await asyncio.sleep(1)
            await ctx.message.delete()

    @commands.command(name='nick')
    @commands.is_owner()
    async def change_nick(self, ctx, user: discord.Member, nick):
        """Change target nickname"""
        await user.edit(nick=nick)
        await ctx.message.delete()

    @is_admin()
    @commands.command(name='purge', aliases=['prune'])
    async def purge(self, ctx, *args):
        """Purge messages. if there is a number, the the last x messages will be deleted, if has user mention,
            the bot will delete that person messages."""

        if ctx.message.mentions:
            mention = ctx.message.mentions[0]
        else:
            mention = None

        number = int(args[0])

        await ctx.message.delete()

        if mention:
            await ctx.message.channel.purge(limit=number, check=lambda m: m.author.id == mention.id)
        else:
            await ctx.message.channel.purge(limit=number)

    @commands.command(name='say')
    @commands.is_owner()
    async def say(self, ctx, *, text: str):
        """Repeats what was typed."""
        await ctx.send(text)
        await ctx.message.delete()

    @commands.is_owner()
    @commands.command(name='reload')
    async def reload(self, ctx, *, cog: str):
        """Command to reload cog, admin only. Use path form"""

        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f"**ERROR**: {type(e).__name__} - {e}")
        else:
            m = await ctx.send("Cog reloaded.")
            await asyncio.sleep(5)
            await m.delete()
            await ctx.message.delete()

    @commands.is_owner()
    @commands.command(name="chslow")
    async def chslow(self, ctx, channel: discord.TextChannel, time: int):
        await channel.edit(reason="Sorrow wanted.", slowmode_delay=time)
        m = await ctx.send(f"Channel {channel.name} slow mode edited to {time} seconds")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await m.delete()

    # add role
    @commands.is_owner()
    @commands.command(name="addrole")
    async def addrole(self, ctx, rolename: str):
        await ctx.guild.create_role(name=rolename)

    # edit role color
    @commands.is_owner()
    @commands.command(name="rolecolor")
    async def rolecolor(self, ctx, role: discord.Role, r: int, g: int, b: int):
        await role.edit(colour=discord.Colour.from_rgb(r=r, g=g, b=b))

    @commands.is_owner()
    @commands.command(name='trashping')
    async def trashping(self, ctx, user: discord.Member, num: int):
        for i in range(num):
            await ctx.send(f"{user.mention}")
            await asyncio.sleep(0)

    @is_admin()
    @commands.command(name='selfdestruct', aliases=['sd'], pass_context=True)
    async def selfdestruct(self, ctx, amount):
        """Explodes the last message after a time"""

        async for message in ctx.message.channel.history():
            if message.id == ctx.message.id:
                continue
            if message.author == ctx.message.author:
                killmsg = message
                break
        if not killmsg:
            return await ctx.send("There is no message to explode.")
        await asyncio.sleep(.5)
        await ctx.message.delete()
        timer = int(amount)
        timer -= -1
        msg = await ctx.send(content=':bomb:' + "-" * int(timer) + ":fire:")
        await asyncio.sleep(1)
        while timer:
            timer -= 1
            await msg.edit(content=':bomb:' + "-" * int(timer) + ":fire:")
            await asyncio.sleep(1)
        await msg.edit(content=':boom:')
        await asyncio.sleep(1)
        await killmsg.delete()
        await msg.delete()

    @commands.is_owner()
    @commands.command(name="genuser")
    async def genuser(self, ctx):
        members = ctx.bot.server.members
        connection = await ctx.bot.db.acquire()
        await asyncio.sleep(1)
        await ctx.message.delete()

        for member in members:
            async with connection.transaction():
                await ctx.bot.db.execute("INSERT INTO users (user_id) VALUES($1);", member.id)
                for role in member.roles:
                    if not role.id == 538203428870946816:
                        insert = "INSERT INTO roles (user_id, role_id) VALUES($1, $2);"
                        await ctx.bot.db.execute(insert, member.id, role.id)
        await ctx.bot.db.release(connection)


def setup(bot):
    bot.add_cog(AdminCog(bot))
