import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta, timezone
import asyncio
from urllib.request import urlopen
from urllib import request, parse
from socket import timeout
import json
import parser
import math
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import time
from operator import itemgetter
import itertools
# ^ some modules might be unused, I'll clean up in the future

# it's a mess so please read these comments to not get lost:

# starting with our global variables (most are initialized by loadConfig() or load() )
# TO DO : make a class maybe. I tried but it's a pain to edit everything
# discord key
bot_token = None
# google drive folder ID where is stored the save data
bot_drive = None
# bot description
description = '''MizaBOT version 4.6
Source code: https://github.com/MizaGBF/MizaBOT.
Default command prefix is '$', use $setPrefix to change it on your server.'''
# various ids and discord stuff (check the save/config.json examples for details)
owner_id = None
debug_channel = None
lucilog_channel = None
lucimain_channel = None
you_id = None
debug_id = None
debug_chid = None
select_channel = {}
you_announcement = None
xil_id = None
wawi_id = None
xil_str = []
wawi_str = []
gbfg_id = None
bot_emotes = {}
# used for debugging
debug_str = ""
# server settings
banned_server = []
banned_owner = []
pending_server = {}
# (you) gw buff related id (of corresponding roles)
buff_role_id = []
fo_role_id = [] # [role, corresponding custom emote key]
gl_role_id = []
# for the bot message status
mygames = []
# used by the gw mode
gw = False
gw_dates = {}
gw_buffs = []
gw_task = None
gw_skip = False
# used by the gbf maintenance mode
maintenance = None
maintenance_d = 0
# server specific settings for st
st_list = {}
# user specific settings for their sparks
spark_list = {}
spark_ban = []
# gbf stream text
stream_txt = []
stream_time = None
# gbf schedule text
gbfschedule = ""
# server prefixes
prefixes = {}
# bot strings
bot_msgs = {}
# bot last maintenance date
bot_m = None
# graceful exit flag
exit_flag = False # if true, it means we just restarted after a heroku reboot
# gbfg lucilius variables
luciMember = {}
luciParty = [None, None, None, None, None, None]
luciBlacklist = {}
luciChannel = []
luciRole = None
luciLog = None
luciMain = None
luciServer = None
luciElemRole = [0, 0, 0, 0, 0, 0]
luciWarning = [0, 0, 0, 0, 0, 0]

# ignore this
gbfdd = None
try:
    import baguette
    gbfdm = True
except:
    gbfdm = False
gbfd = {}
gbfc = None

# we load some of the stuff above here
def loadConfig():
    global bot_token
    global gbfdd
    global debug_chid
    global owner_id
    global you_id
    global debug_id
    global select_channel
    global you_announcement
    global xil_id
    global xil_str
    global wawi_id
    global wawi_str
    global buff_role_id
    global fo_role_id
    global gl_role_id
    global mygames
    global bot_msgs
    global bot_drive
    global luciChannel
    global luciRole
    global luciLog
    global luciMain
    global luciServer
    global luciElemRole
    global gbfg_id
    global bot_emotes
    try:
        # we store everything in string, same for save.json, hence the int() calls
        with open('config.json') as f:
            data = json.load(f)
            bot_token = data['discord_token']
            bot_drive = data['drive_folder']
            if 'baguette' in data:
                gbfdd = data['baguette']
            debug_chid = int(data['debug'])
            debug_id = int(data['debug_server'])
            owner_id = int(data['you']['owner'])
            you_announcement = int(data['you']['announcement'])
            you_id = int(data['you']['server'])
            gbfg_id = int(data['gbfg'])
            bot_emotes = {}
            if 'emote' in data:
                for x in data['emote']:
                    bot_emotes[x] = int(data['emote'][x])
            select_channel = {}
            for s in data['select']:
                select_channel[int(s)] = []
                for c in data['select'][s]:
                    select_channel[int(s)].append(int(c))
            buff_role_id = []
            for i in data['you']['buff']:
                buff_role_id.append([int(i[0]), i[1]]) # buff role id + emote str (as put in bot_emotes)
            fo_role_id = []
            for i in data['you']['fo']:
                fo_role_id.append(int(i))
            gl_role_id = []
            for i in data['you']['gl']:
                gl_role_id.append(int(i))
            xil_id = int(data['xil']['id'])
            xil_str = []
            for i in data['xil']['str']:
                xil_str.append(i)
            wawi_id = int(data['wawi']['id'])
            wawi_str = []
            for i in data['wawi']['str']:
                wawi_str.append(i)
            mygames = []
            for i in data['games']:
                mygames.append(i)
            bot_msgs = data['str'].copy()
            if "lucilius" in data:
                luciServer = int(data["lucilius"]["server"])
                luciMain = int(data["lucilius"]["main"])
                luciLog = int(data["lucilius"]["log"])
                luciChannel = []
                for c in data["lucilius"]["channel"]:
                    luciChannel.append(int(c))
                luciRole = []
                for c in data["lucilius"]["role"]:
                    luciRole.append(int(c))
                luciElemRole = []
                for c in data["lucilius"]["elem"]:
                    luciElemRole.append(int(c))
            return True
    except Exception as e:
        print('Exception: ' + str(e))
        return False

# we do it right now and exit if an error happens
if not loadConfig():
    exit(1) # return code != 0 so heroku understands it's an unusual exit

# #####################################################################################
# various functions to check if an user has a certain role/permission, etc...
def isYouAndU2(roles): # check for (you) and (you)too roles
    for r in roles:
        if r.id == 281138561150091265 or r.id == 320225109447278592: # hard coded, might change the role ids later
            return True
    return False

def isYouServer(server): # check for (you) server id
    if server and server.id == you_id:
        return True
    return False

def isGBFGServer(server): # check for /gbfg/ server id
    if server and server.id == gbfg_id:
        return True
    return False

def isDebugServer(server): # check for the bot debug server id
    if server and server.id == debug_id:
        return True
    return False

def isWawiServer(server): # check for wawi server id
    if server and server.id == 327162356327251969:
        return True
    return False

def isAuthorized(guild, channel): # check if the command is authorized
    if guild.id in select_channel: # if the server uses this mode
        if channel.id in select_channel[guild.id]: # some commands are limited to the channel listed in select_channel (defined in config.json)
            return True
        return False
    return True

def isMod(author): # consider someone with the manage message permision is a mod
    if author.guild_permissions.manage_messages:
        return True
    return False

def isLuciliusMainChannel(channel): # check for the lucilius main channel
    if channel.id == luciMain:
        return True
    return False

def isLuciliusPartyChannel(channel): # check for a lucilius party channel
    if channel.id in luciChannel:
        return True
    return False

# function to fix the case (for $wiki)
def fixCase(term): # term is a string
    fixed = ""
    up = False
    if term.lower() == "and": # if it's just 'and', we don't don't fix anything and return a lowercase 'and'
        return "and"
    for i in range(0, len(term)): # for each character
        if term[i].isalpha(): # if letter
            if term[i].isupper(): # is uppercase
                if not up: # we haven't encountered an uppercase letter
                    up = True
                    fixed += term[i] # save
                else: # we have
                    fixed += term[i].lower() # make it lowercase and save
            elif term[i].islower(): # is lowercase
                if not up: # we haven't encountered an uppercase letter
                    fixed += term[i].upper() # make it uppercase and save
                    up = True
                else: # we have
                    fixed += term[i] # save
            else: # error case
                fixed += term[i] # we just save
        elif term[i] == "/" or term[i] == ":" or term[i] == "#": # we reset the uppercase detection if we encounter those
            up = False
            fixed += term[i]
        else: # everything else,
            fixed += term[i] # we save
    return fixed # return the result

# #####################################################################################
# math parser used by $calc
class Parser:
    def __init__(self, string, vars={}):
        self.string = string
        self.index = 0
        self.vars = {
            'pi' : 3.141592653589793,
            'e' : 2.718281828459045
            }
        for var in vars.keys():
            if self.vars.get(var) != None:
                raise Exception("Cannot redefine the value of " + var)
            self.vars[var] = vars[var]
    
    def getValue(self):
        value = self.parseExpression()
        self.skipWhitespace()
        if self.hasNext():
            raise Exception(
                "Unexpected character found: '" +
                self.peek() +
                "' at index " +
                str(self.index))
        return value
    
    def peek(self):
        return self.string[self.index:self.index + 1]
    
    def hasNext(self):
        return self.index < len(self.string)
    
    def skipWhitespace(self):
        while self.hasNext():
            if self.peek() in ' \t\n\r':
                self.index += 1
            else:
                return
    
    def parseExpression(self):
        return self.parseAddition()
    
    def parseAddition(self):
        values = [self.parseMultiplication()]
        while True:
            self.skipWhitespace()
            char = self.peek()
            if char == '+':
                self.index += 1
                values.append(self.parseMultiplication())
            elif char == '-':
                self.index += 1
                values.append(-1 * self.parseMultiplication())
            else:
                break
        return sum(values)
    
    def parseMultiplication(self):
        values = [self.parseParenthesis()]
        while True:
            self.skipWhitespace()
            char = self.peek()
            if char == '*' or char == 'x':
                self.index += 1
                values.append(self.parseParenthesis())
            elif char == '/':
                div_index = self.index
                self.index += 1
                denominator = self.parseParenthesis()
                if denominator == 0:
                    raise Exception(
                        "Division by 0 (occured at index " +
                        str(div_index) +
                        ")")
                values.append(1.0 / denominator)
            else:
                break
        value = 1.0
        for factor in values:
            value *= factor
        return value
    
    def parseParenthesis(self):
        self.skipWhitespace()
        char = self.peek()
        if char == '(':
            self.index += 1
            value = self.parseExpression()
            self.skipWhitespace()
            if self.peek() != ')':
                raise Exception(
                    "No closing parenthesis found at character "
                    + str(self.index))
            self.index += 1
            return value
        else:
            return self.parseNegative()
    
    def parseNegative(self):
        self.skipWhitespace()
        char = self.peek()
        if char == '-':
            self.index += 1
            return -1 * self.parseParenthesis()
        else:
            return self.parseValue()
    
    def parseValue(self):
        self.skipWhitespace()
        char = self.peek()
        if char in '0123456789.':
            return self.parseNumber()
        else:
            return self.parseVariable()
    
    def parseVariable(self):
        self.skipWhitespace()
        var = ''
        while self.hasNext():
            char = self.peek()
            if char.lower() in '_abcdefghijklmnopqrstuvwxyz0123456789':
                var += char
                self.index += 1
            else:
                break
        
        value = self.vars.get(var, None)
        if value == None:
            raise Exception(
                "Unrecognized variable: '" +
                var +
                "'")
        return float(value)
    
    def parseNumber(self):
        self.skipWhitespace()
        strValue = ''
        decimal_found = False
        char = ''
        
        while self.hasNext():
            char = self.peek()            
            if char == '.':
                if decimal_found:
                    raise Exception(
                        "Found an extra period in a number at character " +
                        str(self.index))
                decimal_found = True
                strValue += '.'
            elif char in '0123456789':
                strValue += char
            else:
                break
            self.index += 1
        
        if len(strValue) == 0:
            if char == '':
                raise Exception("Unexpected end found")
            else:
                raise Exception(
                    "I was expecting to find a number at character " +
                    str(self.index) +
                    " but instead I found a '" +
                    char)
    
        return float(strValue)
        
def evaluate(expression, vars={}):
    try:
        p = Parser(expression, vars)
        value = p.getValue()
    except Exception as ex:
        raise Exception(ex)
    
    # Return an integer type if the answer is an integer 
    if int(value) == value:
        return int(value)
    
    # If Python made some silly precision error 
    # like x.99999999999996, just return x + 1 as an integer 
    epsilon = 0.0000000001
    if int(value + epsilon) != int(value):
        return int(value + epsilon)
    elif int(value - epsilon) != int(value):
        return int(value)
    
    return value

# #####################################################################################
# get a 4chan thread
def get4chan(board, search): # be sure to not abuse it, you are supposed to not call the api more than once per second
    try:
        search = search.lower()
        url = 'http://a.4cdn.org/' + board + '/catalog.json' # board catalog url
        data = json.load(urlopen(url)) # we get the json
        threads = []
        for p in data:
            for t in p["threads"]:
                try:
                    if t["sub"].lower().find(search) != -1 or t["com"].lower().find(search) != -1:
                        threads.append(t["no"]) # store the thread ids matching our search word
                except:
                    pass
        threads.sort(reverse=True)
        return threads
    except:
        return []

# #####################################################################################
# pretty explicit
async def printServers():
    global debug_channel
    msg = '\n**Server List:**\n'
    for s in bot.guilds:
        msg += '**' + s.name + ':** ' + str(s.id) + ' owned by ' + s.owner.name + ' (' + str(s.owner.id) + ')\n'
    msg += '\n**Pending List:**\n'
    for s in pending_server:
        msg += '**' + pending_server[s] + ':** ' + str(s) + '\n'
    msg += '\n**Banned servers:**\n'
    for s in banned_server:
        msg += '[' + str(s) + '] '
    msg += '\n**Banned owners:**\n'
    for s in banned_owner:
        msg += '[' + str(s) + '] '
    await debug_channel.send(msg)

async def sendDebugStr(): # in theory: used to send debug strings we couldn't send
    global debug_channel
    global debug_str
    if debug_str:
        await debug_channel.send(debug_str)
        debug_str = ""

# get the general channel of a server
def getGeneral(server):
    for c in server.text_channels:
        if c.name.lower() == 'general':
            return c
    return None

# used by the gacha games
def getRoll(ssr):
    d = random.randint(1, 10000)
    if d < ssr: return 0
    elif d < 1500 + ssr: return 1
    return 2

legfestWord = {"double", "x2", "legfest", "flashfest"}
def isLegfest(word):
    if word.lower() in legfestWord: return 2 # 2 because the rates are doubled
    return 1

# other important stuff
def savePendingCallback(): # for external modules if any
    global savePending
    savePending = True

def getEmote(key): # retrieve a custom emote
    if key in bot_emotes:
        try:
            return bot.get_emoji(bot_emotes[key]) # ids are defined in config.json
        except:
            return None
    return None

def getEmoteStr(key): # same stuff but we get the string equivalent
    e = getEmote(key)
    if e is None: return ""
    return str(e)

async def react(ctx, key): # react using a custom emote
    try:
        await ctx.message.add_reaction(getEmote(key))
    except Exception as e:
        await ctx.send(str(e))

