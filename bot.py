import discord
from discord.ext import commands
import asyncio
import tweepy
import signal
import zlib
import json
import random
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib import request, parse
from urllib.parse import unquote
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import itertools
import psutil
import time
import re
import os
import cogs # our cogs folder

# ########################################################################################
# custom help command used by the bot
class MizabotHelp(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__()
        self.dm_help = True # force dm only (although our own functions only send in dm, so it should be unneeded)

    async def send_error_message(self, error):
        try: await self.context.message.add_reaction('❎') # white negative mark
        except: pass

    async def send_bot_help(self, mapping): # main help command (called when you do $help). this function reuse the code from the commands.DefaultHelpCommand class
        ctx = self.context # get $help context
        bot = ctx.bot
        me = ctx.author.guild.me # bot own user infos

        try:
            await bot.react(ctx.message, '📬')
        except:
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="Unblock me to receive the Help"))
            return

        if bot.description: # send the bot description first
            try:
                await ctx.author.send(embed=bot.buildEmbed(title=me.name + " Help", description=bot.description, thumbnail=me.avatar_url)) # author.send = dm
            except:
                await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                await bot.unreact(ctx.message, '📬')
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
                            await bot.unreact(ctx.message, '📬')
                            return
                        embed = discord.Embed(title="{} **{}** Category".format(bot.getEmote('mark'), category[:-1]), color=embed.colour)
                if len(embed.fields) > 0: # only send if there is at least one field
                    try:
                        await ctx.author.send(embed=embed) # author.send = dm
                    except:
                        await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                        await bot.unreact(ctx.message, '📬')
                        return

        # final words
        await ctx.author.send(embed=bot.buildEmbed(title="{} Need more help?".format(bot.getEmote('question')), description="Use help <command name>\nOr help <category name>"))

        try:
            await bot.unreact(ctx.message, '📬')
            await bot.react(ctx.message, '✅') # white check mark
        except:
            await ctx.send(embed=bot.buildEmbed(title="Help Error", description="Did {} delete its message?".format(ctx.author)))

    async def send_command_help(self, command): # same thing, but for a command ($help <command>)
        ctx = self.context
        bot = ctx.bot
        try:
            await bot.react(ctx.message, '📬')
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
            await bot.unreact(ctx.message, '📬')
            return

        await bot.unreact(ctx.message, '📬')
        await self.context.message.add_reaction('✅') # white check mark

    async def send_cog_help(self, cog): # category help ($help <category)
        ctx = self.context
        bot = ctx.bot
        try:
            await bot.react(ctx.message, '📬')
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
                    await bot.unreact(ctx.message, '📬')
                    return
                embed = discord.Embed(title="{} **{}** Category".format(bot.getEmote('mark'), cog.qualified_name), description=cog.description, color=embed.colour)
        if len(embed.fields) > 0:
            try:
                await ctx.author.send(embed=embed) # author.send = dm
            except:
                await ctx.send(embed=bot.buildEmbed(title="Help Error", description="I can't send you a direct message"))
                await bot.unreact(ctx.message, '📬')
                return

        await bot.unreact(ctx.message, '📬')
        await bot.react(ctx.message, '✅') # white check mark

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
            # search the save file
            for s in file_list:
                if s['title'] == "save.json":
                    s.GetContentFile(s['title']) # iterate until we find save.json and download it
                    return True
            #if no save file on google drive, make an empty one
            with open('save.json', 'w') as outfile:
                data = {}
                json.dump(data, outfile, default=self.bot.json_serial)
                self.bot.savePending = True
                self.bot.boot_msg += "Created an empty save file\n"
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

    def saveDiskFile(self, target, mime, name, folder): # write a file from the local storage to a drive folder
        drive = self.login()
        s = drive.CreateFile({'title':name, 'mimeType':mime, "parents": [{"kind": "drive#file", "id": folder}]})
        s.SetContentFile(target)
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

    def delFiles(self, names, folder): # delete matching files from a folder
        drive = self.login()
        if not drive:
            print("Can't login into Google Drive")
            return False
        try:
            file_list = drive.ListFile({'q': "'" + folder + "' in parents and trashed=false"}).GetList() # get the file list in our folder
            for s in file_list:
                if s['title'] in names:
                    s.Delete()
            return True
        except Exception as e:
            print(e)
            return False

