import disnake
from disnake.ext import commands
import itertools
import json
import re
import html
import math
from views.poll import Poll

# ----------------------------------------------------------------------------------------------------------------
# General Cog
# ----------------------------------------------------------------------------------------------------------------
# Commands related to the current instance of MizaBOT
# ----------------------------------------------------------------------------------------------------------------

class General(commands.Cog):
    """MizaBot commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xd12e57

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 100, commands.BucketType.user)
    async def invite(self, inter: disnake.GuildCommandInteraction):
        """Get the MizaBOT invite link"""
        if 'invite' not in self.bot.data.save:
            await inter.response.send_message(embed=self.bot.util.embed(title="Invite Error", description="Invitation settings aren't set, hence the bot can't be invited.\nIf you are the server owner, check the `setInvite` command", timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)
        elif self.bot.data.save['invite']['state'] == False or len(self.bot.guilds) >= self.bot.data.save['invite']['limit']:
            await inter.response.send_message(embed=self.bot.util.embed(title="Invite Error", description="Invitations are currently closed.", timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title=inter.guild.me.name, description="{}\nCurrently only servers of 30 members or more can be added.\nMisuses of this link will result in a server-wide ban.".format(self.bot.data.config['strings']["invite()"]), thumbnail=inter.guild.me.display_avatar, timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def bug_report(self, inter: disnake.GuildCommandInteraction, report : str = commands.Param()):
        """Send a bug report (or your love confessions) to the developer"""
        await self.bot.send('debug', embed=self.bot.util.embed(title="Bug Report", description=report, footer="{} ▫️ User ID: {}".format(inter.author.name, inter.author.id), thumbnail=inter.author.display_avatar, color=self.color))
        await inter.response.send_message(embed=self.bot.util.embed(title="Information", description='Thank you, your report has been sent with success', color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def help(self, inter: disnake.GuildCommandInteraction, search : str = commands.Param(description="What do you need help for?", default="")):
        """Get the bot help"""
        await inter.response.defer(ephemeral=True)
        t = search.replace('  ', '').replace('  ', '').lower()
        try:
            with open('help.json') as json_file:
                data = json.load(json_file)
        except:
            data = {}
        # searching command match
        result = []
        stop_flag = False
        for k in data:
            if stop_flag: break
            for cmd in data[k]:
                if "command group" in cmd.get('comment', '').lower(): continue
                name = cmd['name']
                if 'parent' in cmd: name =  cmd['parent'] + " " + name
                name = name.lower()
                if t == name:
                    result = [cmd]
                    stop_flag = True
                    break
                elif t in name or t in cmd.get('comment', '').lower():
                    result.append(cmd)
        msg = ""
        if search == "":
            msg = "Online Help [here](https://mizagbf.github.io/MizaBOT/)\nGithub [here](https://github.com/MizaGBF/MizaBOT)".format(search)
        elif len(result) == 0:
            msg = "No results found for `{}`\n**For more help:**\nOnline Help [here](https://mizagbf.github.io/MizaBOT/)\nGithub [here](https://github.com/MizaGBF/MizaBOT)".format(search)
        elif len(result) == 1:
            match result[0]['type']:
                case 1:
                    msg = "**User Command**\n**"
                case 2:
                    msg = "**Message Command**\n**"
                case _:
                    msg = "**Slash Command\n/"
            if 'parent' in result[0]: msg += result[0]['parent'] + " "
            msg += result[0]['name'] + "**\n"
            if 'comment' in result[0]: msg += result[0]['comment'] + '\n'
            if result[0]['args'][0] > 0:
                msg += "**Parameters:**\n"
                msg += result[0]['args'][1]
        else:
            msg = "**Results**\n"
            count = len(result)
            for r in result:
                msg += "**"
                name = r['name']
                if 'parent' in r: name = r['parent'] + " " + name
                match r['type']:
                    case 1:
                        msg += name + "** *(User Command)*"
                    case 2:
                        msg += name + "** *(Message Command)*"
                    case _:
                        msg += "/" + name + "**"
                if result[0]['args'][0] > 0:
                    msg += "▫️ {} parameter".format(result[0]['args'][0])
                    if result[0]['args'][0] > 1: msg += "s"
                msg += "\n"
                count -= 1
                if len(msg) > 1500 and count > 0:
                    msg += "**And {} more commands...**\n**For more help:**\nOnline Help [here](https://mizagbf.github.io/MizaBOT/)\nGithub [here](https://github.com/MizaGBF/MizaBOT)".format(count)
                    break

        await inter.edit_original_message(embed=self.bot.util.embed(title=self.bot.user.name + " Help", description=msg, thumbnail=self.bot.user.display_avatar, color=self.color, url="https://mizagbf.github.io/MizaBOT/"))
        await self.bot.util.clean(inter, 60)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def mizabot(self, inter: disnake.GuildCommandInteraction):
        """Post the bot status"""
        await inter.response.send_message(embed=self.bot.util.embed(title="{} is Ready".format(self.bot.user.display_name), description=self.bot.util.statusString(), thumbnail=self.bot.user.display_avatar, timestamp=self.bot.util.timestamp(), color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def changelog(self, inter: disnake.GuildCommandInteraction):
        """Post the bot changelog"""
        msg = ""
        for c in self.bot.changelog:
            msg += "▫️ {}\n".format(c)
        if msg != "":
            await inter.response.send_message(embed=self.bot.util.embed(title="{} ▫️ v{}".format(inter.me.display_name, self.bot.version), description="**Changelog**\n" + msg, thumbnail=inter.me.display_avatar, color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="No Changelog available", color=self.color), ephemeral=True)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 100, commands.BucketType.guild)
    @commands.max_concurrency(5, commands.BucketType.default)
    async def poll(self, inter: disnake.GuildCommandInteraction, duration : int = commands.Param(description="In seconds", ge=60, le=500), poll_data : str = commands.Param(description="Format is: `title;choice1;choice2;...;choiceN`")):
        """Make a poll"""
        try:
            splitted = poll_data.split(';')
            if len(splitted) < 2: raise Exception('Specify at least a poll title and two choices\nFormat: `duration title;choice1;choice2;...;choiceN`')
            view = Poll(self.bot, inter.author, self.color, splitted[0], splitted[1:])
            await inter.response.send_message(embed=self.bot.util.embed(title="Information", description="Your poll is starting", color=self.color), ephemeral=True)
            msg_to_edit = await inter.channel.send(embed=self.bot.util.embed(author={'name':'{} started a poll'.format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, title=splitted[0], description="{} seconds remaining to vote".format(duration), color=self.color))
            msg_view = await inter.channel.send('\u200b', view=view)
            await view.run_poll(duration, msg_to_edit, inter.channel)
            await msg_view.delete()
        except Exception as e:
            try: await inter.response.send_message(embed=self.bot.util.embed(title="Poll error", description="{}".format(e), color=self.color), ephemeral=True)
            except: await inter.edit_original_message(embed=self.bot.util.embed(title="Poll error", description="{}".format(e), color=self.color))

    @commands.slash_command(default_permission=True)
    @commands.cooldown(3, 10, commands.BucketType.guild)
    async def utility(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    @utility.sub_command()
    async def calc(self, inter: disnake.GuildCommandInteraction, expression : str = commands.Param(description='Mathematical Expression')):
        """Process a mathematical expression. Support variables (Example: cos(a + b) / c, a = 1, b=2,c = 3)."""
        try:
            m = expression.split(",")
            d = {}
            for i in range(1, len(m)): # process the variables if any
                x = m[i].replace(" ", "").split("=")
                if len(x) == 2: d[x[0]] = float(x[1])
                else: raise Exception('')
            msg = "`{}` = **{}**".format(m[0], self.bot.calc.evaluate(m[0], d))
            if len(d) > 0:
                msg += "\nwith:\n"
                for k in d:
                    msg += "{} = {}\n".format(k, d[k])
            await inter.response.send_message(embed=self.bot.util.embed(title="Calculator", description=msg, color=self.color))
        except Exception as e:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Error\n"+str(e), color=self.color), ephemeral=True)
        await self.bot.util.clean(inter, 60)

    @utility.sub_command()
    async def jst(self, inter: disnake.GuildCommandInteraction):
        """Post the current time, JST timezone"""
        await inter.response.send_message(embed=self.bot.util.embed(title="{} {:%Y/%m/%d %H:%M} JST".format(self.bot.emote.get('clock'), self.bot.util.JST()), color=self.color), ephemeral=True)

    @utility.sub_command()
    async def rollchance(self, inter, count : str = commands.Param(description="Amount of rolls. Leave empty to use your set spark count", default="")):
        """Calculate your chance of rolling the rate up for a given amount of rolls."""
        await inter.response.defer(ephemeral=True)
        try:
            if count == '':
                if str(inter.author.id) in self.bot.data.save['spark']:
                    s = self.bot.data.save['spark'][str(inter.author.id)]
                    count = (s[0] // 300) + s[1] + s[2] * 10
                else:
                    raise Exception("Please specify a valid number of rolls")
            elif int(count) <= 0:
                raise Exception("Please specify a valid number of rolls")
            else:
                count = int(count)
            msg = "Your chances of getting at least one of the following rate ups with {} rolls:\n".format(count)
            rateups = self.bot.get_cog('Games').gachaRateUp()[1]
            if rateups is None: raise Exception("Unavailable")
            for r in rateups:
                msg += "{:} **{:}%** ▫️ {:.2f}%\n".format(self.bot.emote.get('SSR'), r, 100*(1-math.pow(1-float(r)*0.01, count)))
            await inter.edit_original_message(embed=self.bot.util.embed(title="Roll Chance Calculator", description=msg, color=self.color))
        except Exception as e:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Roll Chance Calculator Error", description=str(e), color=self.color))

    @utility.sub_command()
    async def fortunechance(self, inter, cards : str = commands.Param(description="Your list of cards, separated by spaces")):
        """Calculate your chance at the GBF summer fortune game from Summer 2021"""
        await inter.response.defer(ephemeral=True)
        cards = cards.split(" ")
        tier3 = []
        tier2 = []
        tier1 = []
        for c in cards:
            try:
                if c == "": continue
                if len(c) > 3 or int(c) < 0: raise Exception()
            except:
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Invalid card number `{}`".format(c), color=self.color))
                return
            sc = c.zfill(3)
            if sc[:2] not in tier3: tier3.append(sc[:2])
            if sc[1:] not in tier2: tier2.append(sc[1:])
            if sc not in tier1: tier1.append(sc)
        await inter.edit_original_message(embed=self.bot.util.embed(title="Summer Fortune Calculator", description="Your chances of winning at least one\n**Tier 3** ▫️ {:.2f}%\n**Tier 2** ▫️ {:.2f}%\n**Tier 1** ▫️ {:.2f}%".format(100*(1-math.pow(1-0.03, len(tier3))), 100*(1-math.pow(1-0.02, len(tier2))), 100*(1-math.pow(1-0.002, len(tier1)))), color=self.color))

    """cleanhtml()
    Clean the html and escape the string properly
    
    Parameters
    ------
    raw: String to clean
    
    Returns
    ----------
    str: Cleaned string
    """
    def cleanhtml(self, raw):
      cleaner = re.compile('<.*?>')
      return html.unescape(re.sub(cleaner, '', raw.replace('<br>', ' '))).replace('>', '')

    """get4chan()
    Call the 4chan api to retrieve a list of thread based on a search term
    
    Parameters
    ------
    board: board to search for (example: a for /a/)
    search: search terms
    
    Returns
    ----------
    list: Matching threads
    """
    def get4chan(self, board : str, search : str): # be sure to not abuse it, you are not supposed to call the api more than once per second
        try:
            search = search.lower()
            data = self.bot.gbf.request('http://a.4cdn.org/{}/catalog.json'.format(board), no_base_headers=True, load_json=True)
            threads = []
            for p in data:
                for t in p["threads"]:
                    try:
                        if t.get("sub", "").lower().find(search) != -1 or t.get("com", "").lower().find(search) != -1:
                            threads.append([t["no"], t["replies"], self.cleanhtml(t.get("com", ""))]) # store the thread ids matching our search word
                    except:
                        pass
            threads.sort(reverse=True)
            return threads
        except:
            return []

    @commands.slash_command(default_permission=True, name="4chan")
    @commands.cooldown(1, 2, commands.BucketType.default)
    async def fourchan(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    @fourchan.sub_command()
    async def search(self, inter: disnake.GuildCommandInteraction, board : str = commands.Param(description="The board to search on."), search : str = commands.Param(description="Search string")):
        """Search 4chan threads"""
        await inter.response.defer(ephemeral=True)
        nsfw = ['b', 'r9k', 'pol', 'bant', 'soc', 's4s', 's', 'hc', 'hm', 'h', 'e', 'u', 'd', 'y', 't', 'hr', 'gif', 'aco', 'r']
        board = board.lower().replace('/', '')
        if board in nsfw and not inter.channel.is_nsfw():
            await inter.edit_original_message("The board `{}` is restricted to NSFW channels".format(board))
            return
        threads = await self.bot.do(self.get4chan, board, search)
        if len(threads) > 0:
            msg = ""
            for t in threads:
                if len(t[2]) > 34:
                    msg += ':four_leaf_clover: [{} replies](https://boards.4channel.org/{}/thread/{}) ▫️ {}...\n'.format(t[1], board, t[0], t[2][:33])
                else:
                    msg += ':four_leaf_clover: [{} replies](https://boards.4channel.org/{}/thread/{}) ▫️ {}\n'.format(t[1], board, t[0], t[2])
                if len(msg) > 1800:
                    msg += 'and more...'
                    break
            await inter.edit_original_message(embed=self.bot.util.embed(title="4chan Search result", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await inter.edit_original_message(embed=self.bot.util.embed(title="4chan Search result", description="No matching threads found", color=self.color))

    @fourchan.sub_command()
    async def gbfg(self, inter: disnake.GuildCommandInteraction):
        """Post the latest /gbfg/ threads"""
        await inter.response.defer(ephemeral=True)
        threads = await self.bot.do(self.get4chan, 'vg', '/gbfg/')
        if len(threads) > 0:
            msg = ""
            for t in threads:
                if len(t[2]) > 34:
                    msg += ':poop: [{} replies](https://boards.4channel.org/vg/thread/{}) ▫️ {}...\n'.format(t[1], t[0], t[2][:33])
                else:
                    msg += ':poop: [{} replies](https://boards.4channel.org/vg/thread/{}) ▫️ {}\n'.format(t[1], t[0], t[2])
                if len(msg) > 1800:
                    msg += 'and more...'
                    break
            await inter.edit_original_message(embed=self.bot.util.embed(title="/gbfg/ latest thread(s)", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await inter.edit_original_message(embed=self.bot.util.embed(title="/gbfg/ Error", description="I couldn't find a single /gbfg/ thread 😔", color=self.color))

    @fourchan.sub_command()
    async def hgg(self, inter: disnake.GuildCommandInteraction):
        """Post the latest /hgg2d/ threads (NSFW channels Only)"""
        await inter.response.defer(ephemeral=True)
        if not inter.channel.is_nsfw():
            await inter.edit_original_message(embed=self.bot.util.embed(title=':underage: NSFW channels only', color=self.color))
            return
        threads = await self.bot.do(self.get4chan, 'vg', '/hgg2d/')
        if len(threads) > 0:
            msg = ""
            for t in threads:
                if len(t[2]) > 34:
                    msg += '🔞 [{} replies](https://boards.4channel.org/vg/thread/{}) ▫️ {}...\n'.format(t[1], t[0], t[2][:33])
                else:
                    msg += '🔞 [{} replies](https://boards.4channel.org/vg/thread/{}) ▫️ {}\n'.format(t[1], t[0], t[2])
                if len(msg) > 1800:
                    msg += 'and more...'
                    break
            await inter.edit_original_message(embed=self.bot.util.embed(title="/hgg2d/ latest thread(s)", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await inter.edit_original_message(embed=self.bot.util.embed(title="/hgg2d/ Error", description="I couldn't find a single /hgg2d/ thread 😔", color=self.color))