# GBF maintenance stuff
async def maintenanceCheck(ctx): # check the gbf maintenance status in memory and display a message
    global savePending
    global maintenance
    current_time = datetime.utcnow() + timedelta(seconds=32400)
    if maintenance:
        if current_time < maintenance:
            d = maintenance - current_time
            msg = getEmoteStr('cog') + " Maintenance in **" + str(d.days) + "d" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m**, for **" + str(maintenance_d) + " hour(s)**"
        else:
            d = current_time - maintenance
            if maintenance_d <= 0:
                msg = getEmoteStr('cog') + " Emergency maintenance on going"
            elif (d.seconds // 3600) >= maintenance_d:
                maintenance = None
                msg = "No Maintenance planned"
                savePending = True
            else:
                e = maintenance + timedelta(seconds=3600*maintenance_d)
                d = e - current_time
                msg = getEmoteStr('cog') + " Maintenance ends in **" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m**"
    else:
        msg = "No Maintenance planned"
    await ctx.send(msg)

def maintenanceUpdate(): # same thing pretty much but return False or True instead
    global savePending
    global maintenance
    current_time = datetime.utcnow() + timedelta(seconds=32400)
    if maintenance:
        if current_time < maintenance:
            d = maintenance - current_time
            return False
        else:
            d = current_time - maintenance
            if maintenance_d <= 0:
                return True
            elif (d.seconds // 3600) >= maintenance_d:
                maintenance = None
                savePending = True
                return False
            else:
                return False
    else:
        return False

# google drive login
# I recommend to generate credentials.json separately, as heroku has no storage
def loginDrive():
    global debug_str
    try:
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile("credentials.json")
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
        gauth.SaveCredentialsFile("credentials.json")
        return GoogleDrive(gauth)
    except Exception as e:
        print('Exception: ' + str(e))
        debug_str += 'load(): ' + str(e) + '\n'
        return None

# load settings
def loadDrive():
    drive = loginDrive()
    if not drive: return False
    file_list = drive.ListFile({'q': "'" + bot_drive + "' in parents and trashed=false"}).GetList()
    for s in file_list:
        if s['title'] == "save.json": s.GetContentFile(s['title'])
    return True

# same stuff as loadConfig()
def load():
    global banned_server
    global banned_owner
    global pending_server
    global prefixes
    global gw
    global gw_dates
    global gw_buffs
    global gw_skip
    global gw_task
    global maintenance
    global maintenance_d
    global st_list
    global spark_list
    global spark_ban
    global debug_str
    global bot_m
    global stream_txt
    global stream_time
    global gbfschedule
    global luciParty
    global luciBlacklist
    global luciMember
    global luciWarning
    global gbfd 
    with open('save.json') as f:
        data = json.load(f)
        if 'bot' in data: bot_m = datetime.strptime(data["bot"], '%Y-%m-%d %H:%M:%S')
        if gbfdm and 'baguette' in data:
            gbfd  = data['baguette']
            try:
                gbfc.set(gbfd)
            except:
                pass
        banned_server = []
        if 'banned_server' in data:
            for s in data['banned_server']:
                banned_server.append(int(s))
        banned_owner = []
        if 'banned_owner' in data:
            for s in data['banned_owner']:
                banned_owner.append(int(s))
        pending_server = {}
        if 'pending_server' in data:
            for s in data['pending_server']:
                pending_server[int(s)] = data['pending_server'][s]
        prefixes =  {}
        if 'prefixes' in data:
            for p in data['prefixes']:
                prefixes[int(p)] = data['prefixes'][p]
        if 'maintenance' in data and data['maintenance'][0]:
            maintenance = datetime.strptime(data['maintenance'][1], '%Y-%m-%d %H:%M:%S')
            maintenance_d = int(data['maintenance'][2])
        else:
            maintenance = None
            maintenance_d = 0
        if 'stream' in data: stream_txt = data['stream']
        if 'stream_time' in data and data['stream_time']: stream_time = datetime.strptime(data['stream_time'], '%Y-%m-%d %H:%M:%S')
        if 'schedule' in data: gbfschedule = data['schedule']
        st_list = {}
        if 'st' in data:
            for st in data['st']:
                st_list[int(st)] = [int(data['st'][st][0]), int(data['st'][st][1])]
        spark_list = {}
        if 'spark' in data:
            for sp in data['spark']:
                spark_list[int(sp)] = [int(data['spark'][sp][0]), int(data['spark'][sp][1]), int(data['spark'][sp][2])]
        spark_ban = []
        if 'spark_ban' in data:
            for spb in data['spark_ban']:
                spark_ban.append(int(spb))
        if 'lucilius' in data:
            luciParty = []
            for p in data['lucilius']:
                if p is None:
                    luciParty.append(None)
                else:
                    luciParty.append([ datetime.strptime(p[0], '%Y-%m-%d %H:%M:%S'), p[1] ])
                    for y in range(2, len(p)):
                        luciParty[-1].append(int(p[y]))
        if 'luciliusban' in data:
            luciBlacklist = {}
            for p in data['luciliusban']:
                luciBlacklist[int(p)] = int(data['luciliusban'][p])
        if 'luciliusmember' in data:
            luciMember = {}
            for p in data['luciliusmember']:
                luciMember[int(p)] = 0
        if 'luciliuswarning' in data:
            luciWarning = []
            for w in data['luciliuswarning']:
                luciWarning.append(int(w))
        gw = False
        if gw_task:
            gw_task.cancel()
            gw_task = None
        if 'gw' in data:
            if 'state' in data['gw']: gw = data['gw']['state']
            if 'buffs' in data['gw']: gw_buffs = data['gw']['buffs']
            if 'skip' in data['gw']: gw_skip = data['gw']['skip']
            if 'dates' in data['gw']:
                gw_dates = {}
                for d in data['gw']['dates']:
                    gw_dates[d] = datetime.strptime(data['gw']['dates'][d], '%Y-%m-%d %H:%M:%S')
            if 'buffs' in data['gw']:
                gw_buffs = data['gw']['buffs']
                for i in range(0, len(gw_buffs)):
                    gw_buffs[i][0] = datetime.strptime(gw_buffs[i][0], '%Y-%m-%d %H:%M:%S')
        return True

# save settings
def saveDrive(data, sortBackup):
    drive = loginDrive()
    if not drive: return False
    # backup
    file_list = drive.ListFile({'q': "'" + bot_drive + "' in parents and trashed=false"}).GetList()
    if sortBackup and not exit_flag and len(file_list) > 9: # delete if we have too many backups
        for f in file_list:
            if f['title'].find('backup') == 0:
                f.Delete()
    for f in file_list:
        if f['title'] == "save.json":
            f['title'] = "backup_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
            f.Upload()
    # saving
    s = drive.CreateFile({'title':'save.json', 'mimeType':'text/JSON', "parents": [{"kind": "drive#file", "id": bot_drive}]})
    s.SetContentString(data)
    s.Upload()
    return True

def save(sortBackup=True):
    global debug_str
    try:
        data = {}
        if bot_m:
            data['bot'] = bot_m
        data['banned_server'] = banned_server
        data['banned_owner'] = banned_owner
        data['pending_server'] = pending_server
        data['prefixes'] = prefixes
        if gbfdm:
            data['baguette'] = gbfc.get()
        if maintenance:
            data['maintenance'] = [True, maintenance, maintenance_d]
        else:
            data['maintenance'] = [False]
        data['stream'] = stream_txt.copy()
        if stream_time:
            data['stream_time'] = stream_time
        else:
            data['stream_time'] = False
        data['schedule'] = gbfschedule
        data['st'] = st_list.copy()
        data['spark'] = spark_list.copy()
        data['spark_ban'] = spark_ban.copy()
        data['lucilius'] = luciParty.copy()
        data['luciliusban'] = luciBlacklist.copy()
        data['luciliusmember'] = luciMember.copy()
        data['luciliuswarning'] = luciWarning.copy()
        data['gw'] = {}
        data['gw']['state'] = gw
        data['gw']['dates'] = gw_dates.copy()
        data['gw']['buffs'] = gw_buffs.copy()
        data['gw']['skip'] = gw_skip
        with open('save.json', 'w') as outfile:
            json.dump(data, outfile, default=str)
        if not saveDrive(json.dumps(data, default=str), sortBackup):
            raise Exception("Couldn't save to google drive")
    except Exception as e:
        print(e)
        debug_str += 'save(): ' + str(e) + '\n'
        return False
    return True

autosaving = False # very dirty way to check so we don't run two autosave
async def autosave(discordDump = False):
    global savePending
    global autosaving
    if autosaving: return
    autosaving = True
    await debug_channel.send('Saving...')
    if save():
        await debug_channel.send('Autosave Success')
        savePending = False
    else:
        await sendDebugStr()
        await debug_channel.send('Autosave Failed')
        discordDump = True
    if discordDump:
        try:
            with open('save.json', 'r') as infile:
                await debug_channel.send('Latest save', file=discord.File(infile))
        except Exception as e:
            pass
    autosaving = False

# ########################################################################################
# custom help command
class MizabotHelp(commands.DefaultHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.sort_commands = False
        self.dm_help = True

    async def send_bot_help(self, mapping): # main help command
        ctx = self.context
        bot = ctx.bot

        await ctx.message.add_reaction('✅') # white check mark

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)
            self.paginator.close_page()

        no_category = "No Category:"
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name + ':' if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, commands in to_iterate:
            if self.helpAuthorize(ctx, category[:-1]):
                commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
                self.add_indented_commands(commands, heading=category, max_size=max_size)
                self.paginator.close_page()

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        await self.context.message.add_reaction('✅') # white check mark
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()

    async def send_group_help(self, group):
        await self.context.message.add_reaction('✅') # white check mark
        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading)

        if filtered:
            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog): # category help
        if not self.helpAuthorize(self.context, cog.qualified_name):
            return
        await self.context.message.add_reaction('✅') # white check mark
        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

    def helpAuthorize(self, ctx, category): # some categories are hidden depending on who or where you are using $help
        if category == "Lucilius" and ctx.author.guild.id != luciServer: return False
        if category == "Owner" and ctx.author.id != owner_id: return False
        if category == "Baguette" and ctx.author.id != owner_id: return False
        if category == "No Category": return False
        return True

# ########################################################################################
# the function used to check which prefix the server is using (default is $)
def prefix(client, message):
    try:
        id = message.guild.id
        if id in prefixes:
            return prefixes[id]
    except:
        pass
    return '$'

# ########################################################################################
# done declaring some of the stuff
# we start the discord bot
loadDrive() # download the save file
first_load = load() # load the save file
bot = commands.Bot(command_prefix=prefix, case_insensitive=True, description=description, help_command=MizabotHelp())
isRunning = True
savePending = False

# background task running to change the bot status and manage the autosave
async def backtask():
    global bot_m
    global savePending
    while True:
        await bot.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=random.choice(mygames)))
        await asyncio.sleep(2400)
        # check if it's time for some maintenance for me (every 2 weeks or so)
        c = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if bot_m and c > bot_m and (c.day == 1 or c.day == 17):
            await debug_channel.send(bot.get_user(owner_id).mention + " It's maintenance time!")
            bot_m = c
            savePending = True
        # autosave
        if savePending and not exit_flag:
            await autosave()

# background task managing the gbfg lucilius party system
async def lucitask():
    global savePending
    global luciParty
    global luciMember
    global luciWarning
    await debug_channel.send("lucitask() is starting up")
    guild = bot.get_guild(luciServer)
    await asyncio.sleep(5)
    while True:
        if exit_flag: return
        # party expire
        try:
            c = datetime.utcnow()
            for i in range(0, len(luciParty)):
                if luciParty[i] is not None: # check if the party is in use
                    # warn the users of the time left
                    if luciParty[i][1] == "Playing" and luciWarning[i] < 1 and (c - luciParty[i][0]) > timedelta(seconds=3000): # check if close to time limit AND not extended AND no warning has been issued
                        luciWarning[i] = 1
                        savePending = True
                        lc = bot.get_channel(luciChannel[i])
                        try:
                            await lc.send(getEmoteStr('clock') + " " + bot.get_user(luciParty[i][2]).mention + " Less than 10 minutes left, use `%lextend` if you need more time") # we notify
                        except:
                            await lc.send(getEmoteStr('clock') + " Less than 10 minutes left, use `%lextend` if you need more time") # we notify
                    # check the time left
                    if luciParty[i][1] == "Preparing": gameover = ((c - luciParty[i][0]) > timedelta(seconds=600))
                    elif luciParty[i][1] == "Playing": gameover = ((c - luciParty[i][0]) > timedelta(seconds=3600))
                    elif luciParty[i][1] == "Playing (Extended)": gameover = ((c - luciParty[i][0]) > timedelta(seconds=10800))
                    else: gameover = False
                    if gameover: # if true, it's over, disband the party
                        if luciParty[i][1] != "Preparing":
                            role = guild.get_role(luciRole[i])
                            for j in range(2, len(luciParty[i])):
                                try:
                                    await guild.get_member(luciParty[i][j]).remove_roles(role)
                                except:
                                    pass
                        luciParty[i] = None
                        luciWarning[i] = 0
                        savePending = True
                        await lucimain_channel.send(":x: **Party** " + getEmoteStr(str(i+1)) + " has been automatically disbanded (Time Limit exceeded)")
                        await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: Party #" + str(i+1) + " has been automatically disbanded (Time Limit exceeded)")
        except Exception as e:
            await debug_channel.send("lucitask() A: " + str(e))
        await asyncio.sleep(0.001)
        # member check
        try:
            fulllist = lucimain_channel.members # members in the channel
            memberlist = {}
            to_add = {}
            to_del = {}
            msg = ""
            for m in fulllist: # reading the current real member list
                if m.id not in luciMember: # if not in our database
                    msg += "**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + m.display_name + " joined the channel (discord id: " + str(m) + " / id: " + str(m.id) + ")\n" # update the log
                    to_add[m.id] = 0 # plan to add
                    if len(msg) > 1500: 
                        await lucilog_channel.send(msg)
                        msg = ""
                else: # take not we encountered tthis member
                    memberlist[m.id] = m
            for i in luciMember: # reading our database
                if i not in memberlist: # if not in the members we encountered, he/she left
                    u = guild.get_member(i) # get the user
                    if u is not None: # update the lod
                        msg += "**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + u.display_name + " left the channel (discord id: " + str(u) + " / id: " + str(u.id) + ")\n"
                    else:
                        msg += "**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: <deleted-user> left the channel (id: " + str(i) + ")\n"
                    to_del[i] = 0
                    if len(msg) > 1500: 
                        await lucilog_channel.send(msg)
                        msg = ""
            for i in to_add:
                luciMember[i] = 0
            for i in to_del:
                luciMember.pop(i)
            if len(to_add) > 0 or len(to_del) > 0:
                savePending = True
                await debug_channel.send("Lucilius: Member List changed")
            if len(msg) > 0:
                await lucilog_channel.send(msg)
        except Exception as e:
            await debug_channel.send("lucitask() B: " + str(e))
        await asyncio.sleep(80)

# THE FIRST THING EVER RUNNING BY THE BOT IS HERE
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.activity.Game(name='Booting up, please wait'))
    global debug_channel
    global lucilog_channel
    global lucimain_channel
    global first_load
    global gw_task
    global bot_emotes
    #set our channels
    debug_channel = bot.get_channel(debug_chid)
    if gbfdm:
        gbfc.setDebugChannel(debug_channel)
    lucilog_channel = bot.get_channel(luciLog)
    lucimain_channel = bot.get_channel(luciMain)
    # start up message and check if we loaded the save properly
    msg = ':electric_plug: Starting up, Loading my data\n'
    await sendDebugStr()
    if first_load:
        msg += 'Data loaded\n'
    else:
        msg += bot.get_user(owner_id).mention + ' Failed\n' # ping me if the save load failed
    if gw:
        gw_task = bot.loop.create_task(checkGWBuff())
    msg += 'Ready'
    await debug_channel.send(msg)
    # start the background tasks
    bot.loop.create_task(backtask())
    bot.loop.create_task(lucitask())

# happen when the bot joins a guild
@bot.event
async def on_guild_join(guild):
    global pending_server
    global savePending
    if guild.id in banned_server or guild.owner.id in banned_owner: # leave if the server is blacklisted
        try:
            await debug_channel.send(":no_entry: Banned guild request: **" + guild.name + "** : " + str(guild.id) + ' owned by ' + guild.owner.name + ' (' + str(guild.owner.id) + ')')
        except Exception as e:
            await debug_channel.send("on_guild_join(): " + str(e))
        await guild.leave()
    else: # notify me and add to the pending servers
        await debug_channel.send(":new: I joined a new server")
        general = getGeneral(guild)
        if general and general.permissions_for(guild.me).send_messages:
            await general.send('A request has been sent to master.\nYou can use me once it has been accepted')
        pending_server[guild.id] = guild.name
        await debug_channel.send("Pending guild request **" + guild.name + "** : " + str(guild.id) + ' owned by ' + guild.owner.name + ' (' + str(guild.owner.id) + ')')
        savePending = True

