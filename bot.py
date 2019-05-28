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

# ########################################################################################
# custom help command used by the bot
class MizabotHelp(commands.DefaultHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.dm_help = True # force dm only (although our own functions only send in dm, so it should be unneeded)

    async def send_bot_help(self, mapping): # main help command (called when you do $help). this function reuse the code from the commands.DefaultHelpCommand class
        ctx = self.context # get $help context
        bot = ctx.bot
        me = ctx.author.guild.me # bot own user infos

        await ctx.message.add_reaction('✅') # white check mark

        if bot.description: # send the bot description first
            await ctx.author.send(embed=bot.buildEmbed(title=me.name + " Help", description=bot.description, thumbnail=me.avatar_url)) # author.send = dm

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
                if len(embed) > 5800: # embeds have a 6000 characters limit, I send and make a new embed if needed
                    await ctx.author.send(embed=embed)
                    embed = discord.Embed(title=bot.getEmoteStr('mark') + " **" + category[:-1] + "** Category", color=embed.colour)
                if len(embed.fields) > 0: # only send if there is at least one field
                    await ctx.author.send(embed=embed)

        # final words
        await ctx.author.send(embed=bot.buildEmbed(title=bot.getEmoteStr('question') + " Need more help?", description="Use help <command name>\nOr help <category name>"))

    async def send_command_help(self, command): # same thing, but for a command ($help <command>)
        ctx = self.context
        bot = ctx.bot
        await self.context.message.add_reaction('✅') # white check mark
        # send the help
        embed = discord.Embed(title=bot.getEmoteStr('mark') + " **" + command.name + "** Command", description=command.help, color=random.randint(0, 16777216)) # random color
        embed.add_field(name="Usage", value=self.get_command_signature(command), inline=False)
        await ctx.author.send(embed=embed)

    async def send_cog_help(self, cog): # category help ($help <category)
        ctx = self.context
        bot = ctx.bot
        await ctx.message.add_reaction('✅') # white check mark

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands) # sort
        embed = discord.Embed(title=bot.getEmoteStr('mark') + " **" + cog.qualified_name + "** Category", description=cog.description, color=random.randint(0, 16777216)) # random color
        for c in filtered:
            embed.add_field(name=c.name + " ▫ " + self.get_command_signature(c), value=c.short_doc, inline=False)
        if len(embed.fields) > 0:
            await ctx.author.send(embed=embed)

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
        self.starttime = datetime.utcnow()
        self.process = psutil.Process() # script process
        self.process.cpu_percent()
        self.errn = 0 # count the number of errors
        self.cogn = 0 # will store how many cogs are expected to be in memory (check at the bottom of this file)
        self.exit_flag = False
        self.savePending = False
        self.special = False
        self.tasks = {}
        self.autosaving = False
        self.drive = MizabotDrive(self)
        self.channels = {}
        self.newserver = {'servers':[], 'owners':[], 'pending':{}}
        self.gw = {'state':False}
        self.maintenance = {"state" : False, "time" : None, "duration" : "0"}
        self.striketimes = {}
        self.spark = [{}, []]
        self.stream = {'time':None, 'content':[]}
        self.schedule = []
        self.prefixes = {}
        self.st = {}
        self.bot_maintenance = None
        self.reminders = {}
        self.lucilius = {}
        self.tokens = {}
        self.baguette = {}
        self.baguette_save = {}
        self.ids = {}
        self.permitted = {}
        self.games = {}
        self.strings = {}
        self.specialstrings = {}
        self.emotes = {}
        # load
        self.loadConfig()
        self.drive.load()
        if not self.load(): exit(2) # first loading must success
        super().__init__(command_prefix=self.prefix, case_insensitive=True, description='''MizaBOT version 5.1
Source code: https://github.com/MizaGBF/MizaBOT.
Default command prefix is '$', use $setPrefix to change it on your server.''', help_command=MizabotHelp(), activity=discord.activity.Game(name='Booting up, please wait'), owner=self.ids['owner'])

    def mainLoop(self): # main loop
        while self.running:
            try:
                self.loop.run_until_complete(self.start(self.tokens['discord']))
            except Exception as e:
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
        return '$' # default prefix is $

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
                self.permitted = data['permitted']
                self.games = data['games']
                self.strings = data['strings']
                self.specialstrings = data['specialstrings']
                self.emotes = data['emotes']
                self.lucilius = data['lucilius']
        except Exception as e:
            print('loadConfig(): ' + str(e))
            exit(1) # instant quit if error

    def load(self): # same thing but for save.json
        try:
            with open('save.json') as f:
                data = json.load(f, object_pairs_hook=self.json_deserial_dict) # deserializer here
                # more check to avoid issues when reloading the file during runtime
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
        await self.send('debug', embed=self.buildEmbed(title="Autosaving...", footer="{0:%Y/%m/%d %H:%M} JST".format(self.getJST())))
        if self.save():
            await self.send('debug', embed=self.buildEmbed(title="Autosave Success", footer="{0:%Y/%m/%d %H:%M} JST".format(self.getJST())))
            self.savePending = False
        else:
            await self.send('debug', embed=self.buildEmbed(title="Autosave Failed", footer="{0:%Y/%m/%d %H:%M} JST".format(self.getJST())))
            discordDump = True
        if discordDump:
            try:
                with open('save.json', 'r') as infile:
                    await self.send('debug', 'save.json', file=discord.File(infile))
            except Exception as e:
                pass
        self.autosaving = False

    async def statustask(self): # background task changing the bot status and calling autosave()
        await self.send('debug', embed=self.buildEmbed(title="statustask() started", footer="{0:%Y/%m/%d %H:%M} JST".format(self.getJST())))
        while True:
            try:
                await self.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=random.choice(self.games)))
                # check if it's time for the bot maintenance for me (every 2 weeks or so)
                c = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                if self.bot_maintenance and c > self.bot_maintenance and (c.day == 1 or c.day == 17):
                    await self.send('debug', self.get_user(self.owner_id).mention + " ▪ Time for maintenance!")
                    self.bot_maintenance = c
                    self.savePending = True
                await asyncio.sleep(2400)
                # autosave
                if self.savePending and not self.exit_flag:
                    await self.autosave()
            except asyncio.CancelledError:
                await self.sendError('statustask', 'cancelled')
                return
            except Exception as e:
                await self.sendError('statustask', str(e))

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
        if ctx.author.guild_permissions.manage_messages:
            return True
        return False

    def isOwner(self, ctx): # check if the member has the manage_message permission
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
        if e is None: return ":" + key + ":"
        return str(e)

    async def react(self, ctx, key): # react using a custom emote defined in config.json
        try:
            await ctx.message.add_reaction(self.getEmote(key))
        except Exception as e:
            await self.sendError('react', str(e))

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
        return embed

    def runTask(self, name, func): # start a task (cancel a previous one with the same name)
        self.cancelTask(name)
        self.tasks[name] = self.loop.create_task(func())

    def cancelTask(self, name): # cancel a task
        if name in self.tasks:
            self.tasks[name].cancel()

    def startTasks(self): # start our tasks
        self.runTask('status', self.statustask)
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
        if cmds:
            for c in cmds:
                if c.name == command:
                    await ctx.invoke(c, *args, **kwargs)
                    break

    async def send(self, channel_name : str, msg : str = "", embed : discord.Embed = None, file : discord.File = None): # send something to a channel
        try:
            await self.channels[channel_name].send(msg, embed=embed, file=file)
        except Exception as e:
            self.errn += 1
            print(channel_name + " error: " + str(e))

    async def sendError(self, func_name : str, msg : str, id = None): # send an error to the debug channel
        if id is None: id = ""
        else: id = " " + str(id)
        self.errn += 1
        await self.send('debug', embed=self.buildEmbed(title="Error in " + func_name + "()" + id, description=msg, footer="{0:%Y/%m/%d %H:%M} JST".format(self.getJST())))

    def getJST(self, nomicro=False): # get the time in jst
        if nomicro: return datetime.utcnow().replace(microsecond=0) + timedelta(seconds=32400)
        return datetime.utcnow() + timedelta(seconds=32400)

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
        if self.bot.save(False):
            print('Autosave Success')
        else:
            print('Autosave Failed')
    exit(0) # not graceful at all

