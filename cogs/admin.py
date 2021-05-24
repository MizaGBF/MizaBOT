import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import random
import html

# ----------------------------------------------------------------------------------------------------------------
# Admin Cog
# ----------------------------------------------------------------------------------------------------------------
# Tools for the Bot Owner
# ----------------------------------------------------------------------------------------------------------------

class Admin(commands.Cog):
    """Owner only."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x7a1472

    def startTasks(self):
        self.bot.runTask('status', self.status)
        self.bot.runTask('clean', self.clean)

    async def status(self): # background task changing the bot status and calling autosave()
        while True:
            try:
                await self.bot.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=random.choice(self.bot.data.config['games'])))
                await asyncio.sleep(1200)
                # check if it's time for the bot maintenance for me (every 2 weeks or so)
                c = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                if self.bot.data.save['bot_maintenance'] and c > self.bot.data.save['bot_maintenance'] and c.day == 16:
                    await self.bot.send('debug', self.bot.get_user(self.bot.data.config['ids']['owner']).mention + " ▫️ Time for maintenance!")
                    with self.bot.data.lock:
                        self.bot.data.save['bot_maintenance'] = c
                        self.bot.data.pending = True
                # autosave
                if self.bot.data.pending and self.bot.running:
                    await self.bot.data.autosave()
            except asyncio.CancelledError:
                await self.bot.sendError('statustask', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('statustask', str(e))

    async def clean(self): # background task cleaning the save file from useless data
        try:
            await asyncio.sleep(1000) # after 1000 seconds
            if not self.bot.running: return
            count = await self.bot.do(self.bot.data.clean_spark) # clean up spark data
            if count > 0:
                await self.bot.send('debug', embed=self.bot.util.embed(title="cleansave()", description="Cleaned {} unused spark saves".format(count), timestamp=datetime.utcnow()))
            count = await self.bot.do(self.bot.data.clean_profile) # clean up profile data
            if count > 0:
                await self.bot.send('debug', embed=self.bot.util.embed(title="cleansave()", description="Cleaned {} unused profiles".format(count), timestamp=datetime.utcnow()))
            if await self.bot.do(self.bot.data.clean_schedule): # clean up schedule data
                await self.bot.send('debug', embed=self.bot.util.embed(title="cleansave()", description="The schedule has been cleaned up", timestamp=datetime.utcnow()))
        except asyncio.CancelledError:
            await self.bot.sendError('cleansave', 'cancelled')
            return
        except Exception as e:
            await self.bot.sendError('cleansave', str(e))

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    async def guildList(self): # list all guilds the bot is in and send it in the debug channel
        msg = ""
        for s in self.bot.guilds:
            msg += "**{}** `{} `owned by **{}** `{}`\n".format(s.name, s.id, s.owner.name, s.owner.id)
            if len(msg) > 1800:
                await self.bot.send('debug', embed=self.bot.util.embed(title=self.bot.user.name, description=msg, thumbnail=self.bot.user.avatar_url, color=self.color))
                msg = ""
        for s in self.bot.data.save['guilds']['pending']:
            msg += "**{}** {} is **Pending**\n".format(s, self.bot.data.save['guilds']['pending'][s])
            if len(msg) > 1800:
                await self.bot.send('debug', embed=self.bot.util.embed(title=self.bot.user.name, description=msg, thumbnail=self.bot.user.avatar_url, color=self.color))
                msg = ""
        if msg != "":
            await self.bot.send('debug', embed=self.bot.util.embed(title=self.bot.user.name, description=msg, thumbnail=self.bot.user.avatar_url, color=self.color))
            msg = ""
        if len(self.bot.data.save['guilds']['banned']) > 0:
            msg += "Banned Guilds are `" + "` `".join(str(x) for x in self.bot.data.save['guilds']['banned']) + "`\n"
        if len(self.bot.data.save['guilds']['owners']) > 0:
            msg += "Banned Owners are `" + "` `".join(str(x) for x in self.bot.data.save['guilds']['owners']) + "`\n"
        if msg != "":
            await self.bot.send('debug', embed=self.bot.util.embed(title=self.bot.user.name, description=msg, thumbnail=self.bot.user.avatar_url, color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def eval(self, ctx, *, expression : str):
        """Evaluate code at run time (Owner only)
        For Debug.
        Use this to print things for example."""
        try:
            eval(expression)
            await ctx.send(embed=self.bot.util.embed(title="Eval", description="Ran `{}` with success".format(expression), color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.util.embed(title="Eval Error", description="Exception\n{}".format(e), footer=expression, color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def exec(self, ctx, *, expression : str):
        """Execute code at run time (Owner only)
        For Debug.
        Use this to modify data for example."""
        try:
            exec(expression)
            await ctx.send(embed=self.bot.util.embed(title="Exec", description="Ran `{}` with success".format(expression), color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.util.embed(title="Exec Error", description="Exception\n{}".format(e), footer=expression, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def checkrole(self, ctx):
        """List all the roles in use on a server (Owner only)
        It will list how many users are in each role."""
        g = ctx.author.guild
        for r in g.roles:
            count = 0
            for m in g.members:
                for mr in m.roles:
                    if r.id == mr.id: count += 1
            await ctx.send("Role `{}` has {} users".format(r.name, count)) # NOTE: possibly use the discord thread later?

    @commands.command(no_pm=True)
    @isOwner()
    async def leave(self, ctx, id: int):
        """Make the bot leave a server (Owner only)"""
        try:
            toleave = self.bot.get_guild(id)
            await toleave.leave()
            await self.bot.util.react(ctx.message, '✅') # white check mark
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('leave', str(e))

    @commands.command(no_pm=True, aliases=['banS', 'ban', 'bs'])
    @isOwner()
    async def ban_server(self, ctx, id: int):
        """Command to leave and ban a server (Owner only)"""
        id = str(id)
        try:
            if id not in self.bot.data.save['guilds']['banned']:
                with self.bot.data.lock:
                    self.bot.data.save['guilds']['banned'].append(id)
                    self.bot.data.pending = True
            try:
                toleave = self.bot.get_guild(id)
                await toleave.leave()
            except:
                pass
            await self.bot.util.react(ctx.message, '✅') # white check mark
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('ban_server', str(e))

    @commands.command(no_pm=True, aliases=['banO', 'bo'])
    @isOwner()
    async def ban_owner(self, ctx, id: int):
        """Command to ban a server owner and leave all its servers (Owner only)"""
        id = str(id)
        try:
            if id not in self.bot.data.save['guilds']['owners']:
                with self.bot.data.lock:
                    self.bot.data.save['guilds']['owners'].append(id)
                    self.bot.data.pending = True
            for g in self.bot.guilds:
                try:
                    if str(g.owner.id) == id:
                        await g.leave()
                except:
                    pass
            await self.bot.util.react(ctx.message, '✅') # white check mark
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('ban_owner', str(e))

    @commands.command(no_pm=True, aliases=['a'])
    @isOwner()
    async def accept(self, ctx, id: int):
        """Command to accept a pending server (Owner only)"""
        sid = str(id)
        try:
            if sid in self.bot.data.save['guilds']['pending']:
                with self.bot.data.lock:
                    self.bot.data.save['guilds']['pending'].pop(sid)
                    self.bot.data.pending = True
                guild = self.bot.get_guild(id)
                if guild:
                    await guild.owner.send(embed=self.bot.util.embed(title="I'm now available for use in {}".format(guild.name), description="Use `$help` for my list of commands, `$help Management` for mod only commands.\nUse `$setPrefix` to change the command prefix (default: `$`)\nIf you encounter an issue, use `$bug_report` and describe the problem.\nIf I'm down or slow, I might be rebooting, in maintenance or Discord itself might be acting up.", thumbnail=guild.icon_url))
                    await self.bot.util.react(ctx.message, '✅') # white check mark
                    await self.guildList()
        except Exception as e:
            await self.bot.sendError('accept', str(e))

    @commands.command(no_pm=True, aliases=['r'])
    @isOwner()
    async def refuse(self, ctx, id: int):
        """Command to refuse a pending server (Owner only)"""
        id = str(id)
        try:
            if id in self.bot.data.save['guilds']['pending']:
                with self.bot.data.lock:
                    self.bot.data.save['guilds']['pending'].pop(id)
                    self.bot.data.pending = True
                guild = self.bot.get_guild(id)
                if guild:
                    await guild.leave()
                await self.bot.util.react(ctx.message, '✅') # white check mark
                await self.guildList()
        except Exception as e:
            await self.bot.sendError('refuse', str(e))

    @commands.command(name='save', no_pm=True, aliases=['s'])
    @isOwner()
    async def _save(self, ctx):
        """Command to make a snapshot of the bot's settings (Owner only)"""
        await self.bot.data.autosave(True)
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(name='load', no_pm=True, aliases=['l'])
    @isOwner()
    async def _load(self, ctx, drive : str = ""):
        """Command to reload the bot settings (Owner only)
        Add drive to load the file from the drive"""
        self.bot.cancelTask('check_buff')
        if drive == 'drive': 
            if not self.bot.drive.load():
                await self.bot.send('debug', embed=self.bot.util.embed(title=ctx.guild.me.name, description="Failed to retrieve save.json on the Google Drive", color=self.color))
                return
        if self.bot.data.loadData():
            self.bot.data.pending = False
            self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
            await self.bot.send('debug', embed=self.bot.util.embed(title=ctx.guild.me.name, description="save.json reloaded", color=self.color))
        else:
            await self.bot.send('debug', embed=self.bot.util.embed(title=ctx.guild.me.name, description="save.json loading failed", color=self.color))
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, aliases=['guilds'])
    @isOwner()
    async def servers(self, ctx):
        """List all servers (Owner only)"""
        await self.guildList()
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, aliases=['checkbuff'])
    @isOwner()
    async def buffcheck(self, ctx): # debug stuff
        """List the GW buff list for (You) (Owner only)"""
        await self.bot.util.react(ctx.message, '✅') # white check mark
        msg = ""
        for b in self.bot.gw['buffs']:
            msg += '{0:%m/%d %H:%M}: '.format(b[0])
            if b[1]: msg += '[Normal Buffs] '
            if b[2]: msg += '[FO Buffs] '
            if b[3]: msg += '[Warning] '
            if b[4]: msg += '[Double duration] '
            msg += '\n'
        await self.bot.send('debug', embed=self.bot.util.embed(title="{} Guild War (You) Buff debug check".format(self.bot.emote.get('gw')), description=msg, color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def setMaintenance(self, ctx, day : int, month : int, hour : int, duration : int):
        """Set a maintenance date (Owner only)"""
        try:
            with self.bot.data.lock:
                self.bot.data.save['maintenance']['time'] = datetime.now().replace(month=month, day=day, hour=hour, minute=0, second=0, microsecond=0)
                self.bot.data.save['maintenance']['duration'] = duration
                self.bot.data.save['maintenance']['state'] = True
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark
        except Exception as e:
            await self.bot.sendError('setmaintenance', str(e))

    @commands.command(no_pm=True)
    @isOwner()
    async def delMaintenance(self, ctx):
        """Delete the maintenance date (Owner only)"""
        with self.bot.data.lock:
            self.bot.data.save['maintenance'] = {"state" : False, "time" : None, "duration" : 0}
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, aliases=['ss'])
    @isOwner()
    async def setStream(self, ctx, *, txt : str):
        """Set the stream command text (Owner only)"""
        if txt == "": return
        with self.bot.data.lock:
            self.bot.data.save['stream']['content'] = txt.split('\n')
            self.bot.data.pending = True
        await ctx.send(embed=self.bot.util.embed(title="Stream Settings", description="Stream text sets to\n`{}`".format(txt), color=self.color))

    @commands.command(no_pm=True, aliases=['sst'])
    @isOwner()
    async def setStreamTime(self, ctx, day : int, month : int, year : int, hour : int):
        """Set the stream time (Owner only)
        The text needs to contain {} for the cooldown to show up"""
        try:
            with self.bot.data.lock:
                self.bot.data.save['stream']['time'] = datetime.now().replace(year=year, month=month, day=day, hour=hour, minute=0, second=0, microsecond=0)
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark
        except Exception as e:
            await self.bot.sendError('setstreamtime', str(e))

    @commands.command(no_pm=True, aliases=['cs'])
    @isOwner()
    async def clearStream(self, ctx):
        """Clear the stream command text (Owner only)"""
        with self.bot.data.lock:
            self.bot.data.save['stream']['content'] = []
            self.bot.data.save['stream']['time'] = None
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def clearTracker(self, ctx):
        """Clear the gw match tracker (Owner only)"""
        with self.bot.data.lock:
            self.bot.data.save['youtracker'] = None
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def setSchedule(self, ctx, *, txt : str):
        """Set the GBF schedule for the month (Owner only)
        Use ; to separate elements"""
        with self.bot.data.lock:
            self.bot.data.save['schedule'] = txt.split(';')
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def getSchedule(self, ctx):
        """Retrieve the monthly schedule from @granble_en (Owner only / Tweepy only)
        The tweet must be recent"""
        tw = self.bot.twitter.timeline('granblue_en')
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
                    await self.bot.send('debug', embed=self.bot.util.embed(title="Granblue Fantasy Schedule from @granblue_en", description=msg, color=self.color))
                    await self.bot.util.react(ctx.message, '✅') # white check mark
                    return
        await self.bot.util.react(ctx.message, '❎') # white negative mark

    @commands.command(no_pm=True)
    @isOwner()
    async def cleanSchedule(self, ctx):
        """Remove expired entries from the schedule (Owner only)"""
        c = self.bot.util.JST()
        new_schedule = []
        for i in range(0, len(self.bot.data.save['schedule']), 2):
            try:
                date = self.bot.data.save['schedule'][i].replace(" ", "").split("-")[-1].split("/")
                x = c.replace(month=int(date[0]), day=int(date[1])+1, microsecond=0)
                if c - x > timedelta(days=160):
                    x = x.replace(year=x.year+1)
                if c >= x:
                    continue
            except:
                pass
            new_schedule.append(self.bot.data.save['schedule'][i])
            new_schedule.append(self.bot.data.save['schedule'][i+1])

        with self.bot.data.lock:
            self.bot.data.save['schedule'] = new_schedule
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def setStatus(self, ctx, *, terms : str):
        """Change the bot status (Owner only)"""
        await self.bot.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=terms))
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def banRollID(self, ctx, id: int):
        """ID based Ban for $rollranking (Owner only)"""
        id = str(id)
        if id not in self.bot.data.save['spark'][1]:
            with self.bot.data.lock:
                self.bot.data.save['spark'][1].append(id)
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, aliases=['unbanspark'])
    @isOwner()
    async def unbanRoll(self, ctx, id : int):
        """Unban an user from all the roll ranking (Owner only)
        Ask me for an unban (to avoid abuses)"""
        id = str(id)
        if id in self.bot.data.save['spark'][1]:
            i = 0
            with self.bot.data.lock:
                while i < len(self.bot.data.save['spark'][1]):
                    if id == self.bot.data.save['spark'][1][i]: self.bot.data.save['spark'][1].pop(i)
                    else: i += 1
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def cleanRoll(self, ctx):
        """Remove users with 0 rolls (Owner only)"""
        count = 0
        with self.bot.data.lock:
            for k in list(self.bot.data.save['spark'][0].keys()):
                sum = self.bot.data.save['spark'][0][k][0] + self.bot.data.save['spark'][0][k][1] + self.bot.data.save['spark'][0][k][2]
                if sum == 0:
                    self.bot.data.save['spark'][0].pop(k)
                    count += 1
            if count > 0:
                self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, aliases=['clearGacha'])
    @isOwner()
    async def resetGacha(self, ctx):
        """Reset the gacha settings"""
        with self.bot.data.lock:
            self.bot.data.save['gbfdata']['gachabanner'] = None
            self.bot.data.save['gbfdata']['gachacontent'] = None
            self.bot.data.save['gbfdata']['gachatime'] = None
            self.bot.data.save['gbfdata']['gachatimesub'] = None
            self.bot.data.save['gbfdata']['rateup'] = None
            self.bot.data.pending = True
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    async def logout(self, ctx):
        """Make the bot quit (Owner only)"""
        await self.bot.data.autosave()
        self.bot.running = False
        await self.bot.logout()

    @commands.command(no_pm=True)
    @isOwner()
    async def reboot(self, ctx):
        """Make the bot reboot (Owner only)"""
        await self.bot.data.autosave()
        self.bot.retcode = 1 # heroku restart if the error code isn't 0
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
    async def broadcast(self, ctx, *, terms):
        """Broadcast a message (Owner only)"""
        if len(terms) == 0:
            return
        embed=discord.Embed(title="{} Broadcast".format(ctx.guild.me.display_name), description=terms, thumbnail=ctx.guild.me.avatar_url, color=self.color)
        for g in self.bot.data.save['news']:
            for id in self.bot.data.save['news'][g]:
                try:
                    channel = self.bot.get_channel(id)
                    await channel.send(embed=embed)
                except Exception as e:
                    self.bot.sendError('broadcast', str(e))
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True)
    @isOwner()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def invite(self, ctx):
        """Send the MizaBOT invite link via direct messages (Owner only)"""
        await self.bot.send('debug', embed=self.bot.util.embed(title="Invite Request", description="{} ▫️ {}".format(ctx.author.name, ctx.author.id), thumbnail=ctx.author.avatar_url, timestamp=datetime.utcnow(), color=self.color))
        await ctx.author.send(embed=self.bot.util.embed(title=ctx.guild.me.name, description="{}\nYou'll have to wait for my owner approval.\nMisuses will result in a ban.".format(self.bot.data.config['strings']["invite()"]), thumbnail=ctx.guild.me.avatar_url, timestamp=datetime.utcnow(), color=self.color))

    @commands.command(no_pm=True)
    @isOwner()
    async def gbfg_invite(self, ctx):
        """Generate an invite for the /gbfg/ server (Owner only)"""
        c = self.bot.get_channel(self.bot.data.config['ids']['gbfg_new'])
        link = await c.create_invite(max_age = 3600)
        await ctx.send(embed=self.bot.util.embed(title="/gbfg/ invite", description="`{}`".format(link), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def getfile(self, ctx, *, filename: str):
        """Retrieve a bot file remotely (Owner only)"""
        try:
            with open(filename, 'rb') as infile:
                await self.bot.send('debug', file=discord.File(infile))
            await self.bot.util.react(ctx.message, '✅') # white check mark
        except Exception as e:
            await self.bot.sendError('getfile', str(e))

    @commands.command(no_pm=True)
    @isOwner()
    async def punish(self, ctx):
        """Punish the bot"""
        await ctx.send("Please, Master, make it hurt.")