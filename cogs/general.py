import discord
from discord.ext import commands
import asyncio
import aiohttp
import random
from datetime import datetime, timedelta
import math
import json
import re
from xml.sax import saxutils as su
from collections import defaultdict

# #####################################################################################
# math parser used by $calc
class MathParser:
    def __init__(self):
        self.expression = ""
        self.index = 0
        self.vars = {}
        self.funcs = ['cos', 'sin', 'tan', 'acos', 'asin', 'atan', 'cosh', 'sinh', 'tanh', 'acosh', 'asinh', 'atanh', 'exp', 'ceil', 'abs', 'factorial', 'floor', 'round', 'trunc', 'log', 'log2', 'log10', 'sqrt', 'rad', 'deg']

    def evaluate(self, expression = "", vars={}):
        self.expression = expression.replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '')
        self.index = 0
        self.vars = {
            'pi' : math.pi,
            'e' : math.e
        }
        self.vars = {**self.vars, **vars}
        for func in self.funcs:
            if func in self.vars: raise Exception("Variable name '{}' can't be used".format(func))
        value = float(self.parse())
        if self.isNotDone(): raise Exception("Unexpected character '{}' found at index {}".format(self.peek(), self.index))
        epsilon = 0.0000000001
        if int(value) == value: return int(value)
        elif int(value + epsilon) != int(value):
            return int(value + epsilon)
        elif int(value - epsilon) != int(value):
            return int(value)
        return value

    def isNotDone(self):
        return self.index < len(self.expression)

    def peek(self):
        return self.expression[self.index:self.index + 1]

    def parse(self):
        values = [self.multiply()]
        while True:
            c = self.peek()
            if c in ['+', '-']:
                self.index += 1
                if c == '-': values.append(- self.multiply())
                else: values.append(self.multiply())
            else:
                break
        return sum(values)

    def multiply(self):
        values = [self.parenthesis()]
        while True:
            c = self.peek()
            if c in ['*', 'x']:
                self.index += 1
                values.append(self.parenthesis())
            elif c in ['/', '%']:
                div_index = self.index
                self.index += 1
                denominator = self.parenthesis()
                if denominator == 0:
                    raise Exception("Division by 0 occured at index {}".format(div_index))
                if c == '/': values.append(1.0 / denominator)
                else: values.append(1.0 % denominator)
            elif c == '^':
                self.index += 1
                exponent = self.parenthesis()
                values[-1] = values[-1] ** exponent
            elif c == '!':
                self.index += 1
                values[-1] = math.factorial(values[-1])
            else:
                break
        value = 1.0
        for factor in values: value *= factor
        return value

    def parenthesis(self):
        if self.peek() == '(':
            self.index += 1
            value = self.parse()
            if self.peek() != ')': raise Exception("No closing parenthesis found at character {}".format(self.index))
            self.index += 1
            return value
        else:
            return self.negative()

    def negative(self):
        if self.peek() == '-':
            self.index += 1
            return -1 * self.parenthesis()
        else:
            return self.value()
    
    def value(self):
        if self.peek() in '0123456789.':
            return self.number()
        else:
            return self.variable_or_function()

    def variable_or_function(self):
        var = ''
        while self.isNotDone():
            c = self.peek()
            if c.lower() in '_abcdefghijklmnopqrstuvwxyz0123456789':
                var += c
                self.index += 1
            else:
                break
        
        value = self.vars.get(var, None)
        if value == None:
            if var not in self.funcs: raise Exception("Unrecognized variable '{}'".format(var))
            else:
                param = self.parenthesis()
                if var == 'cos': value = math.cos(param)
                elif var == 'sin': value = math.sin(param)
                elif var == 'tan': value = math.tan(param)
                elif var == 'acos': value = math.acos(param)
                elif var == 'asin': value = math.asin(param)
                elif var == 'atan': value = math.atan(param)
                elif var == 'cosh': value = math.cosh(param)
                elif var == 'sinh': value = math.sinh(param)
                elif var == 'tanh': value = math.tanh(param)
                elif var == 'acosh': value = math.acosh(param)
                elif var == 'asinh': value = math.asinh(param)
                elif var == 'atanh': value = math.atanh(param)
                elif var == 'exp': value = math.exp(param)
                elif var == 'ceil': value = math.ceil(param)
                elif var == 'floor': value = math.floor(param)
                elif var == 'round': value = math.floor(param)
                elif var == 'factorial': value = math.factorial(param)
                elif var == 'abs': value = math.fabs(param)
                elif var == 'trunc': value = math.trunc(param)
                elif var == 'log':
                    if param <= 0: raise Exception("Can't evaluate the logarithm of '{}'".format(param))
                    value = math.log(param)
                elif var == 'log2':
                    if param <= 0: raise Exception("Can't evaluate the logarithm of '{}'".format(param))
                    value = math.log2(param)
                elif var == 'log10':
                    if param <= 0: raise Exception("Can't evaluate the logarithm of '{}'".format(param))
                    value = math.log10(param)
                elif var == 'sqrt': value = math.sqrt(param)
                elif var == 'rad': value = math.radians(param)
                elif var == 'deg': value = math.degrees(param)
                else: raise Exception("Unrecognized function '{}'".format(var))
        return float(value)

    def number(self):
        strValue = ''
        decimal_found = False
        c = ''
        
        while self.isNotDone():
            c = self.peek()
            if c == '.':
                if decimal_found:
                    raise Exception("Found an extra period in a number at character {}".format(self.index))
                decimal_found = True
                strValue += '.'
            elif c in '0123456789':
                strValue += c
            else:
                break
            self.index += 1
        
        if len(strValue) == 0:
            if c == '': raise Exception("Unexpected end found")
            else: raise Exception("A number was expected at character {} but instead '{}' was found".format(self.index, char))
        return float(strValue)

