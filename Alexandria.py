import discord
from discord.ext import commands
import asyncio
import asyncpg
from time import gmtime, strftime
from utils import formatter
import CONFIG
import pendulum


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=CONFIG.PREFIX, description="LO server bot.")
        self.db = kwargs.pop("db")
        self.rt = self.loop.create_task(self.roles_management())
        self.nick_pool = []

    async def roles_management(self):

        now = pendulum.now()

        # Process role time assignment
        role_time = await self.db.fetch("select * from assign_roles")

        if role_time:
            for item in role_time:
                server = self.get_guild(int(item['guild_id']))

                if server:
                    member = server.get_member(item['user_id'])
                else:
                    member = None

                check_time = pendulum.instance(item['time'])

                if now > check_time:

                    # remove role (assign plankton if dunce)
                    if member:
                        role = discord.utils.get(server.roles, id=item['role_id'])
                        await member.remove_roles(role)

                        if item['role_id'] == 311943704237572097:  # dunce
                            # Assign kr role
                            kr_role = discord.utils.get(server.roles, id=295083791884615680)
                            await member.add_roles(kr_role)

                        if item['role_id'] == 506160697323814927:  # NA
                            kr_role = discord.utils.get(server.roles, id=295083791884615680)
                            await member.add_roles(kr_role)

                    # remove row
                    connection = await self.db.acquire()
                    async with connection.transaction():
                        insert = "DELETE FROM assign_roles where user_id = $1;"
                        await self.db.execute(insert, item['user_id'])
                    await self.db.release(connection)

                else:
                    if member:
                        # Assign role if user doesn't have the role (and remove plankton if dunce)
                        role = discord.utils.get(member.roles, id=item['role_id'])

                        if role is None:
                            role = discord.utils.get(server.roles, id=item['role_id'])
                            await member.add_roles(role)

        await asyncio.sleep(60)

    async def on_ready(self):
        print(f'{self.user.name} online!')
        print('----')
        await self.change_presence(activity=discord.Game('?help or Die!'))

    async def load_modules(self):
        modules = ['cogs.admin', 'cogs.fun']

        for extension in modules:
            self.load_extension(extension)

    async def on_command_completion(self, ctx):
        print(f'[{strftime("[%d.%m.%Y %H:%M:%S]", gmtime())}] [Command] {ctx.message.content} by {ctx.author.name}')

    async def on_message(self, message):
        if message.content.startswith('?'):
            await self.process_commands(message)
        else:
            try:
                role = discord.utils.get(message.author.roles, id=311943704237572097)
                if role:
                    await formatter.kirinus_gacha(message)

            except Exception:
                pass


async def run():
    pg_credentials = {"user": CONFIG.USERNAME, "password": CONFIG.PASSWORD, "database": CONFIG.DATABASE,
                      "host": "127.0.0.1"}
    async with asyncpg.create_pool(**pg_credentials) as db:
        bot = Bot(db=db)
        try:
            await bot.load_modules()
            await bot.start(CONFIG.TOKEN)
        except KeyboardInterrupt:
            await bot.logout()

if __name__ == '__main__':
    print("Starting bot...\n")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except Exception as e:
        print(e.__name__)
