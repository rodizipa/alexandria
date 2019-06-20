import discord
from discord.ext import commands
import asyncio
import asyncpg
from time import gmtime, strftime
from utils import formatter
import CONFIG


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=CONFIG.PREFIX, description="LO server bot.")
        self.db = kwargs.pop("db")
        self.rt = self.loop.create_task(self.roles_management())
        self.server = None

    async def roles_management(self):  # background routine
        pass

    async def on_ready(self):
        print(f'{self.user.name} online!')
        print('----')
        self.server = self.get_guild(538203428870946816)
        await self.change_presence(activity=discord.Game('?help or Die!'))

    async def load_modules(self):
        modules = ['cogs.admin', 'cogs.fun']

        for extension in modules:
            self.load_extension(extension)

    async def on_command_completion(self, ctx):
        print(f'[{strftime("[%d.%m.%Y %H:%M:%S]", gmtime())}] [Command] {ctx.message.content} by {ctx.author.name}')

    async def on_member_join(self, member):  # Verify roles every time a user joins
        # Check if user exists in db, if yes, reassign registered roles
        query = "SELECT * FROM roles WHERE user_id = $1"
        roles = await self.db.fetch(query, member.id)

        if roles:
            for role in roles:
                await member.add_roles(discord.utils.get(self.server.roles, id=role['role_id']))

    async def on_member_update(self, before, after):
        # Track when user gets a role
        if not before.roles == after.roles:
            tmp = list(set(before.roles).symmetric_difference(after.roles))

            if len(after.roles) > len(before.roles):
                # If user exists
                user_chk = await self.db.fetch("select * FROM users WHERE user_id = $1", before.id)

                if user_chk:
                    connection = await self.db.acquire()
                    async with connection.transaction():
                        for role in tmp:
                            if not role.id == 538203428870946816:
                                insert = "INSERT INTO roles (user_id, role_id) VALUES($1, $2);"
                                await self.db.execute(insert, after.id, role.id)
                    await self.db.release(connection)
                else:
                    connection = await self.db.acquire()
                    async with connection.transaction():
                        await self.db.execute("INSERT INTO users (user_id) VALUES($1);", after.id)
                        for role in tmp:
                            if not role.id == 538203428870946816:
                                insert = "INSERT INTO roles (user_id, role_id) VALUES($1, $2);"
                                await self.db.execute(insert, after.id, role.id)
                    await self.db.release(connection)

            # Track when user loses a role
            else:
                connection = await self.db.acquire()
                async with connection.transaction():
                    for role in tmp:
                        delete = "DELETE FROM roles WHERE user_id = $1 AND role_id = $2;"
                        await self.db.execute(delete, after.id, role.id)
                await self.db.release(connection)

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
