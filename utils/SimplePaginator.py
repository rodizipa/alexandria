"""The MIT License (MIT)
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import discord
import asyncio


async def pager(entries, chunk: int):
    for x in range(0, len(entries), chunk):
        yield entries[x:x+chunk]


class SimplePaginator:

    __slots__ = ('entries', 'extras', 'dm', 'title', 'description', 'colour', 'footer', 'length', 'names', 'base',
                 'timeout', 'ordered', 'embed', 'prepend', 'append', 'fmt', 'controller', 'pages', 'current', 'previous',
                 'eof', 'controls', 'author', 'favorite')

    def __init__(self, **kwargs):
        self.entries = kwargs.get('entries', None)
        self.extras = kwargs.get('extras', None)
        self.dm = kwargs.get('dm', False)
        self.title = kwargs.get('title', None)
        self.description = kwargs.get('description', None)
        self.colour = kwargs.get('colour', 0x3498db)
        self.footer = kwargs.get('footer', None)
        self.length = kwargs.get('length', 10)
        self.timeout = kwargs.get('timeout', 90)
        self.ordered = kwargs.get('ordered', False)
        self.embed = kwargs.get('embed', True)
        self.prepend = kwargs.get('prepend', '')
        self.append = kwargs.get('append', '')
        self.fmt = kwargs.get('fmt', '')
        self.author = kwargs.get('author', None)
        self.favorite = kwargs.get('favorite', None)

        self.controller = None
        self.pages = []
        self.names = []
        self.base = None

        self.current = 0
        self.previous = 0
        self.eof = 0

        self.controls = {'⬅': -1, '➡': +1, '🛑': 'stop'}

    async def indexer(self, ctx, ctrl):
        if ctrl == 'stop':
            ctx.bot.loop.create_task(self.stop_controller(self.base))

        elif isinstance(ctrl, int):
            self.current += ctrl
            if self.current > self.eof or self.current < 0:
                self.current -= ctrl
        else:
            self.current = int(ctrl)

    async def reaction_controller(self, ctx):
        bot = ctx.bot
        author = ctx.author

        if self.embed is True:
            if self.dm:
                self.base = await ctx.author.send(embed=self.pages[0])
            else:
                self.base = await ctx.send(embed=self.pages[0])
        else:
            if self.dm:
                self.base = await ctx.author.send(f"```{self.pages[0]}```")
            else:
                self.base = await ctx.send(f"```{self.pages[0]}```")

        if len(self.pages) == 1:
            await self.base.add_reaction('🛑')
        else:
            for reaction in self.controls:
                try:
                    await self.base.add_reaction(reaction)
                except discord.HTTPException:
                    return

        def check(r, u):
            if str(r) not in self.controls.keys():
                return False
            elif u.id == bot.user.id or r.message.id != self.base.id:
                return False
            elif u.id != author.id:
                if self.author:
                    if u.id == self.author.id:
                        return True
                return False
            return True

        while True:
            try:
                react, user = await bot.wait_for('reaction_add', check=check, timeout=self.timeout)
            except asyncio.TimeoutError:
                return ctx.bot.loop.create_task(self.stop_controller(self.base))

            control = self.controls.get(str(react))

            try:
                await self.base.remove_reaction(react, user)
            except discord.HTTPException:
                pass

            self.previous = self.current
            await self.indexer(ctx, control)

            if self.previous == self.current:
                continue

            try:
                if self.embed is True:
                    await self.base.edit(embed=self.pages[self.current])
                else:
                    content = self.pages[self.current]
                    await self.base.edit(content=f"```{content}```")
            except KeyError:
                pass

    async def stop_controller(self, message):
        try:
            await message.delete()
        except discord.HTTPException:
            pass

        try:
            self.controller.cancel()
        except Exception:
            pass

    def formmater(self, chunk):
        return '\n'.join(f"{self.prepend}{self.fmt}{value}{self.fmt[::-1]}{self.append}" for value in chunk)

    async def paginate(self, ctx):
        if self.extras:
            self.pages = [p for p in self.extras if isinstance(p, discord.Embed)]

        if self.entries:
            chunks = [c async for c in pager(self.entries, self.length)]

            for index, chunk in enumerate(chunks):
                if self.embed is True:
                    if self.author:
                        page = discord.Embed(title=f'Page {index + 1}/{len(chunks)}', color=self.colour)
                        if len(self.entries) == 2:
                            page.set_author(name=f"{self.author.display_name}'s Lover", icon_url=self.author.avatar_url)
                        else:
                            page.set_author(name=f"{self.author.display_name}'s harem", icon_url=self.author.avatar_url)
                        if self.favorite:
                            page.set_thumbnail(url=self.favorite)
                    else:
                        page = discord.Embed(title=f'{self.title} - {index + 1}/{len(chunks)}', color=self.colour)

                    page.description = self.formmater(chunk)
                    if self.footer:
                        page.set_footer(text=self.footer)
                else:
                    page = f"Page {index + 1}/{len(chunks)}\n {self.formmater(chunk)}"
                self.pages.append(page)

            if not self.pages:
                raise Exception('Not enough data to create at least 1 page for pagination.')

            self.eof = float(len(self.pages) -1)
            self.controller = ctx.bot.loop.create_task(self.reaction_controller(ctx))
