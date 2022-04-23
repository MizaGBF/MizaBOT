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
from components.gacha import Gacha
import cogs

import disnake
from disnake.ext import commands
import asyncio
import time
import concurrent.futures
import functools
from signal import SIGTERM, SIGINT
# conditional import
try:
    import uvloop # unix only
    uvloop.install()
except:
    pass

# Main Bot Class (overload commands.Bot)
class MizaBot(commands.Bot):
    def __init__(self):
        self.version = "9.20" # bot version
        self.changelog = [ # changelog lines
            "Please use `/bug_report` or the [help](https://mizagbf.github.io/MizaBOT/) if you have a problem",
            "`/mod announcement togglechannel` added to receive game or bot news",
            "GW Crew data displays top speed ( `/gbf crew`, `/gw crew`, `/gw find crew`)",
            "`/gw time` and `/db time` use your local system timezone",
            "You can input your current amount of tokens and opened boxes in `/gw box` and `/db box`",
            "`/gbfg ranking` has a speed option (to get a speed ranking)",
            "Added `/gbfg playerranking`"
        ]
        self.running = True # is False when the bot is shutting down
        self.booted = False # goes up to True after the first on_ready event
        self.tasks = {} # contain our user tasks
        self.cogn = 0 # number of cog loaded
        self.errn = 0 # number of internal errors
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
        self.gacha = Gacha(self)
        
        # loading data
        self.data.loadConfig()
        for i in range(0, 50): # try multiple times in case google drive is unresponsive
            if self.drive.load(): break # attempt to download the save file
            elif i == 49:
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
        self.gacha.init()

        # init base class
        super().__init__(case_insensitive=True, description="MizaBOT version {}\n[Source code](https://github.com/MizaGBF/MizaBOT)▫️[Online Command List](https://mizagbf.github.io/MizaBOT/)".format(self.version), help_command=None, owner=self.data.config['ids']['owner'], max_messages=None, intents=disnake.Intents.default())
        self.add_app_command_check(self.global_check, slash_commands=True, user_commands=True, message_commands=True)

    """go()
    Main Bot Loop
    
    Returns
    --------
    int: Exit value
    """
    def go(self):
        self.cogn, failed = cogs.load(self) # load cogs
        if failed > 0:
            print(failed, "Main Cog(s) failed loading, please fix before continuing")
            return
        # graceful exit setup
        graceful_exit = self.loop.create_task(self.exit_gracefully())
        for s in [SIGTERM, SIGINT]:
            self.loop.add_signal_handler(s, graceful_exit.cancel)
        # main loop
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

    """exit_gracefully()
    Coroutine triggered when SIGTERM is received, to close the bot
    """
    async def exit_gracefully(self): # graceful exit (when SIGTERM is received)
        try:
            while self.running: # we wait until we receive the signal
                await asyncio.sleep(10000)
        except asyncio.CancelledError:
            self.running = False
            if self.data.pending:
                self.data.autosaving = False
                if self.data.saveData():
                    print('Autosave Success')
                else:
                    print('Autosave Failed')
            await self.close()
            exit(0)

    """isAuthorized()
    Check if the channel is set as Authorized by the auto clean up system.
    
    Parameters
    ----------
    inter: Command context, message or interaction
    
    Returns
    --------
    bool: True if authorized, False if not
    """
    def isAuthorized(self, inter): # check if the command is authorized in the channel
        id = str(inter.guild.id)
        if id in self.data.save['permitted']: # if id is found, it means the check is enabled
            if inter.channel.id in self.data.save['permitted'][id]:
                return True # permitted
            return False # not permitted
        return True # default

    """isServer()
    Check if the interaction is matching this server (server must be set in config.json)
    
    Parameters
    ----------
    inter: Command interaction
    id_string: Server identifier in config.json
    
    Returns
    --------
    bool: True if matched, False if not
    """
    def isServer(self, inter, id_string : str): # check if the interaction is in the targeted guild (guild id must be in config.json)
        if inter.guild.id == self.data.config['ids'].get(id_string, -1):
            return True
        return False

    """isChannel()
    Check if the interaction is matching this channel (channel must be set in config.json)
    
    Parameters
    ----------
    inter: Command interaction
    id_string: Channel identifier in config.json
    
    Returns
    --------
    bool: True if matched, False if not
    """
    def isChannel(self, inter, id_string : str): # check if the context is in the targeted channel (channel is must be in config.json)
        if inter.channel.id == self.data.config['ids'].get(id_string, -1):
            return True
        return False

    """isMod()
    Check if the interaction author has the manage message permission
    
    Parameters
    ----------
    inter: Command interaction
    
    Returns
    --------
    bool: True if it does, False if not
    """
    def isMod(self, inter): # check if the member has the manage_message permission
        if inter.author.guild_permissions.manage_messages or inter.author.id == self.owner.id:
            return True
        return False

    """isOwner()
    Check if the interaction author is the owner (id must be set in config.json)
    
    Parameters
    ----------
    inter: Command interaction
    
    Returns
    --------
    bool: True if it does, False if not
    """
    def isOwner(self, inter): # check if the member is the bot owner
        if inter.author.id == self.owner.id: # must be defined in config.json
            return True
        return False

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
    disnake.Message: The sent message or None if error
    """
    async def send(self, channel_name, msg : str = "", embed : disnake.Embed = None, file : disnake.File = None, view : disnake.ui.View = None): # send something to a registered channel
        try:
            return await self.channel.get(channel_name).send(msg, embed=embed, file=file, view=view)
        except Exception as e:
            self.errn += 1
            msg = str(self.util.pexc(e))
            if len(msg) > 4000: msg = msg[:4000] + "..."
            print("Channel {} error: {}".format(channel_name, msg))
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
    async def sendMulti(self, channel_names : list, msg : str = "", embed : disnake.Embed = None, file : disnake.File = None): # send to multiple registered channel at the same time
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
        msg = str(self.util.pexc(error))
        if len(msg) > 4000: msg = msg[:4000] + "..."
        await self.send('debug', embed=self.util.embed(title="Error in {}() {}".format(func_name, id), description=msg, timestamp=self.util.timestamp()))

    """on_ready()
    Event. Called on connection
    """
    async def on_ready(self): # called when the bot starts
        if not self.booted:
            # set our used channels for the send function
            self.channel.setMultiple([['debug', 'debug_channel'], ['image', 'image_upload'], ['debug_update', 'debug_update'], ['you_pinned', 'you_pinned'], ['gbfg_pinned', 'gbfg_pinned'], ['gbfglog', 'gbfg_log'], ['youlog', 'you_log']])
            await self.send('debug', embed=self.util.embed(title="{} is Ready".format(self.user.display_name), description=self.util.statusString(), thumbnail=self.user.display_avatar, timestamp=self.util.timestamp()))
            # check guilds and start the tasks
            self.booted = True
            await self.checkGuildList()
            await self.startTasks()

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
    def runTask(self, name, func):
        self.cancelTask(name)
        self.tasks[name] = self.loop.create_task(func())

    """cancelTask()
    Stop a bot task
    
    Parameters
    ----------
    name: Task identifier
    """
    def cancelTask(self, name):
        if name in self.tasks:
            try: self.tasks[name].cancel()
            except: pass

    """startTasks()
    Start all tasks from each cogs (if any)
    """
    async def startTasks(self):
        for c in self.cogs:
            try: self.get_cog(c).startTasks()
            except: pass
        msg = ""
        for t in self.tasks:
            msg += "\▫️ {}\n".format(t)
        if msg != "":
            await self.send('debug', embed=self.util.embed(title="{} user tasks started".format(len(self.tasks)), description=msg, timestamp=self.util.timestamp()))

    """checkGuild()
    Verify if the guild validate our requirements
    
    Parameters
    ----------
    guild: Discord Guild to check
    
    Returns
    ----------
    int: 0 if it's our debug server, 1 if it's banned, 2 if invite check failed, 3 if not enough members, 4 if ok
    """
    def checkGuild(self, guild):
        id = str(guild.id)
        if id == str(self.data.config['ids']['debug_server']) or int(id) in self.data.save['guilds']:
            return 0
        elif id in self.data.save['banned_guilds'] or self.ban.check(guild.owner_id, self.ban.OWNER): # ban check
            return 1
        elif 'invite' not in self.data.save or self.data.save['invite']['state'] == False or len(self.guilds) > self.data.save['invite']['limit']: # invite state check
            return 2
        elif guild.member_count <= 25: # member count check
            return 3
        else: # notify
            return 4

    """newGuildCheck()
    Used to check for new guilds.
    Call checkGuild(), do what's needed and return a value corresponding to it
    
    Parameters
    ----------
    guild: guild to check
    disable_leave: if True, the bot only alerts the owner if a new guild is up
    
    Returns
    ----------
    int: 1 is banned, 2 can't invite, 3 not enough members, 4 is new, everything else is ok
    """
    async def newGuildCheck(self, guild, disable_leave=False):
        ret = self.checkGuild(guild)
        try: icon = guild.icon.url
        except: icon = None
        match ret:
            case 1: # ban check
                await guild.leave()
            case 2: # invite state check
                if disable_leave:
                    await self.send('debug', embed=self.util.embed(title=guild.name + " added me", description=":warning: **It doesn't satisfy the Invite state check**\n**ID** ▫️ `{}`\n**Owner** ▫️ `{}`\n**Text Channels** ▫️ {}\n**Voice Channels** ▫️ {}\n**Members** ▫️ {}\n**Roles** ▫️ {}\n**Emojis** ▫️ {}\n**Boosted** ▫️ {}\n**Boost Tier** ▫️ {}".format(guild.id, guild.owner_id, len(guild.text_channels), len(guild.voice_channels), guild.member_count, len(guild.roles), len(guild.emojis), guild.premium_subscription_count, guild.premium_tier), thumbnail=icon, timestamp=guild.created_at))
                else:
                    try: await (await guild.get_or_fetch_member(guild.owner_id)).send(embed=self.util.embed(title="Error", description="Invitations are currently closed or the bot reached max capacity.", thumbnail=icon))
                    except: pass
                    await guild.leave()
            case 3: # member count check
                if disable_leave:
                    await self.send('debug', embed=self.util.embed(title=guild.name + " added me", description=":warning: **It doesn't satisfy the Member count check**\n**ID** ▫️ `{}`\n**Owner** ▫️ `{}`\n**Text Channels** ▫️ {}\n**Voice Channels** ▫️ {}\n**Members** ▫️ {}\n**Roles** ▫️ {}\n**Emojis** ▫️ {}\n**Boosted** ▫️ {}\n**Boost Tier** ▫️ {}".format(guild.id, guild.owner_id, len(guild.text_channels), len(guild.voice_channels), guild.member_count, len(guild.roles), len(guild.emojis), guild.premium_subscription_count, guild.premium_tier), thumbnail=icon, timestamp=guild.created_at))
                else:
                    try: await (await guild.get_or_fetch_member(guild.owner_id)).send(embed=self.util.embed(title="Error", description="The bot is currently limited to servers of at least 25 members.", thumbnail=icon))
                    except: pass
                    await guild.leave()
            case 4: # notify
                await self.send('debug', embed=self.util.embed(title=guild.name + " added me", description="**ID** ▫️ `{}`\n**Owner** ▫️ `{}`\n**Text Channels** ▫️ {}\n**Voice Channels** ▫️ {}\n**Members** ▫️ {}\n**Roles** ▫️ {}\n**Emojis** ▫️ {}\n**Boosted** ▫️ {}\n**Boost Tier** ▫️ {}".format(guild.id, guild.owner_id, len(guild.text_channels), len(guild.voice_channels), guild.member_count, len(guild.roles), len(guild.emojis), guild.premium_subscription_count, guild.premium_tier), thumbnail=icon, timestamp=guild.created_at))
            case _:
                pass
        return ret

    """checkGuildList()
    Check the server list (on startup) for new servers.
    This is just in case someone invites the bot while it's down.
    """
    async def checkGuildList(self):
        # initialization (for the first time)
        with self.data.lock:
            if self.data.save['guilds'] is None:
                self.data.save['guilds'] = []
                for g in self.guilds:
                    self.data.save['guilds'].append(g.id)
                    self.data.pending = True
        # list all the current guilds and check new ones
        try:
            current_guilds = []
            for g in self.guilds:
                if g.id not in self.data.save['guilds']:
                    ret = await self.newGuildCheck(g, True)
                    if ret not in [1, 2, 3]:
                        current_guilds.append(g.id)
                else:
                    current_guilds.append(g.id)
        except Exception as e:
            await self.sendError("checkGuildList", e)
            return
        with self.data.lock:
            if current_guilds != self.data.save['guilds']:
                self.data.save['guilds'] = current_guilds
                self.data.pending = True

    """on_guild_join()
    Event. Called when the bot join a guild
    
    Parameters
    ----------
    guild: Discord Guild
    """
    async def on_guild_join(self, guild):
        try:
            if await self.newGuildCheck(guild) == 4:
                with self.data.lock:
                    self.data.save['guilds'].append(guild.id)
                    self.data.pending = True
        except Exception as e:
            self.sendError('on_guild_join', e)

    """global_check()
    Check if the command is authorized to run
    
    Parameters
    ----------
    inter: Command context or interaction
    
    Returns
    --------
    bool: True if the command can be processed, False if not
    """
    async def global_check(self, inter): # called whenever a command is used
        if not self.running: return False # do nothing if the bot is stopped
        if inter.guild is None or isinstance(inter.channel, disnake.PartialMessageable): # if none or channel is PartialMessageable, the command has been sent via a direct message
            return False # so we ignore
        try:
            id = str(inter.guild.id)
            if self.ban.check(inter.author.id, self.ban.USE_BOT):
                return False
            elif id in self.data.save['banned_guilds'] or self.ban.check(inter.guild.owner_id, self.ban.OWNER) or inter.guild.owner_id in self.data.config['banned']: # ban check (3rd one is defined in config.json)
                await inter.guild.leave() # leave the server if banned
                return False
            elif not inter.channel.permissions_for(inter.author).send_messages:
                return False
            elif not inter.channel.permissions_for(inter.me).send_messages:
                return False
            return True
        except Exception as e:
            await self.sendError('global_check', e)
            return False

    """application_error_handling()
    Common function for on_error events.
    
    Parameters
    ----------
    inter: Command interaction
    error: Exception
    """
    async def application_error_handling(self, inter, error):
        msg = str(error)
        if msg.startswith('You are on cooldown.'):
            await inter.response.send_message(embed=self.util.embed(title="Command Cooldown Error", description=msg.replace('You are on cooldown.', 'This command is on cooldown.'), timestamp=self.util.timestamp()), ephemeral=True)
        elif msg.startswith('Too many people are using this command.'):
            await inter.response.send_message(embed=self.util.embed(title="Command Concurrency Error", description=msg.replace('Too many people are using this command, try again later'), timestamp=self.util.timestamp()), ephemeral=True)
        elif msg.find('check functions for command') != -1 or msg.find('NotFound: 404 Not Found (error code: 10062): Unknown interaction') != -1:
            return
        elif msg.find('required argument that is missing') != -1 or msg.startswith('Converting to "int" failed for parameter'):
            await inter.response.send_message(embed=self.util.embed(title="Command Argument Error", description="A required parameter is missing.", timestamp=self.util.timestamp()), ephemeral=True)
            return
        elif msg.find('Member "') == 0 or msg.find('Command "') == 0 or msg.startswith('Command raised an exception: Forbidden: 403'):
            try: await inter.response.send_message(embed=self.util.embed(title="Command Permission Error", description="It seems you can't use this command here", timestamp=self.util.timestamp()), ephemeral=True)
            except: pass
            return
        else:
            try: await inter.response.send_message(embed=self.util.embed(title="Command Error", description="An unexpected error occured. My owner has been notified.\nUse /bug_report if you have additional informations to provide", timestamp=self.util.timestamp()), ephemeral=True)
            except: pass
            self.errn += 1
            await self.send('debug', embed=self.util.embed(title="⚠ Error caused by {}".format(inter.author), description=self.util.pexc(error).replace('*', '\*'), thumbnail=inter.author.display_avatar, fields=[{"name":"Options", "value":'`{}`'.format(inter.options)}, {"name":"Server", "value":inter.author.guild.name}, {"name":"Message", "value":msg}], footer='{}'.format(inter.author.id), timestamp=self.util.timestamp()))

    """on_slash_command_error()
    Event. Called when a slash command raise an uncaught error
    
    Parameters
    ----------
    inter: Command interaction
    error: Exception
    """
    async def on_slash_command_error(self, inter, error):
        await self.application_error_handling(inter, error)

    """on_user_command_error()
    Event. Called when an user command raise an uncaught error
    
    Parameters
    ----------
    inter: Command interaction
    error: Exception
    """
    async def on_user_command_error(self, inter, error):
        await self.application_error_handling(inter, error)

    """on_message_command_error()
    Event. Called when a message command raise an uncaught error
    
    Parameters
    ----------
    inter: Command interaction
    error: Exception
    """
    async def on_message_command_error(self, inter, error):
        await self.application_error_handling(inter, error)

    """on_raw_reaction_add()
    Event. Called when a new reaction is added by an user
    
    Parameters
    ----------
    payload: Raw payload
    """
    async def on_raw_reaction_add(self, payload):
        await self.pinboard.check(payload)


if __name__ == "__main__":
    bot = MizaBot()
    bot.go()