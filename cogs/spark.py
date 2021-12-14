import disnake
from disnake.ext import commands
from datetime import datetime, timedelta
import math
from operator import itemgetter
from views.url_button import UrlButton

# ----------------------------------------------------------------------------------------------------------------
# Spark Cog
# ----------------------------------------------------------------------------------------------------------------
# Register and estimate people GBF Spark status
# ----------------------------------------------------------------------------------------------------------------

class Sparking(commands.Cog):
    """Track your Granblue Spark."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xeba834

    @commands.slash_command(default_permission=True)
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def spark(self, inter):
        """Command Group"""
        pass

    """_seeroll()
    Display the user roll count
    
    Parameters
    --------
    inter: Command interaction
    member: A disnake.Member object
    ephemeral: Boolean to display or not the result to everyone
    """
    async def _seeroll(self, inter, member, ephemeral):
        if member is None: member = inter.author
        id = str(member.id)
        try:
            # get the roll count
            if id in self.bot.data.save['spark']:
                s = self.bot.data.save['spark'][id]
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

            t_min, t_max, expected, now = self._estimate(r, timestamp)
            # roll count text
            title = "{} has {} roll".format(member.display_name, fr)
            if fr != 1: title += "s"
            # sending
            if s is None:
                await inter.response.send_message(embed=self.bot.util.embed(author={'name':title, 'icon_url':member.display_avatar}, description="Update your rolls with the `/setroll` command", footer="Next spark between {} and {} from 0 rolls".format(t_min.strftime("%y/%m/%d"), t_max.strftime("%y/%m/%d")), color=self.color), ephemeral=ephemeral)
            else:
                await inter.response.send_message(embed=self.bot.util.embed(author={'name':title, 'icon_url':member.display_avatar}, description="**{} {} {} {} {} {}**\n*Expecting {} to {} rolls in {}*".format(self.bot.emote.get("crystal"), s[0], self.bot.emote.get("singledraw"), s[1], self.bot.emote.get("tendraw"), s[2], expected[0], expected[1], now.strftime("%B")), footer="Next spark between {} and {}".format(t_min.strftime("%y/%m/%d"), t_max.strftime("%y/%m/%d")), timestamp=timestamp, color=self.color), ephemeral=ephemeral)
            await self.bot.util.clean(inter, 30)
        except Exception as e:
            await self.bot.sendError('seeRoll', e)
            await inter.response.send_message(embed=self.bot.util.embed(title="Critical Error", description="I warned my owner", color=self.color, footer=str(e)), ephemeral=True)

    @spark.sub_command()
    async def set(self, inter, crystal : int = commands.Param(description="Your amount of Crystals", ge=0, le=900000, default=0), single : int = commands.Param(description="Your amount of Single Draw Tickets", ge=0, le=1000, default=0), ten : int = commands.Param(description="Your amount of Ten Draw Tickets", ge=0, le=100, default=0)):
        """Set your roll count"""
        id = str(inter.author.id)
        try:
            if crystal < 0 or single < 0 or ten < 0:
                raise Exception('Negative numbers')
            if crystal > 500000 or single > 1000 or ten > 100:
                raise Exception('Big numbers')
            with self.bot.data.lock:
                if crystal + single + ten == 0: 
                    if id in self.bot.data.save['spark']:
                        self.bot.data.save['spark'].pop(id)
                else:
                    self.bot.data.save['spark'][id] = [crystal, single, ten, datetime.utcnow()]
                self.bot.data.pending = True
            await self._seeroll(inter, inter.author, True)
        except:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Give me your number of crystals, single tickets and ten roll tickets, please", color=self.color), ephemeral=True)

    """_estimate()
    Calculate a spark estimation (using my personal stats)
    
    Parameters
    ----------
    r: Current number of rolls
    timestamp: start time, can be None
    
    Returns
    --------
    tuple: Containing:
        - t_min: Earliest time for a spark
        - t_max: Max time for a spark
        - expected: Expected number of rolls during the start month
        - now: start time (set to current time if timestamp is None)
    """
    def _estimate(self, r, timestamp):
        # from january to december
        month_min = [80, 80, 140, 90, 60, 80, 90, 200, 100, 80, 80, 160]
        month_max = [70, 70, 110, 80, 50, 60, 80, 150, 80, 60, 70, 120]
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
        return t_min, t_max, expected, now

    @spark.sub_command()
    async def see(self, inter, member : disnake.Member = None):
        """Post your (or the target) roll count"""
        await self._seeroll(inter, member, False)

    @spark.sub_command()
    async def zero(self, inter, day_difference: int = commands.Param(description="Add a number of days to today date", ge=0, default=0)):
        """Post a spark estimation based on today date"""
        try:
            t_min, t_max, expected, now = self._estimate(day_difference, None)
            # roll count text
            await inter.response.send_message(embed=self.bot.util.embed(title='{} Spark estimation from {} rolls at {}'.format(self.bot.emote.get("crystal"), day_difference, now.strftime("%y/%m/%d")), description="Next spark between {} and {}\n*Expecting {} to {} rolls in {}*".format(t_min.strftime("%y/%m/%d"), t_max.strftime("%y/%m/%d"), expected[0], expected[1], now.strftime("%B")), color=self.color), ephemeral=True)
        except Exception as e:
            await inter.response.send_message(embed=self.bot.util.embed(title="Critical Error", description="I warned my owner", color=self.color, footer=str(e)), ephemeral=True)
            await self.bot.sendError('zeroRoll', e)

    """_ranking()
    Retrieve the spark data of this server users and rank them
    
    Parameters
    ----------
    inter: Command interaction
    guild: Target guild
    
    Returns
    --------
    tuple: Containing:
        - msg: String containing the ranking
        - ar: Integer, Author ranking
        - top: Integer, Top limit
    """
    async def _ranking(self, inter, guild):
        ranking = {}
        for id in self.bot.data.save['spark']:
            if self.bot.ban.check(id, self.bot.ban.SPARK):
                continue
            m = await guild.get_or_fetch_member(int(id))
            if m is not None:
                s = self.bot.data.save['spark'][id]
                if s[0] < 0 or s[1] < 0 or s[2] < 0:
                    continue
                r = (s[0] / 300) + s[1] + s[2] * 10
                if r > 1800:
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
                msg += "**#{:<2}{} {}** with {} roll".format(i+1, emotes.pop(i, "▫️"), await guild.get_or_fetch_member(int(key)).display_name, fr)
                if fr != 1: msg += "s"
                msg += "\n"
            if key == str(inter.author.id):
                ar = i
                if i >= top: break
            i += 1
            if i >= 100:
                break
        return msg, ar, top

    @spark.sub_command()
    async def ranking(self, inter):
        """Show the ranking of everyone saving for a spark in the server"""
        try:
            await inter.response.defer()
            guild = inter.author.guild
            msg, ar, top = await self._ranking(inter, guild)
            if msg is None:
                await inter.edit_original_message(embed=self.bot.util.embed(title="The ranking of this server is empty"))
                return
            if ar >= top: footer = "You are ranked #{}".format(ar+1)
            elif ar == -1: footer = "You aren't ranked ▫️ You need at least one roll to be ranked"
            else: footer = ""
            await inter.edit_original_message(embed=self.bot.util.embed(title="{} Spark ranking of {}".format(self.bot.emote.get('crown'), guild.name), color=self.color, description=msg, footer=footer, thumbnail=guild.icon.url))
            await self.bot.util.clean(inter, 30)
        except Exception as e:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Sorry, something went wrong :bow:", footer=str(e)))
            await self.bot.sendError("rollRanking", e)