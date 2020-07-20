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
                        if t["sub"].lower().find(search) != -1 or t["com"].lower().find(search) != -1:
                            threads.append([t["no"], t["replies"], self.cleanhtml(t['com'])]) # store the thread ids matching our search word
                    except:
                        pass
            threads.sort(reverse=True)
            return threads
        except:
            return []

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def roll(self, ctx, dice : str = ""):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
            result = ", ".join(str(random.randint(1, limit)) for r in range(rolls))
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{}'s dice Roll(s)".format(ctx.message.author.display_name), description=result, color=self.color))
        except:
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Format has to be in NdN", footer="example: roll 2d6", color=self.color))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(20)
            await final_msg.delete()
            await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['choice'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def choose(self, ctx, *, choices : str ):
        """Chooses between multiple choices.
        Use quotes if one of your choices contains spaces.
        Example: $choose I'm Alice ; Bob"""
        try:
            possible = choices.split(";")
            if len(possible) < 2: raise Exception()
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{}, I choose".format(ctx.message.author.display_name), description=random.choice(possible), color=self.color))
        except:
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Give me a list of something to choose from 😔, separated by ';'", color=self.color))
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(20)
            await final_msg.delete()
            await ctx.message.add_reaction('✅') # white check mark

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
            msg = "{} = **{}**".format(m[0], MathParser().evaluate(m[0], d))
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

    @commands.command(no_pm=True, cooldown_after_parsing=True, alias=['inrole', 'rolestat'])
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
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(20)
            await final_msg.delete()
            await ctx.message.add_reaction('✅') # white check mark

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
            await ctx.message.add_reaction('✅') # white check mark
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
                await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def iam(self, ctx, *, role_name : str):
        """Add a role to you that you choose. Role must be on a list of self-assignable roles."""
        g = str(ctx.guild.id)
        roles = self.bot.assignablerole.get(g, {})
        if role_name.lower() not in roles:
            await ctx.message.add_reaction('❎') # negative check mark
        else:
            id = roles[role_name.lower()]
            r = ctx.guild.get_role(id)
            if r is None: # role doesn't exist anymore
                await ctx.message.add_reaction('❎') # negative check mark
                self.bot.assignablerole[g].pop(role_name.lower())
                if len(self.bot.assignablerole[g]) == 0:
                    self.bot.assignablerole.pop(g)
                self.bot.savePending = True
            else:
                try:
                    await ctx.author.add_roles(r)
                except:
                    pass
                await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['iamn'])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def iamnot(self, ctx, *, role_name : str):
        """Remove a role to you that you choose. Role must be on a list of self-assignable roles."""
        g = str(ctx.guild.id)
        roles = self.bot.assignablerole.get(g, {})
        if role_name.lower() not in roles:
            await ctx.message.add_reaction('❎') # negative check mark
        else:
            id = roles[role_name.lower()]
            r = ctx.guild.get_role(id)
            if r is None: # role doesn't exist anymore
                await ctx.message.add_reaction('❎') # negative check mark
                self.bot.assignablerole[g].pop(role_name.lower())
                if len(self.bot.assignablerole[g]) == 0:
                    self.bot.assignablerole.pop(g)
                self.bot.savePending = True
            else:
                try:
                    await ctx.author.remove_roles(r)
                except:
                    pass
                await ctx.message.add_reaction('✅') # white check mark

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
        if not self.bot.isAuthorized(ctx):
            await asyncio.sleep(30)
            await final_msg.delete()
            await ctx.message.add_reaction('✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['nitro', 'here'])
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def serverinfo(self, ctx):
        """Get informations on the current guild (Owner only)"""
        guild = ctx.guild
        await ctx.send(embed=self.bot.buildEmbed(title=guild.name + " status", description="**ID** ▫️ {}\n**Owner** ▫️ {}\n**Region** ▫️ {}\n**Text Channels** ▫️ {}\n**Voice Channels** ▫️ {}\n**Members** ▫️ {}\n**Roles** ▫️ {}\n**Emojis** ▫️ {}\n**Boosted** ▫️ {}\n**Boost Tier** ▫️ {}".format(guild.id, guild.owner, guild.region, len(guild.text_channels), len(guild.voice_channels), len(guild.members), len(guild.roles), len(guild.emojis), guild.premium_subscription_count, guild.premium_tier), thumbnail=guild.icon_url, timestamp=guild.created_at, color=self.color))