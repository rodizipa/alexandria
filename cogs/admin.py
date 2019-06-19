from discord.ext import commands
import discord
import asyncio
from utils import formatter
import pendulum


def is_admin():
    async def predicate(ctx):
        if ctx.author.id == ctx.bot.owner_id or ctx.author.id == 224522663626801152 or ctx.author.id == 308430990307753985:
            return True
        else:
            await ctx.author.send("You have no permissions.")
            await asyncio.sleep(1)
            await ctx.message.delete()

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
    async def cog_reload(self, ctx, *, cog: str):
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

    @commands.command(name='assign')
    async def assign(self, ctx, member: discord.Member, role: discord.Role, timestr):
        if ctx.author.id in (224522663626801152, 114010253938524167):

            if member is None:
                ctx.send("Invalid Member.")
            elif role is None:
                ctx.send("Invalid role.")

            time_list = [int(x) for x in timestr.split(':')]

            time = pendulum.now()
            if time_list[0] != 0:
                time = time.add(hours=time_list[0])
            if time_list[1] != 0:
                time = time.add(minutes=time_list[1])

            if not time:
                ctx.send("Invalid time, use HH:MM format.")
                return True

            time = formatter.pendulum_to_datetime(time)
            connection = await self.bot.db.acquire()

            async with connection.transaction():
                insert = "INSERT INTO assign_roles (user_id, role_id, guild_id, time) VALUES ($1, $2, $3, $4);"
                await self.bot.db.execute(insert, member.id, role.id, ctx.message.guild.id, time)
            await self.bot.db.release(connection)

            await member.add_roles(role)
            # Remove plankton if role is dunce
            if role.id == 311943704237572097:
                kr_role = discord.utils.get(ctx.guild.roles, id=295083791884615680)
                gb_role = discord.utils.get(ctx.guild.roles, id=506160697323814927)
                jp_role = discord.utils.get(ctx.guild.roles, id=505746159365783563)
                await member.remove_roles(kr_role)
                await member.remove_roles(gb_role)
                await member.remove_roles(jp_role)

            if role.id == 515972528016195644: #banish
                for cache in member.roles:
                    if not cache.name.__contains__('everyone') and not cache.name.__contains__('Banished'):
                        await member.remove_roles(cache)

            await ctx.message.add_reaction('✅')
            await asyncio.sleep(5)
            await ctx.message.delete()
        else:
            await ctx.message.delete()
            await ctx.author.send("You have no right of using this cmd.")

    @commands.command(name="deassign")
    async def deassign(self, ctx, member: discord.Member):
        if ctx.author.id in (224522663626801152, 114010253938524167):
            if member is None:
                ctx.send("Invalid Member.")
                return True

            row = await self.bot.db.fetchrow("select * from assign_roles where user_id = $1", member.id)

            if row:
                role_id = int(row['role_id'])
                role = discord.utils.get(ctx.guild.roles, id=role_id)
                await member.remove_roles(role)

                connection = await self.bot.db.acquire()
                async with connection.transaction():
                    insert = "DELETE FROM assign_roles WHERE user_id = $1;"
                    await self.bot.db.execute(insert, member.id)
                await self.bot.db.release(connection)

                await ctx.message.add_reaction('✅')
                await asyncio.sleep(5)
                await ctx.message.delete()

    @commands.command(name="jailtime")
    async def jailtime(self, ctx):
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
        else:
            target = ctx.author

        row = await self.bot.db.fetchrow("select * from assign_roles where user_id = $1", target.id)

        if row:
            jail_time = pendulum.instance(row['time'])
            m = await ctx.send(embed=discord.Embed(description=f"Time left: {jail_time.diff().as_interval()}"))
        else:
            m = await ctx.send("User not found.")
        await asyncio.sleep(10)
        await ctx.message.delete()
        await m.delete()

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


def setup(bot):
    bot.add_cog(AdminCog(bot))
