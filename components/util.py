import disnake
import asyncio
import random
from datetime import datetime, timedelta
import psutil
import os
from shutil import copyfile
import traceback

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
        self.itemEmoteElement = None # to store emote strings used by formatItemElement()

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
                    await self.react(target[0].message, '✅') # white check mark
            elif isinstance(target, disnake.interactions.application_command.ApplicationCommandInteraction):
                if all or not self.bot.isAuthorized(target):
                    await asyncio.sleep(delay)
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
        - Empty (the author GBF ID will be used if set, doesn't work if you set ctx to a channel)
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

    """formatItemElement()
    Format the item string used by the gacha simulator to add an element emoji
    
    Parameters
    ----------
    raw: string to format
    mode: integer, 0 to not display the element, 1 to put an emote, anything else to do nothing
    
    Returns
    --------
    str: resulting string
    """
    def formatItemElement(self, raw : str, mode : int):
        if self.itemEmoteElement is None:
            self.itemEmoteElement = {
                "[1]" : "{}".format(self.bot.emote.get('fire')),
                "[2]" : "{}".format(self.bot.emote.get('water')),
                "[3]" : "{}".format(self.bot.emote.get('earth')),
                "[4]" : "{}".format(self.bot.emote.get('wind')),
                "[5]" : "{}".format(self.bot.emote.get('light')),
                "[6]" : "{}".format(self.bot.emote.get('dark'))
            }
        match mode:
            case 0: # remove element string
                return raw[3:]
            case 1: # replace element string by emote
                return raw.replace(raw[:3], self.itemEmoteElement[raw[:3]])
            case _: # undefined, do nothing
                return raw