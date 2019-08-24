import discord
from discord.ext import commands
import asyncio
import signal
import json
import random
from datetime import datetime, timedelta
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import itertools
import psutil
import time
import cogs # our cogs folder
import logging

#logging.basicConfig(level=logging.INFO)

# ########################################################################################
# custom help command used by the bot
class MizabotHelp(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__()
        self.dm_help = True # force dm only (although our own functions only send in dm, so it should be unneeded)

    async def send_bot_help(self, mapping): # main help command (called when you do $help). this function reuse the code from the commands.DefaultHelpCommand class
        ctx = self.context # get $help context
        bot = ctx.bot
        me = ctx.author.guild.me # bot own user infos

        if not await bot.react(ctx, 'time'):
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="Unblock me to receive the Help"))
            return

        if bot.description: # send the bot description first
            try:
                await ctx.author.send(embed=bot.buildEmbed(title=me.name + " Help", description=bot.description, thumbnail=me.avatar_url)) # author.send = dm
            except:
                await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                return

        no_category = "No Category:"
        def get_category(command, *, no_category=no_category): # function to retrieve the command category
            cog = command.cog
            return cog.qualified_name + ':' if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category) # sort all category and commands
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, commands in to_iterate: # iterate on them
            if category != no_category:
                commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands) # sort
                embed = discord.Embed(title=bot.getEmoteStr('mark') + " **" + category[:-1] + "** Category", color=random.randint(0, 16777216)) # make an embed, random color
                for c in commands: # fill the embed fields with the command infos
                    embed.add_field(name=c.name + " ▫ " + self.get_command_signature(c), value=c.short_doc, inline=False)
                    if len(embed) > 5800 or len(embed.fields) > 24: # embeds have a 6000 and 25 fields characters limit, I send and make a new embed if needed
                        try:
                            await ctx.author.send(embed=embed) # author.send = dm
                        except:
                            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                            return
                        embed = discord.Embed(title=bot.getEmoteStr('mark') + " **" + category[:-1] + "** Category", color=embed.colour)
                if len(embed.fields) > 0: # only send if there is at least one field
                    try:
                        await ctx.author.send(embed=embed) # author.send = dm
                    except:
                        await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                        return

        # final words
        await ctx.author.send(embed=bot.buildEmbed(title=bot.getEmoteStr('question') + " Need more help?", description="Use help <command name>\nOr help <category name>"))

        await bot.unreact(ctx, 'time')
        await ctx.message.add_reaction('✅') # white check mark

    async def send_command_help(self, command): # same thing, but for a command ($help <command>)
        ctx = self.context
        bot = ctx.bot
        if not await bot.react(ctx, 'time'):
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="Unblock me to receive the Help"))
            return

        # send the help
        embed = discord.Embed(title=bot.getEmoteStr('mark') + " **" + command.name + "** Command", description=command.help, color=random.randint(0, 16777216)) # random color
        embed.add_field(name="Usage", value=self.get_command_signature(command), inline=False)

        try:
            await ctx.author.send(embed=embed) # author.send = dm
        except:
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
            return

        await bot.unreact(ctx, 'time')
        await self.context.message.add_reaction('✅') # white check mark

    async def send_cog_help(self, cog): # category help ($help <category)
        ctx = self.context
        bot = ctx.bot
        await ctx.message.add_reaction('✅') # white check mark

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands) # sort
        embed = discord.Embed(title=bot.getEmoteStr('mark') + " **" + cog.qualified_name + "** Category", description=cog.description, color=random.randint(0, 16777216)) # random color
        for c in filtered:
            embed.add_field(name=c.name + " ▫ " + self.get_command_signature(c), value=c.short_doc, inline=False)
            if len(embed) > 5800 or len(embed.fields) > 24: # embeds have a 6000 and 25 fields characters limit, I send and make a new embed if needed
                try:
                    await ctx.author.send(embed=embed) # author.send = dm
                except:
                    await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                    return
                embed = discord.Embed(title=bot.getEmoteStr('mark') + " **" + cog.qualified_name + "** Category", description=cog.description, color=embed.colour)
        if len(embed.fields) > 0:
            try:
                await ctx.author.send(embed=embed) # author.send = dm
            except:
                await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                return

        await bot.unreact(ctx, 'time')
        await self.context.message.add_reaction('✅') # white check mark

