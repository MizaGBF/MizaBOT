import disnake
from disnake.ext import commands
import asyncio
from cogs import DEBUG_SERVER_ID
from datetime import datetime, timedelta
import random
import gc
import os

# ----------------------------------------------------------------------------------------------------------------
# Admin Cog
# ----------------------------------------------------------------------------------------------------------------
# Tools for the Bot Owner
# ----------------------------------------------------------------------------------------------------------------

class Admin(commands.Cog):
    """Owner only."""
    if DEBUG_SERVER_ID is None: guild_ids = []
    else: guild_ids = [DEBUG_SERVER_ID]
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x7a1472

    def startTasks(self):
        self.bot.runTask('status', self.status)
        self.bot.runTask('clean', self.clean)

    """status()
    Bot Task managing the autosave and update of the bot status
    """
    async def status(self): # background task changing the bot status and calling autosave()
        await self.bot.change_presence(status=disnake.Status.online, activity=disnake.activity.Game(name='I rebooted, /changelog for news'))
        while True:
            try:
                await asyncio.sleep(3600)
                await self.bot.change_presence(status=disnake.Status.online, activity=disnake.activity.Game(name=random.choice(self.bot.data.config['games'])))
                gc.collect()
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

    """clean()
    Bot Task managing the autocleanup of the save data
    """
    async def clean(self): # background task cleaning the save file from useless data
        try:
            await asyncio.sleep(1000) # after 1000 seconds
            if not self.bot.running: return
            count = await self.bot.do(self.bot.data.clean_spark) # clean up spark data
            if count > 0:
                await self.bot.send('debug', embed=self.bot.util.embed(title="clean()", description="Cleaned {} unused spark saves".format(count), timestamp=self.bot.util.timestamp()))
            if await self.bot.do(self.bot.data.clean_schedule): # clean up schedule data
                await self.bot.send('debug', embed=self.bot.util.embed(title="clean()", description="The schedule has been cleaned up", timestamp=self.bot.util.timestamp()))
            count = await self.bot.do(self.bot.data.clean_others)
            if count > 0: # clean up ST/cleanup/pinboard data
                await self.bot.send('debug', embed=self.bot.util.embed(title="clean()", description="Cleaned {} unused guild datas".format(count), timestamp=self.bot.util.timestamp()))
            if self.bot.util.JST().day == 3: # only clean on the third day of each month
                count = await self.bot.data.clean_profile() # clean up profile data
                if count > 0:
                    await self.bot.send('debug', embed=self.bot.util.embed(title="clean()", description="Cleaned {} unused profiles".format(count), timestamp=self.bot.util.timestamp()))
        except asyncio.CancelledError:
            await self.bot.sendError('clean', 'cancelled')
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
        async def predicate(inter):
            if inter.bot.isOwner(inter):
                return True
            else:
                await inter.response.send_message(embed=inter.bot.util.embed(title="Error", description="You lack the permission to use this command"), ephemeral=True)
                return False
        return commands.check(predicate)

    """guildList()
    Output the server list of the bot in the debug channel
    """
    async def guildList(self): # list all guilds the bot is in and send it in the debug channel
        msg = ""
        for s in self.bot.guilds:
            msg += "**{}** `{}`owned by `{}`\n".format(s.name, s.id, s.owner_id)
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

    @commands.slash_command(name="owner", guild_ids=guild_ids)
    @commands.default_member_permissions(send_messages=True, read_messages=True)
    @isOwner()
    async def _owner(self, inter: disnake.GuildCommandInteraction):
        """Command Group (Owner Only)"""
        pass

    @_owner.sub_command_group()
    async def utility(self, inter: disnake.GuildCommandInteraction):
        pass

    @utility.sub_command()
    async def eval(self, inter: disnake.GuildCommandInteraction, expression : str = commands.Param()):
        """Evaluate code at run time (Owner Only)"""
        try:
            eval(expression)
            await inter.response.send_message(embed=self.bot.util.embed(title="Eval", description="Ran `{}` with success".format(expression), color=self.color), ephemeral=True)
        except Exception as e:
            await inter.response.send_message(embed=self.bot.util.embed(title="Eval Error", description="Exception\n{}".format(e), footer=expression, color=self.color), ephemeral=True)

    @utility.sub_command()
    async def exec(self, inter: disnake.GuildCommandInteraction, expression : str = commands.Param()):
        """Execute code at run time (Owner Only)"""
        try:
            exec(expression)
            await inter.response.send_message(embed=self.bot.util.embed(title="Exec", description="Ran `{}` with success".format(expression), color=self.color), ephemeral=True)
        except Exception as e:
            await inter.response.send_message(embed=self.bot.util.embed(title="Exec Error", description="Exception\n{}".format(e), footer=expression, color=self.color), ephemeral=True)

    @utility.sub_command()
    async def answer(self, inter: disnake.GuildCommandInteraction, target_id : str = commands.Param(), message : str = commands.Param()):
        """Send feedback to a bug report (Owner Only)"""
        try:
            await inter.response.defer(ephemeral=True)
            u = await self.bot.get_or_fetch_user(int(target_id))
            await u.send(embed=self.bot.util.embed(title="Answer to your bug report", description=message, color=self.color))
            await inter.edit_original_message(embed=self.bot.util.embed(title="Answering to {}".format(u.display_name), description="`{}`\nMessage sent with success".format(message), color=self.color))
        except Exception as e:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Answer Error", description="Exception\n{}".format(e), color=self.color))

    @utility.sub_command()
    async def leave(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """Make the bot leave a server (Owner Only)"""
        try:
            toleave = self.bot.get_guild(int(id))
            await toleave.leave()
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('leave', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @utility.sub_command()
    async def accept(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """Add a server to the confirmed servers list (Owner Only)"""
        try:
            gid = int(id)
            if gid not in self.bot.data.save['guilds']:
                self.bot.data.save['guilds'].append(gid)
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        except Exception as e:
            await self.bot.sendError('accept', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @_owner.sub_command_group()
    async def ban(self, inter: disnake.GuildCommandInteraction):
        pass

    @ban.sub_command()
    async def server(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """Command to leave and ban a server (Owner Only)"""
        try:
            gid = int(id)
            try:
                toleave = self.bot.get_guild(gid)
                await toleave.leave()
            except:
                pass
            if id not in self.bot.data.save['banned_guilds']:
                with self.bot.data.lock:
                    self.bot.data.save['banned_guilds'].append(id)
                    self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
            await self.guildList()
        except Exception as e:
            await self.bot.sendError('ban_server', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="An unexpected error occured", color=self.color), ephemeral=True)

    @ban.sub_command()
    async def owner(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """Command to ban a server owner and leave all its servers (Owner Only)"""
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

    @ban.sub_command()
    async def checkid(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """ID Based Check if an user has a ban registered in the bot (Owner Only)"""
        msg = ""
        if self.bot.ban.check(id, self.bot.ban.OWNER): msg += "Banned from having the bot in its own servers\n"
        if self.bot.ban.check(id, self.bot.ban.SPARK): msg += "Banned from appearing in `rollRanking`\n"
        if self.bot.ban.check(id, self.bot.ban.PROFILE): msg += "Banned from using `setProfile`\n"
        if self.bot.ban.check(id, self.bot.ban.USE_BOT): msg += "Banned from using the bot\n"
        if msg == "": msg = "No Bans set for this user"
        await inter.response.send_message(embed=self.bot.util.embed(title="User {}".format(id), description=msg, color=self.color), ephemeral=True)

    @ban.sub_command()
    async def all(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """Ban an user from using the bot (Owner Only)"""
        self.bot.ban.set(id, self.bot.ban.USE_BOT)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @ban.sub_command()
    async def profile(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """ID based Ban for $setProfile (Owner Only)"""
        self.bot.ban.set(id, self.bot.ban.PROFILE)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @ban.sub_command()
    async def rollid(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """ID based Ban for $rollranking (Owner Only)"""
        self.bot.ban.set(id, self.bot.ban.SPARK)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @_owner.sub_command_group()
    async def unban(self, inter: disnake.GuildCommandInteraction):
        pass

    @unban.sub_command(name="all")
    async def _all(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """Unban an user from using the bot (Owner Only)"""
        self.bot.ban.unset(id, self.bot.ban.USE_BOT)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @unban.sub_command(name="profile")
    async def _profile(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """ID based Unban for $setProfile (Owner Only)"""
        self.bot.ban.unset(id, self.bot.ban.PROFILE)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @unban.sub_command()
    async def roll(self, inter: disnake.GuildCommandInteraction, id : str = commands.Param()):
        """Unban an user from all the roll ranking (Owner Only)
        Ask me for an unban (to avoid abuses)"""
        self.bot.ban.unset(id, self.bot.ban.SPARK)
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @_owner.sub_command_group()
    async def invite(self, inter: disnake.GuildCommandInteraction):
        pass

    @invite.sub_command(name="set")
    async def inviteset(self, inter: disnake.GuildCommandInteraction, state : int = commands.Param(description="Invite State (0 to close, anything else to open)"), limit : int = commands.Param(description="Maximum number of guilds", default=50)):
        """Set the bot invitation settings (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['invite'] = {'state':(state != 0), 'limit':limit}
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="Invitation setting", description="Open: `{}`\nLimited to max `{}` servers".format(self.bot.data.save['invite']['state'], self.bot.data.save['invite']['limit']), timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)

    @invite.sub_command(name="get")
    async def inviteget(self, inter: disnake.GuildCommandInteraction):
        """Show the bot invitation settings (Owner Only)"""
        await inter.response.send_message(embed=self.bot.util.embed(title="Invitation setting", description="Open: `{}`\nLimited to max `{}` servers".format(self.bot.data.save['invite']['state'], self.bot.data.save['invite']['limit']), timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)

    @_owner.sub_command_group(name="bot")
    async def _bot(self, inter: disnake.GuildCommandInteraction):
        pass

    @_bot.sub_command()
    async def save(self, inter: disnake.GuildCommandInteraction):
        """Command to make a snapshot of the bot's settings (Owner Only)"""
        await inter.response.defer(ephemeral=True)
        await self.bot.data.autosave(True)
        await inter.edit_original_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color))

    @_bot.sub_command()
    async def load(self, inter: disnake.GuildCommandInteraction, drive : str = commands.Param(description="Add `drive` to load the file from the drive", default="")):
        """Command to reload the bot saved data (Owner Only)"""
        await inter.response.defer(ephemeral=True)
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
        await edit_original_message(embed=self.bot.util.embed(title="The command finished running", color=self.color))

    @_bot.sub_command()
    async def guilds(self, inter: disnake.GuildCommandInteraction):
        """List all servers (Owner Only)"""
        await self.guildList()
        await inter.response.send_message('\u200b', delete_after=0)

    @_bot.sub_command()
    async def setstatus(self, inter: disnake.GuildCommandInteraction, *, terms : str):
        """Change the bot status (Owner Only)"""
        await self.bot.change_presence(status=disnake.Status.online, activity=disnake.activity.Game(name=terms))
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @_bot.sub_command()
    async def cleanroll(self, inter: disnake.GuildCommandInteraction):
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

    @_bot.sub_command()
    async def clearprofile(self, inter: disnake.GuildCommandInteraction, gbf_id : int = commands.Param(description="A valid GBF Profile ID", ge=0)):
        """Unlink a GBF id (Owner Only)"""
        user_id = await self.bot.do(self.bot.get_cog('GranblueFantasy').searchprofile, gbf_id)
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

    @_bot.sub_command()
    async def resetgacha(self, inter: disnake.GuildCommandInteraction):
        """Reset the gacha settings (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['gbfdata'].pop('gacha', None)
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @_bot.sub_command()
    async def config(self, inter: disnake.GuildCommandInteraction):
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

    @_bot.sub_command()
    async def getfile(self, inter: disnake.GuildCommandInteraction, filename: str = commands.Param(description="Path to a local file")):
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

    @_bot.sub_command()
    async def togglehttps(self, inter: disnake.GuildCommandInteraction):
        """Toggle the use of HTTPS for GBF related urls (Owner Only)"""
        await inter.response.defer(ephemeral=True)
        with self.bot.data.lock:
            self.bot.data.save['https'] = not self.bot.data.save['https']
            self.bot.data.pending = True
            await inter.edit_original_message(embed=self.bot.util.embed(title="The command ran with success\nSetting is set to `{}`".format(self.bot.data.save['https']), color=self.color))

    @_owner.sub_command_group()
    async def maintenance(self, inter: disnake.GuildCommandInteraction):
        pass

    @maintenance.sub_command(name="set")
    async def maintset(self, inter: disnake.GuildCommandInteraction, day : int = commands.Param(ge=1, le=31), month : int = commands.Param(ge=1, le=12), hour : int = commands.Param(ge=0, le=23), duration : int = commands.Param(ge=0)):
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

    @maintenance.sub_command(name="del")
    async def maintdel(self, inter: disnake.GuildCommandInteraction):
        """Delete the maintenance date (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['maintenance'] = {"state" : False, "time" : None, "duration" : 0}
            self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @_owner.sub_command_group()
    async def stream(self, inter: disnake.GuildCommandInteraction):
        pass

    @stream.sub_command(name="set")
    async def streamset(self, inter: disnake.GuildCommandInteraction, txt : str = commands.Param()):
        """Set the stream command text (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['stream']['content'] = txt.split(';')
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="Stream Settings", description="Stream text sets to\n`{}`".format(txt), color=self.color))

    @stream.sub_command()
    async def time(self, inter: disnake.GuildCommandInteraction, day : int = commands.Param(ge=1, le=31), month : int = commands.Param(ge=1, le=12), year : int = commands.Param(ge=2021), hour : int = commands.Param(ge=0, le=23)):
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

    @stream.sub_command()
    async def clear(self, inter: disnake.GuildCommandInteraction):
        """Clear the stream command text (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['stream']['content'] = []
            self.bot.data.save['stream']['time'] = None
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @_owner.sub_command_group()
    async def schedule(self, inter: disnake.GuildCommandInteraction):
        pass

    @schedule.sub_command(name="set")
    async def scheduleset(self, inter: disnake.GuildCommandInteraction, txt : str = commands.Param(description="Format: `Date1;Event1;...;DateN;EventN`")):
        """Set the GBF schedule for the month (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['schedule'] = txt.split(';')
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", description="New Schedule:\n`{}`".format(';'.join(self.bot.data.save['schedule'])), color=self.color), ephemeral=True)

    @schedule.sub_command()
    async def get(self, inter: disnake.GuildCommandInteraction):
        """Retrieve the monthly schedule from @granble_en (Owner Only / Tweepy Only)"""
        await inter.response.defer(ephemeral=True)
        month, schedule, created_at = self.bot.twitter.get_schedule_from_granblue_en()
        if schedule is None:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="I couldn't retrieve the schedule from Twitter", color=self.color))
        else:
            msg = month + '\n'
            msg += '`'
            for el in schedule:
                msg += el + ";"
            if len(schedule) > 0: msg = msg[:-1]
            msg += '`'
            await inter.edit_original_message(embed=self.bot.util.embed(title="Granblue Fantasy Schedule from @granblue_en", description=msg, color=self.color))

    @schedule.sub_command(name="clean")
    async def _clean(self, inter: disnake.GuildCommandInteraction):
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

    @_owner.sub_command_group()
    async def account(self, inter: disnake.GuildCommandInteraction):
        pass

    @account.sub_command()
    async def list(self, inter: disnake.GuildCommandInteraction, id : int = -1):
        """List GBF accounts used by the bot (Owner Only)"""
        if len(self.bot.data.save['gbfaccounts']) == 0:
            await inter.response.send_message(embed=self.bot.util.embed(title="GBF Account status", description="No accounts set", color=self.color), ephemeral=True)
            return

        if id == -1:
            msg = ""
            for i, acc in enumerate(self.bot.data.save['gbfaccounts']):
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
            r = await self.bot.do(self.bot.gbf.request, self.bot.data.config['gbfwatch']['test'], account=id, check=True, force_down=True)
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

    @account.sub_command()
    async def switch(self, inter: disnake.GuildCommandInteraction, id : int):
        """Select the current GBF account to use (Owner Only)"""
        if self.bot.gbf.get(id) is not None:
            with self.bot.data.lock:
                self.bot.data.save['gbfcurrent'] = id
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message("Invalid id", ephemeral=True)

    @account.sub_command()
    async def add(self, inter: disnake.GuildCommandInteraction, uid : int = commands.Param(default=0), ck : str = commands.Param(default=""), ua : str = commands.Param(default="")):
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

    @account.sub_command()
    async def rm(self, inter: disnake.GuildCommandInteraction, num : int):
        """(Owner Only)"""
        if self.bot.gbf.remove(num):
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message("Invalid id", ephemeral=True)

    @account.sub_command()
    async def uid(self, inter: disnake.GuildCommandInteraction, num : int, uid : int = -1):
        """(Owner Only)"""
        if uid < 0:
            acc = self.bot.gbf.get(num)
            if acc is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color), ephemeral=True)
            else:
                await inter.response.send_message('debug', embed=self.bot.util.embed(title="Account #{} current UID".format(num), description="`{}`".format(acc[0]), color=self.color), ephemeral=True)
        elif not self.bot.gbf.update(num, uid=uid):
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(uid), color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color))

    @account.sub_command()
    async def ck(self, inter: disnake.GuildCommandInteraction, num : int, *, ck : str = ""):
        """(Owner Only)"""
        if ck == "":
            acc = self.bot.gbf.get(num)
            if acc is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color), ephemeral=True)
            else:
                await inter.response.send_message('debug', embed=self.bot.util.embed(title="Account #{} current CK".format(num), description="`{}`".format(acc[1]), color=self.color), ephemeral=True)
        elif not self.bot.gbf.update(num, ck=ck):
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ck), color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color))

    @account.sub_command()
    async def ua(self, inter: disnake.GuildCommandInteraction, num : int, *, ua : str = ""):
        """(Owner Only)"""
        if ua == "":
            acc = self.bot.gbf.get(num)
            if acc is None:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color), ephemeral=True)
            else:
                await inter.response.send_message('debug', embed=self.bot.util.embed(title="Account #{} current UA".format(num), description="`{}`".format(acc[2]), color=self.color), ephemeral=True)
        elif not self.bot.gbf.update(num, ua=ua):
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ua), color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color))

    @_owner.sub_command_group()
    async def db(self, inter: disnake.GuildCommandInteraction):
        pass

    @db.sub_command(name="set")
    async def dbset(self, inter: disnake.GuildCommandInteraction, id : int = commands.Param(description="Dread Barrage ID", ge=0, le=999), element : str = commands.Param(description="Dread Barrage Element Advantage", autocomplete=['fire', 'water', 'earth', 'wind', 'light', 'dark']), day : int = commands.Param(description="Dread Barrage Start Day", ge=1, le=31), month : int = commands.Param(description="Dread Barrage Start Month", ge=1, le=12), year : int = commands.Param(description="Dread Barrage Start Year", ge=2021)):
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
                self.bot.data.save['valiant']['dates']["NM135"] = self.bot.data.save['valiant']['dates']["Day 3"] + timedelta(seconds=50400)
                self.bot.data.save['valiant']['dates']["Day 4"] = self.bot.data.save['valiant']['dates']["Day 3"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 5"] = self.bot.data.save['valiant']['dates']["Day 4"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["Day 6"] = self.bot.data.save['valiant']['dates']["Day 5"] + timedelta(days=1)
                self.bot.data.save['valiant']['dates']["NM175"] = self.bot.data.save['valiant']['dates']["Day 5"] + timedelta(seconds=50400)
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

    @db.sub_command()
    async def disable(self, inter: disnake.GuildCommandInteraction):
        """Disable the Dread Barrage mode, but doesn't delete the settings (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['valiant']['state'] = False
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @db.sub_command()
    async def enable(self, inter: disnake.GuildCommandInteraction):
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

    @_owner.sub_command_group()
    async def gw(self, inter: disnake.GuildCommandInteraction):
        pass

    @gw.sub_command()
    async def reloaddb(self, inter: disnake.GuildCommandInteraction):
        """Download GW.sql (Owner Only)"""
        await inter.response.defer(ephemeral=True)
        await self.bot.do(self.bot.ranking.reloadGWDB)
        vers = await self.bot.do(self.bot.ranking.GWDBver)
        msg = ""
        for i in [0, 1]:
            msg += "**{}** ▫️ ".format('GW_old.sql' if (i == 0) else 'GW.sql')
            if vers[i] is None: msg += "Not loaded"
            else:
                msg += 'GW{} '.format(vers[i].get('gw', '??'))
                msg += '(version {})'.format(vers[i].get('ver', 'ERROR'))
            msg += "\n"
        await inter.edit_original_message(embed=self.bot.util.embed(title="Guild War Databases", description=msg, timestamp=self.bot.util.timestamp(), color=self.color))

    @gw.sub_command()
    async def forceupdategbfg(self, inter: disnake.GuildCommandInteraction):
        """Force an update of the GW /gbfg/ Datta (Owner Only)"""
        await inter.response.defer(ephemeral=True)
        await self.bot.do(self.bot.get_cog('GuildWar').updateGBFGData, crews, True)
        await inter.response.edit_original_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color))

    @gw.sub_command(name="disable")
    async def disable__(self, inter: disnake.GuildCommandInteraction):
        """Disable the GW mode (Owner Only)
        It doesn't delete the GW settings"""
        self.bot.cancelTask('check_buff')
        with self.bot.data.lock:
            self.bot.data.save['gw']['state'] = False
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @gw.sub_command(name="enable")
    async def enable__(self, inter: disnake.GuildCommandInteraction):
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

    @gw.sub_command()
    async def cleartracker(self, inter: disnake.GuildCommandInteraction):
        """Clear the GW match tracker (Owner Only)"""
        with self.bot.data.lock:
            self.bot.data.save['youtracker'] = None
            self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @gw.sub_command()
    async def forceupdateranking(self, inter: disnake.GuildCommandInteraction):
        """Force the retrieval of the GW ranking (Owner Only)"""
        await inter.response.defer(ephemeral=True)
        if self.bot.data.save['gw']['state']:
            current_time = self.bot.util.JST()
            await self.bot.ranking.retrieve_ranking(current_time.replace(minute=20 * (current_time.minute // 20), second=1, microsecond=0), force=True)
            await inter.edit_original_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color))
        else:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="The next set of buffs is already beind skipped", color=self.color))

    @gw.sub_command(name="set")
    async def gwset(self, inter: disnake.GuildCommandInteraction, id : int = commands.Param(description="Guild War ID", ge=0, le=999), element : str = commands.Param(description="Guild War Element Advantage", autocomplete=['fire', 'water', 'earth', 'wind', 'light', 'dark']), day : int = commands.Param(description="Guild War Start Day", ge=1, le=31), month : int = commands.Param(description="Guild War Start Month", ge=1, le=12), year : int = commands.Param(description="Guild War Start Year", ge=2021)):
        """Set the GW date (Owner Only)"""
        try:
            # stop the task
            self.bot.cancelTask('check_buff')
            with self.bot.data.lock:
                self.bot.data.save['gw']['state'] = False
                self.bot.data.save['gw']['id'] = id
                self.bot.data.save['gw']['ranking'] = None
                self.bot.data.save['gw']['element'] = element.lower()
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

    @_owner.sub_command_group()
    async def buff(self, inter: disnake.GuildCommandInteraction):
        pass

    @buff.sub_command()
    async def check(self, inter: disnake.GuildCommandInteraction): # debug stuff
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

    @buff.sub_command()
    async def newtask(self, inter: disnake.GuildCommandInteraction):
        """Start a new checkGWBuff() task (Owner Only)"""
        try: self.bot.runTask('check_buff', self.bot.get_cog('GuildWar').checkGWBuff)
        except: pass
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)


    @buff.sub_command()
    async def skip(self, inter: disnake.GuildCommandInteraction):
        """The bot will skip the next GW buff call (Owner Only)"""
        if not self.bot.data.save['gw']['skip']:
            with self.bot.data.lock:
                self.bot.data.save['gw']['skip'] = True
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="The next set of buffs is already beind skipped", color=self.color), ephemeral=True)

    @buff.sub_command()
    async def cancel(self, inter: disnake.GuildCommandInteraction):
        """Cancel the GW buff call skipping (Owner Only)"""
        if self.bot.data.save['gw']['skip']:
            with self.bot.data.lock:
                self.bot.data.save['gw']['skip'] = False
                self.bot.data.pending = True
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)