@bot.check # authorize or not a command
async def global_check(ctx):
    if ctx.guild.id in banned_server or ctx.guild.owner.id in banned_owner: # ban check
        return False
    if ctx.guild.id in pending_server: # pending check
        return False
    return True

@bot.event # if an error happens
async def on_command_error(ctx, error):
    msg = str(error)
    if msg.find('You are on cooldown.') == 0:
        await react(ctx, 'cooldown')
    elif msg.find('Command "') == 0 or msg == 'Command raised an exception: Forbidden: FORBIDDEN (status code: 403): Missing Permissions':
        return
    else:
        await debug_channel.send('Error: `' + msg + "`\nCommand: `" + ctx.message.content + "`\nAuthor: `" + ctx.message.author.name + "`\nServer: `" + ctx.message.author.guild.name + "`")

class General(commands.Cog):
    """General commands."""
    def __init__(self, bot):
        self.bot = bot

    def __unload(self):
        pass

    @commands.command(no_pm=True)
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def roll(self, ctx, dice : str = ""):
        """Rolls a dice in NdN format."""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        try:
            rolls, limit = map(int, dice.split('d'))
            result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
            await ctx.send('**Result:** ' + result)
        except:
            await ctx.send('Format has to be in NdN (example: `roll 2d6`')

    @commands.command(no_pm=True, aliases=['choice'])
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def choose(self, ctx, *choices : str ):
        """Chooses between multiple choices.
        Use quotes if one of your choices contains spaces.
        Example: $choose "I'm Alice" Bob"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        try:
            await ctx.send(random.choice(choices)) # might change how strings with space work
        except:
            await ctx.send('Give me a list of something to choose from :pensive:\nUse quotes `"` if a choice contains spaces')

    @commands.command(no_pm=True, aliases=['math'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def calc(self, ctx, *terms : str):
        """Process a mathematical expression
        You can define a variable by separating using a comma.
        Example: (a + b) / c, a = 1, b=2,c = 3"""
        try:
            m = " ".join(terms).split(",")
            d = {}
            for i in range(1, len(m)): # process the variables if any
                x = m[i].replace(" ", "").split("=")
                if len(x) == 2: d[x[0]] = float(x[1])
                else: raise Exception('')
            if len(d) > 0: await ctx.send(':nerd: The result is: ' + str(evaluate(m[0], d)))
            else: await ctx.send(':nerd: The result is: ' + str(evaluate(m[0])))
        except:
            await ctx.send(getEmoteStr('kmr') + ' I don\'t understand')

    @commands.command(no_pm=True)
    async def roleStats(self, ctx, name : str, exact : str = ""):
        """Search how many users have a matching role
        use quotes if your match contain spaces
        add 'exact' at the end to force an exact match"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        g = ctx.author.guild
        i = 0
        for member in g.members:
            for r in member.roles:
                if r.name == name or (exact != "exact" and r.name.lower().find(name.lower()) != -1):
                    i += 1
        if exact != "exact":
            await ctx.send(str(i) + " member(s) with a role containing `" + name + "`")
        else:
            await ctx.send(str(i) + " member(s) with the role `" + name + "`")