# make the bot instance
bot = Mizabot()

# bot events
@bot.event
async def on_ready(): # when the bot starts
    bot.setChannel('debug', 'debug_channel') # set our debug channel
    bot.startTasks() # start the tasks
    # send a pretty message
    await bot.send('debug', embed=bot.buildEmbed(title=bot.user.display_name + " is Ready", description="**Server Count**: " + str(len(bot.guilds)) + "\n**Servers Pending**: " + str(len(bot.newserver['pending'])) + "\n**Tasks Count**: " + str(len(asyncio.all_tasks())) + "\n**Cogs Loaded**: " + str(len(bot.cogs)) + "/" + str(bot.cogn), thumbnail=bot.user.avatar_url, inline=True, footer="{0:%Y/%m/%d %H:%M} JST".format(bot.getJST())))

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
        await bot.send('debug', embed=bot.buildEmbed(title="⚠ Error caused by " + str(ctx.message.author), thumbnail=ctx.author.avatar_url, fields=[{"name":"Command", "value":'`' + ctx.message.content + '`'}, {"name":"Server", "value":ctx.message.author.guild.name}, {"name":"Message", "value":msg}], footer="{0:%Y/%m/%d %H:%M} JST".format(bot.getJST())))

@bot.event
async def on_member_update(before, after):
    try:
        await bot.get_cog('Lucilius').memberUpdate(before, after)
    except Exception as e:
        pass

