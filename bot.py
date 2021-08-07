from components.data import Data
from components.drive import Drive
from components.util import Util
from components.gbf import GBF
from components.twitter import Twitter
from components.pinboard import Pinboard
from components.emote import Emote
from components.calc import Calc
from components.channel import Channel
from components.file import File
from components.sql import SQL
from components.ranking import Ranking
from components.ban import Ban
import cogs

import discord
from discord.ext import commands
import signal
import time
import concurrent.futures
import functools

"""
    TODO:
        ctrl+F all NOTE
        rollback beta status in config.json
        check @commands and cooldown stuff
        puthon 3.10: use the new match feature
    
    discord.py 2.0 breaking changes:
    https://github.com/Rapptz/discord.py/projects/3
        * remove bot.logout() calls
        * check the custom help
        * remove permissions_in
        * check timestamp timezone
        * fix config.json status
        * clean_prefix for help
"""

# Main Bot Class (overload commands.Bot)
class MizaBot(commands.Bot):
    def __init__(self):
        self.version = "8.0-beta-8" # bot version
        self.changelog = [ # changelog lines
            "**This MizaBOT version is a Beta**, please use `$bug_report` if you see anything wrong",
            "Online command list added [here](https://mizagbf.github.io/MizaBOT/)",
            "Added `$fortune`, `$fortunechance` and `$rollchance`",
            "Crew health indicator in `$crew` (Note: Values has been adjusted)",
            "Added `$gwspeed`, `$invite` and `$scam`",
            "Reworked the `$help` command",
            "All servers can now access the pinboard system using `$enablePinboard` and `$disablePinboard`",
            "Added `$here`, `$when`, `$dbbox`, `$dbtoken`, `$zeroroll`, `$belial`, `$addRoll`, `$dice`, `$8ball` and `$coin`"
        ]
        self.running = True # is False when the bot is shutting down
        self.booted = False # goes up to True after the first on_ready event
        self.tasks = {} # contain our user tasks
        self.cogn = 0 # number of cog loaded
        self.errn = 0 # number of internal errors
        self.retcode = 0 # return code
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=30) # thread pool for blocking codes
        
        # components
        self.data = Data(self)
        self.drive = Drive(self)
        self.util = Util(self)
        self.gbf = GBF(self)
        self.twitter = Twitter(self)
        self.pinboard = Pinboard(self)
        self.emote = Emote(self)
        self.calc = Calc(self)
        self.channel = Channel(self)
        self.file = File(self)
        self.sql = SQL(self)
        self.ranking = Ranking(self)
        self.ban = Ban(self)
        
        # loading data
        self.data.loadConfig()
        for i in range(0, 100): # try multiple times in case google drive is unresponsive
            if self.drive.load(): break # attempt to download the save file
            elif i == 99:
                print("Google Drive might be unavailable")
                exit(3)
            time.sleep(20) # wait 20 sec
        if not self.data.loadData(): exit(2) # load the save file
        
        # initialize components
        self.data.init()
        self.drive.init()
        self.util.init()
        self.gbf.init()
        self.twitter.init()
        self.pinboard.init()
        self.emote.init()
        self.calc.init()
        self.channel.init()
        self.file.init()
        self.sql.init()
        self.ranking.init()
        self.ban.init()

        # graceful exit
        signal.signal(signal.SIGTERM, self.exit_gracefully) # SIGTERM is called by heroku when shutting down

        # intents (for guilds and stuff)
        intents = discord.Intents.default()
        intents.members = True
        
        # init base class
        super().__init__(command_prefix=self.prefix, case_insensitive=True, description="MizaBOT version {}\n[Source code](https://github.com/MizaGBF/MizaBOT)▫️[Online Command List](https://mizagbf.github.io/MizaBOT/)\nDefault command prefix is `$`, use `$setPrefix` to change it on your server.".format(self.version), help_command=None, owner=self.data.config['ids']['owner'], max_messages=None, intents=intents)
        self.add_check(self.global_check)

    """go()
    Main Bot Loop
    
    Returns
    --------
    int: Exit value
    """
    def go(self):
        self.cogn = cogs.load(self) # load cogs
        while self.running:
            try:
                self.loop.run_until_complete(self.start(self.data.config['tokens']['discord'])) # start the bot
            except Exception as e: # handle exceptions here to avoid the bot dying
                if self.data.pending: # save if anything weird happened (if needed)
                    self.data.saveData()
                if str(e).startswith("429 Too Many Requests"): # ignore the rate limit error
                    time.sleep(100)
                else:
                    self.errn += 1
                    print("Main Loop Exception:\n" + self.util.pexc(e))
        if self.data.saveData():
            print('Autosave Success')
        else:
            print('Autosave Failed')
        return self.retcode

    """exit_gracefully()
    Triggered when SIGTERM is received to exit properly
    
    Parameters
    ----------
    signum: Signal Number
    frame: Current Stack frame
    """
    def exit_gracefully(self, signum, frame): # graceful exit (when SIGTERM is received)
        self.running = False
        if self.data.pending:
            self.data.autosaving = False
            if self.data.saveData():
                print('Autosave Success')
            else:
                print('Autosave Failed')
        exit(self.retcode)

    """prefix()
    Return the prefix of the server the command is invoked in (default: $)
    
    Parameters
    ----------
    client: Client instance (unused, it should be equal to self)
    message: The message to process
    
    Returns
    --------
    str: Server prefix
    """
    def prefix(self, client, message): # command prefix check
        try:
            return self.data.save['prefixes'][str(message.guild.id)] # get the guild prefix if set
        except:
            return '$' # else, return the default prefix $

    """isAuthorized()
    Check if the command is authorized to be invoked in this channel
    
    Parameters
    ----------
    ctx: Command context
    
    Returns
    --------
    bool: True if authorized, False if not
    """
    def isAuthorized(self, ctx): # check if the command is authorized in the channel
        id = str(ctx.guild.id)
        if id in self.data.save['permitted']: # if id is found, it means the check is enabled
            if ctx.channel.id in self.data.save['permitted'][id]:
                return True # permitted
            return False # not permitted
        return True # default

    """isServer()
    Check if the context is matching this server (server must be set in config.json)
    
    Parameters
    ----------
    ctx: Command context
    id_string: Server identifier in config.json
    
    Returns
    --------
    bool: True if matched, False if not
    """
    def isServer(self, ctx, id_string : str): # check if the context is in the targeted guild (guild id must be in config.json)
        if ctx.message.author.guild.id == self.data.config['ids'].get(id_string, -1):
            return True
        return False

    """isChannel()
    Check if the context is matching this channel (channel must be set in config.json)
    
    Parameters
    ----------
    ctx: Command context
    id_string: Channel identifier in config.json
    
    Returns
    --------
    bool: True if matched, False if not
    """
    def isChannel(self, ctx, id_string : str): # check if the context is in the targeted channel (channel is must be in config.json)
        if ctx.channel.id == self.data.config['ids'].get(id_string, -1):
            return True
        return False

    """isMod()
    Check if the context author has the manage message permission
    
    Parameters
    ----------
    ctx: Command context
    
    Returns
    --------
    bool: True if it does, False if not
    """
    def isMod(self, ctx): # check if the member has the manage_message permission
        if ctx.author.guild_permissions.manage_messages or ctx.author.id == self.data.config['ids'].get('owner', -1):
            return True
        return False

    """isOwner()
    Check if the context author is the owner (id must be set in config.json)
    
    Parameters
    ----------
    ctx: Command context
    
    Returns
    --------
    bool: True if it does, False if not
    """
    def isOwner(self, ctx): # check if the member is the bot owner
        if ctx.message.author.id == self.data.config['ids'].get('owner', -1): # must be defined in config.json
            return True
        return False

    """callCommand()
    Invoke a command from another command
    
    Parameters
    ----------
    ctx: Command context
    command: New command to be called
    *args: New command parameters
    **kargs: New command keyword parameters
    
    Raises
    ------
    Exception: If the command isn't found
    """
    async def callCommand(self, ctx, command, *args, **kwargs): #call a command from another cog or command
        for cn in self.cogs:
            cmds = self.get_cog(cn).get_commands()
            for cm in cmds:
                if cm.name == command:
                    await ctx.invoke(cm, *args, **kwargs)
                    return
        raise Exception("Command `{}` not found".format(command))

    """send()
    Send a message to a registered channel (must be set in config.json)
    
    Parameters
    ----------
    channel_name: Channel name identifier
    msg: Text message
    embed: Discord Embed
    file: Discord File
    
    Returns
    --------
    discord.Message: The sent message or None if error
    """
    async def send(self, channel_name : str, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send something to a registered channel
        try:
            return await self.channel.get(channel_name).send(msg, embed=embed, file=file)
        except Exception as e:
            self.errn += 1
            print("Channel {} error: {}".format(channel_name, self.util.pexc(e)))
            return None

    """sendMulti()
    Send a message to multiple registered channel (must be set in config.json)
    
    Parameters
    ----------
    channel_names: List of Channel name identifiers
    msg: Text message
    embed: Discord Embed
    file: Discord File
    
    Returns
    --------
    list: A list of the successfully sent messages
    """
    async def sendMulti(self, channel_names : list, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send to multiple registered channel at the same time
        r = []
        for c in channel_names:
            try:
                r.append(await self.send(c, msg, embed, file))
            except:
                await self.sendError('sendMulti', 'Failed to send a message to channel `{}`'.format(c))
                r.append(None)
        return r

    """sendError()
    Send an error message to the debuf channel (must be set in config.json)
    
    Parameters
    ----------
    func_name: Name of the function where the error happened
    error: Exception
    id: Optional identifier to locate the error more precisely
    """
    async def sendError(self, func_name : str, error, id = None): # send an error to the debug channel
        if str(error).startswith("403 FORBIDDEN"): return # I'm tired of those errors because people didn't set their channel permissions right so I ignore it
        if self.errn >= 30: return # disable error messages if too many messages got sent
        if id is None: id = ""
        else: id = " {}".format(id)
        self.errn += 1
        await self.send('debug', embed=self.util.embed(title="Error in {}() {}".format(func_name, id), description=self.util.pexc(error), timestamp=self.util.timestamp()))

    """on_ready()
    Event. Called on connection
    """
    async def on_ready(self): # called when the bot starts
        if not self.booted:
            # set our used channels for the send function
            self.channel.setMultiple([['debug', 'debug_channel'], ['image', 'image_upload'], ['debug_update', 'debug_update'], ['you_pinned', 'you_pinned'], ['gbfg_pinned', 'gbfg_pinned'], ['gbfglog', 'gbfg_log'], ['youlog', 'you_log']])
            await self.send('debug', embed=self.util.embed(title="{} is Ready".format(self.user.display_name), description=self.util.statusString(), thumbnail=self.user.avatar_url, timestamp=self.util.timestamp()))
            # start the task
            await self.startTasks()
            self.booted = True

    """do()
    Run a non awaitable function in the bot event loop
    
    Parameters
    ----------
    func: Function to be called
    *args: Function parameters
    **kargs: Function keyword parameters
    
    Returns
    --------
    unknown: The function return value
    """
    async def do(self, func, *args, **kwargs): # routine to run blocking code in a separate thread
        return await self.loop.run_in_executor(self.executor, functools.partial(func, *args, **kwargs))

    """doAsync()
    Run an awaitable function in the bot event loop
    
    Parameters
    ----------
    coro: The coroutine to be called
    
    Returns
    --------
    unknown: The function return value
    """
    def doAsync(self, coro): # add a task to the event loop (return the task)
        return self.loop.create_task(coro)

    """doAsync()
    Run an awaitable function from non async code (Warning: slow and experimental)
    
    Parameters
    ----------
    coro: The coroutine to be called
    
    Returns
    --------
    unknown: The function return value
    """
    def doAsTask(self, coro): # run a coroutine from a normal function (slow, don't abuse it for small functions)
        task = self.doAsync(coro)
        while not task.done(): # NOTE: is there a way to make it faster?
            time.sleep(0.01)
        return task.result()

    """runTask()
    Start a new bot task (cancel any previous one with the same name
    
    Parameters
    ----------
    name: Task identifier
    coro: The coroutine to be called
    """
    def runTask(self, name, func): # start a task (cancel a previous one with the same name)
        self.cancelTask(name)
        self.tasks[name] = self.loop.create_task(func())

    """cancelTask()
    Stop a bot task
    
    Parameters
    ----------
    name: Task identifier
    """
    def cancelTask(self, name): # cancel a task
        if name in self.tasks:
            self.tasks[name].cancel()

    """startTasks()
    Start all tasks from each cogs (if any)
    """
    async def startTasks(self): # start all our tasks
        for c in self.cogs:
            try: self.get_cog(c).startTasks()
            except: pass
        msg = ""
        for t in self.tasks:
            msg += "\▫️ {}\n".format(t)
        if msg != "":
            await self.send('debug', embed=self.util.embed(title="{} user tasks started".format(len(self.tasks)), description=msg, timestamp=self.util.timestamp()))

    """on_message()
    Event. Called when a message is received
    
    Parameters
    ----------
    message: Discord Message to be processed
    """
    async def on_message(self, message): # to do something with a message
        if self.running: # don't process commands if exiting
            await self.process_commands(message) # never forget this line

    """on_guild_join()
    Event. Called when the bot join a guild
    
    Parameters
    ----------
    guild: Discord Guild
    """
    async def on_guild_join(self, guild): # when the bot joins a new guild
        id = str(guild.id)
        if id == str(self.data.config['ids']['debug_server']):
            return
        elif id in self.data.save['guilds']['banned'] or self.ban.check(guild.owner.id, self.ban.OWNER): # leave if the server is blacklisted
            try:
                await self.send('debug', embed=self.util.embed(title="Banned guild request", description="{} ▫️ {}".format(guild.name, id), thumbnail=guild.icon_url, footer="Owner: {} ▫️ {}".format(guild.owner.name, guild.owner.id)))
            except Exception as e:
                await self.sendError("on_guild_join", e)
            await guild.leave()
        elif 'invite' not in self.data.save or self.data.save['invite']['state'] == False or (len(self.guilds) - len(self.data.save['guilds']['pending'])) >= self.data.save['invite']['limit']:
            try: await guild.owner.send(embed=self.util.embed(title="Error", description="Invitations are currently closed.", thumbnail=guild.icon_url))
            except: pass
            await guild.leave()
        elif len(guild.members) < 30:
            try: await guild.owner.send(embed=self.util.embed(title="Error", description="The bot is currently limited to servers of at least 30 members.", thumbnail=guild.icon_url))
            except: pass
            await guild.leave()
        else: # notify me and add to the pending servers
            self.data.save['guilds']['pending'][id] = guild.name
            self.data.pending = True
            try: await guild.owner.send(embed=self.util.embed(title="Pending guild request", description="Please wait for your server to be accepted.", thumbnail=guild.icon_url))
            except: pass
            await self.send('debug', msg="{} Please review this new server".format(self.get_user(self.data.config['ids']['owner']).mention), embed=self.util.embed(title="Pending guild request for " + guild.name, description="**ID** ▫️ `{}`\n**Owner** ▫️ {} ▫️ `{}`\n**Region** ▫️ {}\n**Text Channels** ▫️ {}\n**Voice Channels** ▫️ {}\n**Members** ▫️ {}\n**Roles** ▫️ {}\n**Emojis** ▫️ {}\n**Boosted** ▫️ {}\n**Boost Tier** ▫️ {}\n\nUse `$accept` or `$refuse`".format(guild.id, guild.owner, guild.owner.id, guild.region, len(guild.text_channels), len(guild.voice_channels), len(guild.members), len(guild.roles), len(guild.emojis), guild.premium_subscription_count, guild.premium_tier), thumbnail=guild.icon_url, timestamp=guild.created_at))

    """global_check()
    Check if the command is authorized to run
    
    Parameters
    ----------
    ctx: Command context
    
    Returns
    --------
    bool: True if the command can be processed, False if not
    """
    async def global_check(self, ctx): # called whenever a command is used
        if ctx.guild is None: # if none, the command has been sent via a direct message
            return False # so we ignore
        try:
            id = str(ctx.guild.id)
            if self.ban.check(ctx.author.id, self.ban.USE_BOT):
                return False
            elif id in self.data.save['guilds']['banned'] or self.ban.check(ctx.guild.owner.id, self.ban.OWNER): # ban check
                await ctx.guild.leave() # leave the server if banned
                return False
            elif id in self.data.save['guilds']['pending']: # pending check
                await self.util.react(ctx.message, 'cooldown')
                return False
            elif ctx.guild.owner.id in self.data.config['banned']:
                return False
            return True
        except Exception as e:
            await self.sendError('global_check', e)
            return False

    """on_command_error()
    Event. Called when a command raise an uncaught error
    
    Parameters
    ----------
    ctx: Command context
    error: Exception
    """
    async def on_command_error(self, ctx, error): # called when an uncatched exception happens in a command
        msg = str(error)
        if msg.find('You are on cooldown.') == 0:
            await self.util.react(ctx.message, 'cooldown')
        elif msg.find('required argument that is missing') != -1:
            return
        elif msg.find('check functions for command') != -1:
            return
        elif msg.find('Member "') == 0 or msg.find('Command "') == 0 or msg.startswith('Command raised an exception: Forbidden: 403'):
            return
        else:
            await self.util.react(ctx.message, '❎')
            self.errn += 1
            await self.send('debug', embed=self.util.embed(title="⚠ Error caused by {}".format(ctx.message.author), description=self.util.pexc(error), thumbnail=ctx.author.avatar_url, fields=[{"name":"Command", "value":'`{}`'.format(ctx.message.content)}, {"name":"Server", "value":ctx.message.author.guild.name}, {"name":"Message", "value":msg}], footer='{}'.format(ctx.message.author.id), timestamp=self.util.timestamp()))

    """on_raw_reaction_add()
    Event. Called when a new reaction is added by an user
    
    Parameters
    ----------
    payload: Raw payload
    """
    async def on_raw_reaction_add(self, payload):
        await self.pinboard.check(payload)

    # under is the log system used by my crew and another server, remove if you don't need those
    # it's a sort of live audit log

    """on_member_update()
    Event. Called when a guild member status is updated
    
    Parameters
    ----------
    before: Previous Member status
    after: New Member status
    """
    async def on_member_update(self, before, after):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if before.guild.id in guilds:
            channel = guilds[before.guild.id]
            if before.display_name != after.display_name:
                    await self.send(channel, embed=self.util.embed(author={'name':"{} ▫️ Name change".format(after.display_name), 'icon_url':after.avatar_url}, description="{}\n**Before** ▫️ {}\n**After** ▫️ {}".format(after.mention, before.display_name, after.display_name), footer="User ID: {}".format(after.id), timestamp=self.util.timestamp(), color=0x1ba6b3))
            elif len(before.roles) < len(after.roles):
                for r in after.roles:
                    if r not in before.roles:
                        await self.send(channel, embed=self.util.embed(author={'name':"{} ▫️ Role added".format(after.name), 'icon_url':after.avatar_url}, description="{} was given the `{}` role".format(after.mention, r.name), footer="User ID: {}".format(after.id), color=0x1b55b3, timestamp=self.util.timestamp()))
                        break
            elif len(before.roles) > len(after.roles):
                for r in before.roles:
                    if r not in after.roles:
                        await self.send(channel, embed=self.util.embed(author={'name':"{} ▫️ Role removed".format(after.name), 'icon_url':after.avatar_url}, description="{} was removed from the `{}` role".format(after.mention, r.name), footer="User ID: {}".format(after.id), color=0x0b234a, timestamp=self.util.timestamp()))
                        break

    """on_member_remove()
    Event. Called when a guild member leaves
    
    Parameters
    ----------
    member: Member status
    """
    async def on_member_remove(self, member):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if member.guild.id in guilds:
            await self.send(guilds[member.guild.id], embed=self.util.embed(author={'name':"{} ▫️ Left the server".format(member.name), 'icon_url':member.avatar_url}, footer="User ID: {}".format(member.id), timestamp=self.util.timestamp(), color=0xff0000))

    """on_member_join()
    Event. Called when a guild member joins
    
    Parameters
    ----------
    member: Member status
    """
    async def on_member_join(self, member):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if member.guild.id in guilds:
            channel = guilds[member.guild.id]
            await self.send(channel, embed=self.util.embed(author={'name':"{} ▫️ Joined the server".format(member.name), 'icon_url':member.avatar_url}, footer="User ID: {}".format(member.id), timestamp=self.util.timestamp(), color=0x00ff3c))

    """on_member_ban()
    Event. Called when an user is banned from a guild
    
    Parameters
    ----------
    guild: Guild where it happened
    user: Banned user
    """
    async def on_member_ban(self, guild, user):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if guild.id in guilds:
            await self.send(guilds[guild.id], embed=self.util.embed(author={'name':"{} ▫️ Banned from the server".format(user.name), 'icon_url':user.avatar_url}, footer="User ID: {}".format(user.id), timestamp=self.util.timestamp(), color=0xff0000))

    """on_member_unban()
    Event. Called when an user is unbanned from a guild
    
    Parameters
    ----------
    guild: Guild where it happened
    user: Unbanned user
    """
    async def on_member_unban(self, guild, user):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if guild.id in guilds:
            await self.send(guilds[guild.id], embed=self.util.embed(author={'name':"{} ▫️ Unbanned from the server".format(user.name), 'icon_url':user.avatar_url}, footer="User ID: {}".format(user.id), timestamp=self.util.timestamp(), color=0x00ff3c))

    """on_guild_emojis_update()
    Event. Called when a guild emoji status is updated
    
    Parameters
    ----------
    before: Previous Emoji status
    after: New Emoji status
    """
    async def on_guild_emojis_update(self, guild, before, after):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if guild.id in guilds:
            channel = guilds[guild.id]
            if len(before) < len(after):
                for e in after:
                    if e not in before:
                        await self.send(channel, embed=self.util.embed(author={'name':"{} ▫️ Emoji added".format(e.name), 'icon_url':e.url}, footer="Emoji ID: {}".format(e.id), timestamp=self.util.timestamp(), color=0x00ff3c))
                        break
            else:
                for e in before:
                    if e not in after:
                        await self.send(channel, embed=self.util.embed(author={'name':"{} ▫️ Emoji removed".format(e.name), 'icon_url':e.url}, footer="Emoji ID: {}".format(e.id), timestamp=self.util.timestamp(), color=0xff0000))
                        break

    """on_guild_role_create()
    Event. Called when a new role is created
    
    Parameters
    ----------
    role: New Role
    """
    async def on_guild_role_create(self, role):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if role.guild.id in guilds:
            channel = guilds[role.guild.id]
            await self.send(channel, embed=self.util.embed(title="Role created ▫️ `{}`".format(role.name), footer="Role ID: {}".format(role.id), timestamp=self.util.timestamp(), color=0x00ff3c))

    """on_guild_role_delete()
    Event. Called when a guild role is deleted
    
    Parameters
    ----------
    role: Deleted Role
    """
    async def on_guild_role_delete(self, role):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if role.guild.id in guilds:
            channel = guilds[role.guild.id]
            await self.send(channel, embed=self.util.embed(title="Role deleted ▫️ `{}`".format(role.name), footer="Role ID: {}".format(role.id), timestamp=self.util.timestamp(), color=0xff0000))

    """on_guild_role_update()
    Event. Called when a guild role is updated
    
    Parameters
    ----------
    before: Previous Role state
    after: New Role state
    """
    async def on_guild_role_update(self, before, after):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if before.guild.id in guilds:
            channel = guilds[before.guild.id]
            if before.name != after.name:
                await self.send(channel, embed=self.util.embed(title="Role name updated", fields=[{'name':"Before", 'value':before.name}, {'name':"After", 'value':after.name}], footer="Role ID: {}".format(after.id), timestamp=self.util.timestamp(), color=0x1ba6b3))
            elif before.colour != after.colour:
                await self.send(channel, embed=self.util.embed(title="Role updated ▫️ `" + after.name + "`", description="Color changed", footer="Role ID: {}".format(after.id), timestamp=self.util.timestamp(), color=0x1ba6b3))
            elif before.hoist != after.hoist:
                if after.hoist:
                    await self.send(channel, embed=self.util.embed(title="Role updated ▫️ `{}`".format(after.name), description="Role is displayed separately from other members", footer="Role ID: {}".format(after.id), timestamp=self.util.timestamp(), color=0x1ba6b3))
                else:
                    await self.send(channel, embed=self.util.embed(title="Role updated ▫️ `{}`".format(after.name), description="Role is displayed as the other members", footer="Role ID: {}".format(after.id), timestamp=self.util.timestamp(), color=0x1ba6b3))
            elif before.mentionable != after.mentionable:
                if after.mentionable:
                    await self.send(channel, embed=self.util.embed(title="Role updated ▫️ `{}`".format(after.name), description="Role is mentionable", footer="Role ID: {}".format(after.id), timestamp=self.util.timestamp(), color=0x1ba6b3))
                else:
                    await self.send(channel, embed=self.util.embed(title="Role updated ▫️ `{}`".format(after.name), description="Role isn't mentionable", footer="Role ID: {}".format(after.id), timestamp=self.util.timestamp(), color=0x1ba6b3))

    """on_guild_channel_create()
    Event. Called when a new channel is created
    
    Parameters
    ----------
    channel: New Channel
    """
    async def on_guild_channel_create(self, channel):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if channel.guild.id in guilds:
            await self.send(guilds[channel.guild.id], embed=self.util.embed(title="Channel created ▫️ `{}`".format(channel.name), footer="Channel ID: {}".format(channel.id), timestamp=self.util.timestamp(), color=0xebe007))

    """on_guild_channel_delete()
    Event. Called when a guild channel is deleted
    
    Parameters
    ----------
    channel: Deleted Channel
    """
    async def on_guild_channel_delete(self, channel):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if channel.guild.id in guilds:
            await self.send(guilds[channel.guild.id], embed=self.util.embed(title="Channel deleted ▫️ `{}`".format(channel.name), footer="Channel ID: {}".format(channel.id), timestamp=self.util.timestamp(), color=0x8a8306))


if __name__ == "__main__":
    bot = MizaBot()
    exit(bot.go())