class GBF_Game(commands.Cog):
    """GBF related commands."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True, aliases=['1'])
    @commands.cooldown(60, 60, commands.BucketType.guild)
    async def single(self, ctx, double : str = ""):
        """Do a single roll
        You can add "double", "x2", "legfest", "flashfest" to double the SSR rates"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        l = isLegfest(double)
        if l == 2: msg = "SSR Rate is **doubled!!**\n"
        else: msg = ""
        r = getRoll(300*l)

        if r == 0: msg += "Luckshitter! {} rolled a " + getEmoteStr('SSR')
        elif r == 1: msg += "{} got a " + getEmoteStr('SR')
        else: msg += "{} got a " + getEmoteStr('R') + ", too bad!"
        await ctx.send(msg.format(ctx.message.author.mention))

    @commands.command(no_pm=True, aliases=['10'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def ten(self, ctx, double : str = ""):
        """Do ten gacha rolls
        You can add "double", "x2", "legfest", "flashfest" to double the SSR rates"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        l = isLegfest(double)
        if l == 2: msg = "SSR Rate is **doubled!!**\n"
        else: msg = ""
        sr_flag = False
        msg += "{} rolled:\n"
        i = 0
        while i < 10:
            r = getRoll(300*l)
            if r <= 1: sr_flag = True
            if i == 9 and not sr_flag:
                continue
            if r == 0: msg += getEmoteStr('SSR')
            elif r == 1: msg += getEmoteStr('SR')
            else: msg += getEmoteStr('R')
            i += 1

        await ctx.send(msg.format(ctx.message.author.mention))

    @commands.command(no_pm=True, aliases=['300'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def spark(self, ctx, double : str = ""):
        """Do thirty times ten gacha rolls
        You can add "double", "x2", "legfest", "flashfest" to double the SSR rates"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        l = isLegfest(double)
        if l == 2: msg = "SSR Rate is **doubled!!**\n"
        else: msg = ""
        result = [0, 0, 0]
        for x in range(0, 30):
            i = 0
            sr_flag = False
            while i < 10:
                r = getRoll(300*l)
                if r <= 1: sr_flag = True
                if i == 9 and not sr_flag:
                    continue
                result[r] += 1
                i += 1
        msg += "{} rolled:\n"
        msg += getEmoteStr('SSR') + ": " + str(result[0]) + "\n"
        msg += getEmoteStr('SR') + ":  " + str(result[1]) + "\n"
        msg += getEmoteStr('R') + ":   " + str(result[2]) + "\n"
        msg += "\nSSR rate: **" + str(100*result[0]/300) + "%**"

        await ctx.send(msg.format(ctx.message.author.mention))

    @commands.command(no_pm=True, aliases=['frenzy'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def gachapin(self, ctx, double : str = ""):
        """Do ten rolls until you get a ssr
        You can add "double", "x2", "legfest", "flashfest" to double the SSR rates"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        l = isLegfest(double)
        if l == 2: msg = "SSR Rate is **doubled!!**\n"
        else: msg = ""
        result = [0, 0, 0]
        count = 0
        for x in range(0, 30):
            i = 0
            count += 1
            sr_flag = False
            ssr_flag = False
            while i < 10:
                r = getRoll(300*l)
                if r <= 1: sr_flag = True
                if i == 9 and not sr_flag:
                    continue
                if r == 0: ssr_flag = True
                result[r] += 1
                i += 1
            if ssr_flag:
                break
        msg += "{} gachapin stopped at **" + str(count*10) + "** rolls\n"
        msg += getEmoteStr('SSR') + ": " + str(result[0]) + "\n"
        msg += getEmoteStr('SR') + ":  " + str(result[1]) + "\n"
        msg += getEmoteStr('R') + ":   " + str(result[2]) + "\n"
        msg += "\nSSR rate: **" + str(100*result[0]/(count*10)) + "%**"

        await ctx.send(msg.format(ctx.message.author.mention))

    @commands.command(no_pm=True, aliases=['mook'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def mukku(self, ctx, super : str = ""):
        """Do ten rolls until you get a ssr, 9% ssr rate
        You can add "super" for a 9% rate and 5 ssr mukku"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        if super.lower() == "super":
            ssr = 1500
            msg = "**Super Mukku!!** 15% SSR Rate and at least 5 SSRs\n"
            limit = 5
        else:
            ssr = 900
            msg = ""
            limit = 1
        result = [0, 0, 0]
        count = 0
        for x in range(0, 30):
            i = 0
            count += 1
            sr_flag = False
            while i < 10:
                r = getRoll(ssr)
                if r <= 1: sr_flag = True
                if i == 9 and not sr_flag:
                    continue
                if r == 0: limit -= 1
                result[r] += 1
                i += 1
            if limit <= 0:
                break
        msg += "{} mukku stopped at **" + str(count*10) + "** rolls\n"
        msg += getEmoteStr('SSR') + ": " + str(result[0]) + "\n"
        msg += getEmoteStr('SR') + ":  " + str(result[1]) + "\n"
        msg += getEmoteStr('R') + ":   " + str(result[2]) + "\n"
        msg += "\nSSR rate: **" + str(100*result[0]/(count*10)) + "%**"

        await ctx.send(msg.format(ctx.message.author.mention))

    @commands.command(no_pm=True)
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def roulette(self, ctx):
        """Imitate the GBF roulette"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        d = random.randint(1, 36000)
        if d < 500: await ctx.send(':confetti_ball: :tada: {} got **100** rolls!! :tada: :confetti_ball:'.format(ctx.message.author.mention))
        elif d < 2000: await ctx.send('{} got a **Gachapin Frenzy** :four_leaf_clover:'.format(ctx.message.author.mention))
        elif d < 6500: await ctx.send('{} got **30** rolls! :clap:'.format(ctx.message.author.mention))
        elif d < 19000: await ctx.send('{} got **20** rolls :open_mouth:'.format(ctx.message.author.mention))
        else: await ctx.send('{} got **10** rolls :pensive:'.format(ctx.message.author.mention))

    @commands.command(no_pm=True, aliases=['bet', 'yakuza', 'sen'])
    @commands.cooldown(30, 60, commands.BucketType.guild)
    async def rig(self, ctx):
        """Post the yakuza rig"""
        await ctx.send('It\'s always SEN')

    @commands.command(no_pm=True, aliases=['setcrystal', 'setspark'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def setRoll(self, ctx, crystal : int, single : int = 0, ten : int = 0):
        """Set your roll count"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        global spark_list
        global savePending
        try:
            if crystal < 0 or single < 0 or ten < 0:
                raise Exception('Negative numbers')
            if crystal > 500000 or single > 1000 or ten > 100:
                raise Exception('Big numbers')
            spark_list[ctx.message.author.id] = [crystal, single, ten]
            await ctx.send(getEmoteStr('crystal') + " **" + str(crystal) + "** crystal(s), **" + str(single) + "** single roll ticket(s) and **" +str(ten) + "** ten roll ticket(s)")
            try:
                cmds = self.bot.get_cog('GBF_Game').get_commands()
                if cmds:
                    for c in cmds:
                        if c.name == 'seeRoll':
                            await ctx.invoke(c)
                            break
            except Exception as e:
                await ctx.send('Success but I failed to calculate your rolls :bow:')
                await debug_channel.send('setRoll() B: ' + str(e))
            await debug_channel.send(ctx.message.author.name + ' updated his/her roll count: ' + str(spark_list[ctx.message.author.id]))
            savePending = True
        except Exception as e:
            await ctx.send(':bow: Give me your crystal, single ticket and ten roll ticket counts.')
            await debug_channel.send('setRoll() A: ' + str(e))

    @commands.command(no_pm=True, aliases=['seecrystal', 'seespark'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def seeRoll(self, ctx):
        """Post your roll count"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        try:
            if ctx.message.author.id in spark_list:
                s = spark_list[ctx.message.author.id]
                if s[0] < 0 or s[1] < 0 or s[2] < 0:
                    raise Exception('Negative numbers')
                r = (s[0] / 300) + s[1] + s[2] * 10
                fr = math.floor(r)
                current_time = datetime.utcnow() + timedelta(days=((300 - (r % 300)) / 2.4), seconds=32400)
                msg = getEmoteStr('crystal') + " You have **" + str(fr) + " roll"
                if fr != 1: msg += "s"
                msg += "**\n"
                if r >= 900: msg += "I have no words :sweat: \n"
                elif r >= 600: msg += "Stop hoarding :pensive:\n"
                elif r >= 350: msg += "What are you waiting for? :thinking:\n"
                elif r >= 300: msg += "Dickpick or e-sport pick? :smirk:\n"
                elif r >= 280: msg += "Almost! :blush: \n"
                elif r >= 240: msg += "One more month :thumbsup: \n"
                elif r >= 200: msg += "You are getting close :ok_hand: \n"
                elif r >= 150: msg += "Half-way done :relieved:\n"
                elif r >= 100: msg += "Stay strong :wink:\n"
                elif r >= 50: msg += "You better save these rolls :spy: \n"
                elif r >= 20: msg += "Start saving **NOW** :rage:\n"
                else: msg += "Pathetic :nauseated_face: \n"
                msg += "Next spark rough estimation: **" + str(current_time.year) + "/" + str(current_time.month) + "/" + str(current_time.day) + "**"
                await ctx.send(msg)
            else:
                await ctx.send('Use the setRoll command first')
        except Exception as e:
            await ctx.send('I can\'t calculate your rolls, sorry :bow:\nUse setRoll to fix it')
            await debug_channel.send('seeRoll(): ' + str(e))

    @commands.command(no_pm=True, aliases=["sparkranking", "hoarders"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def rollRanking(self, ctx):
        """Show the ranking of everyone saving for a spark in the server
        You must use $setRoll to set/update your roll count"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        try:
            ranking = {}
            guild = ctx.message.author.guild
            for m in guild.members:
                if m.id in spark_list:
                    if m.id in spark_ban:
                        continue
                    s = spark_list[m.id]
                    if s[0] < 0 or s[1] < 0 or s[2] < 0:
                        continue
                    r = (s[0] / 300) + s[1] + s[2] * 10
                    if r > 1000:
                        continue
                    ranking[m.id] = r
            if len(ranking) == 0:
                await ctx.send("The ranking of this server is empty")
                return
            ar = -1
            i = 0
            msg = getEmoteStr('crown') + " **Spark ranking** of **" + guild.name + "**\n"
            for key, value in sorted(ranking.items(), key = itemgetter(1), reverse = True):
                if i < 10:
                    fr = math.floor(value)
                    msg += "**#" + str(i+1) + " :black_small_square: " + str(guild.get_member(key).display_name) + "** has **" + str(fr) + "** roll"
                    if fr != 1: msg += "s"
                    if fr >= 900: msg += " :sweat: \n"
                    elif fr >= 600: msg += " :pensive:\n"
                    elif fr >= 350: msg += " :thinking:\n"
                    elif fr >= 300: msg += " :laughing:\n"
                    elif fr >= 240: msg += " :thumbsup:\n"
                    elif fr >= 200: msg += " :ok_hand:\n"
                    elif fr >= 150: msg += " :relieved:\n"
                    elif fr >= 100: msg += " :clap:\n"
                    elif fr >= 50: msg += " :wheelchair:\n"
                    elif fr >= 20: msg += " :rage:\n"
                    else: msg += " :nauseated_face:\n"
                if key == ctx.message.author.id:
                    ar = i
                i += 1
                if i >= 100:
                    break
            if ar >= 10:
                msg += "\nYou are ranked **#" + str(ar+1) + "**"
            elif ar == -1:
                msg += "\nYou aren't ranked, you have been banned or your ranking is too low\n(You must be at least top 100)"
            await ctx.send(msg)
        except Exception as e:
            await ctx.send("Sorry, something went wrong :bow:")
            await debug_channel.send("rollRanking() : " + str(e))

    @commands.command(no_pm=True, aliases=['diexil', 'nemo', 'killxil'])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def xil(self, ctx):
        """Bully Xil"""
        try:
            msg = random.choice(xil_str)
            await ctx.send(msg.format(ctx.message.author.guild.get_member(xil_id).mention))
        except:
            pass

    @commands.command(no_pm=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def wawi(self, ctx):
        """Bully Wawi"""
        try:
            wawiuser = ctx.message.author.guild.get_member(wawi_id)
            if wawiuser is None:
                return
            msg = random.choice(wawi_str)
            r = ctx.message.author.guild.get_role(412989004162793482)
            if r is not None: await ctx.send(msg.format(r.mention))
            else: await ctx.send(msg.format(wawiuser.mention))
        except:
            pass

    @commands.command(no_pm=True, hidden=True, aliases=['yawn', 'mig', 'mizako', 'miza', 'xenn', 'rubbfish', 'rubb', 'snak', 'snakdol', 'xell', 'kins', 'pics', 'roli', 'fresh', 'scrub', 'scrubp', 'milk', 'chen', 'marie', 'kinssim', 'tori', 'leader', 'simova', 'simo', 'den', 'snacks', 'varuna'])
    @commands.cooldown(1, 120, commands.BucketType.user)
    @commands.cooldown(1, 50, commands.BucketType.guild)
    async def selfping(self, ctx):
        """Bully trap"""
        try:
            await debug_channel.send(ctx.message.author.display_name + " triggered 'selfping()' with the message: " + ctx.message.content)

            guild = ctx.message.author.guild
            author = ctx.message.author
            ch = guild.text_channels
            chlist = [] # build a list of channels where is the author
            for c in ch:
                if c.permissions_for(guild.me).send_messages and author in c.members and c.id not in luciChannel and c.id != lucilog_channel.id:
                    chlist.append(c)

            msg = author.mention # get the ping for the author
            n = random.randint(4, 6) # number between 4 and 6
            await react(ctx, 'kmr') # reaction
            await asyncio.sleep(1) # wait one second
            for i in range(0, n):
                await random.choice(chlist).send(msg) # send the ping in a random channel
                await asyncio.sleep(1) # wait one second
        except:
            pass

    @commands.command(no_pm=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def quota(self, ctx):
        """Give you your GW quota for the day"""
        chance = random.randint(1, 50)
        hr = random.randint(0, 300000000)
        mr = random.randint(0, 5000)
        hc = [[220000000, 0.01], [140000000, 0.1], [80000000, 0.4], [60000000, 0.6]]
        mc = [[4000, 0.01], [2500, 0.1], [1000, 0.3], [800, 0.6]]
        h = 0
        m = 0
        for xh in hc:
            if hr >= xh[0]:
                d = hr - xh[0]
                hr = xh[0]
                h += d * xh[1]
        for xm in mc:
            if mr >= xm[0]:
                d = mr - xm[0]
                mr = xm[0]
                m += d * xm[1]
        h = int(h + hr + 6000000)
        m = int(m + mr + 300)
        if ctx.author.id == 157623260526280704 or chance == 1:
            h = h * 35
            m = m * 50
        elif ctx.author.id == wawi_id or chance == 2:
            h = h // 140
            m = m // 60
        await ctx.send(ctx.message.author.mention + '\'s quota for today:\n**{:,}** honors\n**{:,}** meats\nHave fun :relieved:'.format(h, m).replace(',', ' '))

    @commands.command(no_pm=True, aliases=['hgg2d'])
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def hgg(self, ctx):
        """Post the latest /hgg2d/ threads"""
        if not ctx.channel.is_nsfw():
            await ctx.send(':underage: use this command in a NSFW channel')
            return
        threads = get4chan('vg', '/hgg2d/')
        if len(threads) > 0:
            msg = '**Latest thread(s):**\n'
            for t in threads:
                msg += ':underage: <https://boards.4channel.org/vg/thread/'+str(t)+'>\n'
            msg += "Good fap, fellow 4channeler :relieved:"
            await ctx.send(msg)
        else:
            await ctx.send('I couldn\'t find a single /hgg2d/ thread :pensive:')

# the GBF cog
class GBF_Utility(commands.Cog):
    """GBF related commands."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True, aliases=['gbfwiki'])
    @commands.cooldown(3, 4, commands.BucketType.guild)
    async def wiki(self, ctx, *terms : str):
        """Search the GBF wiki
        add embed at the end to show the discord preview"""
        if len(terms) == 0:
            await ctx.send('Please tell me what to search on the wiki')
        else:
            try:
                arr = []
                for s in terms:
                    arr.append(fixCase(s))
                if len(terms) >= 2 and terms[-1] == "embed":
                    sch = "_".join(arr[:-1])
                    terms = terms[:-1]
                    full = True
                else:
                    sch = "_".join(arr)
                    full = False
                urlopen('https://gbf.wiki/' + sch, timeout=5)
                if full: await ctx.send('Click here :point_right: https://gbf.wiki/' + sch + '')
                else: await ctx.send('Click here :point_right: <https://gbf.wiki/' + sch + '>')
            except timeout:
                await ctx.send('The wiki is slow or might be down :thinking:, click here and try to refine the search:\n<https://gbf.wiki/index.php?title=Special:Search&search=' + "+".join(terms) + '>')
            except Exception as e:
                if str(e) != "HTTP Error 404: Not Found":
                    await debug_channel.send("wiki(): " + str(e))
                await ctx.send('404: Not Found :bow:, click here and try to refine the search:\n<https://gbf.wiki/index.php?title=Special:Search&search=' + "+".join(terms) + '>')

    @commands.command(no_pm=True, aliases=['tweet'])
    @commands.cooldown(1, 2, commands.BucketType.default)
    async def twitter(self, ctx, term : str = ""):
        """Post a gbf related twitter account
        default is the official account
        options: en, english, noel, radio, wawi, raidpic, kmr, kakage,
        hag, jk, hecate, hecate_mk2, gbfverification, chiaking, gw, gamewith, anime"""
        term = term.lower()
        if term == "en" or term == "english":
            await ctx.send('Welcome EOP: <https://twitter.com/granblue_en>')
        elif term == "noel" or term == "radio":
            await ctx.send('Your monthly granblue channel summary: <https://twitter.com/noel_gbf>')
        elif term == "wawi":
            await ctx.send('Like: <https://twitter.com/WawiGbf>\nSubscribe: <https://twitter.com/Wawi3313>')
        elif term == "raidpic":
            await ctx.send('To grab the artworks: <https://twitter.com/twihelp_pic>')
        elif term == "kmr":
            await ctx.send('Give praise, for he has no equal ' + getEmoteStr('kmr') + ' : <https://twitter.com/kimurayuito>')
        elif term == "kakage" or term == "jk" or term == "hag":
            await ctx.send('Young JK inside: <https://twitter.com/kakage0904>')
        elif term == "hecate" or term == "hecate_mk2" or term == "gbfverification":
            await ctx.send(':nerd: : <https://twitter.com/hecate_mk2>')
        elif term == "chiaking":
            await ctx.send(':relaxed: :eggplant: : <https://twitter.com/chiaking58>')
        elif term == "gw" or term == "gamewith":
            await ctx.send(':nine: / :keycap_ten: : <https://twitter.com/granblue_gw>')
        elif term == "anime":
            await ctx.send(':u5408:  : <https://twitter.com/anime_gbf>')
        elif term:
            await ctx.send('I don\'t know what you want\nI give you this instead: <https://twitter.com/granbluefantasy>')
        else:
            await ctx.send('Praise KMR: <https://twitter.com/granbluefantasy>')

    @commands.command(no_pm=True, aliases=['4chan', 'thread'])
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def gbfg(self, ctx):
        """Post the latest /gbfg/ threads"""
        threads = get4chan('vg', '/gbfg/')
        if len(threads) > 0:
            msg = '**Latest thread(s):**\n'
            for t in threads:
                msg += ':poop: <https://boards.4channel.org/vg/thread/'+str(t)+'>\n'
            msg += "Have fun, fellow 4channeler :relieved:"
            await ctx.send(msg)
        else:
            await ctx.send('I couldn\'t find a single /gbfg/ thread :pensive:')

    @commands.command(no_pm=True)
    async def reddit(self, ctx):
        """Post a link to /r/Granblue_en
        You wouldn't dare, do you?"""
        await ctx.send('Really? :nauseated_face:: <https://www.reddit.com/r/Granblue_en/>')

    @commands.command(no_pm=True, aliases=['leech'])
    async def leechlist(self, ctx):
        """Post a link to /gbfg/ leechlist collection"""
        await ctx.send(bot_msgs["leechlist()"])

    @commands.command(no_pm=True, name='time', aliases=['st', 'reset', 'status'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def _time(self, ctx):
        """Post remaining time to next reset and strike times (if set)
        Also maintenance and gw times if set"""
        global maintenance
        global gw
        global savePending
        current_time = datetime.utcnow() + timedelta(seconds=32400)

        msg = getEmoteStr('clock') + " **Current Time: " + str(current_time.hour).zfill(2) + ":" + str(current_time.minute).zfill(2) + "**\n"

        reset = current_time.replace(hour=5, minute=0, second=0, microsecond=0)
        if current_time.hour >= reset.hour:
            reset += timedelta(days=1)
        d = reset - current_time
        msg += getEmoteStr('mark') + " Reset in **" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m**"

        guild = ctx.message.author.guild
        if guild.id in st_list:
            st1 = current_time.replace(hour=st_list[guild.id][0], minute=0, second=0, microsecond=0)
            st2 = st1.replace(hour=st_list[guild.id][1])

            if current_time.hour >= st1.hour:
                st1 += timedelta(days=1)
            if current_time.hour >= st2.hour:
                st2 += timedelta(days=1)

            d = st1 - current_time
            if d.seconds >= 82800: msg += "\n" + getEmoteStr('st') + " Strike times in " + getEmoteStr('1') + " **NOW!** "
            else: msg += "\n" + getEmoteStr('st') + " Strike times in " + getEmoteStr('1') + " **" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m** "
            d = st2 - current_time
            if d.seconds >= 82800: msg += getEmoteStr('2') + " **right now!**"
            else: msg += getEmoteStr('2') + " **" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m**"

        await ctx.send(msg)
        try:
            cmds = self.bot.get_cog('GBF_Utility').get_commands()
            if cmds:
                for c in cmds:
                    if c.name == 'gacha':
                        await ctx.invoke(c)
                        break
        except Exception as e:
            await debug_channel.send(str(e))
        if maintenance:
            try:
                cmds = self.bot.get_cog('GBF_Utility').get_commands()
                if cmds:
                    for c in cmds:
                        if c.name == 'maintenance':
                            await ctx.invoke(c)
                            break
            except Exception as e:
                await debug_channel.send(str(e))
        if gw:
            try:
                cmds = self.bot.get_cog('GW').get_commands()
                if cmds:
                    for c in cmds:
                        if c.name == 'fugdidgwstart':
                            await ctx.invoke(c)
                            break
            except Exception as e:
                await debug_channel.send(str(e))

    @commands.command(no_pm=True, aliases=['maint'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def maintenance(self, ctx):
        """Post GBF maintenance status"""
        await maintenanceCheck(ctx)

    @commands.command(no_pm=True)
    async def gacha(self, ctx):
        """Post when the current gacha end"""
        if not gbfdm:
            return
        ignore_update = False
        # maintenance check
        if maintenanceUpdate():
            await maintenanceCheck(ctx)
            return
        await gbfc.getGachatime(ctx)

    @commands.command(no_pm=True, aliases=['rateup'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def banner(self, ctx, jp : str = ""):
        """Post when the current gacha end
        add 'jp' for the japanese image"""
        if not gbfdm:
            return
        ignore_update = False
        # maintenance check
        if maintenanceUpdate():
            await maintenanceCheck(ctx)
            return
        await gbfc.getGachabanner(ctx, jp)

    @commands.command(no_pm=True, hidden=True, aliases=['drive'])
    @commands.is_owner()
    async def gdrive(self, ctx):
        """Post the (You) google drive
        (You) server only"""
        if isYouServer(ctx.message.author.guild):
            await ctx.send(bot_msgs["gdrive()"])
        else:
            await ctx.send('My master didn\'t permit me to post this link here')

    @commands.command(no_pm=True, aliases=['arcarum', 'arca', 'oracle', 'evoker', 'astra'])
    async def arcanum(self, ctx):
        """Post a link to my autistic Arcanum Sheet"""
        await ctx.send(bot_msgs["arcanum()"])

    @commands.command(no_pm=True, aliases=['sparktracker'])
    async def rollTracker(self, ctx):
        """Post a link to my autistic roll tracking Sheet"""
        await ctx.send(bot_msgs["rolltracker()"])

    @commands.command(no_pm=True, aliases=['charlist', 'asset'])
    async def datamining(self, ctx):
        """Post a link to my autistic datamining Sheet"""
        await ctx.send(bot_msgs["datamining()"])

    @commands.command(no_pm=True, aliases=['gwskin', 'blueskin'])
    async def stayBlue(self, ctx):
        """Post a link to my autistic blue eternal outfit grinding Sheet"""
        await ctx.send(bot_msgs["stayblue()"])

    @commands.command(no_pm=True, aliases=['gbfgcrew', 'gbfgpastebin'])
    async def pastebin(self, ctx):
        """Post a link to the /gbfg/ crew pastebin"""
        await ctx.send(bot_msgs["pastebin()"])

    @commands.command(no_pm=True, aliases=['tracker'])
    async def dps(self, ctx):
        """Post the custom Combat tracker"""
        await ctx.send(bot_msgs["dps()"])

    @commands.command(no_pm=True, aliases=['grid', 'pool'])
    async def motocal(self, ctx):
        """Post the motocal link"""
        await ctx.send(bot_msgs["motocal()"])

    @commands.command(no_pm=True)
    async def leak(self, ctx):
        """Post a link to the /gbfg/ leak pastebin"""
        await ctx.send(bot_msgs["leak()"])

    @commands.command(no_pm=True, aliases=['raidfinder', 'python_raidfinder'])
    async def pyfinder(self, ctx):
        """Post the (You) python raidfinder"""
        await ctx.send(bot_msgs["pyfinder()"])

    @commands.command(no_pm=True, aliases=['ubhl', 'ubaha'])
    async def ubahahl(self, ctx):
        """Post a simple Ultimate Baha HL image guide"""
        await ctx.send(bot_msgs["ubahahl()"])
        await ctx.send("Wiki page :point_right: <https://gbf.wiki/Ultimate_Bahamut_(Raid)#impossible>")

    @commands.command(no_pm=True, aliases=["christmas", "anniversary", "xmas", "anniv", "event"])
    @commands.cooldown(20, 30, commands.BucketType.guild)
    async def stream(self, ctx):
        """Post the stream text"""
        if len(stream_txt) == 0:
            await ctx.send("No stream available")
        else:
            msg = ""
            for s in stream_txt:
                msg += s + "\n"
            if stream_time and msg.find('{}') != -1:
                current_time = datetime.utcnow() + timedelta(seconds=32400)
                if current_time < stream_time:
                    d = stream_time - current_time
                    cd = str(d.days) + "d" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m"
                else:
                    cd = "On going!!"
                await ctx.send(msg.format(cd))
            else:
                await ctx.send(msg)

    @commands.command(no_pm=True)
    @commands.cooldown(20, 30, commands.BucketType.guild)
    async def schedule(self, ctx):
        """Post the GBF schedule"""
        if len(gbfschedule) == 0:
            await ctx.send("No schedule available")
        else:
            await ctx.send(":calendar: **GBF Schedule:**\n```" + gbfschedule + "```")


# the background task used to check if we call the GW buffs in (you)
gwbuff_id = 0
async def checkGWBuff():
    global gw
    global gw_buffs
    global gw_skip
    global gwbuff_id
    global gw_task
    gwbuff_id += 1
    tid = gwbuff_id
    try:
        guild = bot.get_guild(you_id)
        channel = bot.get_channel(you_announcement)
        await debug_channel.send('CheckGWBuff() #' + str(tid) + ' started')
        msg = ""
        while gw and (len(gw_buffs) > 0 or len(msg) != 0) :
            if tid != gwbuff_id:
                raise Exception('task cancelled')
            current_time = datetime.utcnow() + timedelta(seconds=32400)
            if len(gw_buffs) > 0 and current_time >= gw_buffs[0][0]:
                msg = ""
                if (current_time - gw_buffs[0][0]) < timedelta(seconds=200):
                    if gw_buffs[0][1]:
                        for r in buff_role_id:
                            msg += getEmoteStr(r[1]) + ' ' + guild.get_role(r[0]).mention + ' '
                    if gw_buffs[0][2]:
                        msg += getEmoteStr('foace') + ' '
                        for r in fo_role_id:
                            msg += guild.get_role(r).mention + ' '
                    if gw_buffs[0][4]:
                        if gw_buffs[0][3]:
                            msg += '**DOUBLE** buffs in 5 minutes'
                        else:
                            msg += '**DOUBLE** buffs now!'
                    else:
                        if gw_buffs[0][3]:
                            msg += 'buffs in 5 minutes'
                        else:
                            msg += 'buffs now!'
                    if gw_skip:
                        msg = ""
                    if not gw_buffs[0][3]:
                        gw_skip = False
                gw_buffs.pop(0)
                await autosave()
            else:
                if len(msg) > 0:
                    await channel.send(msg)
                    msg = ""
                if len(gw_buffs) > 0:
                    d = gw_buffs[0][0] - current_time
                    if d.seconds > 1:
                        await debug_channel.send('Checking buffs in ' + str(d.seconds-1) + ' second(s)')
                        await debug_channel.send('Next buffs setting: ' + str(gw_buffs[0][1]) + ' ' + str(gw_buffs[0][2]) + ' ' + str(gw_buffs[0][3]) + ' ' + str(gw_buffs[0][4]))
                        await debug_channel.send("Buffs in " + str(d.days) + "d" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m" + str(d.seconds % 60) + "s")
                        await asyncio.sleep(d.seconds-1)
        if len(msg) > 0:
            await channel.send(msg)
        await debug_channel.send('CheckGWBuff() #' + str(tid) + ' ended')
    except asyncio.CancelledError:
        await debug_channel.send('CheckGWBuff() #' + str(tid) + ' cancelled')
    except Exception as e:
        await debug_channel.send('**CheckGWBuff() #' + str(tid) + ' : ' + str(e) + '**')

# build the buff timing list
def buildBuffTimes():
    global gw_buffs
    try:
        gw_buffs = []
        # Prelims all
        gw_buffs.append([gw_dates["Preliminaries"]+timedelta(seconds=7200-300), True, True, True, True]) # warning, double
        gw_buffs.append([gw_dates["Preliminaries"]+timedelta(seconds=7200), True, True, False, True])
        gw_buffs.append([gw_dates["Preliminaries"]+timedelta(seconds=43200-300), True, False, True, False]) # warning
        gw_buffs.append([gw_dates["Preliminaries"]+timedelta(seconds=43200), True, False, False, False])
        gw_buffs.append([gw_dates["Preliminaries"]+timedelta(seconds=43200+3600-300), False, True, True, False]) # warning
        gw_buffs.append([gw_dates["Preliminaries"]+timedelta(seconds=43200+3600), False, True, False, False])
        gw_buffs.append([gw_dates["Preliminaries"]+timedelta(days=1, seconds=10800-300), True, True, True, False]) # warning
        gw_buffs.append([gw_dates["Preliminaries"]+timedelta(days=1, seconds=10800), True, True, False, False])
        # Interlude
        gw_buffs.append([gw_dates["Interlude"]-timedelta(seconds=300), True, False, True, False])
        gw_buffs.append([gw_dates["Interlude"], True, False, False, False])
        gw_buffs.append([gw_dates["Interlude"]+timedelta(seconds=3600-300), False, True, True, False])
        gw_buffs.append([gw_dates["Interlude"]+timedelta(seconds=3600), False, True, False, False])
        gw_buffs.append([gw_dates["Interlude"]+timedelta(seconds=54000-300), True, True, True, False])
        gw_buffs.append([gw_dates["Interlude"]+timedelta(seconds=54000), True, True, False, False])
        # Day 1
        gw_buffs.append([gw_dates["Day 1"]-timedelta(seconds=300), True, False, True, False])
        gw_buffs.append([gw_dates["Day 1"], True, False, False, False])
        gw_buffs.append([gw_dates["Day 1"]+timedelta(seconds=3600-300), False, True, True, False])
        gw_buffs.append([gw_dates["Day 1"]+timedelta(seconds=3600), False, True, False, False])
        gw_buffs.append([gw_dates["Day 1"]+timedelta(seconds=54000-300), True, True, True, False])
        gw_buffs.append([gw_dates["Day 1"]+timedelta(seconds=54000), True, True, False, False])
        # Day 2
        gw_buffs.append([gw_dates["Day 2"]-timedelta(seconds=300), True, False, True, False])
        gw_buffs.append([gw_dates["Day 2"], True, False, False, False])
        gw_buffs.append([gw_dates["Day 2"]+timedelta(seconds=3600-300), False, True, True, False])
        gw_buffs.append([gw_dates["Day 2"]+timedelta(seconds=3600), False, True, False, False])
        gw_buffs.append([gw_dates["Day 2"]+timedelta(seconds=54000-300), True, True, True, False])
        gw_buffs.append([gw_dates["Day 2"]+timedelta(seconds=54000), True, True, False, False])
        # Day 3
        gw_buffs.append([gw_dates["Day 3"]-timedelta(seconds=300), True, False, True, False])
        gw_buffs.append([gw_dates["Day 3"], True, False, False, False])
        gw_buffs.append([gw_dates["Day 3"]+timedelta(seconds=3600-300), False, True, True, False])
        gw_buffs.append([gw_dates["Day 3"]+timedelta(seconds=3600), False, True, False, False])
        gw_buffs.append([gw_dates["Day 3"]+timedelta(seconds=54000-300), True, True, True, False])
        gw_buffs.append([gw_dates["Day 3"]+timedelta(seconds=54000), True, True, False, False])
        # Day 4
        gw_buffs.append([gw_dates["Day 4"]-timedelta(seconds=300), True, False, True, False])
        gw_buffs.append([gw_dates["Day 4"], True, False, False, False])
        gw_buffs.append([gw_dates["Day 4"]+timedelta(seconds=3600-300), False, True, True, False])
        gw_buffs.append([gw_dates["Day 4"]+timedelta(seconds=3600), False, True, False, False])
        gw_buffs.append([gw_dates["Day 4"]+timedelta(seconds=54000-300), True, True, True, False])
        gw_buffs.append([gw_dates["Day 4"]+timedelta(seconds=54000), True, True, False, False])
        return True
    except:
        return False

class GW(commands.Cog):
    """GW related commands."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def GW(self, ctx):
        """Post the GW schedule"""
        global gw
        global gw_dates
        global gw_task
        if gw:
            try:
                current_time = datetime.utcnow() + timedelta(seconds=32400)
                msg = getEmoteStr('gw') + " **Guild War** :black_small_square: Time: **{0:%m/%d %H:%M}**\n".format(current_time)
                d = gw_dates["Preliminaries"] - timedelta(days=random.randint(1, 4))
                if current_time < d and random.randint(1, 8) == 1: msg += getEmoteStr('kmr') + ' Ban Wave: **{0:%m/%d %H:%M}**\n'.format(d)
                d = gw_dates["Interlude"] - current_time
                if current_time < gw_dates["Interlude"] and d >= timedelta(seconds=25200): msg += getEmoteStr('gold') + ' Preliminaries: **{0:%m/%d %H:%M}**\n'.format(gw_dates["Preliminaries"])
                d = gw_dates["Day 1"] - current_time
                if current_time < gw_dates["Day 1"] and d >= timedelta(seconds=25200): msg += getEmoteStr('wood') + ' Interlude: **{0:%m/%d %H:%M}**\n'.format(gw_dates["Interlude"])
                d = gw_dates["Day 2"] - current_time
                if current_time < gw_dates["Day 2"] and d >= timedelta(seconds=25200): msg += getEmoteStr('1') + ' Day 1: **{0:%m/%d %H:%M}**\n'.format(gw_dates["Day 1"])
                d = gw_dates["Day 3"] - current_time
                if current_time < gw_dates["Day 3"] and d >= timedelta(seconds=25200): msg += getEmoteStr('2') + ' Day 2: **{0:%m/%d %H:%M}**\n'.format(gw_dates["Day 2"])
                d = gw_dates["Day 4"] - current_time
                if current_time < gw_dates["Day 4"] and d >= timedelta(seconds=25200): msg += getEmoteStr('3') + ' Day 3: **{0:%m/%d %H:%M}**\n'.format(gw_dates["Day 3"])
                d = gw_dates["Day 5"] - current_time
                if current_time < gw_dates["Day 5"] and d >= timedelta(seconds=25200): msg += getEmoteStr('4') + ' Day 4: **{0:%m/%d %H:%M}**\n'.format(gw_dates["Day 4"])
                if current_time < gw_dates["End"]: msg += getEmoteStr('red') + ' Final Rally: **{0:%m/%d %H:%M}**\n'.format(gw_dates["Day 5"])
                else:
                    await ctx.send('No GW set, at the present time')
                    gw = False
                    gw_dates = {}
                    if gw_task:
                        gw_task.cancel()
                        gw_task = None
                    await autosave()
                    return
                await ctx.send(msg)
                try:
                    cmds = self.bot.get_cog('GW').get_commands()
                    if cmds:
                        for c in cmds:
                            if c.name == 'fugdidgwstart':
                                await ctx.invoke(c)
                                break
                except Exception as e:
                    await debug_channel.send(str(e))
            except Exception as e:
                await debug_channel.send('Huh, I\'m confused, did gw start?\n' + str(e))
        else:
            await ctx.send('No GW set, at the present time')

    @commands.command(no_pm=True, aliases=['gwtime'])
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def fugdidgwstart(self, ctx):
        """Check if GW started"""
        global gw
        global gw_dates
        global gw_task
        try:
            if gw:
                current_time = datetime.utcnow() + timedelta(seconds=32400)
                fmsg = ""
                msg = ""
                d = None
                if current_time < gw_dates["Preliminaries"]:
                    d = gw_dates["Preliminaries"] - current_time
                    msg = "Guild War starts in"
                elif current_time >= gw_dates["End"]:
                    await ctx.send('It\'s not Guild War yet')
                    gw = False
                    gw_dates = {}
                    if gw_task:
                        gw_task.cancel()
                        gw_task = None
                    await autosave()
                    return
                elif current_time > gw_dates["Day 5"]:
                    d = gw_dates["End"] - current_time
                    fmsg = "Final Rally is on going"
                    msg = "Guild War ends in"
                elif current_time > gw_dates["Day 4"]:
                    d = gw_dates["Day 5"] - current_time
                    if d < timedelta(seconds=25200): fmsg = "Day 4 ended"
                    else: fmsg = "Day 4 is on going"
                    msg = "Final Rally starts in"
                elif current_time > gw_dates["Day 3"]:
                    d = gw_dates["Day 4"] - current_time
                    if d < timedelta(seconds=25200): fmsg = "Day 3 ended"
                    else: fmsg = "Day 3 is on going"
                    msg = "Day 4 starts in"
                elif current_time > gw_dates["Day 2"]:
                    d = gw_dates["Day 3"] - current_time
                    if d < timedelta(seconds=25200): fmsg = "Day 2 ended"
                    else: fmsg = "Day 2 is on going"
                    msg = "Day 3 starts in"
                elif current_time > gw_dates["Day 1"]:
                    d = gw_dates["Day 2"] - current_time
                    if d < timedelta(seconds=25200): fmsg = "Day 1 ended"
                    else: fmsg = "Day 1 is on going"
                    msg = "Day 2 starts in"
                elif current_time > gw_dates["Interlude"]:
                    fmsg = "Interlude is on going"
                    msg = "Day 1 starts in"
                    d = gw_dates["Day 1"] - current_time
                elif current_time > gw_dates["Preliminaries"]:
                    d = gw_dates["Interlude"] - current_time
                    if d < timedelta(seconds=25200): fmsg = "Preliminaries ended"
                    else: fmsg = "Preliminaries are on going"
                    msg = "Interlude starts in"
                else:
                    await debug_channel.send("Error in $fugdidgwstart")
                    fmsg = "Sorry, I'm bad at timezones too"

                if fmsg: fmsg = getEmoteStr('mark_a') + " " + fmsg
                if d and msg: fmsg += "\n" + getEmoteStr('time') + " " + msg + " **" + str(d.days) + "d" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m**"
                await ctx.send(fmsg)
                try:
                    cmds = self.bot.get_cog('GW').get_commands()
                    if cmds:
                        for c in cmds:
                            if c.name == 'GWbuff':
                                await ctx.invoke(c)
                                break
                except Exception as e:
                    await debug_channel.send(str(e))
            else:
                await ctx.send('It\'s not Guild War yet')
        except Exception as e:
            await ctx.send('Error, I have no idea what the fuck happened')
            await debug_channel.send('Exception: ' + str(e))

    @commands.command(no_pm=True, aliases=['buff'])
    @commands.cooldown(10, 10, commands.BucketType.guild)
    async def GWbuff(self, ctx):
        """Check when is the next GW buff, (You) Only"""
        if not isYouServer(ctx.message.author.guild) and not isYouAndU2(ctx.message.author.roles): return
        try:
            if gw:
                for i in range(0, len(gw_buffs)):
                    if not gw_buffs[i][3]:
                        current_time = datetime.utcnow() + timedelta(seconds=32400)
                        if current_time >= gw_dates["Preliminaries"]:
                            d = gw_buffs[i][0] - current_time
                            msg = getEmoteStr('question') + " Next buffs in **" + str(d.days) + "d" + str(d.seconds // 3600) + "h" + str((d.seconds // 60) % 60) + "m** ("
                            if gw_buffs[i][1]:
                                msg += "Attack " + getEmoteStr('atkace') + ", Defense " + getEmoteStr('deface')
                                if gw_buffs[i][2]:
                                    msg += ", FO"
                            elif gw_buffs[i][2]:
                                msg += "FO " + getEmoteStr('foace')
                            msg += ")"
                            await ctx.send(msg)
                        return
        except Exception as e:
            await debug_channel.send('Exception: ' + str(e))
            await ctx.send('Something is wrong with me')

    @commands.command(no_pm=True, aliases=['searchcrew'])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def search(self, ctx, *terms : str):
        """Search a crew preliminary score (by name)"""
        if not isYouServer(ctx.message.author.guild) and not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        try:
            crew = " ".join(terms)
            if len(crew) == 0:
                raise Exception("No search string")
            req =  request.Request("http://gbf.gw.lt/gw-guild-searcher/search", data=str(json.dumps({"search" : crew})).encode('utf-8'))
            resp = request.urlopen(req, timeout=8)
            data = json.loads(resp.read())
            msg = ""
            i = 0
            for c in data["result"]:
                msg += getEmoteStr('gw') + " **" + c["data"][0]["name"] + "** :black_small_square: GW**" + str(c["data"][0]["gw_num"]) + "** score: **" + "{:,}".format(c["data"][0]["points"])
                if c["data"][0]["is_seed"]: msg += " (seeded)"
                msg += "**\n<http://game.granbluefantasy.jp/#guild/detail/" + str(c["id"]) + ">\n"
                i += 1
                if i >= 5: break
            if len(data["result"]) > 5: msg += "\n**5 / " + str(len(data["result"])) + " results shown, please go here for more: <http://gbf.gw.lt/gw-guild-searcher/>**"
            if msg: await ctx.send(msg)
            else: await ctx.send("Crew not found :pensive:")
        except timeout:
            await ctx.send("I can't search :pensive:\nIs <http://gbf.gw.lt/gw-guild-searcher> down?")
        except Exception as e:
            if str(e) == "BAD REQUEST (status code: 400): Invalid Form Body\nIn content: Must be 2000 or fewer in length.":
                await ctx.send("Error 400, I can't search `" + crew + "` :bow:")
            elif str(e) == "No search string":
                await ctx.send("Give me the name of the crew to search, please :relieved:")
            else:
                await ctx.send("I can't search :pensive:\nIs <http://gbf.gw.lt/gw-guild-searcher> down?")
                await debug_channel.send("search() : " + str(e))

    @commands.command(no_pm=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def searchID(self, ctx, id : int):
        """Search a crew preliminary score (by ID)"""
        if not isYouServer(ctx.message.author.guild) and not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        try:
            req =  request.Request("http://gbf.gw.lt/gw-guild-searcher/info/" + str(id))
            resp = request.urlopen(req, timeout=8)
            data = json.loads(resp.read())
            msg = ""
            i = 0
            for c in data["data"]:
                msg += getEmoteStr('gw') + " **" + c["name"] + "** :black_small_square: GW**" + str(c["gw_num"]) + "** score: **" + "{:,}".format(c["points"])
                if c["is_seed"]: msg += " (seeded)**\n"
                else: msg += "**\n"
                i += 1
                if i >= 5: break
            if msg: msg += "<http://game.granbluefantasy.jp/#guild/detail/" + str(data["id"]) + ">\n"
            if len(data["data"]) > 5: msg += "\n**5 / " + str(len(data["data"])) + " past GW results shown, please go here for more: <http://gbf.gw.lt/gw-guild-searcher/>**"
            if msg: await ctx.send(msg)
            else: await ctx.send("Crew not found :pensive:")
        except timeout:
            await ctx.send("I can't search :pensive:\nIs <http://gbf.gw.lt/gw-guild-searcher> down?")
        except Exception as e:
            if str(e) == "BAD REQUEST (status code: 400): Invalid Form Body\nIn content: Must be 2000 or fewer in length.":
                await ctx.send("Error 400, I can't search `" + str(id) + "` :bow:")
            elif str(e) == "No search string":
                await ctx.send("Give me the name of the crew to search, please :relieved:")
            else:
                await ctx.send("I can't search :pensive:\nIs <http://gbf.gw.lt/gw-guild-searcher> down?")
                await debug_channel.send("search() : " + str(e))

# Bot related commands
class MizaBOT(commands.Cog):
    """Bot related commands. Might require some mod powers"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True)
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def invite(self, ctx):
        """Invite MizaBOT in another server"""
        await debug_channel.send("**" + str(ctx.message.author) + "** requested an invite")
        await ctx.send(bot_msgs["invite()"])

    @commands.command(no_pm=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def setPrefix(self, ctx, prefix_string : str):
        """Set the prefix used on your server (default: '$')
        Requires the "Manage Messages" permission"""
        global prefixes
        global savePending
        if not isMod(ctx.message.author): return
        if len(prefix_string) == 0: return
        prefixes[ctx.message.author.guild.id] = prefix_string
        await ctx.send('Server prefix set to ' + prefix_string)
        savePending = True

    @commands.command(no_pm=True)
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def resetPrefix(self, ctx):
        """Reset the prefix used on your server to '$'
        Requires the "Manage Messages" permission"""
        global prefixes
        global savePending
        if not isMod(ctx.message.author): return
        if ctx.message.author.guild.id in prefixes:
            del prefixes[ctx.message.author.guild.id]
            await ctx.send('Server prefix reset')
            savePending = True

    @commands.command(no_pm=True, aliases=['bug', 'report', 'bug_report'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def bugReport(self, ctx, *terms : str):
        """Send a bug report (or your love confessions) to the author"""
        if len(terms) == 0:
            return
        msg = '**Bug report from ' + str(ctx.message.author) + '** (id: ' + str(ctx.message.author.id) + '):\n'
        msg += " ".join(terms)
        
        await debug_channel.send(msg)
        await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True)
    async def joined(self, ctx, member : discord.Member):
        """Says when a member joined."""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        await ctx.send(':thinking: {0.name} joined in {0.joined_at}'.format(member))

    @commands.command(no_pm=True, aliases=['github'])
    @commands.cooldown(5, 60, commands.BucketType.default)
    async def source(self, ctx):
        """Post the bot.py file running right now"""
        if not isAuthorized(ctx.message.author.guild, ctx.channel):
            return
        try:
            await ctx.send("Give me a second to upload... :wrench:")
            with open('bot.py', 'r') as infile:
                await ctx.send(":scroll: Here's what I'm running right now", file=discord.File(infile))
                await ctx.send("The github is here :arrow_right:  <https://github.com/MizaGBF/MizaBOT>")
        except Exception as e:
            await ctx.send("Sorry, an error happened :pensive:\nMeanwhile, you can check the github: <https://github.com/MizaGBF/MizaBOT>")
            await debug_channel.send("source() : " + str(e))

    @commands.command(no_pm=True)
    async def delST(self, ctx):
        """Delete the ST setting of this server
        Requires the "Manage Messages" permission"""
        global savePending
        if not isMod(ctx.message.author): return
        global st_list
        guild = ctx.message.author.guild
        if guild.id in st_list:
            del st_list[guild.id]
            await ctx.send('Done')
            savePending = True
        else:
            await ctx.send('No ST set, I can\'t delete')

    @commands.command(no_pm=True)
    async def setST(self, ctx, st1 : int, st2 : int):
        """Set the two ST of this server
        Requires the "Manage Messages" permission"""
        if not isMod(ctx.message.author): return
        global st_list
        global savePending
        if st1 < 0 or st1 >= 24 or st2 < 0 or st2 >= 24:
            await ctx.send('Values must be between 0 and 23, included')
            return
        st_list[ctx.message.author.guild.id] = [st1, st2]
        await ctx.send('Done')
        savePending = True

    @commands.command(no_pm=True, aliases=['banspark'])
    async def banRoll(self, ctx, user: discord.Member):
        """Ban an user from the roll ranking
        To avoid retards with fake numbers
        The ban is across all servers
        Requires the "Manage Messages" permission"""
        global savePending
        global spark_ban
        if not isMod(ctx.message.author): return
        if user.id not in spark_ban:
            spark_ban.append(user.id)
            await ctx.send(user.display_name + ' is banned from all roll rankings')
            await debug_channel.send(user.name + " (" + str(user.id) + ") is banned from all roll rankings")
            savePending = True
        else:
            await ctx.send(user.name + ' is already banned')

    @commands.command(no_pm=True)
    async def setGW(self, ctx, day : int, month : int, year : int):
        """Set the GW date
        (You) server only"""
        if not isDebugServer(ctx.message.author.guild) and not isYouServer(ctx.message.author.guild) and not isMod(ctx.message.author):
            await ctx.send('Only available to (You) FOs')
            return
        global gw
        global gw_dates
        global gw_task
        try:
            if gw_task: gw_task.cancel()
            gw_dates = {}
            gw_dates["Preliminaries"] = datetime.utcnow().replace(year=year, month=month, day=day, hour=19, minute=0, second=0, microsecond=0)
            gw_dates["Interlude"] = gw_dates["Preliminaries"] + timedelta(days=1, seconds=43200) # +36h
            gw_dates["Day 1"] = gw_dates["Interlude"] + timedelta(days=1) # +24h
            gw_dates["Day 2"] = gw_dates["Day 1"] + timedelta(days=1) # +24h
            gw_dates["Day 3"] = gw_dates["Day 2"] + timedelta(days=1) # +24h
            gw_dates["Day 4"] = gw_dates["Day 3"] + timedelta(days=1) # +24h
            gw_dates["Day 5"] = gw_dates["Day 4"] + timedelta(days=1) # +24h
            gw_dates["End"] = gw_dates["Day 5"] + timedelta(seconds=64800) # +17h
            if buildBuffTimes():
                gw = True
                gw_task = bot.loop.create_task(checkGWBuff())
                await ctx.send(':timer: Guild War will start at ' + str(gw_dates["Preliminaries"]))
            else:
                gw_task = None
                await debug_channel.send('GW Buff timing error')
                await ctx.send('Error setting the GW, I asked Master to fix me')
                gw = False
                gw_dates = {}
            await autosave()
        except:
            await ctx.send('Error, try again')
            gw_dates = {}
            gw = False

    @commands.command(no_pm=True)
    async def disableGW(self, ctx):
        """Disable the GW mode
        (it doesn't delete the GW date)
        (You) server only"""
        if not isDebugServer(ctx.message.author.guild) and not isYouServer(ctx.message.author.guild) and not isMod(ctx.message.author):
            await ctx.send('Only available to (You) FOs')
            return
        global gw
        global gw_task
        gw = False
        if gw_task: gw_task.cancel()
        gw_task = None
        await autosave()
        await ctx.send('GW mode is disabled')

    @commands.command(no_pm=True)
    async def enableGW(self, ctx):
        """Enable the GW mode
        (You) server only"""
        if not isDebugServer(ctx.message.author.guild) and not isYouServer(ctx.message.author.guild) and not isMod(ctx.message.author):
            await ctx.send('Only available to (You) FOs')
            return
        global gw
        global gw_task
        if gw:
            await ctx.send('GW mode is already enabled!')
        elif len(gw_dates) == 8:
            if gw_task: gw_task.cancel()
            gw = True
            gw_task = bot.loop.create_task(checkGWBuff())
            await ctx.send('GW mode is enabled')
            await autosave()
        else:
            await ctx.send('I can\'t, I have no GW in my memories')

    @commands.command(no_pm=True, aliases=['skipGW'])
    async def skipGWBuff(self, ctx):
        """The bot will skip the next GW buff call
        (You) server only"""
        if not isDebugServer(ctx.message.author.guild) and not isYouServer(ctx.message.author.guild) and not isMod(ctx.message.author):
            await ctx.send('Only available to (You) FOs')
            return
        global gw_skip
        if not gw_skip:
            gw_skip = True
            await ctx.send('Understood')
            await autosave()
        else:
            await ctx.send('I\'m already skipping the next set of buffs')

    @commands.command(no_pm=True)
    async def cancelSkipGWBuff(self, ctx):
        """Cancel the GW buff call skipping
        (You) server only"""
        if not isDebugServer(ctx.message.author.guild) and not isYouServer(ctx.message.author.guild) and not isMod(ctx.message.author):
            await ctx.send('Only available to (You) FOs')
            return
        global gw_skip
        if gw_skip:
            gw_skip = False
            await ctx.send('Understood')
            await autosave()
        else:
            await ctx.send('No buff skip was set')

# Owner only command
class Owner(commands.Cog):
    """Owner only commands."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def clear(self, ctx):
        """Clear the debug channel"""
        await debug_channel.purge()

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def leave(self, ctx, id: int):
        """Make the bot leave a server (Owner only)"""
        try:
            toleave = bot.get_guild(id)
            await toleave.leave()
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')
            await printServers()

    @commands.command(no_pm=True, aliases=['banS', 'ban', 'bs'])
    @commands.is_owner()
    async def ban_server(self, ctx, id: int):
        """Command to leave and ban a server (Owner only)"""
        global banned_server
        try:
            if id not in banned_server: banned_server.append(id)
            toleave = bot.get_guild(id)
            await toleave.leave()
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')
            await printServers()
            await autosave()

    @commands.command(no_pm=True, aliases=['banO', 'bo'])
    @commands.is_owner()
    async def ban_owner(self, ctx, id: int):
        """Command to ban a server owner and leave all its servers (Owner only)"""
        global banned_owner
        try:
            if id not in banned_owner: banned_owner.append(id)
            for g in bot.guilds:
                if g.owner.id == id:
                    await g.leave()
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')
            await printServers()
            await autosave()

    @commands.command(no_pm=True, aliases=['a'])
    @commands.is_owner()
    async def accept(self, ctx, id: int):
        """Command to accept a pending server (Owner only)"""
        global pending_server
        try:
            if id in pending_server:
                guild = bot.get_guild(id)
                if guild:
                    general = getGeneral(guild)
                    if general and general.permissions_for(guild.me).send_messages:
                        await general.send('Here I come, {}!\nUse $help for my list of commands.\nSome commands are restricted to (You) only.\nIf you encounter an issue, use $bug_report and describe the problem.\nIf I\'m down, Master might be working on me :relaxed:.'.format(guild.name))
                del pending_server[id]
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')
            await printServers()
            await autosave()

    @commands.command(no_pm=True, aliases=['r'])
    @commands.is_owner()
    async def refuse(self, ctx, id: int):
        """Command to refuse a pending server (Owner only)"""
        global pending_server
        try:
            if id in pending_server:
                guild = bot.get_guild(id)
                if guild:
                    await guild.leave()
                del pending_server[id]
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')
            await printServers()
            await autosave()

    @commands.command(name='save', no_pm=True, aliases=['s'])
    @commands.is_owner()
    async def _save(self, ctx):
        """Command to make a snapshot of the bot's settings (Owner only)"""
        await ctx.message.add_reaction('✅') # white check mark
        await autosave(True)


    @commands.command(name='load', no_pm=True, aliases=['l'])
    @commands.is_owner()
    async def _load(self, ctx, drive : str = ""):
        """Command to reload the bot settings (Owner only)"""
        global gw_task
        await ctx.message.add_reaction('✅') # white check mark
        if drive == 'drive': 
            loadDrive()
        if load():
            if gw:
                gw_task = bot.loop.create_task(checkGWBuff())
            await debug_channel.send('Data loaded')
            await printServers()
        else:
            await sendDebugStr()
            await debug_channel.send('Failed')

    @commands.command(no_pm=True, aliases=['server'])
    @commands.is_owner()
    async def servers(self, ctx):
        """List all servers (Owner only)"""
        await printServers()

    @commands.command(no_pm=True, aliases=['checkbuff'])
    @commands.is_owner()
    async def buffcheck(self, ctx): # debug stuff
        """List the GW buff list for (You) (Owner only)"""
        msg = ""
        for b in gw_buffs:
            msg += '{0:%m/%d %H:%M}: '.format(b[0])
            if b[1]: msg += '[Normal Buffs] '
            if b[2]: msg += '[FO Buffs] '
            if b[3]: msg += '[Warning] '
            if b[4]: msg += '[Double duration] '
            msg += '\n'
        await debug_channel.send(msg)

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def setMaintenance(self, ctx, day : int, month : int, hour : int, duration : int):
        """Set a maintenance date (Owner only)"""
        global maintenance
        global maintenance_d
        global savePending
        try:
            maintenance = datetime.now().replace(month=month, day=day, hour=hour, minute=0, second=0, microsecond=0)
            maintenance_d = duration
            savePending = True
            await ctx.send('Maintenance set')
        except:
            await ctx.send('Failed to set maintenance')

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def delMaintenance(self, ctx):
        """Delete the maintenance date (Owner only)"""
        global maintenance
        global maintenance_d
        global savePending
        maintenance = None
        maintenance_d = 0
        savePending = True
        await ctx.send('Maintenance deleted')

    @commands.command(no_pm=True, aliases=['as'])
    @commands.is_owner()
    async def addStream(self, ctx, *txt : str):
        """Append a line to the stream command text (Owner only)"""
        global stream_txt
        global savePending
        strs = " ".join(txt).split(';')
        for s in strs:
            stream_txt.append(s)
            await ctx.send('Appending: `' + s + '`')
        savePending = True

    @commands.command(no_pm=True, aliases=['sst'])
    @commands.is_owner()
    async def setStreamTime(self, ctx, day : int, month : int, hour : int):
        """Set the stream time (Owner only)
        The text needs to contain {} for the cooldown to show up"""
        global stream_time
        try:
            stream_time = datetime.now().replace(month=month, day=day, hour=hour, minute=0, second=0, microsecond=0)
            await ctx.send('Stream time set')
            await autosave()
        except:
            await ctx.send('Failed to set Stream time')

    @commands.command(no_pm=True, aliases=['cs'])
    @commands.is_owner()
    async def clearStream(self, ctx):
        """Clear the stream command text (Owner only)
        You can add multiple lines at once by adding ; between them"""
        global stream_txt
        global stream_time
        global savePending
        stream_txt = []
        stream_time = None
        await ctx.send('Done')
        savePending = True

    @commands.command(no_pm=True, aliases=['dsl'])
    @commands.is_owner()
    async def delStreamLine(self, ctx, line : int = 0, many : int = 1):
        """Delete a line from stream command text (Owner only)
        By default, the first line is deleted
        You can specify how many you want to delete"""
        global stream_txt
        global savePending
        if many < 1:
            await ctx.send("You can't delete less than one line")
        elif line < len(stream_txt) and line >= 0:
            if many + line > len(stream_txt):
                many = len(stream_txt) - line
            for i in range(0, many):
                msg = stream_txt.pop(line)
                await ctx.send("Removed: `" + msg + "`")
            savePending = True
        else:
            await ctx.send("The line number isn't valid")

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def setSchedule(self, ctx, *txt : str):
        """Set the GBF schedule for the month (Owner only)
        Use ; to input a newline character"""
        global gbfschedule
        global savePending
        strs = " ".join(txt).split(';')
        msg = ""
        for s in strs:
            msg += s + "\n"
        gbfschedule = msg[:-1]
        await ctx.send('Done')
        savePending = True

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def setStatus(self, ctx, *terms : str):
        """Change the bot status (Owner only)"""
        s = " ".join(terms)
        if not s: return
        await self.bot.change_presence(status=discord.Status.online, activity=discord.activity.Game(name=s))
        await ctx.send('I changed my status to: ' + s)

    @commands.command(no_pm=True, hidden=True)
    @commands.is_owner()
    async def banRollID(self, ctx, user: int):
        """ID based Ban for $rollranking"""
        global savePending
        global spark_ban
        if user not in spark_ban:
            spark_ban.append(user)
            await ctx.send(str(user) + ' is banned from all roll rankings')
            savePending = True
        else:
            await ctx.send(str(user) + ' is already banned')

    @commands.command(no_pm=True, aliases=['unbanspark'])
    @commands.is_owner()
    async def unbanRoll(self, ctx, id : int):
        """Unban an user from all the roll ranking (Owner only)
        Ask me for an unban (to avoid abuses)"""
        global savePending
        global spark_ban
        if id not in spark_ban:
            await ctx.send(str(id) + ' isn\'t banned')
        else:
            i = 0
            while i < len(spark_ban):
                if id == spark_ban[i]: spark_ban.pop(i)
                else: i += 1
            await ctx.send(str(id) + ' is unbanned')
            savePending = True

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def cleanRoll(self, ctx):
        """Remove users with 0 rolls (Owner only)"""
        global spark_list
        global savePending
        count = 0
        for k in list(spark_list.keys()):
            sum = spark_list[k][0] + spark_list[k][1] + spark_list[k][2]
            if sum == 0:
                spark_list.pop(k)
                count += 1
        if count > 0:
            savePending = True
            await ctx.send('Removed ' + str(count) + ' user(s)')
        else:
            await ctx.send('Removed 0 users')

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def resetGacha(self, ctx):
        """Reset the gacha settings"""
        if not gbfdm:
            return
        gbfc.resetGacha()
        await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def logout(self, ctx):
        """Make the bot quit"""
        global isRunning
        isRunning = False
        await autosave()
        await self.bot.logout()

    @commands.command(no_pm=True)
    @commands.is_owner()
    async def config(self, ctx):
        """Post the current config file in the debug channel"""
        try:
            with open('config.json', 'r') as infile:
                await debug_channel.send('config file', file=discord.File(infile))
        except Exception as e:
            pass

# /gbfg/ Lucilius system command
luciStr = ['wish them good luck :wave:', 'bet on the MVP element :top:', 'another fail for the council :pensive:']
elemStr = {"fire":0, "water":1, "gay":1, "wawi":1, "earth":2, "dirt":2, "wind":3, "roach":3, "light":4, "dark":5}
elemEmote = {"fire":"fire", "water":"water", "gay":"water", "wawi":"water", "earth":"earth", "dirt":"earth", "wind":"wind", "roach":"wind", "light":"light", "dark":"dark"}
class Lucilius(commands.Cog):
    """/gbfg/ Lucilius commands."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True, aliases=['lucilist'])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def llist(self, ctx, id : int = 0):
        """List the Lucilius parties
        You can specify the number to get details"""
        if not isLuciliusMainChannel(ctx.channel) and not isLuciliusPartyChannel(ctx.channel): return
        if id == 0:
            x = 0
            msg = ""
            c = datetime.utcnow()
            for i in range(0, len(luciParty)):
                if luciParty[i] is None:
                    x += 1
                    continue
                u = ctx.guild.get_member(luciParty[i][2])
                if u is None: u = "<unknown user>"
                else: u = u.display_name
                msg += getEmoteStr(str(i+1)) + " Leader **" + u + "**, " + str(len(luciParty[i])-2) + " / 6, **" + luciParty[i][1] + "**"
                d = c - luciParty[i][0]
                if luciParty[i][1] == "Preparing": t = timedelta(seconds=600)
                elif luciParty[i][1] == "Playing": t = timedelta(seconds=3600)
                elif luciParty[i][1] == "Playing (Extended)": t = timedelta(seconds=10800)
                else: t = timedelta(seconds=0)
                if d > t: msg += ", **closing soon!!**\n"
                else:
                    dt = t - d
                    m = dt.seconds // 60
                    msg += ", " + str(dt.seconds // 60) + " minute(s) left\n"
            if x == 6:
                msg = "No party playing currently"
            else:
                msg = "**" + str(6-x) + " / " + str(len(luciParty)) + " slots:**\n" + msg
            await ctx.send(msg)
        elif id >= 1 or id <= 6:
            id = id - 1
            if luciParty[id] is None:
                await ctx.send("This party doesn't exist")
            else:
                msg = getEmoteStr(str(id+1)) + " "
                for i in range(2, len(luciParty[id])):
                    try:
                        if i == 2: msg += "**" + ctx.author.guild.get_member(luciParty[id][i]).display_name + "**"
                        else: msg += ctx.author.guild.get_member(luciParty[id][i]).display_name
                    except:
                        msg += "<Unknown>"
                    if i < len(luciParty[id]) - 1:
                        msg += ", "
                msg += "\n" + luciParty[id][1]
                c = datetime.utcnow()
                d = c - luciParty[id][0]
                if luciParty[id][1] == "Preparing": t = timedelta(seconds=600)
                elif luciParty[id][1] == "Playing": t = timedelta(seconds=3600)
                elif luciParty[id][1] == "Playing (Extended)": t = timedelta(seconds=10800)
                else: t = timedelta(seconds=0)
                if d > t: msg += ", **Closing soon!!**\n"
                else:
                    dt = t - d
                    m = dt.seconds // 60
                    msg += ", " + str(dt.seconds // 60) + " minute(s) left"
                await ctx.send(msg)

    @commands.command(no_pm=True, aliases=['lucimake'])
    @commands.cooldown(2, 20, commands.BucketType.user)
    async def lmake(self, ctx):
        """Make a new party
        you have 10 minutes to start before the automatic disband"""
        global savePending
        global luciParty
        if not isLuciliusMainChannel(ctx.channel): return
        if ctx.author.id in luciBlacklist and luciBlacklist[ctx.author.id] <= 1:
            await ctx.send("You are banned from making a party")
            return
        for i in range(0, len(luciParty)):
            if luciParty[i] is None:
                continue
            for j in range(2, len(luciParty[i])):
                if luciParty[i][j] == ctx.author.id:
                    if j == 2:
                        await ctx.send(ctx.author.display_name + ", you are already leader of party " + getEmoteStr(str(i+1)) + ", use `%ldisband` to disband your current party")
                    else:
                        await ctx.send(ctx.author.display_name + ", you are already in party " + getEmoteStr(str(i+1)) + ", use `%lleave " + str(i+1) + "` to leave your current party")
                    return
        for i in range(0, len(luciParty)):
            if luciParty[i] is None:
                luciParty[i] = [datetime.utcnow().replace(microsecond=0), "Preparing", ctx.author.id]
                savePending = True
                await ctx.send(":white_check_mark: Party slot " + getEmoteStr(str(i+1)) + " given to " + ctx.author.display_name + "\nYou have 10 minutes for people to join using `%ljoin` and you to start using `%lstart`")
                await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " made a party in slot " + str(i+1))
                return
        await ctx.send("All slots are in use, please wait")

    @commands.command(no_pm=True, aliases=['lucidisband'])
    async def ldisband(self, ctx, id : int = 0):
        """Disband a party
        you have to be leader of the party
        or, if you are a moderator, you can specify a party number to disband it"""
        global savePending
        global luciParty
        global luciWarning
        if not isLuciliusMainChannel(ctx.channel) and not isLuciliusPartyChannel(ctx.channel): return
        if isMod(ctx.author) and id != 0:
            id = id - 1
            mod = True
            if id < 0 and id >= len(luciParty):
                await ctx.send("Invalid party number")
                return
            if luciParty[id] is None:
                await ctx.send("Party " + getEmoteStr(str(id+1)) + " doesn't exist")
                return
        else:
            id = -1
            mod = False
            for i in range(0, len(luciParty)):
                if luciParty[i] is not None and ctx.author.id == luciParty[i][2]:
                    id = i
                    break
        if id == -1:
            await ctx.send("You aren't leader of a party")
        else:
            if luciParty[id][1] != "Preparing":
                role = ctx.message.author.guild.get_role(luciRole[id])
                for j in range(2, len(luciParty[id])):
                    try:
                        await ctx.author.guild.get_member(luciParty[id][j]).remove_roles(role)
                    except:
                        pass
            luciParty[id] = None
            luciWarning[id] = 0
            savePending = True
            if mod:
                await ctx.send(":x: Party " + getEmoteStr(str(id+1)) + " is now free (moderator action: `" + ctx.author.display_name + "`)")
                await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: Moderator " + ctx.author.display_name + " disbanded the party in slot " + str(id+1))
            else:
                await lucimain_channel.send(":x: Party " + getEmoteStr(str(id+1)) + " is now free")
                await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " disbanded the party in slot " + str(id+1))
            return

    @commands.command(no_pm=True, aliases=['luciextend'])
    async def lextend(self, ctx):
        """Extend a party timer
        you have to be leader of the party"""
        global savePending
        global luciParty
        if not isLuciliusMainChannel(ctx.channel) and not isLuciliusPartyChannel(ctx.channel): return
        id = -1
        for i in range(0, len(luciParty)):
            if luciParty[i] is not None and ctx.author.id == luciParty[i][2]:
                id = i
                break
        if id == -1:
            await ctx.send("You aren't leader of a party")
        elif luciParty[id][1] == "Preparing":
            await ctx.send("You can extend after starting")
        elif luciParty[id][1] == "Playing (Extended)":
            await ctx.send("You can only extend once")
        else:
            luciParty[id][1] = "Playing (Extended)"
            savePending = True
            await ctx.send(getEmoteStr('time') + " **Two** more hours have been added to Party " + getEmoteStr(str(id+1)))
            await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " extended the party in slot " + str(id+1))
            return

    @commands.command(no_pm=True, aliases=['lucistart'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def lstart(self, ctx):
        """Start fighting with your party"""
        global savePending
        global luciParty
        if not isLuciliusMainChannel(ctx.channel): return
        for i in range(0, len(luciParty)):
            if luciParty[i] is not None and ctx.author.id == luciParty[i][2]:
                if luciParty[i][1] == "Preparing":
                    try:
                        role = ctx.message.author.guild.get_role(luciRole[i])
                        lc = self.bot.get_channel(luciChannel[i])
                        luciParty[i][1] = "Playing"
                        luciParty[i][0] = datetime.utcnow().replace(microsecond=0)
                        savePending = True
                        # start message
                        await lucimain_channel.send("Party " + getEmoteStr(str(i+1)) + " started, " + random.choice(luciStr))
                        # ping the party
                        for j in range(2, len(luciParty[i])):
                            try:
                                await ctx.author.guild.get_member(luciParty[i][j]).add_roles(role)
                            except Exception as e:
                                await debug_channel.send(str(e))
                        msg = ":ok: " + role.mention + " can start, you have 60 minutes until the automatic disband.\n`%ldisband` to free the room once you are done.\n`%lextend` to extend the room timer if needed (once).\n`%llist " + str(i+1) + "` to see the remaining time.\n`%lhelp` for the command list.\nMember List: "
                        ### add individual pings
                        for j in range(2, len(luciParty[i])):
                            try:
                                msg += ctx.author.guild.get_member(luciParty[i][j]).mention
                                if j < len(luciParty[i]) - 1:
                                    msg += ", "
                            except:
                                pass
                        await lc.send(msg)
                        await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " started a fight with the party in slot " + str(i+1))
                        # change the channel topic with member names
                        msg = ""
                        for j in range(2, len(luciParty[i])):
                            try:
                                msg += ctx.author.guild.get_member(luciParty[i][j]).name
                                if j < len(luciParty[i]) - 1:
                                    msg += ", "
                            except:
                                pass
                        if len(msg) > 1000: msg = msg[:1000] + "..."
                        await lc.edit(topic=msg)
                    except Exception as e:
                        await debug_channel.send("LuciStart(): " + str(e))
                        await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: LuciStart(): " + str(e))
                        await ctx.send("An error happened")
                return
        await ctx.send("You aren't leader of a party")

    @commands.command(no_pm=True, aliases=['lucikick'])
    async def lkick(self, ctx, user: discord.Member):
        """Kick a member from your party"""
        global savePending
        global luciParty
        if not isLuciliusMainChannel(ctx.channel) and not isLuciliusPartyChannel(ctx.channel): return
        if user is None:
            await ctx.send("Please give me a ping to the user you want to kick")
            return
        for i in range(0, len(luciParty)):
            if luciParty[i] is not None and ctx.author.id == luciParty[i][2]:
                for j in range(3, len(luciParty[i])):
                    if luciParty[i][j] == user.id:
                        luciParty[i].pop(j)
                        savePending = True
                        extra = ""
                        if luciParty[i][1] != "Preparing":
                            lc = self.bot.get_channel(luciChannel[i])
                            role = ctx.message.author.guild.get_role(luciRole[i])
                            try:
                                await user.remove_roles(role)
                            except:
                                pass
                            extra = " (while the party was playing)"
                            if ctx.channel.id != luciChannel[i]:
                                await lc.send(ctx.author.display_name + " has been kicked")
                            # change the channel topic with member names
                            topic = ""
                            for j in range(2, len(luciParty[i])):
                                try:
                                    topic += ctx.author.guild.get_member(luciParty[i][j]).name
                                    if j < len(luciParty[i]) - 1:
                                        topic += ", "
                                except:
                                    pass
                            if len(topic) > 1000: topic = topic[:1000] + "..."
                            await lc.edit(topic=topic)
                        await ctx.send(":no_entry: " + user.display_name + " has been removed from party slot " + getEmoteStr(str(i+1)))
                        await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " kicked " + user.display_name + " from the party in slot " + str(i+1) + extra)
                        return
                await ctx.send(user.display_name + " not found in party slot " + getEmoteStr(str(i+1)))
                return
        await ctx.send("You aren't leader of a party")

    @commands.command(no_pm=True, aliases=['lucijoin'])
    @commands.cooldown(3, 20, commands.BucketType.user)
    async def ljoin(self, ctx, id : int = -999999999998):
        """Join a party"""
        global savePending
        global luciParty
        if not isLuciliusMainChannel(ctx.channel): return
        if ctx.author.id in luciBlacklist and luciBlacklist[ctx.author.id] != 1:
            await ctx.send("You are banned from joining")
            return
        if id == -999999999998:
            cn = 0
            id = 0
            for i in range(0, len(luciParty)):
                if luciParty[i] is not None and luciParty[i][1] == "Preparing":
                    cn += 1
                    id = i + 1
            if cn < 1:
                await ctx.send("No party available at the moment")
                return
            elif cn > 1:
                await ctx.send("Please give me the number of the party that you want to join")
                return
        id = id - 1
        if id < 0 or id >= len(luciParty):
            await ctx.send("Invalid party number")
            return
        for i in range(0, len(luciParty)):
            if luciParty[i] is None:
                continue
            for j in range(2, len(luciParty[i])):
                if luciParty[i][j] == ctx.author.id:
                    if j == 2:
                        await ctx.send(ctx.author.display_name + ", you are already leader of party " + getEmoteStr(str(i+1)) + ", use `%ldisband` to disband your current party")
                    else:
                        await ctx.send(ctx.author.display_name + ", you are already in party " + getEmoteStr(str(i+1)) + ", use `%lleave " + str(i+1) + "` to leave your current party")
                    return
        if luciParty[id] is None:
            await ctx.send("This party doesn't exist")
        elif len(luciParty[id]) >= 8:
            await ctx.send("This party is full")
        elif luciParty[id][1] != "Preparing":
            await ctx.send("This party is already playing")
        else:
            luciParty[id].append(ctx.author.id)
            savePending = True
            msg = ""
            if len(luciParty[id]) >= 8:
                msg = ctx.author.guild.get_member(luciParty[id][2]).mention + ", your party is full: "
                for i in range(3, len(luciParty[id])):
                    try:
                        msg += ctx.author.guild.get_member(luciParty[id][i]).display_name
                    except:
                        msg += "<unknown user>"
                    if i < len(luciParty[id]) - 1:
                        msg += ", "
                msg += "\nUse `%llist " + str(id+1) + "` to see your party or `%lstart` to start playing"
            await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " joined the party in slot " + str(id+1) + " (" + str(len(luciParty[id])-2) + "/6)")
            await ctx.send(ctx.author.display_name + " added to party " + getEmoteStr(str(id+1)))
            if len(msg) > 0:
                await ctx.send(msg)

    @commands.command(no_pm=True, aliases=['luciadd'])
    @commands.cooldown(3, 20, commands.BucketType.user)
    async def ladd(self, ctx, user: discord.Member):
        """Get someone in your party while playing
        you have to be leader of the party"""
        global savePending
        global luciParty
        if not isLuciliusMainChannel(ctx.channel) and not isLuciliusPartyChannel(ctx.channel): return
        if user is None:
            await ctx.send("Please give me a ping to the user you want to add")
            return
        id = -1
        for i in range(0, len(luciParty)):
            if luciParty[i] is None:
                continue
            for j in range(2, len(luciParty[i])):
                if luciParty[i][j] == ctx.author.id:
                    if j == 2:
                        id = i
                        break
                    else:
                        await ctx.send("Only the leader of the party can bring someone in a party")
                        return
        if id == -1 or luciParty[id] is None:
            await ctx.send("You aren't leader of a party")
        elif len(luciParty[id]) >= 8:
            await ctx.send("This party is already full")
        elif luciParty[id][1] == "Preparing":
            await ctx.send("This party isn't playing")
        else:
            luciParty[id].append(user.id)
            savePending = True

            role = ctx.message.author.guild.get_role(luciRole[id])
            lc = self.bot.get_channel(luciChannel[id])
            try:
                await user.add_roles(role)
            except Exception as e:
                await debug_channel.send(str(e))
            # change the channel topic with member names
            topic = ""
            for j in range(2, len(luciParty[id])):
                try:
                    topic += ctx.author.guild.get_member(luciParty[id][j]).name
                    if j < len(luciParty[id]) - 1:
                        topic += ", "
                except:
                    pass
            if len(topic) > 1000: topic = topic[:1000] + "..."
            await lc.edit(topic=topic)
            # msg
            await lc.send(user.mention + " added to party " + getEmoteStr(str(id+1)))
            await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + user.display_name + " has been added to the party in slot " + str(id+1) + " (" + str(len(luciParty[id])-2) + "/6) by " + ctx.author.display_name)
            await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True, aliases=['lucileave'])
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def lleave(self, ctx):
        """Leave a party"""
        global savePending
        global luciParty
        if not isLuciliusMainChannel(ctx.channel) and not isLuciliusPartyChannel(ctx.channel): return
        id = None
        for i in range(0, len(luciParty)):
            if luciParty[i] is None:
                continue
            for j in range(2, len(luciParty[i])):
                if luciParty[i][j] == ctx.author.id:
                    if j == 2:
                        await ctx.send(ctx.author.display_name + ", you are leader of party " + getEmoteStr(str(i+1)) + ", use `%ldisband` to disband your current party")
                        return
                    else:
                        id = [i, j]
                        break
            if id is not None: break

        if id is None:
            await ctx.send("You aren't in a party")
        else:
            m = luciParty[i].pop(j)
            savePending = True
            extra = ""
            if luciParty[i][1] != "Preparing":
                lc = self.bot.get_channel(luciChannel[i])
                role = ctx.message.author.guild.get_role(luciRole[i])
                try:
                    await ctx.author.guild.get_member(m).remove_roles(role)
                except:
                    pass
                if ctx.channel.id != luciChannel[i]:
                    await lc.send(ctx.author.display_name + " left")
                extra = " (while the party was playing)"
                # change the channel topic with member names
                topic = ""
                for x in range(2, len(luciParty[i])):
                    try:
                        topic += ctx.author.guild.get_member(luciParty[i][x]).name
                        if x < len(luciParty[i]) - 1:
                            topic += ", "
                    except:
                        pass
                if len(topic) > 1000: topic = topic[:1000] + "..."
                await lc.edit(topic=topic)
            # msg
            await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " left from the party in slot " + str(i+1) + extra)
            await ctx.send(ctx.author.display_name + " left from party " + getEmoteStr(str(i+1)))

    @commands.command(no_pm=True, aliases=['lucihelp'])
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def lhelp(self, ctx):
        """Post the command list"""
        if not isLuciliusMainChannel(ctx.channel) and not isLuciliusPartyChannel(ctx.channel): return
        await ctx.send(":regional_indicator_p: Party:\n```\nlmake              Make a new party\nljoin <party #>    Join a party\nlleave             Leave the party\nllist              List the Lucilius parties\nllist <party #>    List the party members\n```\n:regional_indicator_l: Party Leader:\n```\nlstart             Start fighting with your party\nldisband           Disband your party\nlextend            Add two hours to a playing party timer (once)\nladd <ping>        Add a member to your party while playing\nlkick <ping>       Kick a member from your party\n```\n:regional_indicator_m: Moderation:\n```\nlban <ping><type>  Ban an user (type: join, make or all)\nlunban <ping>      Unban an user\nldisband <party #> Force disband a party\n```\nUse `lhelp` to show this text or `help <command name>` for details.")

    @commands.command(no_pm=True, aliases=['luciban'])
    async def lban(self, ctx, user: discord.Member, type : str = ""):
        """Ban an user (Mod only)
        you must specify 'all', 'make' or 'join' for the ban type"""
        global savePending
        global luciBlacklist
        if not isLuciliusMainChannel(ctx.channel) and not isLuciliusPartyChannel(ctx.channel): return
        if not isMod(ctx.author): return
        if user is None:
            await ctx.send("Please give me a ping to the user you want to ban")
            return
        if ctx.author.id == user.id:
            await ctx.send(user.display_name + ', you can\'t ban yourself')
            return
        type = type.lower()
        if type == 'all':
            luciBlacklist[user.id] = 0
            savePending = True
            await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " banned " + user.display_name + " (id:" + str(user.id) + ") from making and joining parties")
            await ctx.send(user.display_name + ' has been banned from making and joining parties')
        elif type.lower() == 'make':
            luciBlacklist[user.id] = 1
            savePending = True
            await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " banned " + user.display_name + " (id:" + str(user.id) + ") from making parties")
            await ctx.send(user.display_name + ' has been banned from making parties')
        elif type.lower() == 'join':
            luciBlacklist[user.id] = 2
            savePending = True
            await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " banned " + user.display_name + " (id:" + str(user.id) + ") from joining parties")
            await ctx.send(user.display_name + ' has been banned from joining parties')
        else:
            await ctx.send('Please give me the type of ban `lban <user> <type:all|make|join>`')

    @commands.command(no_pm=True, aliases=['luciunban'])
    async def lunban(self, ctx, user: discord.Member):
        """Unban an user (Mod only)"""
        global savePending
        global luciBlacklist
        if not isLuciliusMainChannel(ctx.channel) and not isLuciliusPartyChannel(ctx.channel): return
        if not isMod(ctx.author): return
        if user is None:
            await ctx.send("Please give me a ping to the user you want to unban")
            return
        if ctx.author.id == user.id:
            await ctx.send(user.display_name + ', you can\'t unban yourself')
            return
        if luciBlacklist.pop(user.id, None) is None:
            await ctx.send(user.display_name + " isn't banned")
        else:
            savePending = True
            await lucilog_channel.send("**" + datetime.utcnow().strftime("%Y/%m/%d at %H-%M-%S") + "**: " + ctx.author.display_name + " unbanned " + user.display_name + " (id:" + str(user.id) + ")")
            await ctx.send(user.display_name + ' has been unbanned')

    @commands.command(no_pm=True)
    async def iam(self, ctx, *elems: str):
        """Add yourself to an element role"""
        if not isLuciliusMainChannel(ctx.channel): return
        f = {}
        for e in elems:
            if e.lower() in elemStr:
                role = ctx.message.author.guild.get_role(luciElemRole[elemStr[e]])
                try:
                    await ctx.author.add_roles(role)
                    f[elemEmote[e]] = None
                except:
                    pass
        for fe in f:
            await react(ctx, fe)

    @commands.command(no_pm=True, aliases=['iamn'])
    async def iamnot(self, ctx, *elems: str):
        """Remove yourself from an element role"""
        if not isLuciliusMainChannel(ctx.channel): return
        f = {}
        for e in elems:
            if e.lower() in elemStr:
                role = ctx.message.author.guild.get_role(luciElemRole[elemStr[e]])
                try:
                    await ctx.author.remove_roles(role)
                    f[elemEmote[e]] = None
                except:
                    pass
        for fe in f:
            await react(ctx, fe)

    @commands.command(no_pm=True, aliases=['summon'])
    @commands.cooldown(10, 60, commands.BucketType.guild)
    async def call(self, ctx, *elems : str):
        """Call user in the element list(s)"""
        if not isLuciliusMainChannel(ctx.channel): return
        for p in range(0, len(luciParty)):
            if luciParty[p] is not None and luciParty[p][2] == ctx.author.id:
                msg = ""
                for e in elems:
                    if e.lower() in elemStr:
                        role = ctx.message.author.guild.get_role(luciElemRole[elemStr[e.lower()]])
                        if len(msg) > 0: msg += ", "
                        msg += role.mention
                if len(msg) == 0:
                    await ctx.send("Tell me what element to call")
                else:
                    await ctx.send("Party " + getEmoteStr(str(p+1)) + " is calling for " + msg + " players")
                return
        await ctx.send("You must be leader of a party")


class WIP(commands.Cog):
    """WIP"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True, hidden=True)
    @commands.is_owner()
    async def test_say(self, ctx, term : str):
        """Say what we want it to say"""
        await ctx.send(term)

    @commands.command(no_pm=True, hidden=True)
    @commands.is_owner()
    async def send_wawi(self, ctx, *terms : str):
        """debug"""
        if len(terms) == 0: return
        guild = self.bot.get_guild(327162356327251969)
        msg = guild.get_member(wawi_id).mention + ' ' + " ".join(terms)
        for c in guild.text_channels:
            if c.permissions_for(guild.me).send_messages:
                await c.send(msg)
                await ctx.send('Message sent')
                return
        await ctx.send('Failed')

    @commands.command(no_pm=True, hidden=True)
    @commands.is_owner()
    async def punish(self, ctx):
        """debug"""
        await ctx.send("Please, Master, make it hurt.")

    @commands.command(no_pm=True, hidden=True)
    @commands.is_owner()
    async def test_wawi(self, ctx):
        """Bully Wawi"""
        try:
            await ctx.send('guild: ' + ctx.message.author.guild.name)
            await ctx.send(str(len(ctx.message.author.guild.roles)) + ' roles')
            for r in ctx.message.author.guild.roles:
                if r.name == 'Wawi':
                    await ctx.send(str(r.id))
                    return
            await ctx.send('Wawi not found')
        except:
            pass

    @commands.command(no_pm=True, hidden=True)
    @commands.is_owner()
    async def gbfg_ubhl(self, ctx):
        ubhl_c = bot.get_channel(352637213089202176)
        gbfg_g = bot.get_guild(339155308767215618)
        whitelist = {}
        await ctx.send("Please be patient...")
        async for message in ubhl_c.history(limit=10000): 
            if message.author.id in whitelist:
                continue
            else:
                whitelist[str(message.author)] = 0
        await ctx.send(str(len(whitelist)) + " user(s) in the last 10 000 messages of #ubaha-hl\nPurging...")
        i = 0
        for member in gbfg_g.members:
            for r in member.roles:
                if r.name == 'UBaha HL':
                    if str(member) in whitelist:
                        pass
                    else:
                        await member.remove_roles(r)
                        i += 1
                    break
        await ctx.send(str(i) + " inactive user(s) removed from #ubaha-hl")

    @commands.command(no_pm=True, hidden=True)
    @commands.is_owner()
    async def gbfg_search(self, ctx):
        u = bot.get_guild(339155308767215618).get_member(384567705853755403)
        if u:
            await ctx.send(U.name)
        else:
            await ctx.send('Not found')

bot.add_cog(General(bot))
bot.add_cog(GBF_Game(bot))
bot.add_cog(GBF_Utility(bot))
bot.add_cog(GW(bot))
bot.add_cog(MizaBOT(bot))
bot.add_cog(Owner(bot))
bot.add_cog(Lucilius(bot))
bot.add_cog(WIP(bot))
if gbfdm:
    gbfc = baguette.Baguette(bot, gbfd, savePendingCallback, getEmoteStr, gbfdd)
    bot.add_cog(gbfc)

#test
import signal
class GracefulExit:
  def __init__(self):
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    global exit_flag
    exit_flag = True
    if savePending:
        if save(False):
            print('Autosave Success')
        else:
            print('Autosave Failed')
    exit(0) # not graceful at all

# main loop
grace = GracefulExit()
while isRunning:
    try:
        bot.loop.run_until_complete(bot.start(bot_token))
    except Exception as e:
        isRunning = False
        print("Main Loop Exception: " + str(e))
if save():
    print('Autosave Success')
else:
    print('Autosave Failed')
time.sleep(10)