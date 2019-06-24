import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

# manage the lucilius channel of /gbfg/. it has been simplified considering the inactivity
class Lucilius(commands.Cog):
    """/gbfg/ Lucilius commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xff00d0
        self.roles = []

    def startTasks(self):
        self.bot.runTask('lucilius', self.setuptask)

    async def setuptask(self): # setup the roles used by the bot.events
        self.bot.setChannelID('lucilog', self.bot.lucilius['log'])
        self.roles = []
        guild = self.bot.get_guild(self.bot.ids['gbfg'])
        self.roles.append(guild.get_role(self.bot.lucilius["mainrole"]))
        for r in self.bot.lucilius["role"]:
            self.roles.append(guild.get_role(r))

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    def isLuciliusChannel(): # for decorators
        async def predicate(ctx):
            id = ctx.channel.id
            bot = ctx.bot
            return (id == bot.lucilius['main'] or id in bot.lucilius['channels'])
        return commands.check(predicate)

    async def memberUpdate(self, before, after): #called by on_member_update, track the lucilius roles change on the server members
        for i in range(0, len(self.roles)):
            bf = (self.roles[i] in before.roles)
            af = (self.roles[i] in after.roles)
            if af != bf: # very simple, just check for a difference in roles
                if i == 0:
                    if bf == True:
                        await self.bot.send('lucilog', embed=self.bot.buildEmbed(title="Left the channel", description="{0:%Y/%m/%d %H:%M} JST".format(self.bot.getJST()), footer=str(after) + " ▪ User ID: " + str(after.id), thumbnail=after.avatar_url))
                    else:
                        await self.bot.send('lucilog', embed=self.bot.buildEmbed(title="Joined the channel", description="{0:%Y/%m/%d %H:%M} JST".format(self.bot.getJST()), footer=str(after) + " ▪ User ID: " + str(after.id), thumbnail=after.avatar_url))
                else:
                    if bf == True:
                        await self.bot.send('lucilog', embed=self.bot.buildEmbed(title="Left the party " + self.bot.getEmoteStr(str(i)), description="{0:%Y/%m/%d %H:%M} JST".format(self.bot.getJST()), footer=str(after) + " ▪ User ID: " + str(after.id), thumbnail=after.avatar_url))
                    else:
                        await self.bot.send('lucilog', embed=self.bot.buildEmbed(title="Joined the party " + self.bot.getEmoteStr(str(i)), description="{0:%Y/%m/%d %H:%M} JST".format(self.bot.getJST()), footer=str(after) + " ▪ User ID: " + str(after.id), thumbnail=after.avatar_url))

    async def memberRemove(self, member): # similar thing but when someone leave
        if self.roles[0] in member.roles:
            await self.bot.send('lucilog', embed=self.bot.buildEmbed(title="Left the server", description="{0:%Y/%m/%d %H:%M} JST".format(self.bot.getJST()), footer=str(member) + " ▪ User ID: " + str(member.id), thumbnail=member.avatar_url, color=self.color))

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

    @commands.command(no_pm=True)
    @isOwner()
    async def purgeLucilius(self, ctx):
        """Remove inactive users from the /gbfg/ lucilius-hard channel (Owner only)"""
        luci_c = self.bot.get_channel(bot.lucilius['main'])
        gbfg_g = self.bot.get_guild(self.bot.ids['gbfg'])
        whitelist = {}
        await self.bot.react(ctx, 'time')
        async for message in luci_c.history(limit=2000): 
            if message.author.id in whitelist:
                continue
            else:
                whitelist[str(message.author)] = 0
        i = 0
        for member in gbfg_g.members:
            for r in member.roles:
                if r.name == self.roles[i].name:
                    if str(member) in whitelist:
                        pass
                    else:
                        await member.remove_roles(r)
                        i += 1
                    break
        await self.bot.unreact(ctx, 'time')
        await self.bot.send('lucilog', embed=self.bot.buildEmbed(title="*lucilius-hard* purge results", description=str(i) + " inactive user(s)", color=self.color))