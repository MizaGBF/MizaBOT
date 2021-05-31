import discord
from discord.ext import commands
from datetime import datetime, timedelta
import math
from operator import itemgetter

# ----------------------------------------------------------------------------------------------------------------
# Spark Cog
# ----------------------------------------------------------------------------------------------------------------
# Register and estimate people GBF Spark status
# ----------------------------------------------------------------------------------------------------------------

class Spark(commands.Cog):
    """Track your Granblue Spark."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xeba834

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['setcrystal', 'setspark'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def setRoll(self, ctx, crystal : int, single : int = 0, ten : int = 0):
        """Set your roll count"""
        id = str(ctx.message.author.id)
        try:
            if crystal < 0 or single < 0 or ten < 0:
                raise Exception('Negative numbers')
            if crystal > 500000 or single > 1000 or ten > 100:
                raise Exception('Big numbers')
            with self.bot.data.lock:
                if crystal + single + ten == 0: 
                    if id in self.bot.data.save['spark'][0]:
                        self.bot.data.save['spark'][0].pop(id)
                else:
                    self.bot.data.save['spark'][0][id] = [crystal, single, ten, datetime.utcnow()]
                self.bot.data.pending = True
            try:
                await self.bot.callCommand(ctx, 'seeRoll')
            except Exception as e:
                final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':ctx.author.display_name, 'icon_url':ctx.author.avatar_url}, description="**{} {} {} {} {} {}**".format(self.bot.emote.get("crystal"), crystal, self.bot.emote.get("singledraw"), single, self.bot.emote.get("tendraw"), ten), color=self.color))
                await self.bot.sendError('setRoll', e, 'B')
        except:
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Error", description="Give me your number of crystals, single tickets and ten roll tickets, please", color=self.color, footer="setRoll <crystal> [single] [ten]"))
        try:
            await self.bot.util.clean(ctx, final_msg, 30)
        except:
            pass

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['seecrystal', 'seespark'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def seeRoll(self, ctx, member : discord.Member = None):
        """Post your roll count"""
        if member is None: member = ctx.author
        id = str(member.id)
        try:
            # get the roll count
            if id in self.bot.data.save['spark'][0]:
                s = self.bot.data.save['spark'][0][id]
                if s[0] < 0 or s[1] < 0 or s[2] < 0:
                    raise Exception('Negative numbers')
                r = (s[0] / 300) + s[1] + s[2] * 10
                fr = math.floor(r)
                if len(s) > 3: timestamp = s[3]
                else: timestamp = None
            else:
                r = 0
                fr = 0
                s = None
                timestamp = None

            # calculate estimation
            # note: those numbers are from my own experimentation
            month_min = [80, 80, 200, 80, 80, 80, 80, 250, 90, 80, 80, 160]
            month_max = [60, 60, 120, 60, 60, 60, 60, 140, 60, 60, 60, 110]
            month_day = [31.0, 28.25, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]

            # get current day
            if timestamp is None: now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else: now = timestamp.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            t_min = now
            t_max = now
            r_min = r % 300
            r_max = r_min
            expected = [month_max[now.month-1], month_min[now.month-1]]
            while r_min < 300 or r_max < 300: # increase the date until we reach the 300 target for both estimation
                if r_min < 300:
                    m = (t_min.month-1) % 12
                    r_min += month_min[m] / month_day[m]
                    t_min += timedelta(days=1)
                if r_max < 300:
                    m = (t_max.month-1) % 12
                    r_max += month_max[m] / month_day[m]
                    t_max += timedelta(days=1)

            # roll count text
            title = "{} has {} roll".format(member.display_name, fr)
            if fr != 1: title += "s"
            # sending
            if s is None:
                final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':title, 'icon_url':member.avatar_url}, description="Update your rolls with the `setRoll` command", footer="Next spark between {} and {} from 0 rolls".format(t_min.strftime("%y/%m/%d"), t_max.strftime("%y/%m/%d")), color=self.color))
            else:
                final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':title, 'icon_url':member.avatar_url}, description="**{} {} {} {} {} {}**\n*Expecting {} to {} rolls in {}*".format(self.bot.emote.get("crystal"), s[0], self.bot.emote.get("singledraw"), s[1], self.bot.emote.get("tendraw"), s[2], expected[0], expected[1], now.strftime("%B")), footer="Next spark between {} and {}".format(t_min.strftime("%y/%m/%d"), t_max.strftime("%y/%m/%d")), timestamp=timestamp, color=self.color))
        except Exception as e:
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Error", description="I warned my owner", color=self.color, footer=str(e)))
            await self.bot.sendError('seeRoll', e)
        await self.bot.util.clean(ctx, final_msg, 30)

    def _ranking(self, ctx, guild):
        ranking = {}
        for m in guild.members:
            id = str(m.id)
            if id in self.bot.data.save['spark'][0]:
                if id in self.bot.data.save['spark'][1]:
                    continue
                s = self.bot.data.save['spark'][0][id]
                if s[0] < 0 or s[1] < 0 or s[2] < 0:
                    continue
                r = (s[0] / 300) + s[1] + s[2] * 10
                if r > 1500:
                    continue
                ranking[id] = r
        if len(ranking) == 0:
            return None, None, None
        ar = -1
        i = 0
        emotes = {0:self.bot.emote.get('SSR'), 1:self.bot.emote.get('SR'), 2:self.bot.emote.get('R')}
        msg = ""
        top = 15
        for key, value in sorted(ranking.items(), key = itemgetter(1), reverse = True):
            if i < top:
                fr = math.floor(value)
                msg += "**#{:<2}{} {}** with {} roll".format(i+1, emotes.pop(i, "▫️"), guild.get_member(int(key)).display_name, fr)
                if fr != 1: msg += "s"
                msg += "\n"
            if key == str(ctx.message.author.id):
                ar = i
                if i >= top: break
            i += 1
            if i >= 100:
                break
        return msg, ar, top


    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["sparkranking", "hoarders"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def rollRanking(self, ctx):
        """Show the ranking of everyone saving for a spark in the server
        You must use $setRoll to set/update your roll count"""
        try:
            guild = ctx.message.author.guild
            msg, ar, top = await self.bot.do(self._ranking, ctx, guild)
            if msg is None:
                final_msg = await ctx.send(embed=self.bot.util.embed(title="The ranking of this server is empty"))
                return
            if ar >= top: footer = "You are ranked #{}".format(ar+1)
            elif ar == -1: footer = "You aren't ranked ▫️ You need at least one roll to be ranked"
            else: footer = ""
            final_msg = await ctx.send(embed=self.bot.util.embed(title="{} Spark ranking of {}".format(self.bot.emote.get('crown'), guild.name), color=self.color, description=msg, footer=footer, thumbnail=guild.icon_url))
        except Exception as e:
            final_msg = await ctx.send(embed=self.bot.util.embed(title="Sorry, something went wrong :bow:", footer=str(e)))
            await self.bot.sendError("rollRanking", e)
        await self.bot.util.clean(ctx, final_msg, 30)