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

    async def send_error_message(self, error):
        destination = self.get_destination()
        await destination.send(embed=bot.buildEmbed(title="Help Error", description=error))

    async def send_bot_help(self, mapping): # main help command (called when you do $help). this function reuse the code from the commands.DefaultHelpCommand class
        ctx = self.context # get $help context
        bot = ctx.bot
        me = ctx.author.guild.me # bot own user infos

        try:
            await ctx.message.add_reaction('📬')
        except:
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="Unblock me to receive the Help"))
            return

        if bot.description: # send the bot description first
            try:
                await ctx.author.send(embed=bot.buildEmbed(title=me.name + " Help", description=bot.description, thumbnail=me.avatar_url)) # author.send = dm
            except:
                await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                await ctx.message.remove_reaction('📬', ctx.guild.me)
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
                embed = discord.Embed(title="{} **{}** Category".format(bot.getEmote('mark'), category[:-1]), color=random.randint(0, 16777216)) # make an embed, random color
                for c in commands: # fill the embed fields with the command infos
                    if c.short_doc == "": embed.add_field(name="{} ▫ {}".format(c.name, self.get_command_signature(c)), value="No description", inline=False)
                    else: embed.add_field(name="{} ▫ {}".format(c.name, self.get_command_signature(c)), value=c.short_doc, inline=False)
                    if len(embed) > 5800 or len(embed.fields) > 24: # embeds have a 6000 and 25 fields characters limit, I send and make a new embed if needed
                        try:
                            await ctx.author.send(embed=embed) # author.send = dm
                        except:
                            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                            await ctx.message.remove_reaction('📬', ctx.guild.me)
                            return
                        embed = discord.Embed(title="{} **{}** Category".format(bot.getEmote('mark'), category[:-1]), color=embed.colour)
                if len(embed.fields) > 0: # only send if there is at least one field
                    try:
                        await ctx.author.send(embed=embed) # author.send = dm
                    except:
                        await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                        await ctx.message.remove_reaction('📬', ctx.guild.me)
                        return

        # final words
        await ctx.author.send(embed=bot.buildEmbed(title="{} Need more help?".format(bot.getEmote('question')), description="Use help <command name>\nOr help <category name>"))

        try:
            await ctx.message.remove_reaction('📬', ctx.guild.me)
            await ctx.message.add_reaction('✅') # white check mark
        except:
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="Did {} delete its message?".format(ctx.author)))

    async def send_command_help(self, command): # same thing, but for a command ($help <command>)
        ctx = self.context
        bot = ctx.bot
        try:
            await ctx.message.add_reaction('📬')
        except:
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="Unblock me to receive the Help"))
            return

        # send the help
        embed = discord.Embed(title="{} **{}** Command".format(bot.getEmote('mark'), command.name), description=command.help, color=random.randint(0, 16777216)) # random color
        embed.add_field(name="Usage", value=self.get_command_signature(command), inline=False)

        try:
            await ctx.author.send(embed=embed) # author.send = dm
        except:
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
            await ctx.message.remove_reaction('📬', ctx.guild.me)
            return

        await ctx.message.remove_reaction('📬', ctx.guild.me)
        await self.context.message.add_reaction('✅') # white check mark

    async def send_cog_help(self, cog): # category help ($help <category)
        ctx = self.context
        bot = ctx.bot
        try:
            await ctx.message.add_reaction('📬')
        except:
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="Unblock me to receive the Help"))
            return

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands) # sort
        embed = discord.Embed(title="{} **{}** Category".format(bot.getEmote('mark'), cog.qualified_name), description=cog.description, color=random.randint(0, 16777216)) # random color
        for c in filtered:
            if c.short_doc == "": embed.add_field(name="{} ▫ {}".format(c.name, self.get_command_signature(c)), value="No description", inline=False)
            else: embed.add_field(name="{} ▫ {}".format(c.name, self.get_command_signature(c)), value=c.short_doc, inline=False)
            if len(embed) > 5800 or len(embed.fields) > 24: # embeds have a 6000 and 25 fields characters limit, I send and make a new embed if needed
                try:
                    await ctx.author.send(embed=embed) # author.send = dm
                except:
                    await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                    await ctx.message.remove_reaction('📬', ctx.guild.me)
                    return
                embed = discord.Embed(title="{} **{}** Category".format(bot.getEmote('mark'), cog.qualified_name), description=cog.description, color=embed.colour)
        if len(embed.fields) > 0:
            try:
                await ctx.author.send(embed=embed) # author.send = dm
            except:
                await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                await ctx.message.remove_reaction('📬', ctx.guild.me)
                return

        await ctx.message.remove_reaction('📬', ctx.guild.me)
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
        if not drive:
            print("Can't login into Google Drive")
            return False
        try:
            file_list = drive.ListFile({'q': "'" + self.bot.tokens['drive'] + "' in parents and trashed=false"}).GetList() # get the file list in our folder
            for s in file_list:
                if s['title'] == "save.json": s.GetContentFile(s['title']) # iterate until we find save.json and download it
            return True
        except Exception as e:
            print(e)
            return False

    def save(self, data): # write save.json to the folder id in bot.tokens
        if self.saving: return False
        drive = self.login()
        if not drive: return False
        try:
            self.saving = True
            prev = []
            # backup
            file_list = drive.ListFile({'q': "'" + self.bot.tokens['drive'] + "' in parents and trashed=false"}).GetList()
            if len(file_list) > 9: # delete if we have too many backups
                for f in file_list:
                    if f['title'].find('backup') == 0:
                        f.Delete()
            for f in file_list: # search the previous save(s)
                if f['title'] == "save.json":
                    prev.append(f)
            # saving
            s = drive.CreateFile({'title':'save.json', 'mimeType':'text/JSON', "parents": [{"kind": "drive#file", "id": self.bot.tokens['drive']}]})
            s.SetContentString(data)
            s.Upload()
            # rename the previous save(s)
            for f in prev:
                f['title'] = "backup_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
                f.Upload()
            self.saving = False
            return True
        except Exception as e:
            print(e)
            self.saving = False
            return False

    def saveFile(self, data, name, folder): # write a json file to a folder
        drive = self.login()
        s = drive.CreateFile({'title':name, 'mimeType':'text/JSON', "parents": [{"kind": "drive#file", "id": folder}]})
        s.SetContentString(data)
        s.Upload()

    def dlFile(self, name, folder): # load a file from a folder
        drive = self.login()
        if not drive:
            print("Can't login into Google Drive")
            return False
        try:
            file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
            for s in file_list:
                if s['title'] == name:
                    s.GetContentFile(s['title']) # iterate until we find the file and download it
                    return True
            return False
        except Exception as e:
            print(e)
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
        self.gbfids = {} # gbf profile ids linked to discord ids
        self.summons = {} # support summon database
        self.summonlast = None # support summon database last update
        self.permitted = {} # guild permitted channels
        self.news = {} # guild news channels
        self.games = {} # bot status messages
        self.strings = {} # bot strings
        self.specialstrings = {} # bot special strings
        self.emotes = {} # bot custom emote ids
        self.emote_cache = {} # store used emotes
        self.granblue = {} # store player/crew ids
        self.extra = {} # extra data storage for plug'n'play cogs
        self.on_message_high = {} # on message callback (high priority)
        self.on_message_low = {} # on message callback
        # load
        self.loadConfig()
        for i in range(0, 100): # try multiple times in case google drive is unresponsive
            if self.drive.load(): break
            elif i == 99:
                print("Google Drive might be unavailable")
                exit(3)
            time.sleep(20)
        if not self.load(): exit(2) # first loading must success
        super().__init__(command_prefix=self.prefix, case_insensitive=True, description='''MizaBOT version 5.49
Source code: https://github.com/MizaGBF/MizaBOT.
Default command prefix is '$', use $setPrefix to change it on your server.''', help_command=MizabotHelp(), owner=self.ids['owner'], max_messages=100)

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
                    self.save()
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
                self.baguette = data.get('baguette', {})
                self.ids = data.get('ids', {})
                self.games = data.get('games', ['Granblue Fantasy'])
                self.strings = data.get('strings', {})
                self.specialstrings = data.get('specialstrings', {})
                self.emotes = data.get('emotes', {})
                self.granblue = data.get('granblue', {"gbfgcrew":{}})
        except Exception as e:
            print('loadConfig(): {}'.format(e))
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
                if 'extra' in data: self.extra = data['extra']
                else: self.extra = {}
                if 'gbfids' in data: self.gbfids = data['gbfids']
                else: self.gbfids = {}
                if 'summons' in data: self.summons = data['summons']
                else: self.summons = {}
                if 'summonlast' in data: self.summonlast = data['summonlast']
                else: self.summonlast = None
                return True
        except Exception as e:
            self.errn += 1
            print('load(): {}'.format(e))
            return False

    def save(self): # saving
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
                data['extra'] = self.extra
                data['gbfids'] = self.gbfids
                data['summons'] = self.summons
                data['summonlast'] = self.summonlast
                json.dump(data, outfile, default=self.json_serial) # locally first
                if not self.drive.save(json.dumps(data, default=self.json_serial)): # sending to the google drive
                    raise Exception("Couldn't save to google drive")
            return True
        except Exception as e:
            self.errn += 1
            print('save(): {}'.format(e))
            return False

    async def autosave(self, discordDump = False): # called when savePending is true by statustask()
        if self.autosaving: return
        self.autosaving = True
        if self.save():
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
                await asyncio.sleep(1200)
                await self.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=random.choice(self.games)))
                # check if it's time for the bot maintenance for me (every 2 weeks or so)
                c = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                if self.bot_maintenance and c > self.bot_maintenance and c.day == 1:
                    await self.send('debug', self.get_user(self.ids['owner']).mention + " ▫️ Time for maintenance!")
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

    async def invitetracker(self): # background task to track the invites of the (You) server
        await asyncio.sleep(2)
        await self.send('debug', embed=self.buildEmbed(title="invitetracker() started", timestamp=datetime.utcnow()))
        guilds = [self.get_guild(self.ids['you_server']), self.get_guild(self.ids['gbfg'])]
        log_channels = {self.ids['you_server']:'youlog', self.ids['gbfg']:'gbfglog'}
        
        try:
            invites = {}
            for g in guilds:
                res = await g.invites()
                invites[g.id] = {}
                for i in res:
                    invites[g.id][i.code] = i
        except:
            await self.sendError('invitetracker', 'cancelled, failed to retrieve a guild data')
            return

        while True:
            try:
                await asyncio.sleep(120)
                for g in guilds:
                    res = await g.invites()
                    currents = {}
                    for i in res:
                        currents[i.code] = i

                    for i in currents:
                        if i in invites[g.id]:
                            if currents[i].uses is not None and currents[i].uses != invites[g.id][i].uses:
                                await self.send(log_channels[g.id], embed=bot.buildEmbed(title="Invite `{}` used".format(i), description="**Uses:** {}".format(currents[i].uses), timestamp=datetime.utcnow(), color=0xfcba03))
                        else:
                            msg = ""
                            if currents[i].max_uses != 0: msg += "**Max uses:** {}\n".format(currents[i].max_uses)
                            if currents[i].inviter is not None:
                                msg += "**Inviter:** {}\n".format(currents[i].inviter)
                            if currents[i].max_age != 0:
                                if currents[i].max_age < 3600: msg += "**Duration:** {} minutes\n".format(currents[i].max_age // 60)
                                else: msg += "**Duration:** {} hours\n".format(currents[i].max_age // 3600)
                            msg += "**Channel:** {}\n".format(currents[i].channel.name)
                            msg += "**Url:** {}\n".format(currents[i].url)
                            await self.send(log_channels[g.id], embed=bot.buildEmbed(title="New Invite ▫️ `{}`".format(i), description=msg, timestamp=datetime.utcnow(), color=0xfcba03))

                    for i in invites[g.id]:
                        if i not in currents:
                            await self.send(log_channels[g.id], embed=bot.buildEmbed(title="Revoked Invite ▫️ `{}`".format(i), timestamp=datetime.utcnow(), color=0xfcba03))

                    invites[g.id] = currents
            except asyncio.CancelledError:
                await self.sendError('invitetracker', 'cancelled')
                return
            except Exception as e:
                await self.sendError('invitetracker', str(e))
                try: invites[g.id] = currents
                except: pass
                if str(e).startswith('500 INTERNAL SERVER ERROR'): # assume discord server issues and sleep
                    await asyncio.sleep(1000)

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
        if key in self.emote_cache:
            return self.emote_cache[key]
        elif key in self.emotes:
            try:
                e = self.get_emoji(self.emotes[key]) # ids are defined in config.json
                if e is not None: self.emote_cache[key] = e
                return e
            except:
                return None
        return None

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
        buffer1 = options.pop('footer', None)
        buffer2 = options.pop('footer_url', None)
        if buffer1 is not None and buffer2 is not None: embed.set_footer(text=buffer1, icon_url=buffer2)
        elif buffer1 is not None: embed.set_footer(text=buffer1)
        elif buffer2 is not None: embed.set_footer(icon_url=buffer2)
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
        self.runTask('invitetracker', self.invitetracker)
        for c in self.cogs:
            try:
                self.get_cog(c).startTasks()
            except:
                pass

    def setOnMessageCallback(self, name, callback, high_prio=False): # register a function to be called by on_message (high prio ones will be called first). Must return True (or False to interrupt on_message) and take message as parameter
        if high_prio:
            self.on_message_high[name] = callback
        else:
            self.on_message_low[name] = callback

    async def runOnMessageCallback(self, message):
        for name in self.on_message_high:
            try:
                if not await self.on_message_high[name](message): return False
            except:
                pass
        for name in self.on_message_low:
            try:
                if not await self.on_message_low[name](message): return False
            except:
                pass
        return True

    def setChannel(self, name, id_key : str): # "register" a channel to use with send()
        try:
            c = self.get_channel(self.ids[id_key])
            if c is not None: self.channels[name] = c
        except:
            self.errn += 1
            print("Invalid key: {}".format(id_key))

    def setChannelID(self, name, id : int): # same but using an id instead of an id defined in config.json
        try:
            c = self.get_channel(id)
            if c is not None: self.channels[name] = c
        except:
            self.errn += 1
            print("Invalid ID: {}".format(id))

    async def callCommand(self, ctx, command, cog, *args, **kwargs): #call a command in a cog
        cmds = self.get_cog(cog).get_commands()
        for c in cmds:
            if c.name == command:
                await ctx.invoke(c, *args, **kwargs)
                return
        raise Exception("Command `{}` not found".format(command))

    async def send(self, channel_name : str, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send something to a channel
        try:
            await self.channels[channel_name].send(msg, embed=embed, file=file)
        except Exception as e:
            self.errn += 1
            print("Channel {} error: {}".format(channel_name, e))

    async def sendMulti(self, channel_names : list, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send to multiple channel at the same time
        for c in channel_names:
            await self.send(c, msg, embed, file)

    async def sendError(self, func_name : str, msg : str, id = None): # send an error to the debug channel
        if msg.startswith("403 FORBIDDEN"): return # I'm tired of those errors because people didn't set their channel permissions right
        if self.errn >= 30: return # disable error messages if too many messages got sent
        if id is None: id = ""
        else: id = " {}".format(id)
        self.errn += 1
        await self.send('debug', embed=self.buildEmbed(title="Error in {}() {}".format(func_name, id), description=msg, timestamp=datetime.utcnow()))

    def getJST(self, nomicro=False): # get the time in jst
        if nomicro: return datetime.utcnow().replace(microsecond=0) + timedelta(seconds=32400) - timedelta(seconds=30)
        return datetime.utcnow() + timedelta(seconds=32400) - timedelta(seconds=30)

    def uptime(self, string=True): # get the uptime
        delta = datetime.utcnow() - self.starttime
        if string: return "{}".format(self.getTimedeltaStr(delta, None))
        else: return delta

    def getTimedeltaStr(self, delta, day=False):
        if day is None: return "{}d{}h{}m{}s".format(delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60, delta.seconds % 60)
        elif day: return "{}d{}h{}m".format(delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60)
        else: return "{}h{}m".format(delta.seconds // 3600, (delta.seconds // 60) % 60)

    # function to build a timedelta from a string (for $remind)
    def makeTimedelta(self, d): # return None if error
        flags = {'d':False,'h':False,'m':False}
        tmp = 0 # buffer
        sum = 0 # delta in seconds
        for i in range(0, len(d)):
            if d[i].isdigit():
                tmp = (tmp * 10) + int(d[i])
            elif d[i].lower() in flags:
                c = d[i].lower()
                if flags[c]:
                    return None
                if tmp < 0:
                    return None
                flags[c] = True
                if c == 'd':
                    sum += tmp * 86400
                elif c == 'h':
                    sum += tmp * 3600
                elif c == 'm':
                    sum += tmp * 60
                tmp = 0
            else:
                return None
        if tmp != 0: return None
        return timedelta(days=sum//86400, seconds=sum%86400)

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
        if self.bot.save():
            print('Autosave Success')
        else:
            print('Autosave Failed')
    exit(0)

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
        await bot.send('debug', embed=bot.buildEmbed(title="{} is Ready".format(bot.user.display_name), description="**Server Count**: {}\n**Servers Pending**: {}\n**Tasks Count**: {}\n**Cogs Loaded**: {}/{}".format(len(bot.guilds), len(bot.newserver['pending']), len(asyncio.all_tasks()), len(bot.cogs), bot.cogn), thumbnail=bot.user.avatar_url, timestamp=datetime.utcnow()))
        bot.boot_flag = True

@bot.event
async def on_guild_join(guild): # when the bot joins a new guild
    id = str(guild.id)
    if id == str(bot.ids['debug_server']):
        return
    elif id in bot.newserver['servers'] or str(guild.owner.id) in bot.newserver['owners']: # leave if the server is blacklisted
        try:
            await bot.send('debug', embed=bot.buildEmbed(title="Banned guild request", description="{} ▫️ {}".format(guild.name, id), thumbnail=guild.icon_url, footer="Owner: {} ▫️ {}".format(guild.owner.name, guild.owner.id)))
        except Exception as e:
            await bot.send('debug', "on_guild_join(): {}".format(e))
        await guild.leave()
    else: # notify me and add to the pending servers
        bot.newserver['pending'][id] = guild.name
        bot.savePending = True
        await guild.owner.send(embed=bot.buildEmbed(title="Pending guild request", description="Wait until my owner approve the new server", thumbnail=guild.icon_url))
        await bot.send('debug', embed=bot.buildEmbed(title="Pending guild request", description="{} ▫️ {}".format(guild.name, id), thumbnail=guild.icon_url, footer="Owner: {} ▫️ {}".format(guild.owner.name, guild.owner.id)))

@bot.event
async def on_message(message): # to do something with a message
    if await bot.runOnMessageCallback(message):
        await bot.process_commands(message) # don't forget

@bot.check # authorize or not a command on a global scale
async def global_check(ctx):
    id = str(ctx.guild.id)
    if id in bot.newserver['servers'] or str(ctx.guild.owner.id) in bot.newserver['owners']: # ban check
        await ctx.guild.leave() # leave the server if banned
        return False
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
    elif msg.find('Member "') == 0 or msg.find('Command "') == 0 or msg.startswith('Command raised an exception: Forbidden: 403'):
        return
    else:
        bot.errn += 1
        await bot.send('debug', embed=bot.buildEmbed(title="⚠ Error caused by {}".format(ctx.message.author), thumbnail=ctx.author.avatar_url, fields=[{"name":"Command", "value":'`{}`'.format(ctx.message.content)}, {"name":"Server", "value":ctx.message.author.guild.name}, {"name":"Message", "value":msg}], timestamp=datetime.utcnow()))

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
    role = message.guild.get_role(bot.ids['you_member'])
    if role is None: return
    for reaction in reactions:
        if reaction.emoji == '📌':
            users = await reaction.users().flatten()
            guild = message.guild
            content = message.content
            isMod = False
            count = 0
            for u in users:
                if u.id == me.id:
                    return
                m = guild.get_member(u.id)
                if m.guild_permissions.manage_messages:
                    isMod = True
                    break
                elif role in m.roles:
                    count += 1
            if not isMod and count < 3:
                return

            await message.add_reaction('📌')

            dict = {}
            dict['color'] = 0xf20252
            dict['title'] = str(message.author)
            if len(content) != 0: dict['description'] = content + "\n\n"
            else: dict['description'] = ""
            dict['description'] += ":earth_asia: [**Link**](https://discordapp.com/channels/{}/{}/{})\n".format(message.guild.id, message.channel.id, message.id)
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
                await bot.send(channel, embed=bot.buildEmbed(author={'name':"{} ▫️ Name change".format(after.display_name), 'icon_url':after.avatar_url}, description="{}\n**Before** ▫️ {}\n**After** ▫️ {}".format(after.mention, before.display_name, after.display_name), footer="User ID: {}".format(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
        elif len(before.roles) < len(after.roles):
            for r in after.roles:
                if r not in before.roles:
                    await bot.send(channel, embed=bot.buildEmbed(author={'name':"{} ▫️ Role added".format(after.name), 'icon_url':after.avatar_url}, description="{} was given the `{}` role".format(after.mention, r.name), footer="User ID: {}".format(after.id), color=0x1b55b3, timestamp=datetime.utcnow()))
                    break
        elif len(before.roles) > len(after.roles):
            for r in before.roles:
                if r not in after.roles:
                    await bot.send(channel, embed=bot.buildEmbed(author={'name':"{} ▫️ Role removed".format(after.name), 'icon_url':after.avatar_url}, description="{} was removed from the `{}` role".format(after.mention, r.name), footer="User ID: {}".format(after.id), color=0x0b234a, timestamp=datetime.utcnow()))
                    break

@bot.event
async def on_member_remove(member):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if member.guild.id in guilds:
        await bot.send(guilds[member.guild.id], embed=bot.buildEmbed(author={'name':"{} ▫️ Left the server".format(member.name), 'icon_url':member.avatar_url}, footer="User ID: {}".format(member.id), timestamp=datetime.utcnow(), color=0xff0000))

@bot.event
async def on_member_join(member):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if member.guild.id in guilds:
        channel = guilds[member.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(author={'name':"{} ▫️ Joined the server".format(member.name), 'icon_url':member.avatar_url}, footer="User ID: {}".format(member.id), timestamp=datetime.utcnow(), color=0x00ff3c))

@bot.event
async def on_member_ban(guild, user):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if guild.id in guilds:
        await bot.send(guilds[guild.id], embed=bot.buildEmbed(author={'name':"{} ▫️ Banned from the server".format(user.name), 'icon_url':user.avatar_url}, footer="User ID: {}".format(user.id), timestamp=datetime.utcnow(), color=0xff0000))

@bot.event
async def on_member_unban(guild, user):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if guild.id in guilds:
        await bot.send(guilds[guild.id], embed=bot.buildEmbed(author={'name':"{} ▫️ Unbanned from the server".format(user.name), 'icon_url':user.avatar_url}, footer="User ID: {}".format(user.id), timestamp=datetime.utcnow(), color=0x00ff3c))

@bot.event
async def on_guild_emojis_update(guild, before, after):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if guild.id in guilds:
        channel = guilds[guild.id]
        if len(before) < len(after):
            for e in after:
                if e not in before:
                    await bot.send(channel, embed=bot.buildEmbed(author={'name':"{} ▫️ Emoji added".format(e.name), 'icon_url':e.url}, footer="Emoji ID: {}".format(e.id), timestamp=datetime.utcnow(), color=0x00ff3c))
                    break
        else:
            for e in before:
                if e not in after:
                    await bot.send(channel, embed=bot.buildEmbed(author={'name':" ▫️ Emoji removed".format(e.name), 'icon_url':e.url}, footer="Emoji ID: {}".format(e.id), timestamp=datetime.utcnow(), color=0xff0000))
                    break

@bot.event
async def on_guild_role_create(role):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if role.guild.id in guilds:
        channel = guilds[role.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(title="Role created ▫️ `{}`".format(role.name), footer="Role ID: {}".format(role.id), timestamp=datetime.utcnow(), color=0x00ff3c))

@bot.event
async def on_guild_role_delete(role):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if role.guild.id in guilds:
        channel = guilds[role.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(title="Role deleted ▫️ `{}`".format(role.name), footer="Role ID: {}".format(role.id), timestamp=datetime.utcnow(), color=0xff0000))

@bot.event
async def on_guild_role_update(before, after):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if before.guild.id in guilds:
        channel = guilds[before.guild.id]
        if before.name != after.name:
            await bot.send(channel, embed=bot.buildEmbed(title="Role name updated", fields=[{'name':"Before", 'value':before.name}, {'name':"After", 'value':after.name}], footer="Role ID: {}".format(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
        elif before.colour != after.colour:
            await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▫️ `" + after.name + "`", description="Color changed", footer="Role ID: {}".format(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
        elif before.hoist != after.hoist:
            if after.hoist:
                await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▫️ `{}`".format(after.name), description="Role is displayed separately from other members", footer="Role ID: {}".format(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
            else:
                await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▫️ `{}`".format(after.name), description="Role is displayed as the other members", footer="Role ID: {}".format(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
        elif before.mentionable != after.mentionable:
            if after.mentionable:
                await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▫️ `{}`".format(after.name), description="Role is mentionable", footer="Role ID: {}".format(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))
            else:
                await bot.send(channel, embed=bot.buildEmbed(title="Role updated ▫️ `{}`".format(after.name), description="Role isn't mentionable", footer="Role ID: {}".format(after.id), timestamp=datetime.utcnow(), color=0x1ba6b3))

@bot.event
async def on_guild_channel_create(channel):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if channel.guild.id in guilds:
        await bot.send(guilds[channel.guild.id], embed=bot.buildEmbed(title="Channel created ▫️ `{}`".format(channel.name), footer="Channel ID: {}".format(channel.id), timestamp=datetime.utcnow(), color=0xebe007))

@bot.event
async def on_guild_channel_delete(channel):
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if channel.guild.id in guilds:
        await bot.send(guilds[channel.guild.id], embed=bot.buildEmbed(title="Channel deleted ▫️ `{}`".format(channel.name), footer="Channel ID: {}".format(channel.id), timestamp=datetime.utcnow(), color=0x8a8306))

# create the graceful exit
grace = GracefulExit(bot)

# load cogs from the cogs folder
bot.loadCog("general", "gbf_game.GBF_Game", "gbf_utility.GBF_Utility", "gw.GW", "management", "owner", "baguette")

# start the loop
bot.mainLoop()