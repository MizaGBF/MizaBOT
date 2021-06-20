from components.data import Data
from components.drive import Drive
from components.util import Util
from components.gbf import GBF
from components.twitter import Twitter
from components.pinboard import Pinboard
from components.emote import Emote
from components.help import Help
from components.calc import Calc
from components.channel import Channel
from components.file import File
from components.sql import SQL
from components.ranking import Ranking
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
    
    discord.py 2.0 breaking changes:
    https://github.com/Rapptz/discord.py/projects/3
        * remove bot.logout() calls
        * check the custom help
        * remove permissions_in
        * check timestamp timezone
"""

# Main Bot Class (overload commands.Bot)
class MizaBot(commands.Bot):
    def __init__(self):
        self.version = "8.0-beta-4" # bot version
        self.changelog = [ # changelog lines
            "**This MizaBOT version is a Beta**, please use `$bug_report` if you see anything wrong",
            "Online command list added [here](https://mizagbf.github.io/MizaBOT/)",
            "Removed `$lightchad` (until next time...)",
            "Added `$zeroroll`",
            "Added `$belial`",
            "Reworked `$profile`",
            "Added `$addRoll`",
            "Added `$dice`, `$8ball` and `$coin`"
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

        # graceful exit
        signal.signal(signal.SIGTERM, self.exit_gracefully) # SIGTERM is called by heroku when shutting down

        # intents (for guilds and stuff)
        intents = discord.Intents.default()
        intents.members = True
        
        # init base class
        super().__init__(command_prefix=self.prefix, case_insensitive=True, description="MizaBOT version {}\n[Source code](https://github.com/MizaGBF/MizaBOT)\n[Command List](https://mizagbf.github.io/MizaBOT/)\nDefault command prefix is `$`, use `$setPrefix` to change it on your server.".format(self.version), help_command=Help(), owner=self.data.config['ids']['owner'], max_messages=None, intents=intents)

    def go(self): # main loop
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
                    print("Main Loop Exception:\n" + self.bot.util.pexc(e))
        if self.data.saveData():
            print('Autosave Success')
        else:
            print('Autosave Failed')
        return self.retcode

    def exit_gracefully(self, signum, frame): # graceful exit (when SIGTERM is received)
        self.running = False
        if self.data.pending:
            self.data.autosaving = False
            if self.data.saveData():
                print('Autosave Success')
            else:
                print('Autosave Failed')
        exit(self.retcode)

    def prefix(self, client, message): # command prefix check
        try:
            return self.data.save['prefixes'][str(message.guild.id)] # get the guild prefix if set
        except:
            return '$' # else, return the default prefix $

    def isAuthorized(self, ctx): # check if the command is authorized in the channel
        id = str(ctx.guild.id)
        if id in self.data.save['permitted']: # if id is found, it means the check is enabled
            if ctx.channel.id in self.data.save['permitted'][id]:
                return True # permitted
            return False # not permitted
        return True # default

    def isServer(self, ctx, id_string : str): # check if the context is in the targeted guild (guild id must be in config.json)
        if ctx.message.author.guild.id == self.data.config['ids'].get(id_string, -1):
            return True
        return False

    def isChannel(self, ctx, id_string : str): # check if the context is in the targeted channel (channel is must be in config.json)
        if ctx.channel.id == self.data.config['ids'].get(id_string, -1):
            return True
        return False

    def isMod(self, ctx): # check if the member has the manage_message permission
        if ctx.author.guild_permissions.manage_messages or ctx.author.id == self.data.config['ids'].get('owner', -1):
            return True
        return False

    def isOwner(self, ctx): # check if the member is the bot owner
        if ctx.message.author.id == self.data.config['ids'].get('owner', -1): # must be defined in config.json
            return True
        return False

    async def callCommand(self, ctx, command, *args, **kwargs): #call a command from another cog or command
        for cn in self.cogs:
            cmds = self.get_cog(cn).get_commands()
            for cm in cmds:
                if cm.name == command:
                    await ctx.invoke(cm, *args, **kwargs)
                    return
        raise Exception("Command `{}` not found".format(command))

    async def send(self, channel_name : str, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send something to a registered channel
        try:
            return await self.channel.get(channel_name).send(msg, embed=embed, file=file)
        except Exception as e:
            self.errn += 1
            print("Channel {} error: {}".format(channel_name, self.bot.util.pexc(e)))
            return None

    async def sendMulti(self, channel_names : list, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send to multiple registered channel at the same time
        r = []
        for c in channel_names:
            try:
                r.append(await self.send(c, msg, embed, file))
            except:
                await self.sendError('sendMulti', 'Failed to send a message to channel `{}`'.format(c))
                r.append(None)
        return r

    async def sendError(self, func_name : str, error, id = None): # send an error to the debug channel
        if str(error).startswith("403 FORBIDDEN"): return # I'm tired of those errors because people didn't set their channel permissions right so I ignore it
        if self.errn >= 30: return # disable error messages if too many messages got sent
        if id is None: id = ""
        else: id = " {}".format(id)
        self.errn += 1
        await self.send('debug', embed=self.util.embed(title="Error in {}() {}".format(func_name, id), description=self.util.pexc(error), timestamp=self.util.timestamp()))

    async def on_ready(self): # called when the bot starts
        if not self.booted:
            # set our used channels for the send function
            self.channel.setMultiple([['debug', 'debug_channel'], ['image', 'image_upload'], ['debug_update', 'debug_update'], ['you_pinned', 'you_pinned'], ['gbfg_pinned', 'gbfg_pinned'], ['gbfglog', 'gbfg_log'], ['youlog', 'you_log']])
            await self.send('debug', embed=self.util.embed(title="{} is Ready".format(self.user.display_name), description=self.util.statusString(), thumbnail=self.user.avatar_url, timestamp=self.util.timestamp()))
            # start the task
            await self.startTasks()
            self.booted = True

    async def do(self, func, *args, **kwargs): # routine to run blocking code in a separate thread
        return await self.loop.run_in_executor(self.executor, functools.partial(func, *args, **kwargs))

    def doAsync(self, coro): # add a task to the event loop (return the task)
        return self.loop.create_task(coro)

    def doAsTask(self, coro): # run a coroutine from a normal function (slow, don't abuse it for small functions)
        task = self.doAsync(coro)
        while not task.done(): # NOTE: is there a way to make it faster?
            time.sleep(0.01)
        return task.result()

    def runTask(self, name, func): # start a task (cancel a previous one with the same name)
        self.cancelTask(name)
        self.tasks[name] = self.loop.create_task(func())

    def cancelTask(self, name): # cancel a task
        if name in self.tasks:
            self.tasks[name].cancel()

    async def startTasks(self): # start all our tasks
        for c in self.cogs:
            try: self.get_cog(c).startTasks()
            except: pass
        msg = ""
        for t in self.tasks:
            msg += "\▫️ {}\n".format(t)
        if msg != "":
            await bot.send('debug', embed=bot.util.embed(title="{} user tasks started".format(len(self.tasks)), description=msg, timestamp=self.util.timestamp()))

    async def on_message(self, message): # to do something with a message
        if self.running: # don't process commands if exiting
            await self.process_commands(message) # never forget this line

    async def on_guild_join(self, guild): # when the bot joins a new guild
        id = str(guild.id)
        if id == str(self.data.config['ids']['debug_server']):
            return
        elif id in self.data.save['guilds']['banned'] or str(guild.owner.id) in self.data.save['guilds']['owners']: # leave if the server is blacklisted
            try:
                await self.send('debug', embed=self.util.embed(title="Banned guild request", description="{} ▫️ {}".format(guild.name, id), thumbnail=guild.icon_url, footer="Owner: {} ▫️ {}".format(guild.owner.name, guild.owner.id)))
            except Exception as e:
                await self.sendError("on_guild_join", e)
            await guild.leave()
        else: # notify me and add to the pending servers
            self.data.save['guilds']['pending'][id] = guild.name
            self.data.pending = True
            await guild.owner.send(embed=self.util.embed(title="Pending guild request", description="Wait until my owner approve the new server", thumbnail=guild.icon_url))
            await self.send('debug', embed=self.util.embed(title="Pending guild request", description="{} ▫️ {}\nUse `$accept {}` or `$refuse {}`".format(guild.name, id, id, id), thumbnail=guild.icon_url, footer="Owner: {} ▫️ {}".format(guild.owner.name, guild.owner.id)))

    async def global_check(self, ctx): # called whenever a command is used
        if ctx.guild is None: # if none, the command has been sent via a direct message
            return False # so we ignore
        try:
            id = str(ctx.guild.id)
            if id in self.data.save['guilds']['banned'] or str(ctx.guild.owner.id) in self.data.save['guilds']['owners']: # ban check
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
            await self.send('debug', embed=self.util.embed(title="⚠ Error caused by {}".format(ctx.message.author), thumbnail=ctx.author.avatar_url, fields=[{"name":"Command", "value":'`{}`'.format(ctx.message.content)}, {"name":"Server", "value":ctx.message.author.guild.name}, {"name":"Message", "value":msg}], footer='{}'.format(ctx.message.author.id), timestamp=self.util.timestamp()))

    # call the pinboard system when a reaction is received
    async def on_raw_reaction_add(self, payload):
        await self.pinboard.check(payload)

    # under is the log system used by my crew and another server, remove if you don't need those
    # it's a sort of live audit log

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

    async def on_member_remove(self, member):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if member.guild.id in guilds:
            await self.send(guilds[member.guild.id], embed=self.util.embed(author={'name':"{} ▫️ Left the server".format(member.name), 'icon_url':member.avatar_url}, footer="User ID: {}".format(member.id), timestamp=self.util.timestamp(), color=0xff0000))

    async def on_member_join(self, member):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if member.guild.id in guilds:
            channel = guilds[member.guild.id]
            await self.send(channel, embed=self.util.embed(author={'name':"{} ▫️ Joined the server".format(member.name), 'icon_url':member.avatar_url}, footer="User ID: {}".format(member.id), timestamp=self.util.timestamp(), color=0x00ff3c))

    async def on_member_ban(self, guild, user):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if guild.id in guilds:
            await self.send(guilds[guild.id], embed=self.util.embed(author={'name':"{} ▫️ Banned from the server".format(user.name), 'icon_url':user.avatar_url}, footer="User ID: {}".format(user.id), timestamp=self.util.timestamp(), color=0xff0000))

    async def on_member_unban(self, guild, user):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if guild.id in guilds:
            await self.send(guilds[guild.id], embed=self.util.embed(author={'name':"{} ▫️ Unbanned from the server".format(user.name), 'icon_url':user.avatar_url}, footer="User ID: {}".format(user.id), timestamp=self.util.timestamp(), color=0x00ff3c))

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

    async def on_guild_role_create(self, role):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if role.guild.id in guilds:
            channel = guilds[role.guild.id]
            await self.send(channel, embed=self.util.embed(title="Role created ▫️ `{}`".format(role.name), footer="Role ID: {}".format(role.id), timestamp=self.util.timestamp(), color=0x00ff3c))

    async def on_guild_role_delete(self, role):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if role.guild.id in guilds:
            channel = guilds[role.guild.id]
            await self.send(channel, embed=self.util.embed(title="Role deleted ▫️ `{}`".format(role.name), footer="Role ID: {}".format(role.id), timestamp=self.util.timestamp(), color=0xff0000))

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

    async def on_guild_channel_create(self, channel):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if channel.guild.id in guilds:
            await self.send(guilds[channel.guild.id], embed=self.util.embed(title="Channel created ▫️ `{}`".format(channel.name), footer="Channel ID: {}".format(channel.id), timestamp=self.util.timestamp(), color=0xebe007))

    async def on_guild_channel_delete(self, channel):
        if 'you_server' not in self.data.config['ids'] or 'gbfg' not in self.data.config['ids']: return
        guilds = {self.data.config['ids']['you_server'] : 'youlog', self.data.config['ids']['gbfg'] : 'gbfglog'}
        if channel.guild.id in guilds:
            await self.send(guilds[channel.guild.id], embed=self.util.embed(title="Channel deleted ▫️ `{}`".format(channel.name), footer="Channel ID: {}".format(channel.id), timestamp=self.util.timestamp(), color=0x8a8306))


if __name__ == "__main__":
    bot = MizaBot()
    exit(bot.go())