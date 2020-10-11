import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import psutil

# Bot related commands
class Management(commands.Cog):
    """Bot related commands. Might require some mod powers in your server"""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xf49242

    def isAuthorized(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isAuthorized(ctx)
        return commands.check(predicate)

    def isMod(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isMod(ctx)
        return commands.check(predicate)

    def isAuthorizedSpecial(): # for decorators
        async def predicate(ctx):
            return (ctx.bot.isServer(ctx, 'debug_server') or (ctx.bot.isServer(ctx, 'you_server') and ctx.bot.isMod(ctx)))
        return commands.check(predicate)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def setPrefix(self, ctx, prefix_string : str):
        """Set the prefix used on your server (Mod Only)"""
        if len(prefix_string) == 0: return
        id = str(ctx.guild.id)
        if prefix_string == '$':
            if id in self.bot.prefixes:
                self.bot.prefixes.pop(id)
                self.bot.savePending = True
        else:
            self.bot.prefixes[id] = prefix_string
            self.bot.savePending = True
        await ctx.send(embed=self.bot.buildEmbed(title=ctx.guild.name, description="Server Prefix changed to `{}`".format(prefix_string), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['bug', 'report', 'bug_report'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def bugReport(self, ctx, *, terms : str):
        """Send a bug report (or your love confessions) to the author"""
        if len(terms) == 0:
            return
        await self.bot.send('debug', embed=self.bot.buildEmbed(title="Bug Report", description=terms, footer="{} ▫️ User ID: {}".format(ctx.author.name, ctx.author.id), thumbnail=ctx.author.avatar_url, color=self.color))
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorized()
    async def joined(self, ctx, member : discord.Member):
        """Says when a member joined."""
        await ctx.send(embed=self.bot.buildEmbed(title=ctx.guild.name, description="Joined at {0.joined_at}".format(member), thumbnail=member.avatar_url, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['source'])
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def github(self, ctx):
        """Post the bot.py file running right now"""
        await ctx.send(embed=self.bot.buildEmbed(title=self.bot.description.splitlines()[0], description="Code source at https://github.com/MizaGBF/MizaBOT", thumbnail=ctx.guild.me.avatar_url, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def delST(self, ctx):
        """Delete the ST setting of this server (Mod Only)"""
        id = str(ctx.guild.id)
        if id in self.bot.st:
            self.bot.st.pop(id)
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.buildEmbed(title=ctx.guild.name, description="No ST set on this server\nI can't delete.", thumbnail=ctx.guild.icon_url, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def setST(self, ctx, st1 : int, st2 : int):
        """Set the two ST of this server (Mod Only)"""
        if st1 < 0 or st1 >= 24 or st2 < 0 or st2 >= 24:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Values must be between 0 and 23 included", color=self.color))
            return
        self.bot.st[str(ctx.message.author.guild.id)] = [st1, st2]
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['banspark'])
    @isMod()
    async def banRoll(self, ctx, member: discord.Member):
        """Ban an user from the roll ranking (Mod Only)
        To avoid retards with fake numbers
        The ban is across all servers"""
        id = str(member.id)
        if id not in self.bot.spark[1]:
            self.bot.spark[1].append(id)
            self.bot.savePending = True
            await ctx.send(embed=self.bot.buildEmbed(title="{} ▫️ {}".format(member.display_name, id), description="Banned from all roll rankings by {}".format(ctx.author.display_name), thumbnail=member.avatar_url, color=self.color, footer=ctx.guild.name))
            await self.bot.send('debug', embed=self.bot.buildEmbed(title="{} ▫️ {}".format(member.display_name, id), description="Banned from all roll rankings by {}".format(ctx.author.display_name), thumbnail=member.avatar_url, color=self.color, footer=ctx.guild.name))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title=member.display_name, description="Already banned", thumbnail=member.avatar_url, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorizedSpecial()
    async def setGW(self, ctx, id : int, element : str, day : int, month : int, year : int):
        """Set the GW date ((You) Mod only)"""
        try:
            # stop the task
            self.bot.cancelTask('check_buff')
            self.bot.gw['state'] = False
            self.bot.gw['id'] = id
            self.bot.gw['ranking'] = ""
            self.bot.gw['element'] = element.lower()
            # build the calendar
            self.bot.gw['dates'] = {}
            self.bot.gw['dates']["Preliminaries"] = datetime.utcnow().replace(year=year, month=month, day=day, hour=19, minute=0, second=0, microsecond=0)
            self.bot.gw['dates']["Interlude"] = self.bot.gw['dates']["Preliminaries"] + timedelta(days=1, seconds=43200) # +36h
            self.bot.gw['dates']["Day 1"] = self.bot.gw['dates']["Interlude"] + timedelta(days=1) # +24h
            self.bot.gw['dates']["Day 2"] = self.bot.gw['dates']["Day 1"] + timedelta(days=1) # +24h
            self.bot.gw['dates']["Day 3"] = self.bot.gw['dates']["Day 2"] + timedelta(days=1) # +24h
            self.bot.gw['dates']["Day 4"] = self.bot.gw['dates']["Day 3"] + timedelta(days=1) # +24h
            self.bot.gw['dates']["Day 5"] = self.bot.gw['dates']["Day 4"] + timedelta(days=1) # +24h
            self.bot.gw['dates']["End"] = self.bot.gw['dates']["Day 5"] + timedelta(seconds=61200) # +17h
            # build the buff list for (you)
            self.bot.gw['buffs'] = []
            # Prelims all
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Preliminaries"]+timedelta(seconds=7200-300), True, True, True, True]) # warning, double
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Preliminaries"]+timedelta(seconds=7200), True, True, False, True])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Preliminaries"]+timedelta(seconds=43200-300), True, False, True, False]) # warning
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Preliminaries"]+timedelta(seconds=43200), True, False, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Preliminaries"]+timedelta(seconds=43200+3600-300), False, True, True, False]) # warning
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Preliminaries"]+timedelta(seconds=43200+3600), False, True, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Preliminaries"]+timedelta(days=1, seconds=10800-300), True, True, True, False]) # warning
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Preliminaries"]+timedelta(days=1, seconds=10800), True, True, False, False])
            # Interlude
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Interlude"]-timedelta(seconds=300), True, False, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Interlude"], True, False, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Interlude"]+timedelta(seconds=3600-300), False, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Interlude"]+timedelta(seconds=3600), False, True, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Interlude"]+timedelta(seconds=54000-300), True, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Interlude"]+timedelta(seconds=54000), True, True, False, False])
            # Day 1
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 1"]-timedelta(seconds=300), True, False, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 1"], True, False, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 1"]+timedelta(seconds=3600-300), False, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 1"]+timedelta(seconds=3600), False, True, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 1"]+timedelta(seconds=54000-300), True, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 1"]+timedelta(seconds=54000), True, True, False, False])
            # Day 2
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 2"]-timedelta(seconds=300), True, False, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 2"], True, False, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 2"]+timedelta(seconds=3600-300), False, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 2"]+timedelta(seconds=3600), False, True, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 2"]+timedelta(seconds=54000-300), True, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 2"]+timedelta(seconds=54000), True, True, False, False])
            # Day 3
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 3"]-timedelta(seconds=300), True, False, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 3"], True, False, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 3"]+timedelta(seconds=3600-300), False, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 3"]+timedelta(seconds=3600), False, True, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 3"]+timedelta(seconds=54000-300), True, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 3"]+timedelta(seconds=54000), True, True, False, False])
            # Day 4
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 4"]-timedelta(seconds=300), True, False, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 4"], True, False, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 4"]+timedelta(seconds=3600-300), False, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 4"]+timedelta(seconds=3600), False, True, False, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 4"]+timedelta(seconds=54000-300), True, True, True, False])
            self.bot.gw['buffs'].append([self.bot.gw['dates']["Day 4"]+timedelta(seconds=54000), True, True, False, False])
            # set the gw state to true
            self.bot.gw['state'] = True
            self.bot.savePending = True
            self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
            await ctx.send(embed=self.bot.buildEmbed(title="{} Guild War Mode".format(self.bot.getEmote('gw')), description="Set to : **{:%m/%d %H:%M}**".format(self.bot.gw['dates']["Preliminaries"]), color=self.color))
        except Exception as e:
            self.bot.cancelTask('check_buff')
            self.bot.gw['dates'] = {}
            self.bot.gw['buffs'] = []
            self.bot.gw['state'] = False
            self.bot.savePending = True
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="An unexpected error occured", footer=str(e), color=self.color))
            await self.bot.sendError('setgw', str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorizedSpecial()
    async def disableGW(self, ctx):
        """Disable the GW mode ((You) Mod only)
        It doesn't delete the GW settings"""
        self.bot.cancelTask('check_buff')
        self.bot.gw['state'] = False
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorizedSpecial()
    async def enableGW(self, ctx):
        """Enable the GW mode ((You) Mod only)"""
        if self.bot.gw['state'] == True:
            await ctx.send(embed=self.bot.buildEmbed(title="{} Guild War Mode".format(self.bot.getEmote('gw')), description="Already enabled", color=self.color))
        elif len(self.bot.gw['dates']) == 8:
            self.bot.gw['state'] = True
            self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="No Guild War available in my memory", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['skipGW'])
    @isAuthorizedSpecial()
    async def skipGWBuff(self, ctx):
        """The bot will skip the next GW buff call ((You) Mod only)"""
        if not self.bot.gw['skip']:
            self.bot.gw['skip'] = True
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I'm already skipping the next set of buffs", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorizedSpecial()
    async def cancelSkipGWBuff(self, ctx):
        """Cancel the GW buff call skipping ((You) Mod only)"""
        if self.bot.gw['skip']:
            self.bot.gw['skip'] = False
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="No buff skip is currently set", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['setDread', 'setDreadBarrage', 'setBarrage'])
    @isAuthorizedSpecial()
    async def setValiant(self, ctx, id : int, element : str, day : int, month : int, year : int):
        """Set the Valiant date ((You) Mod only)"""
        try:
            # stop the task
            self.bot.valiant['state'] = False
            self.bot.valiant['id'] = id
            self.bot.valiant['element'] = element.lower()
            self.bot.valiant['BETA'] = True
            # build the calendar
            # ### PLACEHOLDER ###
            self.bot.valiant['dates'] = {}
            self.bot.valiant['dates']["Day 1"] = datetime.utcnow().replace(year=year, month=month, day=day, hour=19, minute=0, second=0, microsecond=0)
            self.bot.valiant['dates']["Day 2"] = self.bot.valiant['dates']["Day 1"] + timedelta(days=1)
            self.bot.valiant['dates']["Day 3"] = self.bot.valiant['dates']["Day 2"] + timedelta(days=1)
            self.bot.valiant['dates']["Day 4"] = self.bot.valiant['dates']["Day 3"] + timedelta(days=1)
            self.bot.valiant['dates']["Day 5"] = self.bot.valiant['dates']["Day 4"] + timedelta(days=1)
            self.bot.valiant['dates']["Day 6"] = self.bot.valiant['dates']["Day 5"] + timedelta(days=1)
            self.bot.valiant['dates']["Day 7"] = self.bot.valiant['dates']["Day 6"] + timedelta(days=1)
            self.bot.valiant['dates']["Day 8"] = self.bot.valiant['dates']["Day 7"] + timedelta(days=1)
            self.bot.valiant['dates']["End"] = self.bot.valiant['dates']["Day 8"] + timedelta(days=1)
            # set the valiant state to true
            self.bot.valiant['state'] = True
            self.bot.savePending = True
            await ctx.send(embed=self.bot.buildEmbed(title="{} Dread Barrage Mode".format(self.bot.getEmote('gw')), description="Set to : **{:%m/%d %H:%M}**".format(self.bot.valiant['dates']["Day 1"]), color=self.color))
        except Exception as e:
            self.bot.valiant['dates'] = {}
            self.bot.valiant['buffs'] = []
            self.bot.valiant['state'] = False
            self.bot.savePending = True
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="An unexpected error occured", footer=str(e), color=self.color))
            await self.bot.sendError('setgw', str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['disableDread', 'disableBarrage', 'disableDreadBarrage'])
    @isAuthorizedSpecial()
    async def disableValiant(self, ctx):
        """Disable the Valiant mode ((You) Mod only)
        It doesn't delete the Valiant settings"""
        self.bot.valiant['state'] = False
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['enableDread', 'enableBarrage', 'enableDreadBarrage'])
    @isAuthorizedSpecial()
    async def enableValiant(self, ctx):
        """Enable the Valiant mode ((You) Mod only)"""
        if self.bot.valiant['state'] == True:
            await ctx.send(embed=self.bot.buildEmbed(title="{} Dread Barrage Mode".format(self.bot.getEmote('gw')), description="Already enabled", color=self.color))
        elif len(self.bot.valiant['dates']) == 8:
            self.bot.valiant['state'] = True
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="No Dread Barrage available in my memory", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def toggleFullBot(self, ctx):
        """Allow or not this channel to use all commands (Mod only)
        It disables game/obnoxious commands outside of the whitelisted channels"""
        gid = str(ctx.guild.id)
        cid = ctx.channel.id
        if gid not in self.bot.permitted:
            self.bot.permitted[gid] = []
        for i in range(0, len(self.bot.permitted[gid])):
            if self.bot.permitted[gid][i] == cid:
                self.bot.permitted[gid].pop(i)
                self.bot.savePending = True
                try:
                    await self.bot.callCommand(ctx, 'seeBotPermission')
                except Exception as e:
                    pass
                await self.bot.react(ctx.message, '➖')
                return
        self.bot.permitted[gid].append(cid)
        self.bot.savePending = True
        await self.bot.react(ctx.message, '➕')
        try:
            await self.bot.callCommand(ctx, 'seeBotPermission')
        except Exception as e:
            pass

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def allowBotEverywhere(self, ctx):
        """Allow full bot access in every channel (Mod only)"""
        gid = str(ctx.guild.id)
        if gid in self.bot.permitted:
            self.bot.permitted.pop(gid)
            self.bot.savePending = True
            await ctx.send(embed=self.bot.buildEmbed(title="Commands are now sauthorized everywhere", thumbnail=ctx.guild.icon_url, footer=ctx.guild.name + " ▫️ " + str(ctx.guild.id), color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Commands are already sauthorized everywhere", thumbnail=ctx.guild.icon_url, footer=ctx.guild.name + " ▫️ " + str(ctx.guild.id), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def seeBotPermission(self, ctx):
        """See all channels permitted to use all commands (Mod only)"""
        gid = str(ctx.guild.id)
        if gid in self.bot.permitted:
            msg = ""
            for c in ctx.guild.channels:
                if c.id in self.bot.permitted[gid]:
                    try:
                        msg += c.name + "\n"
                    except:
                        pass
            await ctx.send(embed=self.bot.buildEmbed(title="Channels permitted to use all commands", description=msg, thumbnail=ctx.guild.icon_url, footer=ctx.guild.name + " ▫️ " + str(ctx.guild.id), color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Commands are sauthorized everywhere", thumbnail=ctx.guild.icon_url, footer=ctx.guild.name + " ▫️ " + str(ctx.guild.id), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['mizabot'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def status(self, ctx):
        """Post the bot status"""
        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} ▫️ v{}".format(ctx.guild.me.display_name, self.bot.botversion), description="**Uptime**▫️{}\n**CPU**▫️{}%\n**Memory**▫️{}MB\n**Save Pending**▫️{}\n**Errors since boot**▫️{}\n**Tasks Count**▫️{}\n**Servers Count**▫️{}\n**Pending Servers**▫️{}\n**Cogs Loaded**▫️{}/{}\n**Twitter**▫️{}".format(self.bot.uptime(), self.bot.process.cpu_percent(), self.bot.process.memory_full_info().uss >> 20, self.bot.savePending, self.bot.errn, len(asyncio.all_tasks()), len(self.bot.guilds), len(self.bot.guilddata['pending']), len(self.bot.cogs), self.bot.cogn, (self.bot.twitter_api is not None)), thumbnail=ctx.guild.me.avatar_url, color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 40)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def changelog(self, ctx):
        """Post the bot changelog"""
        msg = ""
        for c in self.bot.botchangelog:
            msg += "▫️ {}\n".format(c)
        if msg != "":
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} ▫️ v{}".format(ctx.guild.me.display_name, self.bot.botversion), description="**Changelog**\n" + msg, thumbnail=ctx.guild.me.avatar_url, color=self.color))
            await self.bot.cleanMessage(ctx, final_msg, 40)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def asar(self, ctx, *, role_name : str = ""):
        """Add a role to the list of self-assignable roles (Mod Only)"""
        if role_name == "":
            await self.bot.react(ctx.message, '❎') # negative check mark
            return
        role = None
        for r in ctx.guild.roles:
            if role_name.lower() == r.name.lower():
                role = r
                break
        if role is None:
            await self.bot.react(ctx.message, '❎') # negative check mark
            return
        id = str(ctx.guild.id)
        if id not in self.bot.assignablerole:
            self.bot.assignablerole[id] = {}
        if role.name.lower() in self.bot.assignablerole[id]:
            await self.bot.react(ctx.message, '❎') # negative check mark
            return
        self.bot.assignablerole[id][role.name.lower()] = role.id
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isMod()
    async def rsar(self, ctx, *, role_name : str = ""):
        """Remove a role from the list of self-assignable roles (Mod Only)"""
        if role_name == "":
            await self.bot.react(ctx.message, '❎') # negative check mark
            return
        role = None
        for r in ctx.guild.roles:
            if role_name.lower() == r.name.lower():
                role = r
                break
        if role is None:
            await self.bot.react(ctx.message, '❎') # negative check mark
            return
        id = str(ctx.guild.id)
        if id not in self.bot.assignablerole:
            self.bot.assignablerole[id] = {}
        if role.name.lower() not in self.bot.assignablerole[id]:
            await self.bot.react(ctx.message, '❎') # negative check mark
            return
        self.bot.assignablerole[id].pop(role.name.lower())
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark