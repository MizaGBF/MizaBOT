import discord
import asyncio
import random
from datetime import datetime, timedelta
import psutil
import os
from shutil import copyfile

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

    def init(self):
        self.emote = self.bot.emote
        
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

    def timestamp(self):
        return datetime.utcnow()

    def JST(self): # get the time in jst
        return datetime.utcnow() + timedelta(seconds=32400) - timedelta(seconds=30)
        
    def uptime(self, string=True): # get the uptime
        delta = datetime.utcnow() - self.starttime
        if string: return "{}".format(self.delta2str(delta, 3))
        else: return delta

    def delta2str(self, delta, mode=1):
        if mode == 3: return "{}d{}h{}m{}s".format(delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60, delta.seconds % 60)
        elif mode == 2: return "{}d{}h{}m".format(delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60)
        elif mode == 1: return "{}h{}m".format(delta.seconds // 3600, (delta.seconds // 60) % 60)
        elif mode == 0: return "{}m".format(delta.seconds // 60)

    def str2delta(self, d): # return None if error
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

    def get_cpu_percent(self):
        cpu = self.process.cpu_percent()
        for child in self.process.children(recursive=True):
            cpu += child.cpu_percent()
        return cpu

    def get_memory(self):
        mem = self.process.memory_info()[0]
        for child in self.process.children(recursive=True):
            mem += child.memory_info()()[0]
        return mem

    def status(self):
        return {
            "Version": self.bot.version,
            "Uptime": self.uptime(),
            "CPU": "{}%".format(self.get_cpu_percent()),
            "Memory": "{}MB".format(self.get_memory()>>20),
            "Save": ("**Pending**" if self.bot.data.pending else "Ok"),
            "Errors": ("**{}**".format(self.bot.errn) if self.bot.errn > 0 else str(self.bot.errn)),
            "Task Count": str(len(asyncio.all_tasks())),
            "Server Count": str(len(self.bot.guilds)),
            "Pending Servers": ("**{}**".format(len(self.bot.data.save['guilds']['pending'])) if len(self.bot.data.save['guilds']['pending']) > 0 else str(len(self.bot.data.save['guilds']['pending']))),
            "Cogs Loaded": "{}/{}".format(len(self.bot.cogs), self.bot.cogn) if (len(self.bot.cogs) == self.bot.cogn) else "**{}**/{}".format(len(self.bot.cogs), self.bot.cogn),
            "Twitter": ("Disabled" if (self.bot.twitter.api is None) else "Online")
        }

    def statusString(self):
        status = self.status()
        msg = ""
        for k in status:
            msg += "**{}**▫️{}\n".format(k, status[k])
        return msg

    def delFile(self, filename):
        try: os.remove(filename)
        except: pass

    def cpyFile(self, src, dst):
        try: copyfile(src, dst)
        except: pass

    async def react(self, msg, key): # add a reaction using a custom emote defined in config.json
        try:
            await msg.add_reaction(self.emote.get(key))
            return True
        except Exception as e:
            if str(e) != "404 Not Found (error code: 10008): Unknown Message":
                await self.bot.sendError('react', str(e))
            return False

    async def unreact(self, msg, key): # remove a reaction using a custom emote defined in config.json
        try:
            await msg.remove_reaction(self.emote.get(key), msg.guild.me)
            return True
        except Exception as e:
            if str(e) != "404 Not Found (error code: 10008): Unknown Message":
                await self.bot.sendError('unreact', str(e))
            return False

    async def clean(self, ctx, msg, timeout, all=False): # delete a message after X amount of time if posted in an unauthorized channel (all = False) or everywhere (all = True)
        try:
            if all or not self.bot.isAuthorized(ctx): # TODO
                if timeout is None or timeout > 0: await asyncio.sleep(timeout)
                await msg.delete()
                await self.react(ctx.message, '✅') # white check mark
        except:
            pass

    def embed(self, **options): # make a full embed
        embed = discord.Embed(title=options.get('title', ""), description=options.pop('description', ""), url=options.pop('url', ""), color=options.pop('color', random.randint(0, 16777216)))
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