# #####################################################################################
# Google Drive Access (to save/load the data)
class MizabotDrive():
    def __init__(self, bot):
        self.saving = False
        self.bot = bot # it's the bot

    def login(self): # check credential, update if needed. Run this function on your own once to get the json, before pushing it to heroku
        try:
            gauth = GoogleAuth()
            gauth.LoadCredentialsFile("credentials.json") # load credentials
            if gauth.credentials is None: # if failed, get them
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired: # or if expired, refresh
                gauth.Refresh()
            else:
                gauth.Authorize() # good
            gauth.SaveCredentialsFile("credentials.json") # save
            return GoogleDrive(gauth)
        except Exception as e:
            print('Exception: ' + str(e))
            return None

    def load(self): # load save.json from the folder id in bot.tokens
        if self.saving: return False
        drive = self.login()
        if not drive: return False
        try:
            file_list = drive.ListFile({'q': "'" + self.bot.tokens['drive'] + "' in parents and trashed=false"}).GetList() # get the file list in our folder
            for s in file_list:
                if s['title'] == "save.json": s.GetContentFile(s['title']) # iterate until we find save.json and download it
            return True
        except Exception as e:
            print(e)
            self.saving = False
            return False

    def save(self, data, sortBackup): # write save.json to the folder id in bot.tokens
        if self.saving: return False
        drive = self.login()
        if not drive: return False
        try:
            self.saving = True
            # backup
            file_list = drive.ListFile({'q': "'" + self.bot.tokens['drive'] + "' in parents and trashed=false"}).GetList()
            if sortBackup and len(file_list) > 9: # delete if we have too many backups
                for f in file_list:
                    if f['title'].find('backup') == 0:
                        f.Delete()
            for f in file_list: # rename the previous save
                if f['title'] == "save.json":
                    f['title'] = "backup_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
                    f.Upload()
            # saving
            s = drive.CreateFile({'title':'save.json', 'mimeType':'text/JSON', "parents": [{"kind": "drive#file", "id": self.bot.tokens['drive']}]})
            s.SetContentString(data)
            s.Upload()
            self.saving = False
            return True
        except Exception as e:
            print(e)
            self.saving = False
            return False

