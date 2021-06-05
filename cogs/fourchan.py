from discord.ext import commands
import re
import html

# ----------------------------------------------------------------------------------------------------------------
# FourChan Cog
# ----------------------------------------------------------------------------------------------------------------
# Commands to access and retrieve thread infos from 4channel.org
# ----------------------------------------------------------------------------------------------------------------

class FourChan(commands.Cog):
    """Retrieve 4channel threads."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x17e32b

    def cleanhtml(self, raw):
      cleaner = re.compile('<.*?>')
      return html.unescape(re.sub(cleaner, '', raw.replace('<br>', ' '))).replace('>', '')

    # get a 4chan thread
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

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['hgg2d'])
    @commands.cooldown(1, 10, commands.BucketType.default)
    async def hgg(self, ctx):
        """Post the latest /hgg2d/ threads (NSFW channels Only)"""
        if not ctx.channel.is_nsfw():
            await ctx.reply(embed=self.bot.util.embed(title=':underage: NSFW channels only'))
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
            await ctx.reply(embed=self.bot.util.embed(title="/hgg2d/ latest thread(s)", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await ctx.reply(embed=self.bot.util.embed(title="/hgg2d/ Error", description="I couldn't find a single /hgg2d/ thread 😔", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['thread'])
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def gbfg(self, ctx):
        """Post the latest /gbfg/ threads"""
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
            await ctx.reply(embed=self.bot.util.embed(title="/gbfg/ latest thread(s)", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await ctx.reply(embed=self.bot.util.embed(title="/gbfg/ Error", description="I couldn't find a single /gbfg/ thread 😔", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, name='4chan')
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def _4chan(self, ctx, board : str, *, term : str):
        """Search 4chan threads
        Pink boards are limited to NSFW channels only"""
        nsfw = ['b', 'r9k', 'pol', 'bant', 'soc', 's4s', 's', 'hc', 'hm', 'h', 'e', 'u', 'd', 'y', 't', 'hr', 'gif', 'aco', 'r']
        board = board.lower()
        if board in nsfw and not ctx.channel.is_nsfw():
            await ctx.reply(embed=self.bot.util.embed(title=":underage: The board `{}` is restricted to NSFW channels".format(board)))
            return
        threads = await self.bot.do(self.get4chan, board, term)
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
            await ctx.reply(embed=self.bot.util.embed(title="4chan Search result", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await ctx.reply(embed=self.bot.util.embed(title="4chan Search result", description="No matching threads found", color=self.color))