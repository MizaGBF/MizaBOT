import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

class Lucilius(commands.Cog):
    """/gbfg/ Lucilius commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xff00d0

    def isLuciliusChannel(): # for decorators
        async def predicate(ctx):
            id = ctx.channel.id
            bot = ctx.bot
            return (id == bot.lucilius['main'] or id in bot.lucilius['channels'])
        return commands.check(predicate)

    @commands.command(no_pm=True)
    @isLuciliusChannel()
    async def iam(self, ctx, *elems: str):
        """Add to yourself an element role (Lucilius Only)"""
        f = {}
        for e in elems:
            el = e.lower()
            if el in self.bot.lucilius['str']:
                role = ctx.message.author.guild.get_role(self.bot.lucilius["elem"][self.bot.lucilius['str'][el]])
                try:
                    await ctx.author.add_roles(role)
                    f[self.bot.lucilius["emote"][el]] = None
                except:
                    pass
        for fe in f:
            await self.bot.react(ctx, fe)

    @commands.command(no_pm=True, aliases=['iamn'])
    @isLuciliusChannel()
    async def iamnot(self, ctx, *elems: str):
        """Remove from yourself an element role (Lucilius Only)"""
        f = {}
        for e in elems:
            el = e.lower()
            if el in self.bot.lucilius['str']:
                role = ctx.message.author.guild.get_role(self.bot.lucilius["elem"][self.bot.lucilius['str'][el]])
                try:
                    await ctx.author.remove_roles(role)
                    f[self.bot.lucilius["emote"][el]] = None
                except:
                    pass
        for fe in f:
            await self.bot.react(ctx, fe)

    @commands.command(no_pm=True, aliases=['ljoin', 'joinparty'])
    @isLuciliusChannel()
    async def partyjoin(self, ctx, id : int):
        """Add yourself to a party role (Lucilius Only)
        Only up to one role at a given time (Previous roles will be removed)"""
        # joke
        if ctx.author.id == self.bot.ids['wawi']:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description=ctx.author.display_name + ' has been banned from making and joining parties', thumbnail=ctx.author.avatar_url, color=self.color))
            return

        id = id - 1
        if id < 0 or id >= 6:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="ID must be in the 1-6 range", color=self.color))
        else:
            for i in range(0, 6):
                if i != id:
                    try:
                        role = ctx.message.author.guild.get_role(self.bot.lucilius["role"][i])
                        await ctx.author.remove_roles(role)
                    except:
                        pass
            try:
                role = ctx.message.author.guild.get_role(self.bot.lucilius["role"][id])
                await ctx.author.add_roles(role)
            except:
                pass
            await self.bot.react(ctx, str(id+1))

    @commands.command(no_pm=True, aliases=['lleave', 'leaveparty'])
    @isLuciliusChannel()
    async def partyleave(self, ctx):
        """Remove the party role, if any (Lucilius Only)"""
        for i in range(0, 6):
            try:
                role = ctx.message.author.guild.get_role(self.bot.lucilius["role"][i])
                await ctx.author.remove_roles(role)
                await ctx.message.add_reaction('✅') # white check mark
            except:
                pass
