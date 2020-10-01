import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import json
import re
import html

# Owner only command
class Owner(commands.Cog):
    """Owner only commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x9842f4

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    async def guildList(self):
        msg = ""
        for s in self.bot.guilds:
            msg += "**{}** `{} `owned by **{}** `{}`\n".format(s.name, s.id, s.owner.name, s.owner.id)
        for s in self.bot.guilddata['pending']:
            msg += "**{}** {} is **Pending**\n".format(s, self.bot.guilddata['pending'][s])
        if len(self.bot.guilddata['banned']) > 0:
            msg += "Banned Guilds are `" + "` `".join(str(x) for x in self.bot.guilddata['banned']) + "`\n"
        if len(self.bot.guilddata['owners']) > 0:
            msg += "Banned Owners are `" + "` `".join(str(x) for x in self.bot.guilddata['owners']) + "`\n"
        await self.bot.send('debug', embed=self.bot.buildEmbed(title=self.bot.user.name, description=msg, thumbnail=self.bot.user.avatar_url, color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def eval(self, ctx, *, expression : str):
        """Execute code at run time (Owner only)"""
        try:
            eval(expression)
            await ctx.send(embed=self.bot.buildEmbed(title="Eval", description="Ran `{}` with success".format(expression), color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Exception\n{}".format(e), footer=expression, color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def clear(self, ctx):
        """Clear the debug channel"""
        try:
            await self.bot.channels['debug'].purge()
        except Exception as e:
            await self.bot.sendError('clear', str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def checkrole(self, ctx):
        """List all the roles in use on a server (Owner only)"""
        g = ctx.author.guild
        for r in g.roles:
            count = 0
            for m in g.members:
                for mr in m.roles:
                    if r.id == mr.id: count += 1
            await ctx.send("Role `{}` has {} users".format(r.name, count))

    @commands.command(no_pm=True)
    @isOwner()
    async def leave(self, ctx, id: int):
        """Make the bot leave a server (Owner only)"""
        try:
            toleave = self.bot.get_guild(id)
            await toleave.leave()
            await self.bot.react(ctx.message, '✅') # white check mark
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('leave', str(e))

    @commands.command(no_pm=True, aliases=['banS', 'ban', 'bs'])
    @isOwner()
    async def ban_server(self, ctx, id: int):
        """Command to leave and ban a server (Owner only)"""
        id = str(id)
        try:
            if id not in self.bot.guilddata['banned']:
                self.bot.guilddata['banned'].append(id)
                self.bot.savePending = True
            try:
                toleave = self.bot.get_guild(id)
                await toleave.leave()
            except:
                pass
            await self.bot.react(ctx.message, '✅') # white check mark
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('ban_server', str(e))

    @commands.command(no_pm=True, aliases=['banO', 'bo'])
    @isOwner()
    async def ban_owner(self, ctx, id: int):
        """Command to ban a server owner and leave all its servers (Owner only)"""
        id = str(id)
        try:
            if id not in self.bot.guilddata['owners']:
                self.bot.guilddata['owners'].append(id)
                self.bot.savePending = True
            for g in self.bot.guilds:
                try:
                    if str(g.owner.id) == id:
                        await g.leave()
                except:
                    pass
            await self.bot.react(ctx.message, '✅') # white check mark
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('ban_owner', str(e))

    @commands.command(no_pm=True, aliases=['a'])
    @isOwner()
    async def accept(self, ctx, id: int):
        """Command to accept a pending server (Owner only)"""
        sid = str(id)
        try:
            if sid in self.bot.guilddata['pending']:
                self.bot.guilddata['pending'].pop(sid)
                self.bot.savePending = True
                guild = self.bot.get_guild(id)
                if guild:
                    await guild.owner.send(embed=self.bot.buildEmbed(title="I'm now available for use in {}".format(guild.name), description="Use `$help` for my list of commands, `$help Management` for mod only commands.\nUse `$setPrefix` to change the command prefix (default: `$`)\nIf you encounter an issue, use `$bug_report` and describe the problem.\nIf I'm down or slow, I might be rebooting, in maintenance or Discord itself might be acting up.", thumbnail=guild.icon_url))
                    await self.bot.react(ctx.message, '✅') # white check mark
                    await self.guildList()
        except Exception as e:
            await self.bot.sendError('accept', str(e))

    @commands.command(no_pm=True, aliases=['r'])
    @isOwner()
    async def refuse(self, ctx, id: int):
        """Command to refuse a pending server (Owner only)"""
        id = str(id)
        try:
            if id in self.bot.guilddata['pending']:
                self.bot.guilddata['pending'].pop(id)
                self.bot.savePending = True
                guild = self.bot.get_guild(id)
                if guild:
                    await guild.leave()
                await self.bot.react(ctx.message, '✅') # white check mark
                await self.guildList()
        except Exception as e:
            await self.bot.sendError('refuse', str(e))

    @commands.command(name='save', no_pm=True, aliases=['s'])
    @isOwner()
    async def _save(self, ctx):
        """Command to make a snapshot of the bot's settings (Owner only)"""
        await self.bot.autosave(True)
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(name='load', no_pm=True, aliases=['l'])
    @isOwner()
    async def _load(self, ctx, drive : str = ""):
        """Command to reload the bot settings (Owner only)"""
        self.bot.cancelTask('check_buff')
        if drive == 'drive': 
            if not self.bot.drive.load():
                await self.bot.send('debug', embed=self.bot.buildEmbed(title=ctx.guild.me.name, description="Failed to retrieve save.json on the Google Drive", color=self.color))
        if self.bot.load():
            self.bot.savePending = False
            self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
            await self.bot.send('debug', embed=self.bot.buildEmbed(title=ctx.guild.me.name, description="save.json reloaded", color=self.color))
        else:
            await self.bot.send('debug', embed=self.bot.buildEmbed(title=ctx.guild.me.name, description="save.json loading failed", color=self.color))
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, aliases=['guilds'])
    @isOwner()
    async def servers(self, ctx):
        """List all servers (Owner only)"""
        await self.guildList()
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, aliases=['checkbuff'])
    @isOwner()
    async def buffcheck(self, ctx): # debug stuff
        """List the GW buff list for (You) (Owner only)"""
        await self.bot.react(ctx.message, '✅') # white check mark
        msg = ""
        for b in self.bot.gw['buffs']:
            msg += '{0:%m/%d %H:%M}: '.format(b[0])
            if b[1]: msg += '[Normal Buffs] '
            if b[2]: msg += '[FO Buffs] '
            if b[3]: msg += '[Warning] '
            if b[4]: msg += '[Double duration] '
            msg += '\n'
        await self.bot.send('debug', embed=self.bot.buildEmbed(title="{} Guild War (You) Buff debug check".format(self.bot.getEmote('gw')), description=msg, color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def setMaintenance(self, ctx, day : int, month : int, hour : int, duration : int):
        """Set a maintenance date (Owner only)"""
        try:
            self.bot.maintenance['time'] = datetime.now().replace(month=month, day=day, hour=hour, minute=0, second=0, microsecond=0)
            self.bot.maintenance['duration'] = duration
            self.bot.maintenance['state'] = True
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        except Exception as e:
            await self.bot.sendError('setmaintenance', str(e))

    @commands.command(no_pm=True)
    @isOwner()
    async def delMaintenance(self, ctx):
        """Delete the maintenance date (Owner only)"""
        self.bot.maintenance = {"state" : False, "time" : None, "duration" : 0}
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, aliases=['ss'])
    @isOwner()
    async def setStream(self, ctx, *, txt : str):
        """Set the stream command text (Owner only)"""
        if txt == "": return
        self.bot.stream['content'] = txt.split('\n')
        self.bot.savePending = True
        await ctx.send(embed=self.bot.buildEmbed(title="Stream Settings", description="Stream text sets to\n`{}`".format(txt), color=self.color))

    @commands.command(no_pm=True, aliases=['sst'])
    @isOwner()
    async def setStreamTime(self, ctx, day : int, month : int, year : int, hour : int):
        """Set the stream time (Owner only)
        The text needs to contain {} for the cooldown to show up"""
        try:
            self.bot.stream['time'] = datetime.now().replace(year=year, month=month, day=day, hour=hour, minute=0, second=0, microsecond=0)
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        except Exception as e:
            await self.bot.sendError('setstreamtime', str(e))

    @commands.command(no_pm=True, aliases=['cs'])
    @isOwner()
    async def clearStream(self, ctx):
        """Clear the stream command text (Owner only)"""
        self.bot.stream['content'] = []
        self.bot.stream['time'] = None
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def setSchedule(self, ctx, *, txt : str):
        """Set the GBF schedule for the month (Owner only)
        Use ; to separate elements"""
        self.bot.schedule = txt.split(';')
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def getSchedule(self, ctx):
        """Retrieve the monthly schedule from @granble_en (Owner only / Tweepy only)
        The tweet must be recent"""
        tw = self.bot.getTwitterTimeline('granblue_en')
        if tw is not None:
            for t in tw:
                txt = html.unescape(t.full_text)
                if txt.find(" = ") != -1 and txt.find("chedule") != -1:
                    s = txt.find("https://t.co/")
                    if s != -1: txt = txt[:s]
                    lines = txt.split('\n')
                    msg = lines[0] + '\n`'
                    for i in range(1, len(lines)):
                        if lines[i] != "":
                            msg += lines[i].replace(" = ", ";") + ";"
                    msg = msg[:-1]
                    msg += "`"
                    await self.bot.send('debug', embed=self.bot.buildEmbed(title="Automatic schedule detection", description=msg, color=self.color))
                    await self.bot.react(ctx.message, '✅') # white check mark
                    return
        await self.bot.react(ctx.message, '❎') # white negative mark

    @commands.command(no_pm=True)
    @isOwner()
    async def cleanSchedule(self, ctx):
        """Remove expired entries from the schedule (Owner only)"""
        c = self.bot.getJST()
        new_schedule = []
        for i in range(0, len(self.bot.schedule), 2):
            try:
                date = self.bot.schedule[i].replace(" ", "").split("-")[-1].split("/")
                x = c.replace(month=int(date[0]), day=int(date[1])+1, microsecond=0)
                if c - x > timedelta(days=160):
                    x = x.replace(year=x.year+1)
                if c >= x:
                    continue
            except:
                pass
            new_schedule.append(self.bot.schedule[i])
            new_schedule.append(self.bot.schedule[i+1])

        self.bot.schedule = new_schedule
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def setStatus(self, ctx, *, terms : str):
        """Change the bot status (Owner only)"""
        await self.bot.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=terms))
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def banRollID(self, ctx, id: int):
        """ID based Ban for $rollranking (Owner only)"""
        id = str(id)
        if id not in self.bot.spark[1]:
            self.bot.spark[1].append(id)
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, aliases=['unbanspark'])
    @isOwner()
    async def unbanRoll(self, ctx, id : int):
        """Unban an user from all the roll ranking (Owner only)
        Ask me for an unban (to avoid abuses)"""
        id = str(id)
        if id in self.bot.spark[1]:
            i = 0
            while i < len(self.bot.spark[1]):
                if id == self.bot.spark[1][i]: self.bot.spark[1].pop(i)
                else: i += 1
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def cleanRoll(self, ctx):
        """Remove users with 0 rolls (Owner only)"""
        count = 0
        for k in list(self.bot.spark[0].keys()):
            sum = self.bot.spark[0][k][0] + self.bot.spark[0][k][1] + self.bot.spark[0][k][2]
            if sum == 0:
                self.bot.spark[0].pop(k)
                count += 1
        if count > 0:
            self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def resetGacha(self, ctx):
        """Reset the gacha settings"""
        self.bot.gbfdata['gachabanner'] = None
        self.bot.gbfdata['gachacontent'] = None
        self.bot.gbfdata['gachatime'] = None
        self.bot.gbfdata['gachatimesub'] = None
        self.bot.gbfdata['rateup'] = None
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def logout(self, ctx):
        """Make the bot quit (Owner only)"""
        await self.bot.autosave()
        self.bot.running = False
        await self.bot.logout()

    @commands.command(no_pm=True)
    @isOwner()
    async def config(self, ctx):
        """Post the current config file in the debug channel (Owner only)"""
        try:
            with open('config.json', 'rb') as infile:
                await self.bot.send('debug', 'config.json', file=discord.File(infile))
        except Exception as e:
            await self.bot.sendError('config', str(e))

    @commands.command(no_pm=True)
    @isOwner()
    async def cleanSave(self, ctx):
        """Do some clean up (Owner only)"""
        guild_ids = []
        for s in self.bot.guilds:
            guild_ids.append(str(s.id))
        for k in list(self.bot.permitted.keys()):
            if k not in guild_ids:
                self.bot.permitted.pop(k)
                self.bot.savePending = True
        for k in list(self.bot.news.keys()):
            if k not in guild_ids or len(self.bot.news[k]) == 0:
                self.bot.news.pop(k)
                self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def broadcast(self, ctx, *, terms):
        """Broadcast a message (Owner only)"""
        if len(terms) == 0:
            return
        embed=discord.Embed(title="{} Broadcast".format(ctx.guild.me.display_name), description=terms, thumbnail=ctx.guild.me.avatar_url, color=self.color)
        for g in self.bot.news:
            for id in self.bot.news[g]:
                try:
                    channel = self.bot.get_channel(id)
                    await channel.send(embed=embed)
                except Exception as e:
                    self.bot.sendError('broadcast', str(e))
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def newgwtask(self, ctx):
        """Start a new checkGWBuff() task (Owner only)"""
        self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def invite(self, ctx):
        """Post the invite link (Owner only)"""
        await self.bot.send('debug', embed=self.bot.buildEmbed(title="Invite Request", description="{} ▫️ {}".format(ctx.author.name, ctx.author.id), thumbnail=ctx.author.avatar_url, timestamp=datetime.utcnow(), color=self.color))
        await ctx.author.send(embed=self.bot.buildEmbed(title=ctx.guild.me.name, description="{}\nYou'll have to wait for my owner approval.\nMisuses will result in a ban.".format(self.bot.strings["invite()"]), thumbnail=ctx.guild.me.avatar_url, timestamp=datetime.utcnow(), color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def purgeUbhl(self, ctx):
        """Remove inactive users from the /gbfg/ ubaha-hl channel (Owner only)"""
        ubhl_c = self.bot.get_channel(self.bot.ids['gbfg_ubhl'])
        gbfg_g = self.bot.get_guild(self.bot.ids['gbfg'])
        whitelist = {}
        await self.bot.react(ctx.message, 'time')
        async for message in ubhl_c.history(limit=10000): 
            if message.author.id in whitelist:
                continue
            else:
                whitelist[str(message.author)] = 0
        i = 0
        for member in gbfg_g.members:
            for r in member.roles:
                if r.name == 'UBaha HL':
                    if str(member) in whitelist:
                        pass
                    else:
                        await member.remove_roles(r)
                        i += 1
                    break
        await self.bot.unreact(ctx.message, 'time')
        await ctx.send(embed=self.bot.buildEmbed(title="*ubaha-hl* purge results", description="{} inactive user(s)".format(i), color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def purgeLucilius(self, ctx):
        """Remove inactive users from the /gbfg/ lucilius-hard channel (Owner only)"""
        luci_c = self.bot.get_channel(bot.lucilius['main'])
        gbfg_g = self.bot.get_guild(self.bot.ids['gbfg'])
        whitelist = {}
        await self.bot.react(ctx.message, 'time')
        async for message in luci_c.history(limit=10000): 
            if message.author.id in whitelist:
                continue
            else:
                whitelist[str(message.author)] = 0
        i = 0
        for member in gbfg_g.members:
            for r in member.roles:
                if r.name == 'Lucilius HL':
                    if str(member) in whitelist:
                        pass
                    else:
                        await member.remove_roles(r)
                        i += 1
                    break
        await self.bot.unreact(ctx.message, 'time')
        await ctx.send(embed=self.bot.buildEmbed(title="*ubaha-hl* purge results", description="{} inactive user(s)".format(i), color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def gbfg_inactive(self, ctx):
        """Remove inactive users from the /gbfg/ server (Owner only)"""
        g = self.bot.get_guild(self.bot.ids['gbfg'])
        t = datetime.utcnow() - timedelta(days=30)
        whitelist = {}
        await self.bot.react(ctx.message, 'time')
        for c in g.channels:
            try:
                async for message in c.history(limit=50000): 
                    if message.created_at < t:
                        break
                    whitelist[message.author.id] = 0
            except:
                pass
        await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ purge starting", description="Kicking {} inactive user(s)".format(len(g.members) - len(whitelist)), color=self.color))
        i = 0
        for member in g.members:
            try:
                if member.id not in whitelist:
                    await member.kick()
                    i += 1
            except:
                pass
        await self.bot.unreact(ctx.message, 'time')
        await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ purge results", description="{} inactive user(s) successfully kicked".format(i), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def getfile(self, ctx, *, filename: str):
        """Retrieve a bot file (Owner only)"""
        try:
            with open(filename, 'rb') as infile:
                await self.bot.send('debug', file=discord.File(infile))
            await self.bot.react(ctx.message, '✅') # white check mark
        except Exception as e:
            await self.bot.sendError('getfile', str(e))

    @commands.command(no_pm=True)
    @isOwner()
    async def punish(self, ctx):
        """Punish the bot"""
        await ctx.send("Please, Master, make it hurt.")