# #####################################################################################
# Bot
class Mizabot(commands.Bot):
    def __init__(self):
        self.botversion = "6.19" # version number
        self.saveversion = 0 # save version
        self.botchangelog = ["Added `$news` and automatic translation"] # bot changelog
        self.running = True # if True, the bot is running
        self.boot_flag = False # if True, the bot has booted
        self.boot_msg = "" # msg to be displayed on the debug channel after boot
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
        self.guilddata = {'banned':[], 'owners':[], 'pending':{}} # banned servers, banned owners, pending servers
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
        self.gbfaccounts = [] # gbf bot accounts
        self.gbfcurrent = 0  # gbf current bot account
        self.gbfversion = None  # gbf version
        self.gbfwatch = {}  # gbf special data
        self.pastebin = {}  # pastebin credentials
        self.twitter = {} # twitter credentials
        self.twitter_api = None # twitter api object
        self.ids = {} # discord ids used by the bot
        self.gbfids = {} # gbf profile ids linked to discord ids
        self.summonlast = None # support summon database last update
        self.permitted = {} # guild permitted channels
        self.news = {} # guild news channels
        self.games = {} # bot status messages
        self.strings = {} # bot strings
        self.emotes = {} # bot custom emote ids
        self.emote_cache = {} # store used emotes
        self.granblue = {} # store player/crew ids
        self.assignablerole = {} # self assignable role
        self.bannedusers = [] # user banned from using the bot
        self.extra = {} # extra data storage for plug'n'play cogs
        self.on_message_high = {} # on message callback (high priority)
        self.on_message_low = {} # on message callback
        self.memmonitor = {0, None} # for monitoring the memory
        self.vregex = re.compile("Game\.version = \"(\d+)\";") # for the gbf version check
        # load
        self.loadConfig() # load the config
        for i in range(0, 100): # try multiple times in case google drive is unresponsive
            if self.drive.load(): break
            elif i == 99:
                print("Google Drive might be unavailable")
                exit(3)
            time.sleep(20) # wait 20 sec
        if not self.load(): exit(2) # first loading of the save file must succeed, if not we exit
        # start tweepy
        try:
            auth = tweepy.OAuthHandler(self.twitter['key'], self.twitter['secret'])
            auth.set_access_token(self.twitter['access'], self.twitter['access_secret'])
            self.twitter_api = tweepy.API(auth)
        except:
            self.twitter_api = None
        # init bot
        super().__init__(command_prefix=self.prefix, case_insensitive=True, description="MizaBOT version {}\nSource code: https://github.com/MizaGBF/MizaBOT.\nDefault command prefix is '$', use $setPrefix to change it on your server.".format(self.botversion), help_command=MizabotHelp(), owner=self.ids['owner'], max_messages=None)

    def mainLoop(self): # main loop of the bot
        while self.running:
            try:
                self.loop.run_until_complete(self.start(self.tokens['discord']))
            except Exception as e: # handle exceptions here to avoid the bot dying
                if self.savePending:
                    self.save()
                    self.savePending = False
                self.errn += 1
                print("Main Loop Exception: " + str(e))
                if str(e).startswith("429 Too Many Requests"): time.sleep(80)
        if self.save():
            print('Autosave Success')
        else:
            print('Autosave Failed')

    def prefix(self, client, message): # command prefix check
        try:
            return self.prefixes.get(str(message.guild.id), '$') # get the guild prefix if it exists
        except:
            return '$' # else, return the default prefix $

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

    def loadConfig(self): # pretty simple, load the config file
        try:
            with open('config.json') as f:
                data = json.load(f, object_pairs_hook=self.json_deserial_dict) # deserializer here
                self.tokens = data['tokens']
                self.ids = data.get('ids', {})
                self.bannedusers = data.get('banned', [])
                self.games = data.get('games', ['Granblue Fantasy'])
                self.strings = data.get('strings', {})
                self.emotes = data.get('emotes', {})
                self.granblue = data.get('granblue', {"gbfgcrew":{}})
                self.gbfwatch = data.get('gbfwatch', {})
                self.pastebin = data.get('pastebin', {"dev_key" : "", "user_key" : "", "user" : "", "pass" : ""})
                self.twitter = data.get('twitter', {"key" : "", "secret" : "", "access" : "", "access_secret" : ""})
        except Exception as e:
            print('loadConfig(): {}\nCheck your \'config.json\' for the above error.'.format(e))
            exit(1) # instant quit if error

    def load(self): # same thing but for save.json
        try:
            with open('save.json') as f:
                data = json.load(f, object_pairs_hook=self.json_deserial_dict) # deserializer here
                ver = data.get('version', None)
                if ver is None:
                    self.guilddata = data.get('newserver', {'servers':[], 'owners':[], 'pending':{}})
                    self.guilddata['banned'] = self.guilddata['servers']
                    self.guilddata.pop('servers', None)
                elif ver > self.saveversion:
                    raise Exception("Save file version higher than the expected version")
                else:
                    self.guilddata = data.get('guilds', {'banned':[], 'owners':[], 'pending':{}})
                self.prefixes = data.get('prefixes', {})
                self.gbfaccounts = data.get('gbfaccounts', [])
                self.gbfcurrent = data.get('gbfcurrent', 0)
                self.gbfversion = data.get('gbfversion', None)
                self.gbfdata = data.get('gbfdata', {})
                self.bot_maintenance = data.get('bot_maintenance', None)
                if 'maintenance' in data:
                    if data['maintenance'].get('state', False) == True:
                        self.maintenance = data['maintenance']
                    else:
                        self.maintenance = {"state" : False, "time" : None, "duration" : 0}
                else: self.maintenance = {"state" : False, "time" : None, "duration" : 0}
                self.stream = data.get('stream', {'time':None, 'content':[]})
                self.schedule = data.get('schedule', [])
                self.st = data.get('st', {})
                self.spark = data.get('spark', [{}, []])
                self.gw = data.get('gw', {})
                self.reminders = data.get('reminders', {})
                self.permitted = data.get('permitted', {})
                self.news = data.get('news', {})
                self.extra = data.get('extra', {})
                self.gbfids = data.get('gbfids', {})
                self.summonlast = data.get('summonlast', None)
                self.assignablerole = data.get('assignablerole', {})
                return True
        except Exception as e:
            self.errn += 1
            print('load(): {}'.format(e))
            return False

    def save(self): # saving
        try:
            with open('save.json', 'w') as outfile:
                data = {}
                data['version'] = self.saveversion
                data['guilds'] = self.guilddata
                data['prefixes'] = self.prefixes
                data['gbfaccounts'] = self.gbfaccounts
                data['gbfcurrent'] = self.gbfcurrent
                data['gbfversion'] = self.gbfversion
                data['gbfdata'] = self.gbfdata
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
                data['summonlast'] = self.summonlast
                data['assignablerole'] = self.assignablerole
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
        result = False
        for i in range(0, 3):
            if self.save():
                self.savePending = False
                result = True
                break
            await asyncio.sleep(0.001)
        if not result:
            await self.send('debug', embed=self.buildEmbed(title="Failed Save", timestamp=datetime.utcnow()))
            discordDump = True
        if discordDump:
            try:
                with open('save.json', 'r') as infile:
                    await self.send('debug', 'save.json', file=discord.File(infile))
            except Exception as e:
                pass
        self.autosaving = False

    async def statustask(self): # background task changing the bot status and calling autosave()
        while True:
            try:
                await asyncio.sleep(1200)
                await self.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=random.choice(self.games)))
                # check if it's time for the bot maintenance for me (every 2 weeks or so)
                c = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                if self.bot_maintenance and c > self.bot_maintenance and c.day == 16:
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

    async def invitetracker(self): # background task to track the invites of the (You) and /gbfg/ servers
        if 'you_server' not in self.ids or 'gbfg' not in self.ids: return

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
                await asyncio.sleep(150)
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

    async def cleansave(self): # background task to clean up the save data, once per boot
        await asyncio.sleep(1000) # after 1000 seconds
        if self.exit_flag: return
        try:
            change = False
            # clean up spark data
            c = datetime.utcnow()
            for id in list(self.spark[0].keys()):
                if len(self.spark[0][id]) == 3: # backward compatibility
                    self.spark[0][id].append(c)
                    change = True
                else:
                    d = c - self.spark[0][id][3]
                    if d.days >= 30:
                        del self.spark[0][id]
                        change = True

            # clean up schedule
            c = self.getJST()
            new_schedule = []
            for i in range(0, len(self.schedule), 2):
                try:
                    date = self.schedule[i].replace(" ", "").split("-")[-1].split("/")
                    x = c.replace(month=int(date[0]), day=int(date[1])+1, microsecond=0)
                    if c - x > timedelta(days=160):
                        x = x.replace(year=x.year+1)
                    if c >= x:
                        continue
                except:
                    pass
                new_schedule.append(self.schedule[i])
                new_schedule.append(self.schedule[i+1])

            if len(new_schedule) != len(self.schedule):
                self.schedule = new_schedule
                change = True
                await self.send('debug', embed=self.buildEmbed(title="cleansave()", description="The schedule has been cleaned up", timestamp=datetime.utcnow()))

            # raise save flag
            if change: self.savePending = True
        except asyncio.CancelledError:
            await self.sendError('cleansave', 'cancelled')
            return
        except Exception as e:
            await self.sendError('cleansave', str(e))

    def isAuthorized(self, ctx): # check if the command is authorized in the channel
        id = str(ctx.guild.id)
        if id in self.permitted: # if id is found, it means the check is enabled
            if ctx.channel.id in self.permitted[id]:
                return True # permitted
            return False # not permitted
        return True # default

    def isServer(self, ctx, id_string : str): # check if the context is in the targeted guild (must be in config.json)
        if ctx.message.author.guild.id == self.ids.get(id_string, -1):
            return True
        return False

    def isMod(self, ctx): # check if the member has the manage_message permission
        if ctx.author.guild_permissions.manage_messages or ctx.author.id == self.ids.get('owner', -1):
            return True
        return False

    def isOwner(self, ctx):
        if ctx.message.author.id == self.ids.get('owner', -1):
            return True
        return False

    def getEmote(self, key): # retrieve a custom emote
        if key in self.emote_cache:
            return self.emote_cache[key]
        elif key in self.emotes:
            try:
                e = self.get_emoji(self.emotes[key]) # ids are defined in config.json
                if e is not None:
                    self.emote_cache[key] = e
                    return e
                return ""
            except:
                return ""
        return key

    async def react(self, msg, key): # add a reaction using a custom emote defined in config.json
        try:
            await msg.add_reaction(self.getEmote(key))
            return True
        except Exception as e:
            await self.sendError('react', str(e))
            return False

    async def unreact(self, msg, key): # remove a reaction using a custom emote defined in config.json
        try:
            await msg.remove_reaction(self.getEmote(key), msg.guild.me)
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

    def getTwitterUser(self, screen_name : str):
        try: return self.twitter_api.get_user(screen_name)
        except: return None

    def getTwitterTimeline(self, screen_name : str):
        try: return self.twitter_api.user_timeline(screen_name, tweet_mode='extended')
        except: return None

    async def sendRequest(self, url, **options): # to send a request over the internet
        try:
            data = None
            headers = {}
            if not options.get('no_base_headers', False):
                headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
                headers['Accept-Encoding'] = 'gzip, deflate'
                headers['Accept-Language'] = 'en'
                headers['Connection'] = 'keep-alive'
                headers['Host'] = 'game.granbluefantasy.jp'
                headers['Origin'] = 'http://game.granbluefantasy.jp'
                headers['Referer'] = 'http://game.granbluefantasy.jp/'
            if "headers" in options:
                headers = {**headers, **options["headers"]}
            id = options.get('account', None)
            if id is not None: acc = self.getGBFAccount(id)
            if options.get('check', False):
                ver = await self.getGameversion()
            else:
                ver = self.gbfversion
            if ver == "Maintenance": return "Maintenance"
            elif ver is not None:
                url = url.replace("VER", "{}".format(ver))
            ts = int(datetime.utcnow().timestamp() * 1000)
            url = url.replace("TS1", "{}".format(ts))
            url = url.replace("TS2", "{}".format(ts+300))
            if id is not None:
                if ver is None or acc is None:
                    return None
                url = url.replace("ID", "{}".format(acc[0]))
                if 'Cookie' not in headers: headers['Cookie'] = acc[1]
                if 'User-Agent' not in headers: headers['User-Agent'] = acc[2]
                if 'X-Requested-With' not in headers: headers['X-Requested-With'] = 'XMLHttpRequest'
                if 'X-VERSION' not in headers: headers['X-VERSION'] = ver
            payload = options.get('payload', None)
            if payload is None: req = request.Request(url, headers=headers)
            else:
                if not options.get('no_base_headers', False) and 'Content-Type' not in headers: headers['Content-Type'] = 'application/json'
                if 'user_id' in payload and payload['user_id'] == "ID": payload['user_id'] = acc[0]
                req = request.Request(url, headers=headers, data=json.dumps(payload).encode('utf-8'))
            url_handle = request.urlopen(req)
            if id is not None:
                self.refreshGBFAccount(id, url_handle.info()['Set-Cookie'])
            if options.get('decompress', False): data = zlib.decompress(url_handle.read(), 16+zlib.MAX_WBITS)
            else: data = url_handle.read()
            if options.get('load_json', False): data = json.loads(data)
            return data
        except Exception as e:
            if options.get('error', False):
                await self.sendError('request', 'Request failed for url `{}`\nCause \▫️ {}'.format(url, e))
            try:
                self.gbfaccounts[id][3] = 0
                self.savePending = True
            except: pass
            return None

    def getGBFAccount(self, id : int = 0): # retrive one of our gbf account
        if id < 0 or id >= len(self.gbfaccounts):
            return None
        return self.gbfaccounts[id]

    def addGBFAccount(self, uid : int, ck : str, ua : str): # add a gbf account
        self.gbfaccounts.append([uid, ck, ua, 0, 0, None])
        self.savePending = True
        return True

    def updateGBFAccount(self, id : int, **options): # update a part of a gbf account
        if id < 0 or id >= len(self.gbfaccounts):
            return False
        uid = options.pop('uid', None)
        ck = options.pop('ck', None)
        ua = options.pop('ua', None)
        if uid is not None:
            self.gbfaccounts[id][0] = uid
            self.gbfaccounts[id][4] = 0
        if ck is not None:
            self.gbfaccounts[id][1] = ck
            self.gbfaccounts[id][5] = None
        if ua is not None:
            self.gbfaccounts[id][2] = ua
        self.gbfaccounts[id][3] = 0
        self.savePending = True
        return True

    def delGBFAccount(self, id : int): # del a gbf account
        if id < 0 or id >= len(self.gbfaccounts):
            return False
        self.gbfaccounts.pop(id)
        if self.gbfcurrent >= id and self.gbfcurrent >= 0: self.gbfcurrent -= 1
        self.savePending = True
        return True

    def refreshGBFAccount(self, id : int, ck : str): # refresh a valid gbf account
        if id < 0 or id >= len(self.gbfaccounts):
            return False
        A = self.gbfaccounts[id][1].split(';')
        B = ck.split(';')
        for c in B:
            tA = c.split('=')
            if tA[0][0] == " ": tA[0] = tA[0][1:]
            f = False
            for i in range(0, len(A)):
                tB = A[i].split('=')
                if tB[0][0] == " ": tB[0] = tB[0][1:]
                if tA[0] == tB[0]:
                    A[i] = c
                    f = True
                    break
        self.gbfaccounts[id][1] = ";".join(A)
        self.gbfaccounts[id][3] = 1
        self.gbfaccounts[id][5] = self.getJST()
        self.savePending = True
        return True

    def versionToDateStr(self, version_number): # convert gbf version number to its timestamp
        try: return "{0:%Y/%m/%d %H:%M} JST".format(datetime.fromtimestamp(int(version_number)) + timedelta(seconds=32400)) # JST
        except: return ""

    async def getGameversion(self): # retrieve the game version
        res = await self.sendRequest('http://game.granbluefantasy.jp/', headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36', 'Accept-Language':'en', 'Accept-Encoding':'gzip, deflate', 'Host':'game.granbluefantasy.jp', 'Connection':'keep-alive'}, decompress=True, no_base_headers=True)
        if res is None: return None
        try:
            return int(self.vregex.findall(str(res))[0])
        except:
            return "Maintenance" # if not found on the page, return "Maintenance"

    async def isGameAvailable(self): # use the above to check if the game is up
        v = await self.getGameversion()
        return ((v is not None) and (v != "Maintenance"))

    def updateGameversion(self, v): # update self.gbfversion and return a value depending on what happened
        try:
            i = int(v)
            if v is None:
                return 1 # unchanged because of invalid parameter
            elif self.gbfversion is None:
                self.gbfversion = v
                self.savePending = True
                return 2 # value is set
            elif self.gbfversion != v:
                self.gbfversion = v
                self.savePending = True
                return 3 # update happened
            return 0 # unchanged
        except:
            return -1 # v isn't an integer

    def runTask(self, name, func): # start a task (cancel a previous one with the same name)
        self.cancelTask(name)
        self.tasks[name] = self.loop.create_task(func())

    def cancelTask(self, name): # cancel a task
        if name in self.tasks:
            self.tasks[name].cancel()

    async def startTasks(self): # start our tasks
        self.runTask('status', self.statustask)
        self.runTask('invitetracker', self.invitetracker)
        self.runTask('cleansave', self.cleansave)
        for c in self.cogs:
            try:
                self.get_cog(c).startTasks()
            except:
                pass
        msg = ""
        for t in self.tasks:
            msg += "\▫️ {}\n".format(t)
        if msg != "":
            await bot.send('debug', embed=bot.buildEmbed(title="{} user tasks started".format(len(self.tasks)), description=msg, timestamp=datetime.utcnow()))

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

    async def callCommand(self, ctx, command, *args, **kwargs): #call a command in a cog
        for cn in self.cogs:
            cmds = self.get_cog(cn).get_commands()
            for cm in cmds:
                if cm.name == command:
                    await ctx.invoke(cm, *args, **kwargs)
                    return
        raise Exception("Command `{}` not found".format(command))

    async def send(self, channel_name : str, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send something to a channel
        try:
            return await self.channels[channel_name].send(msg, embed=embed, file=file)
        except Exception as e:
            self.errn += 1
            print("Channel {} error: {}".format(channel_name, e))
            return None

    async def sendMulti(self, channel_names : list, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send to multiple channel at the same time
        r = []
        for c in channel_names:
            try:
                r.append(await self.send(c, msg, embed, file))
            except:
                await self.sendError('sendMulti', 'Failed to send a message to channel `{}`'.format(c))
        return r

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

    def delFile(self, filename):
        try: os.remove(filename)
        except: pass

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
# Prepare the bot
bot = Mizabot()

# #####################################################################################
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
        await bot.send('debug', embed=bot.buildEmbed(title="{} is Ready".format(bot.user.display_name), description="**Version** {}\n**CPU**▫️{}%\n**Memory**▫️{}MB\n**Tasks Count**▫️{}\n**Servers Count**▫️{}\n**Pending Servers**▫️{}\n**Cogs Loaded**▫️{}/{}\n**Twitter**▫️{}".format(bot.botversion, bot.process.cpu_percent(), bot.process.memory_full_info().uss >> 20, len(asyncio.all_tasks()), len(bot.guilds), len(bot.guilddata['pending']), len(bot.cogs), bot.cogn, (bot.twitter_api is not None)), thumbnail=bot.user.avatar_url, timestamp=datetime.utcnow()))
        await bot.startTasks() # start the tasks
        bot.boot_flag = True
    if bot.boot_msg != "":
        await bot.send('debug', embed=bot.buildEmbed(title="Boot message", description=bot.boot_msg, timestamp=datetime.utcnow()))
        bot.boot_msg = ""

@bot.event
async def on_guild_join(guild): # when the bot joins a new guild
    id = str(guild.id)
    if id == str(bot.ids['debug_server']):
        return
    elif id in bot.guilddata['banned'] or str(guild.owner.id) in bot.guilddata['owners']: # leave if the server is blacklisted
        try:
            await bot.send('debug', embed=bot.buildEmbed(title="Banned guild request", description="{} ▫️ {}".format(guild.name, id), thumbnail=guild.icon_url, footer="Owner: {} ▫️ {}".format(guild.owner.name, guild.owner.id)))
        except Exception as e:
            await bot.send('debug', "on_guild_join(): {}".format(e))
        await guild.leave()
    else: # notify me and add to the pending servers
        bot.guilddata['pending'][id] = guild.name
        bot.savePending = True
        await guild.owner.send(embed=bot.buildEmbed(title="Pending guild request", description="Wait until my owner approve the new server", thumbnail=guild.icon_url))
        await bot.send('debug', embed=bot.buildEmbed(title="Pending guild request", description="{} ▫️ {}".format(guild.name, id), thumbnail=guild.icon_url, footer="Owner: {} ▫️ {}".format(guild.owner.name, guild.owner.id)))

@bot.event
async def on_message(message): # to do something with a message
    if await bot.runOnMessageCallback(message):
        # end
        await bot.process_commands(message) # don't forget

@bot.check # authorize or not a command on a global scale
async def global_check(ctx):
    id = str(ctx.guild.id)
    if id in bot.guilddata['banned'] or str(ctx.guild.owner.id) in bot.guilddata['owners']: # ban check
        await ctx.guild.leave() # leave the server if banned
        return False
    elif id in bot.guilddata['pending']: # pending check
        await bot.react(ctx.message, 'cooldown')
        return False
    elif ctx.guild.owner.id in bot.bannedusers:
        await bot.send('debug', embed=bot.buildEmbed(title="[TEST] Banned message by {}".format(ctx.message.author), thumbnail=ctx.author.avatar_url, fields=[{"name":"Command", "value":'`{}`'.format(ctx.message.content)}, {"name":"Server", "value":ctx.message.author.guild.name}, {"name":"Message", "value":msg}], footer='{}'.format(ctx.message.author.id), timestamp=datetime.utcnow()))
        return False
    return True

@bot.event # if an error happens
async def on_command_error(ctx, error):
    msg = str(error)
    if msg.find('You are on cooldown.') == 0:
        await bot.react(ctx.message, 'cooldown')
    elif msg.find('required argument that is missing') != -1:
        return
    elif msg.find('check functions for command') != -1:
        return
    elif msg.find('Member "') == 0 or msg.find('Command "') == 0 or msg.startswith('Command raised an exception: Forbidden: 403'):
        return
    else:
        bot.errn += 1
        await bot.send('debug', embed=bot.buildEmbed(title="⚠ Error caused by {}".format(ctx.message.author), thumbnail=ctx.author.avatar_url, fields=[{"name":"Command", "value":'`{}`'.format(ctx.message.content)}, {"name":"Server", "value":ctx.message.author.guild.name}, {"name":"Message", "value":msg}], footer='{}'.format(ctx.message.author.id), timestamp=datetime.utcnow()))

# (You) pin board system
@bot.event
async def on_raw_reaction_add(payload):
    try:
        if payload.channel_id != bot.ids.get('you_general', -1):
            return
        message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        reactions = message.reactions
    except Exception as e:
        await bot.sendError('raw_react', str(e))
        return
    me = message.guild.me
    role = message.guild.get_role(bot.ids.get('you_member', 0))
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
            # search for image url if no attachment
            if 'image' not in dict:
                s = content.find("http")
                for ext in ['.png', '.jpeg', '.jpg', '.gif', '.webp']:
                    e = content.find(ext, s)
                    if e != -1:
                        e += len(ext)
                        break
                if content.find(' ', s, e) == -1 and s != -1:
                    dict['image'] = {'url':content[s:e]}
            embed = discord.Embed.from_dict(dict)
            embed.timestamp=message.created_at
            await bot.send('pinned', embed=embed)
            return

# used by /gbfg/ and (You)
@bot.event
async def on_member_update(before, after):
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
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
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if member.guild.id in guilds:
        await bot.send(guilds[member.guild.id], embed=bot.buildEmbed(author={'name':"{} ▫️ Left the server".format(member.name), 'icon_url':member.avatar_url}, footer="User ID: {}".format(member.id), timestamp=datetime.utcnow(), color=0xff0000))

@bot.event
async def on_member_join(member):
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if member.guild.id in guilds:
        channel = guilds[member.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(author={'name':"{} ▫️ Joined the server".format(member.name), 'icon_url':member.avatar_url}, footer="User ID: {}".format(member.id), timestamp=datetime.utcnow(), color=0x00ff3c))

@bot.event
async def on_member_ban(guild, user):
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if guild.id in guilds:
        await bot.send(guilds[guild.id], embed=bot.buildEmbed(author={'name':"{} ▫️ Banned from the server".format(user.name), 'icon_url':user.avatar_url}, footer="User ID: {}".format(user.id), timestamp=datetime.utcnow(), color=0xff0000))

@bot.event
async def on_member_unban(guild, user):
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if guild.id in guilds:
        await bot.send(guilds[guild.id], embed=bot.buildEmbed(author={'name':"{} ▫️ Unbanned from the server".format(user.name), 'icon_url':user.avatar_url}, footer="User ID: {}".format(user.id), timestamp=datetime.utcnow(), color=0x00ff3c))

@bot.event
async def on_guild_emojis_update(guild, before, after):
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
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
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if role.guild.id in guilds:
        channel = guilds[role.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(title="Role created ▫️ `{}`".format(role.name), footer="Role ID: {}".format(role.id), timestamp=datetime.utcnow(), color=0x00ff3c))

@bot.event
async def on_guild_role_delete(role):
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if role.guild.id in guilds:
        channel = guilds[role.guild.id]
        await bot.send(channel, embed=bot.buildEmbed(title="Role deleted ▫️ `{}`".format(role.name), footer="Role ID: {}".format(role.id), timestamp=datetime.utcnow(), color=0xff0000))

@bot.event
async def on_guild_role_update(before, after):
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
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
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if channel.guild.id in guilds:
        await bot.send(guilds[channel.guild.id], embed=bot.buildEmbed(title="Channel created ▫️ `{}`".format(channel.name), footer="Channel ID: {}".format(channel.id), timestamp=datetime.utcnow(), color=0xebe007))

@bot.event
async def on_guild_channel_delete(channel):
    if 'you_server' not in bot.ids or 'gbfg' not in bot.ids: return
    guilds = {bot.ids['you_server'] : 'youlog', bot.ids['gbfg'] : 'gbfglog'}
    if channel.guild.id in guilds:
        await bot.send(guilds[channel.guild.id], embed=bot.buildEmbed(title="Channel deleted ▫️ `{}`".format(channel.name), footer="Channel ID: {}".format(channel.id), timestamp=datetime.utcnow(), color=0x8a8306))

# #####################################################################################
# Start the bot
# load cogs
grace = GracefulExit(bot)
bot.cogn = cogs.load(bot)
bot.mainLoop()