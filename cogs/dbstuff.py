from discord.ext import commands
from discord import Embed
import asyncio
import pendulum
from utils import formatter


class DBStuff(commands.Cog):
    """Database related cmds"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="maint")
    async def maint(self, ctx, *args):
        """Countdown to maint. Args: <add> 'MM/DD HH/mm'"""

        # Add/Update maint
        if args:
            if args[0] == 'add':
                if ctx.author.id == 224522663626801152 or ctx.author.id == 114010253938524167:
                    query = "SELECT * FROM alarms WHERE $1 = alarm_name;"
                    row = await self.bot.db.fetchrow(query, 'maint')
                    connection = await self.bot.db.acquire()

                    # convert pen to datatime for saving in db

                    if len(args) == 3:
                        maint_time = pendulum.from_format(f'{args[1]} {args[2]}', 'MM/DD HH:mm', tz='Asia/Seoul')
                    else:
                        maint_time = pendulum.parse(args[1], tz='Asia/Seoul', strict=False)

                    maint_time = formatter.pendulum_to_datetime(maint_time)

                    if row:
                        async with connection.transaction():
                            update = "UPDATE alarms SET alarm_time = $1  WHERE alarm_name = $2;"
                            await self.bot.db.execute(update, maint_time, 'maint')
                        await self.bot.db.release(connection)
                        m = await ctx.send('Maint time updated.')
                        await asyncio.sleep(5)
                        await m.delete()
                    else:
                        async with connection.transaction():
                            insert = "INSERT INTO alarms (alarm_name, alarm_time) VALUES ($1, $2);"
                            await self.bot.db.execute(insert, 'maint', maint_time)
                        await self.bot.db.release(connection)
                        m = await ctx.send('Maint time created.')
                        await asyncio.sleep(5)
                        await m.delete()
                    await ctx.message.delete()
                else:
                    ctx.message.delete()
                    ctx.author.send("you have no permissions to do that.")

        # Normal Maint call
        else:
            query = "SELECT alarm_time FROM alarms WHERE alarm_name = $1;"
            row = await self.bot.db.fetchrow(query, 'maint')
            if row:
                maint_time = row['alarm_time']
                now = pendulum.now('Asia/Seoul')
                maint_time = pendulum.instance(maint_time, tz="Asia/Seoul")
                diff = maint_time.diff(now)

                if now > maint_time:
                    em = Embed(description=f":alarm_clock: Maint started {diff.as_interval()} ago. :alarm_clock:")
                else:
                    em = Embed(description=f':alarm_clock: Maint will start in {diff.as_interval()} from now. :alarm_clock:')

                m = await ctx.send(embed=em)
                await asyncio.sleep(20)
                await ctx.message.delete()
                await m.delete()

            else:
                m = await ctx.send("maint not yet created.")
                await asyncio.sleep(5)
                await ctx.message.delete()
                await m.delete()


def setup(bot):
    bot.add_cog(DBStuff(bot))