# #####################################################################################
# Cogs
class General(commands.Cog):
    """General commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x8fe3e8
        self.pokergames = {}

    def startTasks(self):
        self.bot.runTask('reminder', self.remindertask)

    async def remindertask(self):
        while True:
            if self.bot.exit_flag: return
            try:
                c = self.bot.getJST() + timedelta(seconds=30)
                for r in list(self.bot.reminders.keys()):
                    di = 0
                    u = self.bot.get_user(int(r))
                    if u is None: continue
                    while di < len(self.bot.reminders[r]):
                        if c > self.bot.reminders[r][di][0]:
                            try:
                                await u.send(embed=self.bot.buildEmbed(title="Reminder", description=self.bot.reminders[r][di][1]))
                            except Exception as e:
                                await self.bot.sendError('remindertask', "User: {}\nReminder: {}\nError: {}".format(u.name, self.bot.reminders[r][di][1], e))
                            self.bot.reminders[r].pop(di)
                            self.bot.savePending = True
                        else:
                            di += 1
                    if len(self.bot.reminders[r]) == 0:
                        self.bot.reminders.pop(r)
                        self.bot.savePending = True
            except asyncio.CancelledError:
                await self.bot.sendError('remindertask', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('remindertask', str(e))
                await asyncio.sleep(200)
            await asyncio.sleep(40)

    def isDisabled(): # for decorators
        async def predicate(ctx):
            return False
        return commands.check(predicate)

    def cleanhtml(self, raw):
      cleaner = re.compile('<.*?>')
      return su.unescape(re.sub(cleaner, '', raw.replace('<br>', ' '))).replace('>', '')

    # get a 4chan thread
    async def get4chan(self, board : str, search : str): # be sure to not abuse it, you are not supposed to call the api more than once per second
        try:
            search = search.lower()
            url = 'http://a.4cdn.org/{}/catalog.json'.format(board) # board catalog url
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status == 200:
                        data = await r.json()
            threads = []
            for p in data:
                for t in p["threads"]:
                    try:
                        if t.get("sub", "").lower().find(search) != -1 or t.get("com", "").lower().find(search) != -1:
                            threads.append([t["no"], t["replies"], su.unescape(self.cleanhtml(t.get("com", "")))]) # store the thread ids matching our search word
                    except:
                        pass
            threads.sort(reverse=True)
            return threads
        except:
            return []

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['chose'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def choose(self, ctx, *, choices : str):
        """Select a random string from the user's choices
        Example: $choose I'm Alice ; Bob"""
        try:
            possible = choices.split(";")
            if len(possible) < 2: raise Exception()
            final_msg = await ctx.send(embed=self.bot.buildEmbed(author={'name':"{}'s choice".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=random.choice(possible), color=self.color))
        except:
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Give me a list of something to choose from, separated by `;`", color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 30)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['math'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def calc(self, ctx, *terms : str):
        """Process a mathematical expression
        You can define a variable by separating using a comma.
        Some functions are also available.
        Example: cos(a + b) / c, a = 1, b=2,c = 3"""
        try:
            m = " ".join(terms).split(",")
            d = {}
            for i in range(1, len(m)): # process the variables if any
                x = m[i].replace(" ", "").split("=")
                if len(x) == 2: d[x[0]] = float(x[1])
                else: raise Exception('')
            msg = "`{}` = **{}**".format(m[0], MathParser().evaluate(m[0], d))
            if len(d) > 0:
                msg += "\nwith:\n"
                for k in d:
                    msg += "{} = {}\n".format(k, d[k])
            await ctx.send(embed=self.bot.buildEmbed(title="Calculator", description=msg, color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description=str(e), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def jst(self, ctx):
        """Post the current time, JST timezone"""
        await ctx.send(embed=self.bot.buildEmbed(title="{} {:%Y/%m/%d %H:%M} JST".format(self.bot.getEmote('clock'), self.bot.getJST()), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['inrole', 'rolestat'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def roleStats(self, ctx, *name : str):
        """Search how many users have a matching role
        use quotes if your match contain spaces
        add 'exact' at the end to force an exact match"""
        g = ctx.author.guild
        i = 0
        if len(name) > 0 and name[-1] == "exact":
            exact = True
            name = name[:-1]
        else:
            exact = False
        name = ' '.join(name)
        for member in g.members:
            for r in member.roles:
                if r.name == name or (exact == False and r.name.lower().find(name.lower()) != -1):
                    i += 1
        if exact != "exact":
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Roles containing: {}".format(name), description="{} user(s)".format(i), thumbnail=g.icon_url, footer="on server {}".format(g.name), color=self.color))
        else:
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Roles matching: {}".format(name), description="{} user(s)".format(i), thumbnail=g.icon_url, footer="on server {}".format(g.name), color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 20)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['hgg2d'])
    @commands.cooldown(1, 10, commands.BucketType.default)
    async def hgg(self, ctx):
        """Post the latest /hgg2d/ threads"""
        if not ctx.channel.is_nsfw():
            await ctx.send(embed=self.bot.buildEmbed(title=':underage: NSFW channels only'))
            return
        threads = await self.get4chan('vg', '/hgg2d/')
        if len(threads) > 0:
            msg = ""
            for t in threads:
                if len(t[2]) > 23:
                    msg += '🔞 [{}](https://boards.4channel.org/vg/thread/{}) ▫️ *{} replies* ▫️ {}...\n'.format(t[0], t[0], t[1], t[2][:23])
                else:
                    msg += '🔞 [{}](https://boards.4channel.org/vg/thread/{}) ▫️ *{} replies* ▫️ {}\n'.format(t[0], t[0], t[1], t[2])
                if len(msg) > 1800:
                    msg += 'and more...'
                    break
            await ctx.send(embed=self.bot.buildEmbed(title="/hgg2d/ latest thread(s)", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="/hgg2d/ Error", description="I couldn't find a single /hgg2d/ thread 😔", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['thread'])
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def gbfg(self, ctx):
        """Post the latest /gbfg/ threads"""
        threads = await self.get4chan('vg', '/gbfg/')
        if len(threads) > 0:
            msg = ""
            for t in threads:
                if len(t[2]) > 23:
                    msg += ':poop: [{}](https://boards.4channel.org/vg/thread/{}) ▫️ *{} replies* ▫️ {}...\n'.format(t[0], t[0], t[1], t[2][:23])
                else:
                    msg += ':poop: [{}](https://boards.4channel.org/vg/thread/{}) ▫️ *{} replies* ▫️ {}\n'.format(t[0], t[0], t[1], t[2])
                if len(msg) > 1800:
                    msg += 'and more...'
                    break
            await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ latest thread(s)", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ Error", description="I couldn't find a single /gbfg/ thread 😔", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, name='4chan')
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def _4chan(self, ctx, board : str, *, term : str):
        """Search 4chan threads"""
        nsfw = ['b', 'r9k', 'pol', 'bant', 'soc', 's4s', 's', 'hc', 'hm', 'h', 'e', 'u', 'd', 'y', 't', 'hr', 'gif', 'aco', 'r']
        board = board.lower()
        if board in nsfw and not ctx.channel.is_nsfw():
            await ctx.send(embed=self.bot.buildEmbed(title=":underage: The board `{}` is restricted to NSFW channels".format(board)))
            return
        threads = await self.get4chan(board, term)
        if len(threads) > 0:
            msg = ""
            for t in threads:
                if len(t[2]) > 23:
                    msg += ':four_leaf_clover: [{}](https://boards.4channel.org/{}/thread/{}) ▫️ *{} replies* ▫️ {}...\n'.format(t[0], board, t[0], t[1], t[2][:23])
                else:
                    msg += ':four_leaf_clover: [{}](https://boards.4channel.org/{}/thread/{}) ▫️ *{} replies* ▫️ {}\n'.format(t[0], board, t[0], t[1], t[2])
                if len(msg) > 1800:
                    msg += 'and more...'
                    break
            await ctx.send(embed=self.bot.buildEmbed(title="4chan Search result", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="4chan Search result", description="No matching threads found", color=self.color))


    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['reminder'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def remind(self, ctx, duration : str, *, msg : str):
        """Remind you of something at the specified time (±30 seconds precision)
        <duration> format: XdXhXmXs for day, hour, minute, second, each are optionals"""
        id = str(ctx.author.id)
        if id not in self.bot.reminders:
            self.bot.reminders[id] = []
        if len(self.bot.reminders[id]) >= 5 and ctx.author.id != self.bot.ids.get('owner', -1):
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Sorry, I'm limited to 5 reminders per user 🙇", color=self.color))
            return
        try:
            d = self.bot.makeTimedelta(duration)
            if d is None: raise Exception()
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Invalid duration string `{}`, format is `NdNhNm`".format(duration), color=self.color))
            return
        if msg == "":
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Tell me what I'm supposed to remind you 🤔", color=self.color))
            return
        if len(msg) > 200:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Reminders are limited to 200 characters", color=self.color))
            return
        try:
            self.bot.reminders[id].append([datetime.utcnow().replace(microsecond=0) + timedelta(seconds=32400) + d, msg]) # keep JST
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", footer="I have no clues about what went wrong", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['rl', 'reminderlist'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def remindlist(self, ctx):
        """Post your current list of reminders"""
        id = str(ctx.author.id)
        if id not in self.bot.reminders or len(self.bot.reminders[id]) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="You don't have any reminders", color=self.color))
        else:
            embed = discord.Embed(title="{}'s Reminder List".format(ctx.author.display_name), color=random.randint(0, 16777216)) # random color
            embed.set_thumbnail(url=ctx.author.avatar_url)
            for i in range(0, len(self.bot.reminders[id])):
                embed.add_field(name="#{} ▫️ {:%Y/%m/%d %H:%M} JST".format(i, self.bot.reminders[id][i][0]), value=self.bot.reminders[id][i][1], inline=False)
            await ctx.send(embed=embed)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['rd', 'reminderdel'])
    @commands.cooldown(2, 3, commands.BucketType.user)
    async def reminddel(self, ctx, rid : int):
        """Delete one of your reminders"""
        id = str(ctx.author.id)
        if id not in self.bot.reminders or len(self.bot.reminders[id]) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="You don't have any reminders", color=self.color))
        else:
            if rid < 0 or rid >= len(self.bot.reminders[id]):
                await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Invalid id `{}`".format(rid), color=self.color))
            else:
                self.bot.reminders[id].pop(rid)
                if len(self.bot.reminders[id]) == 0:
                    self.bot.reminders.pop(id)
                self.bot.savePending = True
                await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def iam(self, ctx, *, role_name : str):
        """Add a role to you that you choose. Role must be on a list of self-assignable roles."""
        g = str(ctx.guild.id)
        roles = self.bot.assignablerole.get(g, {})
        if role_name.lower() not in roles:
            await self.bot.react(ctx.message, '❎') # negative check mark
        else:
            id = roles[role_name.lower()]
            r = ctx.guild.get_role(id)
            if r is None: # role doesn't exist anymore
                await self.bot.react(ctx.message, '❎') # negative check mark
                self.bot.assignablerole[g].pop(role_name.lower())
                if len(self.bot.assignablerole[g]) == 0:
                    self.bot.assignablerole.pop(g)
                self.bot.savePending = True
            else:
                try:
                    await ctx.author.add_roles(r)
                except:
                    pass
                await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['iamn'])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def iamnot(self, ctx, *, role_name : str):
        """Remove a role to you that you choose. Role must be on a list of self-assignable roles."""
        g = str(ctx.guild.id)
        roles = self.bot.assignablerole.get(g, {})
        if role_name.lower() not in roles:
            await self.bot.react(ctx.message, '❎') # negative check mark
        else:
            id = roles[role_name.lower()]
            r = ctx.guild.get_role(id)
            if r is None: # role doesn't exist anymore
                await self.bot.react(ctx.message, '❎') # negative check mark
                self.bot.assignablerole[g].pop(role_name.lower())
                if len(self.bot.assignablerole[g]) == 0:
                    self.bot.assignablerole.pop(g)
                self.bot.savePending = True
            else:
                try:
                    await ctx.author.remove_roles(r)
                except:
                    pass
                await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def lsar(self, ctx, page : int = 1):
        """List the self-assignable roles available in this server"""
        g = str(ctx.guild.id)
        if page < 1: page = 1
        roles = self.bot.assignablerole.get(str(ctx.guild.id), {})
        if len(roles) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="No self assignable roles available on this server", color=self.color))
            return
        if (page -1) >= len(roles) // 20:
            page = ((len(roles) - 1) // 20) + 1
        fields = []
        count = 0
        for k in list(roles.keys()):
            if count < (page - 1) * 20:
                count += 1
                continue
            if count >= page * 20:
                break
            if count % 10 == 0:
                fields.append({'name':'{} '.format(self.bot.getEmote(str(len(fields)+1))), 'value':'', 'inline':True})
            r = ctx.guild.get_role(roles[k])
            if r is not None:
                fields[-1]['value'] += '{}\n'.format(k)
            else:
                self.bot.assignablerole[str(ctx.guild.id)].pop(k)
                self.bot.savePending = True
            count += 1

        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Self Assignable Roles", fields=fields, footer="Page {}/{}".format(page, 1+len(roles)//20), color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 30)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['nitro', 'here'])
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def serverinfo(self, ctx):
        """Get informations on the current guild (Owner only)"""
        guild = ctx.guild
        await ctx.send(embed=self.bot.buildEmbed(title=guild.name + " status", description="**ID** ▫️ {}\n**Owner** ▫️ {}\n**Region** ▫️ {}\n**Text Channels** ▫️ {}\n**Voice Channels** ▫️ {}\n**Members** ▫️ {}\n**Roles** ▫️ {}\n**Emojis** ▫️ {}\n**Boosted** ▫️ {}\n**Boost Tier** ▫️ {}".format(guild.id, guild.owner, guild.region, len(guild.text_channels), len(guild.voice_channels), len(guild.members), len(guild.roles), len(guild.emojis), guild.premium_subscription_count, guild.premium_tier), thumbnail=guild.icon_url, timestamp=guild.created_at, color=self.color))

    def checkPokerHand(self, hand):
        flush = False
        # flush detection
        suits = [h[-1] for h in hand]
        if len(set(suits)) == 1: flush = True
        # other checks
        values = [i[:-1] for i in hand] # get card values
        value_counts = defaultdict(lambda:0)
        for v in values:
            value_counts[v] += 1 # count each match
        rank_values = [int(i) for i in values] # rank them
        value_range = max(rank_values) - min(rank_values) # and get the difference
        # determinate hand from their
        if flush and set(values) == set(["10", "11", "12", "13", "14"]): return "**Royal Straight Flush**"
        elif flush and ((len(set(value_counts.values())) == 1 and (value_range==4)) or set(values) == set(["14", "2", "3", "4", "5"])): return "**Straight Flush, high {}**".format(self.highestCardStripped(list(value_counts.keys())).replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif sorted(value_counts.values()) == [1,4]: return "**Four of a Kind of {}**".format(list(value_counts.keys())[list(value_counts.values()).index(4)].replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif sorted(value_counts.values()) == [2,3]: return "**Full House, high {}**".format(list(value_counts.keys())[list(value_counts.values()).index(3)].replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif flush: return "**Flush**"
        elif (len(set(value_counts.values())) == 1 and (value_range==4)) or set(values) == set(["14", "2", "3", "4", "5"]): return "**Straight, high {}**".format(self.highestCardStripped(list(value_counts.keys())).replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif set(value_counts.values()) == set([3,1]): return "**Three of a Kind of {}**".format(list(value_counts.keys())[list(value_counts.values()).index(3)].replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif sorted(value_counts.values())==[1,2,2]:
            k = list(value_counts.keys())
            k.pop(list(value_counts.values()).index(1))
            return "**Two Pairs, high {}**".format(self.highestCardStripped(k).replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        elif 2 in value_counts.values(): return "**Pair of {}**".format(list(value_counts.keys())[list(value_counts.values()).index(2)].replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
        else: return "**Highest card is {}**".format(self.highestCard(hand).replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))

    def highestCardStripped(self, selection):
        ic = [int(i) for i in selection]
        return str(sorted(ic)[-1])

    def highestCard(self, selection):
        for i in range(0, len(selection)): selection[i] = '0'+selection[i] if len(selection[i]) == 2 else selection[i]
        last = sorted(selection)[-1]
        if last[0] == '0': last = last[1:]
        return last

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(15, 30, commands.BucketType.guild)
    async def deal(self, ctx):
        """Deal a random poker hand"""
        hand = []
        while len(hand) < 5:
            card = str(random.randint(2, 14)) + random.choice(["D", "S", "H", "C"])
            if card not in hand:
                hand.append(card)
        final_msg = await ctx.send(embed=self.bot.buildEmbed(author={'name':"{}'s hand".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="🎴, 🎴, 🎴, 🎴, 🎴", color=self.color))
        for x in range(0, 5):
            await asyncio.sleep(1)
            # check result
            msg = ""
            for i in range(len(hand)):
                if i > x: msg += "🎴"
                else: msg += hand[i].replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")
                if i < 4: msg += ", "
                else: msg += "\n"
            if x == 4:
                await asyncio.sleep(2)
                msg += self.checkPokerHand(hand)
            await final_msg.edit(embed=self.bot.buildEmbed(author={'name':"{}'s hand".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 45)

    def pokerNameStrip(self, name):
        if len(name) > 10:
            if len(name.split(" ")[0]) < 10: return name.split(" ")[0]
            else: return name[:9] + "…"
        return name

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(10, 30, commands.BucketType.guild)
    async def poker(self, ctx):
        """Play a poker mini-game with other people"""
        # search game
        id = ctx.channel.id
        if id in self.pokergames:
            if self.pokergames[id]['state'] == 'waiting':
                if len(self.pokergames[id]['players']) >= 6:
                    await self.bot.cleanMessage(ctx, (await ctx.send(embed=self.bot.buildEmbed(title="Error", description="This game is full", color=self.color))), 6)
                elif ctx.author.id not in self.pokergames[id]['players']:
                    self.pokergames[id]['players'].append(ctx.author.id)
                    await self.bot.react(ctx.message, '✅') # white check mark
                else:
                    await self.bot.cleanMessage(ctx, (await ctx.send(embed=self.bot.buildEmbed(title="Error", description="You are already in the next game", color=self.color))), 10)
            else:
                await self.bot.cleanMessage(ctx, (await ctx.send(embed=self.bot.buildEmbed(title="Error", description="This game started", color=self.color))), 10)
        else:
            self.pokergames[id] = {'state':'waiting', 'players':[ctx.author.id]}
            msg = await ctx.send(embed=self.bot.buildEmbed(title="♠️ Multiplayer Poker ♥️", description="Starting in 30s\n1/6 players", footer="Use the poker command to join", color=self.color))
            cd = 29
            while cd >= 0:
                await asyncio.sleep(1)
                await msg.edit(embed=self.bot.buildEmbed(title="♠️ Multiplayer Poker ♥️", description="Starting in {}s\n{}/6 players".format(cd, len(self.pokergames[id]['players'])), footer="Use the poker command to join", color=self.color))
                cd -= 1
                if len(self.pokergames[id]['players']) >= 6:
                    break
            self.pokergames[id]['state'] = "playing"
            if len(self.pokergames[id]['players']) > 6: self.pokergames[id]['players'] = self.pokergames[id]['players'][:6]
            await self.bot.cleanMessage(ctx, msg, 0, True)
            # game start
            draws = []
            final_msg = None
            while len(draws) < 3 + 2 * len(self.pokergames[id]['players']):
                card = str(random.randint(2, 14)) + random.choice(["D", "S", "H", "C"])
                if card not in draws:
                    draws.append(card)
            for s in range(-1, 5):
                msg = ":spy: Dealer \▫️ "
                n = s - 2
                for j in range(0, 3):
                    if j > n: msg += "🎴"
                    else: msg += draws[j].replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")
                    if j < 2: msg += ", "
                    else: msg += "\n\n"
                n = max(1, s)
                for x in range(0, len(self.pokergames[id]['players'])):
                    pid = self.pokergames[id]['players'][x]
                    msg += "{} {} \▫️ ".format(self.bot.getEmote(str(x+1)), self.pokerNameStrip(ctx.guild.get_member(pid).display_name))
                    if s == 4:
                        highest = self.highestCard(draws[3+2*x:5+2*x])
                    for j in range(0, 2):
                        if j > s: msg += "🎴"
                        elif s == 4 and draws[3+j+2*x] == highest: msg += "__" + draws[3+j+2*x].replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A") + "__"
                        else: msg += draws[3+j+2*x].replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A")
                        if j == 0: msg += ", "
                        else:
                            if s == 4:
                                msg += " \▫️ "
                                hand = draws[0:3] + draws[3+2*x:5+2*x]
                                hstr = self.checkPokerHand(hand)
                                if hstr.startswith("**Highest"):
                                    msg += "**Highest card is {}**".format(self.highestCard(draws[3+2*x:5+2*x]).replace("D", "\♦️").replace("S", "\♠️").replace("H", "\♥️").replace("C", "\♣️").replace("11", "J").replace("12", "Q").replace("13", "K").replace("14", "A"))
                                else:
                                    msg += hstr
                            msg += "\n"
                if final_msg is None: final_msg = await ctx.send(embed=self.bot.buildEmbed(title="♠️ Multiplayer Poker ♥️", description=msg, color=self.color))
                else: await final_msg.edit(embed=self.bot.buildEmbed(title="♠️ Multiplayer Poker ♥️", description=msg, color=self.color))
                await asyncio.sleep(2)
            self.pokergames.pop(id)
            await self.bot.cleanMessage(ctx, final_msg, 45)