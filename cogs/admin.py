﻿import disnake
from disnake.ext import commands
import asyncio
from datetime import datetime, timedelta
import random
import html
import gc
import os

# ----------------------------------------------------------------------------------------------------------------
# Admin Cog
# ----------------------------------------------------------------------------------------------------------------
# Tools for the Bot Owner
# ----------------------------------------------------------------------------------------------------------------

class Admin(commands.Cog):
    """Owner only."""
    guild_ids = []
    def __init__(self, bot):
        self.bot = bot
        try: self.guild_ids.append(self.bot.data.config['ids']['debug_server'])
        except: pass
        self.color = 0x7a1472

    def startTasks(self):
        self.bot.runTask('status', self.status)
        self.bot.runTask('clean', self.clean)

    """status()
    Bot Task managing the autosave and update of the bot status
    """
    async def status(self): # background task changing the bot status and calling autosave()
        while True:
            try:
                await self.bot.change_presence(status=disnake.Status.online, activity=disnake.activity.Game(name=random.choice(self.bot.data.config['games'])))
                gc.collect()
                await asyncio.sleep(1200)
                # check if it's time for the bot maintenance for me (every 2 weeks or so)
                c = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                if self.bot.data.save['bot_maintenance'] and c > self.bot.data.save['bot_maintenance'] and c.day == 16:
                    await self.bot.send('debug', self.bot.owner.mention + " ▫️ Time for maintenance!")
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
                await self.bot.sendError('statustask', e)

    """status()
    Bot Task managing the autocleanup of the save data
    """
    async def clean(self): # background task cleaning the save file from useless data
        try:
            await asyncio.sleep(1000) # after 1000 seconds
            if not self.bot.running: return
            count = await self.bot.do(self.bot.data.clean_spark) # clean up spark data
            if count > 0:
                await self.bot.send('debug', embed=self.bot.util.embed(title="cleansave()", description="Cleaned {} unused spark saves".format(count), timestamp=self.bot.util.timestamp()))
            count = await self.bot.do(self.bot.data.clean_profile) # clean up profile data
            if count > 0:
                await self.bot.send('debug', embed=self.bot.util.embed(title="cleansave()", description="Cleaned {} unused profiles".format(count), timestamp=self.bot.util.timestamp()))
            if await self.bot.do(self.bot.data.clean_schedule): # clean up schedule data
                await self.bot.send('debug', embed=self.bot.util.embed(title="cleansave()", description="The schedule has been cleaned up", timestamp=self.bot.util.timestamp()))
        except asyncio.CancelledError:
            await self.bot.sendError('cleansave', 'cancelled')
            return
        except Exception as e:
            await self.bot.sendError('cleansave', e)

    """isOwner()
    Command decorator, to check if the command is used by the bot owner
    
    Returns
    --------
    command check
    """
    def isOwner():
        async def predicate(ctx):
            return ctx.self.bot.isOwner(ctx)
        return commands.check(predicate)

    """guildList()
    Output the server list of the bot in the debug channel
    """
    async def guildList(self): # list all guilds the bot is in and send it in the debug channel
        msg = ""
        for s in self.bot.guilds:
            msg += "**{}** `{}`owned by **{}** `{}`\n".format(s.name, s.id, s.owner.name, s.owner.id)
            if len(msg) > 1800:
                await self.bot.send('debug', embed=self.bot.util.embed(title=self.bot.user.name, description=msg, thumbnail=self.bot.user.display_avatar, color=self.color))
                msg = ""
        if msg != "":
            await self.bot.send('debug', embed=self.bot.util.embed(title=self.bot.user.name, description=msg, thumbnail=self.bot.user.display_avatar, color=self.color))
            msg = ""
        if len(self.bot.data.save['banned_guilds']) > 0:
            msg += "Banned Guilds are `" + "` `".join(str(x) for x in self.bot.data.save['banned_guilds']) + "`\n"
        if msg != "":
            await self.bot.send('debug', embed=self.bot.util.embed(title=self.bot.user.name, description=msg, thumbnail=self.bot.user.display_avatar, color=self.color))

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def eval(self, inter, expression : str = commands.Param(autocomplete=['print("hello world")'])):
        """Evaluate code at run time (Owner Only)"""
        try:
            eval(expression)
            await inter.response.send_message(embed=self.bot.util.embed(title="Eval", description="Ran `{}` with success".format(expression), color=self.color), ephemeral=True)
        except Exception as e:
            await inter.response.send_message(embed=self.bot.util.embed(title="Eval Error", description="Exception\n{}".format(e), footer=expression, color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def exec(self, inter, expression : str = commands.Param(autocomplete=['print("hello world")'])):
        """Execute code at run time (Owner Only)"""
        try:
            exec(expression)
            await inter.response.send_message(embed=self.bot.util.embed(title="Exec", description="Ran `{}` with success".format(expression), color=self.color), ephemeral=True)
        except Exception as e:
            await inter.response.send_message(embed=self.bot.util.embed(title="Exec Error", description="Exception\n{}".format(e), footer=expression, color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def leave(self, inter, id: int):
        """Make the bot leave a server (Owner Only)"""
        try:
            toleave = self.bot.get_guild(id)
            await toleave.leave()
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('leave', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def ban_server(self, inter, id: int):
        """Command to leave and ban a server (Owner Only)"""
        id = str(id)
        try:
            if id not in self.bot.data.save['banned_guilds']:
                with self.bot.data.lock:
                    self.bot.data.save['banned_guilds'].append(id)
                    self.bot.data.pending = True
            try:
                toleave = self.bot.get_guild(id)
                await toleave.leave()
            except:
                pass
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('ban_server', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def ban_owner(self, inter, id: int):
        """Command to ban a server owner and leave all its servers (Owner Only)"""
        id = str(id)
        try:
            self.bot.ban.set(id, self.bot.ban.OWNER)
            for g in self.bot.guilds:
                try:
                    if str(g.owner.id) == id:
                        await g.leave()
                except:
                    pass
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('ban_owner', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def setinvite(self, inter, state : int = commands.Param(description="Invite State (0 to close, anything else to open)", autocomplete=[0, 1]), limit : int = commands.Param(description="Maximum number of guilds", default=50, autocomplete=[50])):
        """Set the bot invitation settings (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['invite'] = {'state':(state != 0), 'limit':limit}
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="Invitation setting", description="Open: `{}`\nLimited to max `{}` servers".format(self.bot.data.save['invite']['state'], self.bot.data.save['invite']['limit']), timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def seeinvite(self, inter):
        """Show the bot invitation settings (Owner Only)"""
        await inter.response.send_message(embed=self.bot.util.embed(title="Invitation setting", description="Open: `{}`\nLimited to max `{}` servers".format(self.bot.data.save['invite']['state'], self.bot.data.save['invite']['limit']), timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def save(self, inter):
        """Command to make a snapshot of the bot's settings (Owner Only)"""
        await self.bot.data.autosave(True)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def load(self, inter, drive : str = commands.Param(description="Add `drive` to load the file from the drive", default="")):
        """Command to reload the bot saved data (Owner Only)"""
        self.bot.cancelTask('check_buff')
        if drive == 'drive': 
            if not self.bot.drive.load():
                await inter.response.send_message("Failed to retrieve save.json on the Google Drive", ephemeral=True)
                return
        if self.bot.data.loadData():
            self.bot.data.pending = False
            await self.bot.send('debug', embed=self.bot.util.embed(title=inter.me.name, description="save.json reloaded", color=self.color))
        else:
            await self.bot.send('debug', embed=self.bot.util.embed(title=inter.me.name, description="save.json loading failed", color=self.color))
        await inter.response.send_message(embed=self.bot.util.embed(title="The command finished running", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def guilds(self, inter):
        """List all servers (Owner Only)"""
        await self.guildList()
        await inter.response.send_message('\u200b', delete_after=0)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def buffcheck(self, inter): # debug stuff
        """List the GW buff list for (You) (Owner Only)"""
        try:
            msg = ""
            for b in self.bot.data.save['gw']['buffs']:
                msg += '{0:%m/%d %H:%M}: '.format(b[0])
                if b[1]: msg += '[Normal Buffs] '
                if b[2]: msg += '[FO Buffs] '
                if b[3]: msg += '[Warning] '
                if b[4]: msg += '[Double duration] '
                msg += '\n'
            await inter.response.send_message(embed=self.bot.util.embed(title="{} Guild War (You) Buff debug check".format(self.bot.emote.get('gw')), description=msg, color=self.color))
        except:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error, buffs aren't set.", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def setmaintenance(self, inter, day : int = commands.Param(ge=1, le=31), month : int = commands.Param(ge=1, le=12), hour : int = commands.Param(ge=0, le=23), duration : int = commands.Param(ge=0)):
        """Set a maintenance date (Owner Only)"""
        try:
            with self.bot.data.lock:
                self.bot.data.save['maintenance']['time'] = datetime.now().replace(month=month, day=day, hour=hour, minute=0, second=0, microsecond=0)
                self.bot.data.save['maintenance']['duration'] = duration
                self.bot.data.save['maintenance']['state'] = True
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        except Exception as e:
            await self.bot.sendError('setmaintenance', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def delmaintenance(self, inter):
        """Delete the maintenance date (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['maintenance'] = {"state" : False, "time" : None, "duration" : 0}
            self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def setstream(self, inter, txt : str = commands.Param()):
        """Set the stream command text (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['stream']['content'] = txt.split('\n')
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="Stream Settings", description="Stream text sets to\n`{}`".format(txt), color=self.color))

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def setstreamtime(self, inter, day : int = commands.Param(ge=1, le=31), month : int = commands.Param(ge=1, le=12), year : int = commands.Param(ge=2021), hour : int = commands.Param(ge=0, le=23)):
        """Set the stream time (Owner Only)
        The text needs to contain {} for the cooldown to show up"""
        try:
            with self.bot.data.lock:
                self.bot.data.save['stream']['time'] = datetime.now().replace(year=year, month=month, day=day, hour=hour, minute=0, second=0, microsecond=0)
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        except Exception as e:
            await self.bot.sendError('setstreamtime', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def clearstream(self, inter):
        """Clear the stream command text (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['stream']['content'] = []
            self.bot.data.save['stream']['time'] = None
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def cleartracker(self, inter):
        """Clear the gw match tracker (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['youtracker'] = None
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def setschedule(self, inter, txt : str = commands.Param(description="Format: `Date1;Event1;...;DateN;EventN`")):
        """Set the GBF schedule for the month (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['schedule'] = txt.split(';')
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def getschedule(self, inter):
        """Retrieve the monthly schedule from @granble_en (Owner Only / Tweepy Only)"""
        tw = self.bot.twitter.pinned('granblue_en')
        if tw is not None:
            txt = html.unescape(tw.text)
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
                await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
                return
        await inter.response.send_message("I couldn't retrieve the schedule from Twitter", ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def cleanschedule(self, inter):
        """Remove expired entries from the schedule (Owner Only)"""
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
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def setstatus(self, inter, *, terms : str):
        """Change the bot status (Owner Only)"""
        await self.bot.change_presence(status=disnake.Status.online, activity=disnake.activity.Game(name=terms))
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def bancheckid(self, inter, id : int):
        """ID Based Check if an user has a ban registered in the bot (Owner Only)"""
        msg = ""
        if self.bot.ban.check(id, self.bot.ban.OWNER): msg += "Banned from having the bot in its own servers\n"
        if self.bot.ban.check(id, self.bot.ban.SPARK): msg += "Banned from appearing in `rollRanking`\n"
        if self.bot.ban.check(id, self.bot.ban.PROFILE): msg += "Banned from using `setProfile`\n"
        if self.bot.ban.check(id, self.bot.ban.OWNER): msg += "Banned from using the bot\n"
        if msg == "": msg = "No Bans set for this user"
        await inter.response.send_message(embed=self.bot.util.embed(title="User {}".format(id), description=msg, color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def ban(self, inter, id: int):
        """Ban an user from using the bot (Owner Only)"""
        self.bot.ban.set(id, self.bot.ban.USE_BOT)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def unban(self, inter, id : int):
        """Unban an user from using the bot (Owner Only)"""
        self.bot.ban.unset(id, self.bot.ban.USE_BOT)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def banprofile(self, inter, id: int):
        """ID based Ban for $setProfile (Owner Only)"""
        self.bot.ban.set(id, self.bot.ban.PROFILE)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def unbanprofile(self, inter, id : int):
        """ID based Unban for $setProfile (Owner Only)"""
        self.bot.ban.unset(id, self.bot.ban.PROFILE)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def cleanroll(self, inter):
        """Remove users with 0 rolls (Owner Only)"""
        count = 0
        with self.bot.data.lock:
            for k in list(self.bot.data.save['spark'].keys()):
                sum = self.bot.data.save['spark'][k][0] + self.bot.data.save['spark'][k][1] + self.bot.data.save['spark'][k][2]
                if sum == 0:
                    self.bot.data.save['spark'].pop(k)
                    count += 1
            if count > 0:
                self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def resetgacha(self, inter):
        """Reset the gacha settings (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['gbfdata']['gachabanner'] = None
            self.bot.data.save['gbfdata']['gachacontent'] = None
            self.bot.data.save['gbfdata']['gachatime'] = None
            self.bot.data.save['gbfdata']['gachatimesub'] = None
            self.bot.data.save['gbfdata']['rateup'] = None
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def config(self, inter):
        """Post the current config file in the debug channel (Owner Only)"""
        try:
            with open('config.json', 'rb') as infile:
                df = disnake.File(infile)
                await self.bot.send('debug', 'config.json', file=df)
                df.close()
                await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        except Exception as e:
            await self.bot.sendError('config', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def gbfg_invite(self, inter):
        """Generate an invite for the /gbfg/ server (Owner Only)"""
        c = self.bot.get_channel(self.bot.data.config['ids']['gbfg_new'])
        link = await c.create_invite(max_age = 3600)
        await inter.response.send_message(embed=self.bot.util.embed(title="/gbfg/ invite", description="`{}`".format(link), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def getfile(self, inter, filename: str = commands.Param(description="Path to a local file")):
        """Retrieve a bot file remotely (Owner Only)"""
        try:
            with open(filename, 'rb') as infile:
                df = disnake.File(infile)
                await self.bot.send('debug', file=df)
                df.close()
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        except Exception as e:
            await self.bot.sendError('getfile', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def account(self, inter, id : int = -1):
        """List GBF accounts used by the bot (Owner Only)
        Specify one to test it"""
        if len(self.bot.data.save['gbfaccounts']) == 0:
            await inter.response.send_message(embed=self.bot.util.embed(title="GBF Account status", description="No accounts set", color=self.color), ephemeral=True)
            return

        if id == -1:
            msg = ""
            for i in range(0, len(self.bot.data.save['gbfaccounts'])):
                acc = self.bot.data.save['gbfaccounts'][i]
                if i == self.bot.data.save['gbfcurrent']: msg += "👉 "
                else: msg += "{} ".format(i)
                msg += "**{}** ".format(acc[0])
                match acc[3]:
                    case 0: msg += "❔"
                    case 1: msg += "✅"
                    case 2: msg += "❎"
                msg += "\n"
            await inter.response.send_message(embed=self.bot.util.embed(title="GBF Account status", description=msg, color=self.color), ephemeral=True)
        else:
            acc = self.bot.gbf.get(id)
            if acc is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="GBF Account status", description="No accounts set in slot {}".format(id), color=self.color), ephemeral=True)
                return
            r = await self.bot.do(self.bot.gbf.request, self.bot.data.config['gbfwatch']['test'], account=id, decompress=True, load_json=True, check=True, force_down=True)
            if r is None or r.get('user_id', None) != acc[0]:
                await inter.response.send_message('debug', embed=self.bot.util.embed(title="GBF Account status", description="Account #{} is down\nck: `{}`\nuid: `{}`\nua: `{}`\n".format(id, acc[0], acc[1], acc[2]) , color=self.color), ephemeral=True)
                with self.bot.data.lock:
                    self.bot.data.save['gbfaccounts'][id][3] = 2
                    self.bot.data.pending = True
            elif r == "Maintenance":
                await inter.response.send_message(embed=self.bot.util.embed(title="GBF Account status", description="Game is in maintenance", color=self.color), ephemeral=True)
            else:
                await inter.response.send_message(embed=self.bot.util.embed(title="GBF Account status", description="Account #{} is up\nck: `{}`\nuid: `{}`\nua: `{}`\n".format(id, acc[0], acc[1], acc[2]), color=self.color), ephemeral=True)
                with self.bot.data.lock:
                    self.bot.data.save['gbfaccounts'][id][3] = 1
                    self.bot.data.save['gbfaccounts'][id][5] = self.bot.util.JST()
                    self.bot.data.pending = True

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def switch(self, inter, id : int):
        """Select the current GBF account to use (Owner Only)"""
        if self.bot.gbf.get(id) is not None:
            with self.bot.data.lock:
                self.bot.data.save['gbfcurrent'] = id
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message("Invalid id", ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def aacc(self, inter, uid : int, ck : str = commands.Param(), ua : str = commands.Param()):
        """(Owner Only)"""
        if uid < 1:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(uid), color=self.color), ephemeral=True)
            return
        if ck == "":
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ck), color=self.color), ephemeral=True)
            return
        if ua == "":
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ua), color=self.color), ephemeral=True)
            return
        self.bot.gbf.add(uid, ck, str)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def dacc(self, inter, num : int):
        """(Owner Only)"""
        if self.bot.gbf.remove(num):
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
           await inter.response.send_message("Invalid id", ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def sauid(self, inter, num : int, uid : int = -1):
        """(Owner Only)"""
        if uid < 0:
            acc = self.bot.gbf.get(num)
            if acc is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color), ephemeral=True)
            else:
                await inter.response.send_message('debug', embed=self.bot.util.embed(title="Account #{} current UID".format(num), description="`{}`".format(acc[0]), color=self.color), ephemeral=True)
        elif not self.bot.gbf.update(num, uid=uid):
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(uid), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def sack(self, inter, num : int, *, ck : str = ""):
        """(Owner Only)"""
        if ck == "":
            acc = self.bot.gbf.get(num)
            if acc is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color), ephemeral=True)
            else:
                await inter.response.send_message('debug', embed=self.bot.util.embed(title="Account #{} current CK".format(num), description="`{}`".format(acc[1]), color=self.color), ephemeral=True)
        elif not self.bot.gbf.update(num, ck=ck):
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ck), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def saua(self, inter, num : int, *, ua : str = ""):
        """(Owner Only)"""
        if ua == "":
            acc = self.bot.gbf.get(num)
            if acc is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color), ephemeral=True)
            else:
                await inter.response.send_message('debug', embed=self.bot.util.embed(title="Account #{} current UA".format(num), description="`{}`".format(acc[2]), color=self.color), ephemeral=True)
        elif not self.bot.gbf.update(num, ua=ua):
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ua), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def clearprofile(self, inter, gbf_id : int = commands.Param(description="A valid GBF Profile ID", ge=0)):
        """Unlink a GBF id (Owner Only)"""
        user_id = await self.bot.do(self.searchProfile, gbf_id)
        if user_id is None:
            await inter.response.send_message(embed=self.bot.util.embed(title="Clear Profile Error", description="ID not found", color=self.color), ephemeral=True)
        else:
            try:
                with self.bot.data.lock:
                    del self.bot.data.save['gbfids'][user_id]
                    self.bot.data.pending = True
            except:
                pass
            await inter.response.send_message(embed=self.bot.util.embed(title="Clear Profile", description='User `{}` has been removed'.format(user_id), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def setdread(self, inter, id : int = commands.Param(description="Dread Barrage ID", ge=0, le=999), element : str = commands.Param(description="Dread Barrage Element Advantage", autocomplete=['fire', 'water', 'earth', 'wind', 'light', 'dark']), day : int = commands.Param(description="Dread Barrage Start Day", ge=1, le=31), month : int = commands.Param(description="Dread Barrage Start Month", ge=1, le=12), year : int = commands.Param(description="Dread Barrage Start Year", ge=2021)):
        """Set the Valiant date (Owner Only)"""
        try:
            # stop the task
            with self.bot.data.lock:
                self.bot.data.save['valiant']['state'] = False
                self.bot.data.save['valiant']['id'] = id
                self.bot.data.save['valiant']['element'] = element.lower()
                # build the calendar
                self.bot.data.save['valiant']['dates'] = {}
                self.bot.data.save['valiant']['dates']["Day 1"] = datetime.utcnow().replace(year=year, month=month, day=day, hour=19, minute=0, second=0, microsecond=0)
                self.bot.data.save['valiant']['dates']["Day 2"] = self.bot.data.save['valiant']['dates']["Day 1"] + timedelta(seconds=36000)
                self.bot.data.save['valiant']['dates']["Day 3"] = self.bot.data.save['valiant']['dates']["Day 2"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["New Foes"] = self.bot.data.save['valiant']['dates']["Day 3"] + timedelta(seconds=50400)
                self.bot.data.save['valiant']['dates']["Day 4"] = self.bot.data.save['valiant']['dates']["Day 3"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 5"] = self.bot.data.save['valiant']['dates']["Day 4"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 6"] = self.bot.data.save['valiant']['dates']["Day 5"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 7"] = self.bot.data.save['valiant']['dates']["Day 6"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 8"] = self.bot.data.save['valiant']['dates']["Day 7"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["End"] = self.bot.data.save['valiant']['dates']["Day 8"] + timedelta(seconds=50400)
                # set the valiant state to true
                self.bot.data.save['valiant']['state'] = True
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="{} Dread Barrage Mode".format(self.bot.emote.get('gw')), description="Set to : **{:%m/%d %H:%M}**".format(self.bot.data.save['valiant']['dates']["Day 1"]), color=self.color), ephemeral=True)
        except Exception as e:
            with self.bot.data.lock:
                self.bot.data.save['valiant']['dates'] = {}
                self.bot.data.save['valiant']['buffs'] = []
                self.bot.data.save['valiant']['state'] = False
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", footer=str(e), color=self.color), ephemeral=True)
            await self.bot.sendError('setdread', e)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def disabledread(self, inter):
        """Disable the Dread Barrage mode, but doesn't delete the settings (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['valiant']['state'] = False
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def enabledread(self, inter):
        """Enable the Dread Barrage mode (Owner Only)"""
        if self.bot.data.save['valiant']['state'] == True:
            await inter.response.send_message(embed=self.bot.util.embed(title="{} Dread Barrage Mode".format(self.bot.emote.get('gw')), description="Already enabled", color=self.color), ephemeral=True)
        elif len(self.bot.data.save['valiant']['dates']) == 8:
            with self.bot.data.lock:
                self.bot.data.save['valiant']['state'] = True
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No Dread Barrage available in my memory", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def newgwtask(self, inter):
        """Start a new checkGWBuff() task (Owner Only)"""
        try: self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
        except: pass
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def reloaddb(self, inter):
        """Download GW.sql (Owner Only)"""
        await inter.response.defer()
        await self.bot.do(self.bot.ranking.reloadGWDB)
        vers = await self.bot.do(self.bot.ranking.GWDBver)
        msg = ""
        for i in [0, 1]:
            msg += "**{}** :white_small_square: ".format('GW_old.sql' if (i == 0) else 'GW.sql')
            if vers[i] is None: msg += "Not loaded"
            else:
                msg += 'GW{} '.format(vers[i].get('gw', '??'))
                msg += '(version {})'.format(vers[i].get('ver', 'ERROR'))
            msg += "\n"
        await inter.edit_original_message(embed=self.bot.util.embed(title="Guild War Databases", description=msg, timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def resetleader(self, inter):
        """Reset the saved captain list (Owner Only)"""
        with self.bot.data.lock:
            if 'leader' in self.bot.data.save['gbfdata']:
                self.bot.data.save['gbfdata'].pop('leader')
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)


    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def disablegw(self, inter):
        """Disable the GW mode (Owner Only)
        It doesn't delete the GW settings"""
        self.bot.cancelTask('check_buff')
        with self.bot.data.lock:
            self.bot.data.save['gw']['state'] = False
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def enablegw(self, inter):
        """Enable the GW mode (Owner Only)"""
        if self.bot.data.save['gw']['state'] == True:
            await inter.response.send_message(embed=self.bot.util.embed(title="{} Guild War Mode".format(self.bot.emote.get('gw')), description="Already enabled", color=self.color), ephemeral=True)
        elif len(self.bot.data.save['gw']['dates']) == 8:
            with self.bot.data.lock:
                self.bot.data.save['gw']['state'] = True
                self.bot.data.pending = True
            try: self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
            except: pass
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No Guild War available in my memory", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def skipgwbuff(self, inter):
        """The bot will skip the next GW buff call (Owner Only)"""
        if not self.bot.data.save['gw']['skip']:
            with self.bot.data.lock:
                self.bot.data.save['gw']['skip'] = True
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message("The next set of buffs is already beind skipped", ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def cancelskipgwbuff(self, inter):
        """Cancel the GW buff call skipping (Owner Only)"""
        if self.bot.data.save['gw']['skip']:
            with self.bot.data.lock:
                self.bot.data.save['gw']['skip'] = False
                self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True, guild_ids=guild_ids)
    @isOwner()
    async def setgw(self, inter, id : int = commands.Param(description="Guild War ID", ge=0, le=999), element : str = commands.Param(description="Guild War Element Advantage", autocomplete=['fire', 'water', 'earth', 'wind', 'light', 'dark']), day : int = commands.Param(description="Guild War Start Day", ge=1, le=31), month : int = commands.Param(description="Guild War Start Month", ge=1, le=12), year : int = commands.Param(description="Guild War Start Year", ge=2021)):
        """Set the GW date (Owner Only)"""
        try:
            # stop the task
            self.bot.cancelTask('check_buff')
            with self.bot.data.lock:
                self.bot.data.save['gw']['state'] = False
                self.bot.data.save['gw']['id'] = id
                self.bot.data.save['gw']['ranking'] = None
                self.bot.data.save['gw']['element'] = advElement.lower()
                # build the calendar
                self.bot.data.save['gw']['dates'] = {}
                self.bot.data.save['gw']['dates']["Preliminaries"] = datetime.utcnow().replace(year=year, month=month, day=day, hour=19, minute=0, second=0, microsecond=0)
                self.bot.data.save['gw']['dates']["Interlude"] = self.bot.data.save['gw']['dates']["Preliminaries"] + timedelta(days=1, seconds=43200) # +36h
                self.bot.data.save['gw']['dates']["Day 1"] = self.bot.data.save['gw']['dates']["Interlude"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["Day 2"] = self.bot.data.save['gw']['dates']["Day 1"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["Day 3"] = self.bot.data.save['gw']['dates']["Day 2"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["Day 4"] = self.bot.data.save['gw']['dates']["Day 3"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["Day 5"] = self.bot.data.save['gw']['dates']["Day 4"] + timedelta(days=1) # +24h
                self.bot.data.save['gw']['dates']["End"] = self.bot.data.save['gw']['dates']["Day 5"] + timedelta(seconds=61200) # +17h
                # build the buff list for (you)
                self.bot.data.save['gw']['buffs'] = []
                # Prelims all
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=7200-300), True, True, True, True]) # warning, double
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=7200), True, True, False, True])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=43200-300), True, False, True, False]) # warning
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=43200), True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=43200+3600-300), False, True, True, False]) # warning
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(seconds=43200+3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(days=1, seconds=10800-300), True, True, True, False]) # warning
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Preliminaries"]+timedelta(days=1, seconds=10800), True, True, False, False])
                # Interlude
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Interlude"]+timedelta(seconds=54000), True, True, False, False])
                # Day 1
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 1"]+timedelta(seconds=54000), True, True, False, False])
                # Day 2
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 2"]+timedelta(seconds=54000), True, True, False, False])
                # Day 3
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 3"]+timedelta(seconds=54000), True, True, False, False])
                # Day 4
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]-timedelta(seconds=300), True, False, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"], True, False, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]+timedelta(seconds=3600-300), False, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]+timedelta(seconds=3600), False, True, False, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]+timedelta(seconds=54000-300), True, True, True, False])
                self.bot.data.save['gw']['buffs'].append([self.bot.data.save['gw']['dates']["Day 4"]+timedelta(seconds=54000), True, True, False, False])
                # set the gw state to true
                self.bot.data.save['gw']['state'] = True
                self.bot.data.pending = True
            try: self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
            except: pass
            await inter.response.send_message(embed=self.bot.util.embed(title="{} Guild War Mode".format(self.bot.emote.get('gw')), description="Set to : **{:%m/%d %H:%M}**".format(self.bot.data.save['gw']['dates']["Preliminaries"]), color=self.color), ephemeral=True)
        except Exception as e:
            self.bot.cancelTask('check_buff')
            with self.bot.data.lock:
                self.bot.data.save['gw']['dates'] = {}
                self.bot.data.save['gw']['buffs'] = []
                self.bot.data.save['gw']['state'] = False
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", footer=str(e), color=self.color), ephemeral=True)
            await self.bot.sendError('setgw', e)