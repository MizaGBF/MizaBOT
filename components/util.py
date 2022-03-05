import disnake
import asyncio
import random
from datetime import datetime, timedelta
import psutil
import os
from shutil import copyfile
import traceback
import re

# ----------------------------------------------------------------------------------------------------------------
# Utility Component
# ----------------------------------------------------------------------------------------------------------------
# Feature a lot of utility functions
# ----------------------------------------------------------------------------------------------------------------

class Util():
    def __init__(self, bot):
        self.bot = bot
        self.emote = None
        self.starttime = datetime.utcnow() # used to check the uptime
        self.process = psutil.Process(os.getpid())
        self.process.cpu_percent() # called once to initialize
        self.search_re = [
            re.compile('([12][0-9]{9})\\.'),
            re.compile('([12][0-9]{9}_02)\\.')
        ]

    def init(self):
        self.emote = self.bot.emote

    """json_deserial_array()
    Deserialize a list (used for our json files)
    
    Parameters
    ----------
    array: List
    
    Returns
    --------
    list: Deserialized list
    """
    def json_deserial_array(self, array):
        a = []
        for v in array:
            match v:
                case list():
                    a.append(self.json_deserial_array(v))
                case dict():
                    a.append(self.json_deserial_dict(list(v.items())))
                case str():
                    try:
                        a.append(datetime.strptime(v, "%Y-%m-%dT%H:%M:%S")) # needed for datetimes
                    except ValueError:
                        a.append(v)
                case _:
                    a.append(v)
        return a

    """json_deserial_dict()
    Deserialize a dict (used for our json files)
    
    Parameters
    ----------
    pairs: dict
    
    Returns
    --------
    dict: Deserialized Dict
    """
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

    """json_serial()
    Serialize a datetime instance (used for our json files)
    
    Parameters
    ----------
    obj: datetime instance
    
    Raises
    ------
    TypeError: obj isn't a datetime
    
    Returns
    --------
    unknown: Serialized object
    """
    def json_serial(self, obj): # serialize everything including datetime objects
        if isinstance(obj, datetime):
            return obj.replace(microsecond=0).isoformat()
        raise TypeError ("Type %s not serializable" % type(obj))

    """timestamp()
    Return the current time, UTC timezone

    Returns
    --------
    datetime: Current time
    """
    def timestamp(self):
        return datetime.utcnow()

    """JST()
    Return the current time, JST timezone

    Returns
    --------
    datetime: Current time
    """
    def JST(self):
        return datetime.utcnow() + timedelta(seconds=32400) - timedelta(seconds=30)

    """time()
    Format a timestamp or datetime object

    Parameters
    --------
    to_convert: time to format
    style: format style, see https://discord.com/developers/docs/reference#message-formatting-timestamp-styles
           you can combine multiple styles together
    jstshift: Bool, if True, remove 9h to the datetime

    Returns
    --------
    str: Formatted time
    """
    def time(self, to_convert = None, style = 'f', removejst = False):
        if to_convert is None: to_convert = datetime.utcnow()
        msg = ""
        if removejst: to_convert -= timedelta(seconds=32400)
        for c in style:
            msg += disnake.utils.format_dt(to_convert, c)
            msg += " "
        return msg[:-1]

    """uptime()
    Return the bot uptime
    
    Parameters
    ----------
    string: If true, the uptime is returned as a string
    
    Returns
    --------
    timedelta: Bot uptime
    """
    def uptime(self, string=True): # get the uptime
        delta = datetime.utcnow() - self.starttime
        if string: return "{}".format(self.delta2str(delta, 3))
        else: return delta

    """delta2str()
    Convert a timedelta object to a string (format: XdXhXmXs)
    
    Parameters
    ----------
    delta: Timedelta object
    mode: Affect the formatting:
        1 (default): Hours and Minutes
        2: Days, Hours and Minutes
        3: Days, Hours, Minutes and Seconds
        Anything else: Minutes
    
    Returns
    --------
    str: Resulting string
    """
    def delta2str(self, delta, mode=1):
        match mode:
            case 3: return "{}d{}h{}m{}s".format(delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60, delta.seconds % 60)
            case 2: return "{}d{}h{}m".format(delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60)
            case 1: return "{}h{}m".format(delta.seconds // 3600, (delta.seconds // 60) % 60)
            case _: return "{}m".format(delta.seconds // 60)

    """str2delta()
    Convert string to a a timedelta object (format: XdXhXmXs)
    
    Parameters
    ----------
    d: The string to convert
    
    Returns
    --------
    timedelta: Resulting timedelta object
    """
    def str2delta(self, d): # return None if error
        flags = {'d':False,'h':False,'m':False}
        tmp = 0 # buffer
        sum = 0 # delta in seconds
        for c in d:
            if c.isdigit():
                tmp = (tmp * 10) + int(c)
            elif c.lower() in flags:
                if flags[c.lower()]:
                    return None
                if tmp < 0:
                    return None
                flags[c.lower()] = True
                match c:
                    case 'd': sum += tmp * 86400
                    case 'h': sum += tmp * 3600
                    case 'm': sum += tmp * 60
                tmp = 0
            else:
                return None
        if tmp != 0: return None
        return timedelta(days=sum//86400, seconds=sum%86400)

    """status()
    Return the bot status
    
    Returns
    --------
    dict: Dict of string
    """
    def status(self):
        return {
            "Version": self.bot.version,
            "Uptime": self.uptime(),
            "CPU": "{}%".format(self.process.cpu_percent()),
            "Memory": "{}MB".format(self.process.memory_info()[0]>>20),
            "Save": ("**Pending**" if self.bot.data.pending else "Ok"),
            "Errors": ("**{}**".format(self.bot.errn) if self.bot.errn > 0 else str(self.bot.errn)),
            "Task Count": str(len(asyncio.all_tasks())),
            "Server Count": str(len(self.bot.guilds)),
            "Cogs Loaded": "{}/{}".format(len(self.bot.cogs), self.bot.cogn) if (len(self.bot.cogs) == self.bot.cogn) else "**{}**/{}".format(len(self.bot.cogs), self.bot.cogn),
            "Twitter": ("Disabled" if (self.bot.twitter.client is None) else "Online")
        }

    """statusString()
    Return the bot status as a single string (call status() )
    
    Returns
    --------
    str: Status string
    """
    def statusString(self):
        status = self.status()
        msg = ""
        for k in status:
            msg += "**{}**▫️{}\n".format(k, status[k])
        return msg

    """react()
    React to a message with an emoji
    
    Parameters
    ----------
    msg: disnake.Message object
    key: Either the emoji key set in config.json or the emoji in string format

    Returns
    --------
    bool: True if success, False if not
    """
    async def react(self, msg, key):
        try:
            await msg.add_reaction(self.emote.get(key))
            return True
        except Exception as e:
            if str(e) != "404 Not Found (error code: 10008): Unknown Message":
                await self.bot.sendError('react', e)
            return False

    """unreact()
    Remove a bot reaction to a message
    
    Parameters
    ----------
    msg: disnake.Message object
    key: Either the emoji key set in config.json or the emoji in string format

    Returns
    --------
    bool: True if success, False if not
    """
    async def unreact(self, msg, key): # remove a reaction using a custom emote defined in config.json
        try:
            await msg.remove_reaction(self.emote.get(key), msg.guild.me)
            return True
        except Exception as e:
            if str(e) != "404 Not Found (error code: 10008): Unknown Message":
                await self.bot.sendError('unreact', e)
            return False

    """clean()
    Delete a bot command message after X amount of time.
    A white check mark is added in reaction to the original command after deletion
    
    Parameters
    ----------
    target: Tuple of a Disnake Context and Message OR a Disnake Interaction
    delay: Time in second before deletion
    all: if True, the message will be deleted, if False, the message is deleted it it was posted in an unauthorized channel
    """
    async def clean(self, target, delay=None, all=False):
        try:
            if isinstance(target, tuple):
                if all or not self.bot.isAuthorized(target[0]):
                    await target[1].delete(delay=delay)
                    try: await self.react(target[0].message, '✅') # white check mark
                    except: pass
            elif isinstance(target, disnake.interactions.application_command.ApplicationCommandInteraction):
                if all or not self.bot.isAuthorized(target):
                    if delay is not None: await asyncio.sleep(delay)
                    await target.edit_original_message(content="{}".format(self.bot.emote.get('lyria')), embed=None, view=None, attachments=[])
        except Exception as e:
            if "Unknown Message" not in str(e):
                await self.bot.sendError("clean", e)

    """embed()
    Create a disnake.Embed object
    
    Parameters
    ----------
    **options: disnake.Embed options

    Returns
    --------
    disnake.Embed: The created embed
    """
    def embed(self, **options): # make a full embed
        embed = disnake.Embed(title=options.get('title', ""), description=options.pop('description', ""), url=options.pop('url', ""), color=options.pop('color', random.randint(0, 16777216)))
        fields = options.pop('fields', [])
        inline = options.pop('inline', False)
        for f in fields:
            embed.add_field(name=f.get('name'), value=f.get('value'), inline=f.pop('inline', inline))
        A = options.pop('thumbnail', None)
        if A is not None: embed.set_thumbnail(url=A)
        A = options.pop('footer', None)
        B = options.pop('footer_url', None)
        if A is not None and B is not None: embed.set_footer(text=A, icon_url=B)
        elif A is not None: embed.set_footer(text=A)
        elif B is not None: embed.set_footer(icon_url=B)
        A = options.pop('image', None)
        if A is not None: embed.set_image(url=A)
        A = options.pop('timestamp', None)
        if A is not None: embed.timestamp=A
        if 'author' in options:
            embed.set_author(name=options['author'].pop('name', ""), url=options['author'].pop('url', ""), icon_url=options['author'].pop('icon_url', ""))
        return embed

    """pexc()
    Convert an exception to a string with the full traceback
    
    Parameters
    ----------
    exception: The error
    
    Returns
    --------
    unknown: The string, else the exception parameter if an error occured
    """
    def pexc(self, exception): # format an exception
        try:
            return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        except:
            return exception

    """formatName()
    Shorten player or crew names if they use long characters.
    For now, it only checks for the arabic character range.
    
    Parameters
    ----------
    name: The player name to shorten
    
    Returns
    --------
    name: The resulting name
    """
    def shortenName(self, name):
        count = 0
        for c in name:
            i = ord(c)
            if i >= 0xFB50 and i <= 0xFDFF:
                count += 1
        if count > 1: return name[0] + "..."
        else: return name

    """str2gbfid()
    Convert a string to a GBF profile ID.
    
    Parameters
    ----------
    inter: The command interaction
    target: String, which can be:
        - Empty (the author GBF ID will be used if set, doesn't work if you set inter to a channel)
        - Positive integer, representing a GBF ID
        - A Discord Mention (<@discord_id> or <@!discord_id>)
    
    Returns
    --------
    int or str: The GBF ID or an error string if an error happened
    """
    async def str2gbfid(self, inter, target, color):
        if target == "":
            if str(inter.author.id) not in self.bot.data.save['gbfids']:
                return "{} didn't set its profile ID\nUse `findplayer` to search the GW Database"
            id = self.bot.data.save['gbfids'][str(inter.author.id)]
        elif target.startswith('<@') and target.endswith('>'):
            try:
                if target[2] == "!": target = int(target[3:-1])
                else: target = int(target[2:-1])
                if target not in self.bot.data.save['gbfids']:
                    return "This member didn't set its profile ID\nUse `findplayer` to search the GW Database"
                id = self.bot.data.save['gbfids'][str(member.id)]
            except:
                return "Invalid parameter {} -> {}".format(target, type(target))
        else:
            try: id = int(target)
            except: return "`{}` isn't a valid target".format(target)
        if id < 0 or id >= 100000000:
            try: id = self.bot.data.save['gbfids'][str(id)]
            except: return "Invalid ID range"
        if id < 0 or id >= 100000000:
            return "Invalid ID range"
        return id

    """formatElement()
    Format the unite&fight/dread barrage element into a string containing the superior and inferior elements
    
    Parameters
    ----------
    elem: unite&fight/dread barrage element string
    
    Returns
    --------
    str: Formatted string
    """
    def formatElement(self, elem):
        return "{}⚔️{}".format(self.bot.emote.get(elem), self.bot.emote.get({'fire':'wind', 'water':'fire', 'earth':'water', 'wind':'earth', 'light':'dark', 'dark':'light'}.get(elem)))

    """strToInt()
    Convert string to int, with support for B, M and K
    
    Parameters
    ----------
    s: String to convert
    
    Returns
    --------
    int: Converted value
    """
    def strToInt(self, s):
        try:
            return int(s)
        except:
            n = float(s[:-1]) # float to support for example 1.2B
            m = s[-1].lower()
            l = {'k':1000, 'm':1000000, 'b':1000000000}
            return int(n * l[m])

    """valToStr()
    Convert an int or float to str and shorten it with B, M, K
    One decimal precision
    If None is sent in parameter, it returns "n/a"
    
    Parameters
    ----------
    v: Value to convert
    
    Returns
    --------
    int: Converted string
    """
    def valToStr(self, s):
        if s is None: return "n/a"
        if isinstance(s, int): s = float(s)
        bs = abs(s)
        if bs >= 1000000000:
            return "{:,.1f}B".format(s/1000000000).replace('.0', '')
        elif bs >= 1000000:
            return "{:,.1f}M".format(s/1000000).replace('.0', '')
        elif bs >= 1000:
            return "{:,.1f}K".format(s/1000).replace('.0', '')
        else:
            return "{:,.1f}".format(s).replace('.0', '')

    """valToStrBig()
    Convert an int or float to str and shorten it with B, M, K
    Two to three decimal precision
    If None is sent in parameter, it returns "n/a"
    
    Parameters
    ----------
    v: Value to convert
    
    Returns
    --------
    int: Converted string
    """
    def valToStrBig(self, s):
        if s is None: return "n/a"
        if isinstance(s, int): s = float(s)
        bs = abs(s)
        if bs >= 1000000000:
            if bs < 10000000000: return "{:,.3f}B".format(s/1000000000).replace('.000', '')
            else: return "{:,.2f}B".format(s/1000000000).replace('.00', '')
        elif bs >= 1000000:
            if bs < 10000000: return "{:,.3f}M".format(s/1000000).replace('.000', '')
            else: return "{:,.2f}M".format(s/1000000).replace('.00', '')
        elif bs >= 1000:
            if bs < 10000: return "{:,.3f}K".format(s/1000).replace('.000', '')
            else: return "{:,.2f}K".format(s/1000).replace('.00', '')
        else:
            return "{:,.1f}".format(s).replace('.0', '')

    """players2mentions()
    Take a list of users and return a string mentionning all of them.
    Used for Games.
    
    Parameters
    ----------
    players: list of disnake.User/Member
    
    Returns
    --------
    str: resulting string
    """
    def players2mentions(self, players : list):
        s = ""
        for p in players:
            s += p.mention + " "
        if len(s) > 0: s = s[:-1]
        return s

    """wiki_fixCase()
    Fix the case of individual element for gbf.wiki search terms
    
    Parameters
    ----------
    term: Word or String to fix
    
    Returns
    --------
    str: Fixed word
    """
    def wiki_fixCase(self, term):
        if ' ' in term: # in case we sent a whole string (this function only process word by word, originally)
            result = []
            for t in term.split(' '):
                result.append(self.wiki_fixCase(t))
            return "_".join(result)
        else:
            fixed = ""
            up = False
            match term.lower():
                case "and": # if it's just 'and', we don't don't fix anything and return a lowercase 'and'
                    return "and"
                case "of":
                    return "of"
                case "de":
                    return "de"
                case "the":
                    return "the"
                case "(sr)":
                    return "(SR)"
                case "(ssr)":
                    return "(SSR)"
                case "(r)":
                    return "(R)"
            for c in term: # for each character
                if c.isalpha(): # if letter
                    if c.isupper(): # is uppercase
                        if not up: # we haven't encountered an uppercase letter
                            up = True
                            fixed += c # save
                        else: # we have
                            fixed += c.lower() # make it lowercase and save
                    elif c.islower(): # is lowercase
                        if not up: # we haven't encountered an uppercase letter
                            fixed += c.upper() # make it uppercase and save
                            up = True
                        else: # we have
                            fixed += c # save
                    else: # other characters
                        fixed += c # we just save
                elif c == "/" or c == ":" or c == "#" or c == "-": # we reset the uppercase detection if we encounter those
                    up = False
                    fixed += c
                else: # everything else,
                    fixed += c # we save
            return fixed # return the result

    """search_wiki_for_id()
    Search the wiki for a weapon/summon id
    
    Parameters
    ----------
    sps: Target name
    
    Returns
    --------
    str: Target ID, None if error/not found
    """
    def search_wiki_for_id(self, sps: str):
        try:
            if "(summon)" not in sps.lower(): # search summon names first
                data = self.search_wiki_for_id(sps + ' (Summon)')
                if data is not None: return data
            data = self.bot.gbf.request("https://gbf.wiki/" + self.wiki_fixCase(sps), no_base_headers=True).decode('utf-8')
            group = self.search_re[1].findall(data)
            if len(group) > 0: return group[0]
            group = self.search_re[0].findall(data)
            return group[0]
        except:
            return None

    """progressBar()
    Coroutine to display a progress bar message
    
    Parameters
    ----------
    inter: Command interaction
    percent: percentage value (between 0 and 1)
    edit: True to edit the original message, False to send one
    ephemeral: type of message, only when edit is False
    """
    async def progressBar(self, inter, percent: float, edit, ephemeral=False):
        if percent < 0: percent = 0
        elif percent > 1: percent = 1
        percent = int(100 * percent)
        msg = ""
        for i in range(0, 110, 10):
            if i - percent <= -10: msg += ":green_square:"
            elif i - percent <= -5: msg += ":yellow_square:"
            elif i - percent < 0: msg += ":blue_square:"
            else: msg += ":black_large_square:"
        if edit: await inter.edit_original_message(embed=self.embed(description="**{}%** {}".format(percent, msg), footer="patience", color=0xffffff))
        else: await inter.response.send_message(embed=self.embed(description="**{}%** {}".format(percent, msg), footer="patience", color=0xffffff), ephemeral=True)
            