# #####################################################################################
# Bot
class Mizabot(commands.Bot):
    def __init__(self):
        self.running = True
        self.boot_flag = False
        self.starttime = datetime.utcnow() # used to check the uptime
        self.process = psutil.Process() # script process
        self.process.cpu_percent() # called once to initialize
        self.errn = 0 # count the number of errors
        self.cogn = 0 # will store how many cogs are expected to be in memory
        self.exit_flag = False # set to true when sigterm is received
        self.savePending = False # set to true when a change is made to a variable
        self.tasks = {} # store my tasks
        self.autosaving = False # set to true during a save
        self.drive = MizabotDrive(self) # google drive instance
        self.channels = {} # store my channels
        self.newserver = {'servers':[], 'owners':[], 'pending':{}} # banned servers, banned owners, pending servers
        self.gw = {'state':False} # guild war data
        self.maintenance = {"state" : False, "time" : None, "duration" : "0"} # gbf maintenance data
        self.spark = [{}, []] # user spark data, banned users
        self.stream = {'time':None, 'content':[]} # stream command content
        self.schedule = [] # gbf schedule
        self.prefixes = {} # guild prefixes
        self.st = {} # guild strike times
        self.bot_maintenance = None # bot maintenance day
        self.reminders = {} # user reminders
        self.tokens = {} # bot tokens
        self.baguette = {} # secret, config
        self.baguette_save = {} # secret, save
        self.ids = {} # discord ids used by the bot
        self.permitted = {} # guild permitted channels
        self.news = {} # guild news channels
        self.games = {} # bot status messages
        self.strings = {} # bot strings
        self.specialstrings = {} # bot special strings
        self.emotes = {} # bot custom emotes
        # /gbfg/ game
        self.pitroulette = False
        self.pitroulettevictim = []
        self.pitroulettelist = []
        self.pitroulettecount = 0
        self.pitroulettemax = 0
        # load
        self.loadConfig()
        for i in range(0, 100): # try multiple times in case google drive is unresponsive
            if self.drive.load(): break
            elif i == 99: exit(3)
            time.sleep(20)
        if not self.load(): exit(2) # first loading must success
        super().__init__(command_prefix=self.prefix, case_insensitive=True, description='''MizaBOT version 5.21
Source code: https://github.com/MizaGBF/MizaBOT.
Default command prefix is '$', use $setPrefix to change it on your server.''', help_command=MizabotHelp(), activity=discord.activity.Game(name='Booting up, please wait'), owner=self.ids['owner'])

    def loadCog(self, *cog_classes):
        for c in cog_classes:
            try:
                self.add_cog(cogs.cog_get(c, self))
            except Exception as e:
                print("import " + c + ": " + str(e))
                self.errn += 1
            self.cogn += 1

    def mainLoop(self): # main loop
        while self.running:
            try:
                self.loop.run_until_complete(self.start(self.tokens['discord']))
            except Exception as e: # handle exceptions here to avoid the bot dying
                if self.savePending:
                    self.save(False)
                self.errn += 1
                print("Main Loop Exception: " + str(e))
        if self.save():
            print('Autosave Success')
        else:
            print('Autosave Failed')

    def prefix(self, client, message): # command prefix check
        try:
            id = str(message.guild.id)
            if id in self.prefixes:
                return self.prefixes[id] # retrieve the prefix used by the server
        except:
            pass
        return '$' # else, return default prefix is $

    def json_deserial_array(self, array): # deserialize a list from a json
        a = []
        for v in array:
            if isinstance(v, list):
                a.append(self.json_deserial_array(v))
            elif isinstance(v, dict):
                a.append(self.json_deserial_dict(list(v.items())))
            elif isinstance(v, str):
                try:
                    a.append(datetime.strptime(v, "%Y-%m-%dT%H:%M:%S")) # needed for datetimes
                except ValueError:
                    a.append(v)
            else:
                a.append(v)
        return a

    def json_deserial_dict(self, pairs): # deserialize a dict from a json
        d = {}
        for k, v in pairs:
            if isinstance(v, list):
                d[k] = self.json_deserial_array(v)
            elif isinstance(v, dict):
                d[k] = self.json_deserial_dict(list(v.items()))
            elif isinstance(v, str):
                try:
                    d[k] = datetime.strptime(v, "%Y-%m-%dT%H:%M:%S") # needed for datetimes
                except ValueError:
                    d[k] = v
            else:
                d[k] = v
        return d

    def json_serial(self, obj): # serialize everything including datetime objects
        if isinstance(obj, datetime):
            return obj.replace(microsecond=0).isoformat()
        raise TypeError ("Type %s not serializable" % type(obj))

    def loadConfig(self): # pretty simple
        try:
            with open('config.json') as f:
                data = json.load(f, object_pairs_hook=self.json_deserial_dict) # deserializer here
                self.tokens = data['tokens']
                self.baguette = data['baguette']
                self.ids = data['ids']
                self.games = data['games']
                self.strings = data['strings']
                self.specialstrings = data['specialstrings']
                self.emotes = data['emotes']
        except Exception as e:
            print('loadConfig(): ' + str(e))
            exit(1) # instant quit if error

    def load(self): # same thing but for save.json
        try:
            with open('save.json') as f:
                data = json.load(f, object_pairs_hook=self.json_deserial_dict) # deserializer here
                # more check to avoid issues when reloading the file during runtime, if new data was added
                if 'newserver' in data: self.newserver = data['newserver']
                else: self.newserver = {'servers':[], 'owners':[], 'pending':{}}
                if 'prefixes' in data: self.prefixes = data['prefixes']
                else: self.prefixes = {}
                if 'baguette_save' in data: self.baguette_save = data['baguette_save']
                else: self.baguette_save = {}
                if 'bot_maintenance' in data: self.bot_maintenance = data['bot_maintenance']
                else: self.bot_maintenance = None
                if 'maintenance' in data:
                    if data['maintenance']['state'] == True:
                        self.maintenance = data['maintenance']
                    else:
                        self.maintenance = {"state" : False, "time" : None, "duration" : 0}
                if 'stream' in data: self.stream = data['stream']
                else: self.stream = {'time':None, 'content':[]}
                if 'schedule' in data: self.schedule = data['schedule']
                else: self.schedule = []
                if 'st' in data: self.st = data['st']
                else: self.st = {}
                if 'spark' in data: self.spark = data['spark']
                else: self.spark = [{}, []]
                if 'gw' in data: self.gw = data['gw']
                else: self.gw = {}
                if 'reminders' in data: self.reminders = data['reminders']
                else: self.reminders = {}
                if 'permitted' in data: self.permitted = data['permitted']
                else: self.permitted = {}
                if 'news' in data: self.news = data['news']
                else: self.news = {}
                return True
        except Exception as e:
            self.errn += 1
            print('load(): ' + str(e))
            return False

    def save(self, sortBackup=True): # saving
        try:
            with open('save.json', 'w') as outfile:
                data = {}
                data['newserver'] = self.newserver
                data['prefixes'] = self.prefixes
                data['baguette_save'] = self.baguette_save
                data['bot_maintenance'] = self.bot_maintenance
                data['maintenance'] = self.maintenance
                data['stream'] = self.stream
                data['schedule'] = self.schedule
                data['st'] = self.st
                data['spark'] = self.spark
                data['gw'] = self.gw
                data['reminders'] = self.reminders
                data['news'] = self.news
                data['permitted'] = self.permitted
                json.dump(data, outfile, default=self.json_serial) # locally first
                if not self.drive.save(json.dumps(data, default=self.json_serial), sortBackup): # sending to the google drive
                    raise Exception("Couldn't save to google drive")
            return True
        except Exception as e:
            self.errn += 1
            print('save(): ' + str(e))
            return False

    async def autosave(self, discordDump = False): # called when savePending is true by statustask()
        if self.autosaving: return
        self.autosaving = True
        await self.send('debug', embed=self.buildEmbed(title="Autosaving...", timestamp=datetime.utcnow()))
        if self.save():
            await self.send('debug', embed=self.buildEmbed(title="Autosave Success", timestamp=datetime.utcnow()))
            self.savePending = False
        else:
            await self.send('debug', embed=self.buildEmbed(title="Autosave Failed", timestamp=datetime.utcnow()))
            discordDump = True
        if discordDump:
            try:
                with open('save.json', 'r') as infile:
                    await self.send('debug', 'save.json', file=discord.File(infile))
            except Exception as e:
                pass
        self.autosaving = False

    async def statustask(self): # background task changing the bot status and calling autosave()
        await self.send('debug', embed=self.buildEmbed(title="statustask() started", timestamp=datetime.utcnow()))
        while True:
            try:
                await asyncio.sleep(2400)
                await self.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=random.choice(self.games)))
                # check if it's time for the bot maintenance for me (every 2 weeks or so)
                c = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                if self.bot_maintenance and c > self.bot_maintenance and (c.day == 1 or c.day == 17):
                    await self.send('debug', self.get_user(self.ids['owner']).mention + " ▪ Time for maintenance!")
                    self.bot_maintenance = c
                    self.savePending = True
                # autosave
                if self.savePending and not self.exit_flag:
                    await self.autosave()
            except asyncio.CancelledError:
                await self.sendError('statustask', 'cancelled')
                return
            except Exception as e:
                await self.sendError('statustask', str(e))

    async def youinvite(self): # background task to track the invites of the (You) server
        await asyncio.sleep(2)
        await self.send('debug', embed=self.buildEmbed(title="youinvite() started", timestamp=datetime.utcnow()))
        g = self.get_guild(self.ids['you_server'])
        res = await g.invites()
        invites = {}
        for i in res:
            invites[i.code] = i

        while True:
            try:
                await asyncio.sleep(50)
                res = await g.invites()
                currents = {}
                for i in res:
                    currents[i.code] = i

                for i in currents:
                    if i in invites:
                        if currents[i].uses is not None and currents[i].uses != invites[i].uses:
                            if currents[i].max_uses is None:
                                await self.send('youlog', embed=bot.buildEmbed(title="Invite `" + i + "` used", description="**Uses:** " + str(currents[i].uses), timestamp=datetime.utcnow(), color=0xfcba03))
                            else:
                                await self.send('youlog', embed=bot.buildEmbed(title="Invite `" + i + "` used", description="**Uses:** " + str(currents[i].uses) + " / " + str(currents[i].max_uses), timestamp=datetime.utcnow(), color=0xfcba03))
                    else:
                        msg = ""
                        if currents[i].max_uses != 0: msg += "**Max uses:** " + str(currents[i].max_uses) + "\n"
                        if currents[i].inviter is not None:
                            msg += "**Inviter:** " + str(currents[i].inviter) + "\n"
                        if currents[i].max_age != 0:
                            if currents[i].max_age < 3600: msg += "**Duration:** " + str(currents[i].max_age // 60) + " minutes\n"
                            else: msg += "**Duration:** " + str(currents[i].max_age // 3600) + " hours\n"
                        msg += "**Channel:** " + currents[i].channel.name + "\n"
                        msg += "**Url:** " + str(currents[i].url) + "\n"
                        await self.send('youlog', embed=bot.buildEmbed(title="New Invite ▪ `" + i + "`", description=msg, timestamp=datetime.utcnow(), color=0xfcba03))

                for i in invites:
                    if i not in currents:
                        await self.send('youlog', embed=bot.buildEmbed(title="Revoked Invite ▪ `" + i + "`", timestamp=datetime.utcnow(), color=0xfcba03))

                invites = currents
            except asyncio.CancelledError:
                await self.sendError('youinvite', 'cancelled')
                return
            except Exception as e:
                await self.sendError('youinvite', str(e))
                invites = currents

    def isAuthorized(self, ctx): # check if the command is authorized
        id = str(ctx.guild.id)
        if id in self.permitted:
            if ctx.channel.id in self.permitted[id]:
                return True
            return False
        return True

    def isYouServer(self, ctx): # check if the context is in the (You) guild
        if ctx.message.author.guild.id == self.ids['you_server']:
            return True
        return False

    def isDebugServer(self, ctx): # check if the context is in the debug guild
        if ctx.message.author.guild.id == self.ids['debug_server']:
            return True
        return False

    def isMod(self, ctx): # check if the member has the manage_message permission
        if ctx.author.guild_permissions.manage_messages or ctx.author.id == self.ids['owner']:
            return True
        return False

    def isOwner(self, ctx):
        if ctx.message.author.id == self.ids['owner']:
            return True
        return False

    def getEmote(self, key): # retrieve a custom emote
        if key in self.emotes:
            try:
                return self.get_emoji(self.emotes[key]) # ids are defined in config.json
            except:
                return None
        return None

    def getEmoteStr(self, key): # same but we get the string equivalent
        e = self.getEmote(key)
        if e is None: return ""
        return str(e)

    async def react(self, ctx, key): # add a reaction using a custom emote defined in config.json
        try:
            await ctx.message.add_reaction(self.getEmote(key))
            return True
        except Exception as e:
            await self.sendError('react', str(e))
            return False

    async def unreact(self, ctx, key): # remove a reaction using a custom emote defined in config.json
        try:
            await ctx.message.remove_reaction(self.getEmote(key), ctx.guild.me)
            return True
        except Exception as e:
            await self.sendError('unreact', str(e))
            return False

    def buildEmbed(self, **options): # make a full embed
        embed = discord.Embed(title=options.get('title'), description=options.pop('description', ""), url=options.pop('url', ""), color=options.pop('color', random.randint(0, 16777216)))
        fields = options.pop('fields', [])
        inline = options.pop('inline', False)
        for f in fields:
            embed.add_field(name=f.get('name'), value=f.get('value'), inline=f.pop('inline', inline))
        buffer = options.pop('thumbnail', None)
        if buffer is not None: embed.set_thumbnail(url=buffer)
        buffer = options.pop('footer', None)
        if buffer is not None: embed.set_footer(text=buffer)
        buffer = options.pop('image', None)
        if buffer is not None: embed.set_image(url=buffer)
        buffer = options.pop('timestamp', None)
        if buffer is not None: embed.timestamp=buffer
        if 'author' in options:
            embed.set_author(name=options['author'].pop('name', ""), url=options['author'].pop('url', ""), icon_url=options['author'].pop('icon_url', ""))
        return embed

    def runTask(self, name, func): # start a task (cancel a previous one with the same name)
        self.cancelTask(name)
        self.tasks[name] = self.loop.create_task(func())

    def cancelTask(self, name): # cancel a task
        if name in self.tasks:
            self.tasks[name].cancel()

    def startTasks(self): # start our tasks
        self.runTask('status', self.statustask)
        self.runTask('youinvite', self.youinvite)
        for c in self.cogs:
            try:
                self.get_cog(c).startTasks()
            except:
                pass

    def setChannel(self, name, id_key : str): # "register" a channel to use with send()
        try:
            c = self.get_channel(self.ids[id_key])
            if c is not None: self.channels[name] = c
        except:
            self.errn += 1
            print("Invalid key: " + id_key)

    def setChannelID(self, name, id : int): # same but using an id instead of an id defined in config.json
        try:
            c = self.get_channel(id)
            if c is not None: self.channels[name] = c
        except:
            self.errn += 1
            print("Invalid ID: " + str(id))

    async def callCommand(self, ctx, command, cog, *args, **kwargs): #call a command in a cog
        cmds = self.get_cog(cog).get_commands()
        for c in cmds:
            if c.name == command:
                await ctx.invoke(c, *args, **kwargs)
                return
        raise Exception("Command `" + command + "` not found")

    async def send(self, channel_name : str, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send something to a channel
        try:
            await self.channels[channel_name].send(msg, embed=embed, file=file)
        except Exception as e:
            self.errn += 1
            print(channel_name + " error: " + str(e))

    async def sendError(self, func_name : str, msg : str, id = None): # send an error to the debug channel
        if self.errn >= 50: return # disable error messages if too many messages got sent
        if id is None: id = ""
        else: id = " " + str(id)
        self.errn += 1
        await self.send('debug', embed=self.buildEmbed(title="Error in " + func_name + "()" + id, description=msg, timestamp=datetime.utcnow()))

    def getJST(self, nomicro=False): # get the time in jst
        if nomicro: return datetime.utcnow().replace(microsecond=0) + timedelta(seconds=32400) - timedelta(seconds=30)
        return datetime.utcnow() + timedelta(seconds=32400) - timedelta(seconds=30)

    def uptime(self, string=True): # get the uptime
        delta = datetime.utcnow() - self.starttime
        if string: return str(delta.days) + "d" + str(delta.seconds // 3600) + "h" + str((delta.seconds // 60) % 60) + "m" + str(delta.seconds % 60) + "s"
        else: return delta

# #####################################################################################
# GracefulExit
class GracefulExit: # when heroku force the bot to shutdown
  def __init__(self, bot):
    self.bot = bot
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.bot.exit_flag = True
    if self.bot.savePending:
        self.bot.autosaving = False
        if self.bot.save(False):
            print('Autosave Success')
        else:
            print('Autosave Failed')
    exit(0) # not graceful at all

# #####################################################################################
# Start
# make the bot instance
bot = Mizabot()

# bot events
@bot.event
async def on_ready(): # when the bot starts or reconnects
    await bot.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=random.choice(bot.games)))
    if not bot.boot_flag:
        # send a pretty message
        bot.setChannel('debug', 'debug_channel') # set our debug channel
        bot.setChannel('pinned', 'you_pinned') # set (you) pinned channel
        bot.setChannel('gbfglog', 'gbfg_log') # set /gbfg/ lucilius log channel
        bot.setChannel('youlog', 'you_log') # set (you) log channel
        bot.startTasks() # start the tasks
        await bot.send('debug', embed=bot.buildEmbed(title=bot.user.display_name + " is Ready", description="**Server Count**: " + str(len(bot.guilds)) + "\n**Servers Pending**: " + str(len(bot.newserver['pending'])) + "\n**Tasks Count**: " + str(len(asyncio.all_tasks())) + "\n**Cogs Loaded**: " + str(len(bot.cogs)) + "/" + str(bot.cogn), thumbnail=bot.user.avatar_url, timestamp=datetime.utcnow()))
        bot.boot_flag = True

@bot.event
async def on_guild_join(guild): # when the bot joins a new guild
    id = str(guild.id)
    if id in bot.newserver['servers'] or str(guild.owner.id) in bot.newserver['owners']: # leave if the server is blacklisted
        try:
            await bot.send('debug', embed=bot.buildEmbed(title="Banned guild request", description=guild.name + " ▪ " + str(id), thumbnail=guild.icon_url, footer="Owner: " + guild.owner.name + " ▪ " + str(guild.owner.id)))
        except Exception as e:
            await bot.send('debug', "on_guild_join(): " + str(e))
        await guild.leave()
    else: # notify me and add to the pending servers
        bot.newserver['pending'][id] = guild.name
        bot.savePending = True
        await bot.send('debug', embed=bot.buildEmbed(title="Pending guild request", description=guild.name + " ▪ " + id, thumbnail=guild.icon_url, footer="Owner: " + guild.owner.name + " ▪ " + str(guild.owner.id)))

# called by on_message
# games/jokes for /gbfg/
async def pitroulette():
    try:
        message = bot.pitroulettevictim.pop()
        bot.pitroulettelist.append([message.author.display_name, bot.pitroulettecount])
        description = "After **" + str(bot.pitroulettecount) + "** message(s)"
        title = random.choice([message.author.display_name + " has fallen into the pit...", message.author.display_name + " tripped and fell...", message.author.display_name + " jumped into the pit willingly...", message.author.display_name + " got pushed in the back..."])
        footer = random.choice(["Will " + message.author.display_name + " manage to climb up?", "Stay down here where you belong", "Straight into the hellish pit", message.author.display_name + " has met with a terrible fate"])
        if bot.pitroulettemax > 0:
            description += "\nI'm expecting **" + str(bot.pitroulettemax) + "** more victim(s)"
        else:
            bot.pitroulette = False # disable
        await message.channel.send(embed=bot.buildEmbed(title=title, description=description, thumbnail=message.author.avatar_url, footer=footer))
        if bot.pitroulettemax == 0 and len(bot.pitroulettelist) > 1:
            description = ""
            for a in bot.pitroulettelist:
                description += a[0] + " ▪ after " + str(a[1]) + " message(s)\n"
            await message.channel.send(embed=bot.buildEmbed(title="Pit Roulette results", description=description, thumbnail=message.author.avatar_url))
        g = bot.get_guild(bot.ids['gbfg'])
        await message.author.add_roles(g.get_role(bot.ids['pit']))
        await asyncio.sleep(60)
        await message.author.remove_roles(g.get_role(bot.ids['pit']))
    except asyncio.CancelledError:
        try:
            await message.author.remove_roles(g.get_role(bot.ids['pit']))
        except:
            pass
        return
    except Exception as e:
        await bot.sendError('pitroulette', str(e))

@bot.event
async def on_message(message): # to do something with a message
    try:
        # games/jokes for /gbfg/
        if bot.pitroulette and bot.pitroulettemax > 0 and message.channel.id == bot.ids['gbfg_general'] and message.author.id != bot.ids['owner'] and not message.author.bot:
            bot.pitroulettecount += 1
            proba = 3 * (bot.pitroulettemax + 1)
            if random.randint(1, 100) <= proba:
                bot.pitroulettevictim.append(message)
                bot.runTask('pitroulette', pitroulette)
                bot.pitroulettemax -= 1
                return
    except:
        pass
    # don't forget this
    await bot.process_commands(message)

@bot.check # authorize or not a command on a global scale
async def global_check(ctx):
    id = str(ctx.guild.id)
    if id in bot.newserver['servers'] or str(ctx.guild.owner.id) in bot.newserver['owners']: # ban check
        await ctx.guild.leave() # leave the server if banned
    if id in bot.newserver['pending']: # pending check
        await bot.react(ctx, 'cooldown')
        return False
    return True

@bot.event # if an error happens
async def on_command_error(ctx, error):
    msg = str(error)
    if msg.find('You are on cooldown.') == 0:
        await bot.react(ctx, 'cooldown')
    elif msg.find('required argument that is missing') != -1:
        return
    elif msg.find('check functions for command') != -1:
        return
    elif msg.find('Command "') == 0 or msg == 'Command raised an exception: Forbidden: FORBIDDEN (status code: 403): Missing Permissions':
        return
    else:
        bot.errn += 1
        await bot.send('debug', embed=bot.buildEmbed(title="⚠ Error caused by " + str(ctx.message.author), thumbnail=ctx.author.avatar_url, fields=[{"name":"Command", "value":'`' + ctx.message.content + '`'}, {"name":"Server", "value":ctx.message.author.guild.name}, {"name":"Message", "value":msg}], timestamp=datetime.utcnow()))


# Logging

# (You) pin board system
@bot.event
async def on_raw_reaction_add(payload):
    try:
        if payload.channel_id != bot.ids['you_general']:
            return
        message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        reactions = message.reactions
    except Exception as e:
        await bot.sendError('raw_react', str(e))
        return
    me = message.guild.me
    for reaction in reactions:
        if reaction.emoji == '📌':
            users = await reaction.users().flatten()
            guild = message.guild
            content = message.content
            isMod = False
            for u in users:
                if u.id == me.id:
                    return
                m = guild.get_member(u.id)
                if m.guild_permissions.manage_messages:
                    isMod = True
            if not isMod:
                return

            await message.add_reaction('📌')

            dict = {}
            dict['color'] = 0xf20252
            dict['title'] = str(message.author)
            if len(content) != 0: dict['description'] = content + "\n\n"
            else: dict['description'] = ""
            dict['description'] += ":earth_asia: [**Link**](https://discordapp.com/channels/"+str(message.guild.id)+"/"+str(message.channel.id)+"/"+str(message.id) + ")\n"
            dict['thumbnail'] = {'url':str(message.author.avatar_url)}
            dict['fields'] = []

            # for attachments
            if message.attachments:
                for file in message.attachments:
                    if file.is_spoiler():
                        dict['fields'].append({'inline': True, 'name':'Attachment', 'value':f'[{file.filename}]({file.url})'})
                    elif file.url.lower().endswith(('.png', '.jpeg', '.jpg', '.gif', '.webp')) and 'image' not in dict:
                        dict['image'] = {'url':file.url}
                    else:
                        dict['fields'].append({'inline': True, 'name':'Attachment', 'value':f'[{file.filename}]({file.url})'})
            embed = discord.Embed.from_dict(dict)
            embed.timestamp=message.created_at
            await bot.send('pinned', embed=embed)
            return

# used by /gbfg/ and (You)
@bot.event
async def on_member_update(before, after):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if before.guild.id in guilds:
        channel = guilds[before.guild.id]
        if before.display_name != after.display_name:
                await bot.send(channel, embed=bot.buildEmbed(author={'name':str(after) + " ▪ Name change", 'icon_url':after.avatar_url}, description=after.mention + "\n**Before** ▪ " + before.display_name + "\n**After** ▪ " + after.display_name, footer="User ID: " + str(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
        elif len(before.roles) < len(after.roles):
            for r in after.roles:
                if r not in before.roles:
                    await bot.send(channel, embed=bot.buildEmbed(author={'name':str(after) + " ▪ Role added", 'icon_url':after.avatar_url}, description=after.mention + " was given the `" + str(r) + "` role", footer="User ID: " + str(after.id), color=0x1b55b3, timestamp=datetime.utcnow()))
                    break
        elif len(before.roles) > len(after.roles):
            for r in before.roles:
                if r not in after.roles:
                    await bot.send(channel, embed=bot.buildEmbed(author={'name':str(after) + " ▪ Role removed", 'icon_url':after.avatar_url}, description=after.mention + " was removed from the `" + str(r) + "` role", footer="User ID: " + str(after.id), color=0x0b234a, timestamp=datetime.utcnow()))
                    break

@bot.event
async def on_member_remove(member):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if member.guild.id in guilds:
        channel = guilds[member.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(author={'name':str(member) + " ▪ Left the server", 'icon_url':member.avatar_url}, footer="User ID: " + str(member.id), timestamp=datetime.utcnow(), color=0xff0000))

@bot.event
async def on_member_join(member):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if member.guild.id in guilds:
        channel = guilds[member.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(author={'name':str(member) + " ▪ Joined the server", 'icon_url':member.avatar_url}, footer="User ID: " + str(member.id), timestamp=datetime.utcnow(), color=0x00ff3c))

@bot.event
async def on_member_ban(guild, user):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if guild.id in guilds:
        channel = guilds[guild.id]
        await bot.send(channel, embed=bot.buildEmbed(author={'name':str(user) + " ▪ Banned from the server", 'icon_url':user.avatar_url}, footer="User ID: " + str(user.id), timestamp=datetime.utcnow(), color=0xff0000))

@bot.event
async def on_member_unban(guild, user):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if guild.id in guilds:
        channel = guilds[guild.id]
        await bot.send(channel, embed=bot.buildEmbed(author={'name':str(user) + " ▪ Unbanned from the server", 'icon_url':user.avatar_url}, footer="User ID: " + str(user.id), timestamp=datetime.utcnow(), color=0x00ff3c))

@bot.event
async def on_guild_emojis_update(guild, before, after):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if guild.id in guilds:
        channel = guilds[guild.id]
        if len(before) < len(after):
            for e in after:
                if e not in before:
                    await bot.send(channel, embed=bot.buildEmbed(author={'name':e.name + " ▪ Emoji added", 'icon_url':e.url}, footer="Emoji ID: " + str(e.id), timestamp=datetime.utcnow(), color=0x00ff3c))
                    break
        else:
            for e in before:
                if e not in after:
                    await bot.send(channel, embed=bot.buildEmbed(author={'name':e.name + " ▪ Emoji removed", 'icon_url':e.url}, footer="Emoji ID: " + str(e.id), timestamp=datetime.utcnow(), color=0xff0000))
                    break

@bot.event
async def on_guild_role_create(role):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if role.guild.id in guilds:
        channel = guilds[role.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(title="Role created ▪ `" + role.name + "`", footer="Role ID: " + str(role.id), timestamp=datetime.utcnow(), color=0x00ff3c))

@bot.event
async def on_guild_role_delete(role):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if role.guild.id in guilds:
        channel = guilds[role.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(title="Role deleted ▪ `" + role.name + "`", footer="Role ID: " + str(role.id), timestamp=datetime.utcnow(), color=0xff0000))

@bot.event
async def on_guild_role_update(before, after):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if before.guild.id in guilds:
        channel = guilds[before.guild.id]
        if before.name != after.name:
            await bot.send(channel, embed=bot.buildEmbed(title="Role name updated", fields=[{'name':"Before", 'value':before.name}, {'name':"After", 'value':after.name}], footer="Role ID: " + str(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
        elif before.colour != after.colour:
            await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▪ `" + after.name + "`", description="Color changed", footer="Role ID: " + str(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
        elif before.hoist != after.hoist:
            if after.hoist:
                await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▪ `" + after.name + "`", description="Role is displayed separately from other members", footer="Role ID: " + str(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
            else:
                await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▪ `" + after.name + "`", description="Role is displayed as the other members", footer="Role ID: " + str(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
        elif before.mentionable != after.mentionable:
            if after.mentionable:
                await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▪ `" + after.name + "`", description="Role is mentionable", footer="Role ID: " + str(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
            else:
                await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▪ `" + after.name + "`", description="Role isn't mentionable", footer="Role ID: " + str(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))

# create the graceful exit
grace = GracefulExit(bot)

# load cogs from the cogs folder
bot.loadCog("general", "gbf_game.GBF_Game", "gbf_utility.GBF_Utility", "gw.GW", "management", "owner", "baguette")

# start the loop
bot.mainLoop()
