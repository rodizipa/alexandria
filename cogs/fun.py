import random
import asyncio
from discord.ext import commands
from utils import formatter
from discord import Embed
import discord

quotes = [
    'Signs point to yes.',
    'Yes.',
    'Reply hazy, try again.',
    'My sources say no.',
    'You may rely on it.',
    'Concentrate and ask again.',
    'Outlook not so good.',
    'It is decidedly so.',
    'Better not tell you now.',
    'Very doubtful.',
    'Yes - definitely.',
    'It is certain.',
    'Cannot predict now.',
    'Most likely.',
    'Ask again later.',
    'My reply is no.',
    'Outlook good.',
    "Don't count on it."
]

slaps = [
    'slaps {} around a bit with a large trout',
    'gives {} a clout round the head with a fresh copy of WeeChat',
    'slaps {} with a large smelly trout',
    'breaks out the slapping rod and looks sternly at {}',
    "slaps {}'s bottom and grins cheekily",
    'slaps {} a few times',
    'slaps {} and starts getting carried away',
    'would slap {}, but (s)he is too lazy to do it.',
    'gives {} a hearty slap',
    'finds the closest large object and gives {} a slap with it',
    'likes slapping people and randomly picks {} to slap',
    'dusts off a kitchen towel and slaps it at {}',
    'breaks the 4th wall and slaps {} with the pieces of it.',
    'slaps {} with a b grade stop sign.',
    'slaps {} with a baguette that still freshly baked.'
    'got a whip from chest. Time to try it, {} will be the target.'
]


class FunCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name='8ball')
    async def eight_ball(self, ctx):
        """Ask the great 8ball for answer."""
        await ctx.send(random.choice(quotes))

    @commands.command(name='choose', aliases=['choice', 'pick'])
    async def choose(self, ctx, *, args):
        """Choose one or another args:<option> , <option2> [, <option3>...]"""
        split_message = args.split(',')
        await ctx.send(random.choice(split_message))

    @commands.command(name='slap')
    async def slap(self, ctx, mention: discord.Member):
        """Slap someone. args: <mention>"""
        em = Embed(description=ctx.author.display_name + " " + random.choice(slaps).format(mention.display_name))
        await ctx.send(embed=em)
        await ctx.message.delete()

    @commands.command(name="insult")
    async def insult(self, ctx):
        await formatter.random_insult(ctx)

    @commands.command(name='user', aliases=['userinfo', 'info', 'ui', 'uinfo'])
    @commands.guild_only()
    async def user_info(self, ctx, *args):
        """returns mentioned user info. Aliases: userinfo, info, ui, uinfo"""
        if args:
            user = ctx.message.mentions[0]
        else:
            user = ctx.author

        if user.avatar_url_as(static_format='png')[54:].startswith('a_'):
            avi = user.avatar_url.rsplit("?", 1)[0]
        else:
            avi = user.avatar_url_as(static_format='png')

        em = Embed(timestamp=ctx.message.created_at)
        em.add_field(name='Nick', value=user.display_name, inline=False)
        em.add_field(name='Account Created', value=user.created_at.__format__('%A, %d. %B %Y  %H:%M:%S'))
        em.add_field(name='Join Date', value=user.joined_at.__format__('%A, %d. %B %Y  %H:%M:%S'))
        em.set_thumbnail(url=avi)
        em.set_footer(text=f'Invoked by: {ctx.author.display_name}')
        await ctx.message.delete()
        await ctx.send(embed=em)

    @commands.command(name="poll", aliases=['p'])
    async def poll(self, ctx, *, msg):
        """Create poll using [,] as delimiter. [Question], [answer1],...,[answer9], time=[minutes]"""
        await asyncio.sleep(1)
        await ctx.message.delete()

        options = msg.split(',')

        time = [x for x in options if x.startswith("time=")]

        if time:
            time = time[0]
        if time:
            options.remove(time)

        if (len(options) < 3) or (len(options) > 11):
            return await ctx.send("Min 2 options, Max 9.")
        if time:
            time = int(time.strip("time="))
        else:
            time = 60

        emoji = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
        to_react = []
        em = discord.Embed(title=f"**{options[0]}**")
        em.set_footer(text=f"Created by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        confirm_msg = ""
        #  add options
        for index, option in enumerate(options[1:]):
            confirm_msg += f"{emoji[index]} - {option}\n"
            to_react.append(emoji[index])
        confirm_msg += f"\n\nYou have {time} seconds to vote!"
        em.description = confirm_msg
        poll_msg = await ctx.send(embed=em)

        for emote in to_react:
            await poll_msg.add_reaction(emote)

        await asyncio.sleep(time)

        async for message in ctx.message.channel.history():
            if message.id == poll_msg.id:
                poll_msg = message

        results = {}

        for reaction in poll_msg.reactions:
            if reaction.emoji in to_react:
                results[reaction.emoji] = reaction.count - 1

        em2 = discord.Embed(title=f"{em.title}")
        end_msg = "The poll ended. Here the results:\n\n"
        for result in results:
            end_msg += f"{result} {options[emoji.index(result) + 1]} - {results[result]} votes\n"
        top_result = max(results, key=lambda key: results[key])
        if len([x for x in results if results[x] == results[top_result]]) > 1:
            top_results = []
            for key, value in results.items():
                if value == results[top_result]:
                    top_results.append(options[emoji.index(key)+1])
            tied = ", ".join(top_results)
            if max(results.values()) == 0:
                end_msg += "\nBah, nobody voted"
            else:
                end_msg += f"\nVictory tied between {tied}"
        else:
            top_result = options[emoji.index(top_result) + 1]
            end_msg += f"\n{top_result} is the winner!"
        em2.description = end_msg
        await ctx.send(embed=em2)


def setup(bot):
    bot.add_cog(FunCog(bot))