@bot.event
async def on_member_remove(member):
    try:
        await bot.get_cog('Lucilius').memberRemove(member)
    except Exception as e:
        pass

# load cogs
try:
    from cogs.general import General
    bot.add_cog(General(bot))
except Exception as e:
    print("import General: " + str(e))
    bot.errn += 1
bot.cogn += 1 # count the cogs

try:
    from cogs.gbf_game import GBF_Game
    bot.add_cog(GBF_Game(bot))
except Exception as e:
    print("import GBF_Game: " + str(e))
    bot.errn += 1
bot.cogn += 1

try:
    from cogs.gbf_utility import GBF_Utility
    bot.add_cog(GBF_Utility(bot))
except Exception as e:
    print("import GBF_Utility: " + str(e))
    bot.errn += 1
bot.cogn += 1

try:
    from cogs.gw import GW
    bot.add_cog(GW(bot))
except Exception as e:
    print("import GW: " + str(e))
    bot.errn += 1
bot.cogn += 1

try:
    from cogs.management import Management
    bot.add_cog(Management(bot))
except Exception as e:
    print("import Management: " + str(e))
    bot.errn += 1
bot.cogn += 1

try:
    from cogs.owner import Owner
    bot.add_cog(Owner(bot))
except Exception as e:
    print("import Owner: " + str(e))
    bot.errn += 1
bot.cogn += 1

try:
    from cogs.lucilius import Lucilius
    bot.add_cog(Lucilius(bot))
except Exception as e:
    print("import Lucilius: " + str(e))
    bot.errn += 1
bot.cogn += 1

try:
    from baguette import Baguette
    bot.add_cog(Baguette(bot))
except Exception as e:
    print("import Baguette: " + str(e))
    bot.errn += 1
bot.cogn += 1

# create the graceful exit
grace = GracefulExit(bot)

# start the loop
bot.mainLoop()
