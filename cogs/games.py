from discord.ext import commands
import asyncio
import random
from datetime import datetime

# ----------------------------------------------------------------------------------------------------------------
# Games Cog
# ----------------------------------------------------------------------------------------------------------------
# Fun commands
# ----------------------------------------------------------------------------------------------------------------

class Games(commands.Cog):
    """Granblue-themed Games and more."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xeb6b34
        self.legfest = {"double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2"}
        self.notfest = {"normal", "x1", "3%", "gacha", "1"}
        self.scratcher_loot = {
            100 : ['Siero Ticket'],
            300 : ['Sunlight Stone', 'Gold Brick'],
            450 : ['Damascus Ingot'],
            600 : ['Agni', 'Varuna', 'Titan', 'Zephyrus', 'Zeus', 'Hades', 'Shiva', 'Europa', 'Godsworn Alexiel', 'Grimnir', 'Lucifer', 'Bahamut', 'Michael', 'Gabriel', 'Uriel', 'Raphael', 'Metatron', 'Sariel', 'Belial'],
            400 : ['Murgleis', 'Benedia', 'Gambanteinn', 'Love Eternal', 'AK-4A', 'Reunion', 'Ichigo-Hitofuri', 'Taisai Spirit Bow', 'Unheil', 'Sky Ace', 'Ivory Ark', 'Blutgang', 'Eden', 'Parazonium', 'Ixaba', 'Blue Sphere', 'Certificus', 'Fallen Sword', 'Mirror-Blade Shard', 'Galilei\'s Insight', 'Purifying Thunderbolt', 'Vortex of the Void', 'Sacred Standard', 'Bab-el-Mandeb', 'Cute Ribbon', 'Kerak', 'Sunya', 'Fist of Destruction', 'Yahata\'s Naginata', 'Cerastes', 'World Ender', 'Ouroboros Prime'],
            8000 : ['Crystals x3000', 'Damascus Crystal', 'Intricacy Ring', 'Gold Moon x2', 'Brimston Earrings', 'Permafrost Earrings', 'Brickearth Earrings', 'Jetstream Earrings', 'Sunbeam Earrings', 'Nightshade Earrings'],
            11250 : ['Gold Spellbook', 'Moonlight Stone', 'Ultima Unit x3', 'Silver Centrum x5', 'Primeval Horn x3', 'Horn of Bahamut x4', 'Legendary Merit x5', 'Steel Brick'],
            22000: ['Lineage Ring x2', 'Coronation Ring x3', 'Silver Moon x5', 'Bronze Moon x10'],
            33000: ['Elixir x100', 'Soul Berry x300']
        }
        self.scratcher_thumb = {
            'Siero Ticket':'item/article/s/30041.jpg', 'Sunlight Stone':'item/evolution/s/20014.jpg', 'Gold Brick':'item/evolution/s/20004.jpg', 'Damascus Ingot':'item/evolution/s/20005.jpg','Agni':'summon/s/2040094000.jpg', 'Varuna':'summon/s/2040100000.jpg', 'Titan':'summon/s/2040084000.jpg', 'Zephyrus':'summon/s/2040098000.jpg', 'Zeus':'summon/s/2040080000.jpg', 'Hades':'summon/s/2040090000.jpg', 'Shiva':'summon/s/2040185000.jpg', 'Europa':'summon/s/2040225000.jpg', 'Godsworn Alexiel':'summon/s/2040205000.jpg', 'Grimnir':'summon/s/2040261000.jpg', 'Lucifer':'summon/s/2040056000.jpg', 'Bahamut':'summon/s/2040030000.jpg', 'Michael':'summon/s/2040306000.jpg', 'Gabriel':'summon/s/2040311000.jpg', 'Uriel':'summon/s/2040203000.jpg', 'Raphael':'summon/s/2040202000.jpg', 'Metatron':'summon/s/2040330000.jpg', 'Sariel':'summon/s/2040327000.jpg', 'Belial':'summon/s/2040347000.jpg', 'Murgleis':'weapon/s/1040004600.jpg', 'Benedia':'weapon/s/1040502500.jpg',  'Gambanteinn':'weapon/s/1040404300.jpg',  'Love Eternal':'weapon/s/1040105400.jpg',  'AK-4A':'weapon/s/1040004600.jpg',  'Reunion':'weapon/s/1040108200.jpg',  'Ichigo-Hitofuri':'weapon/s/1040910000.jpg',  'Taisai Spirit Bow':'weapon/s/1040708700.jpg',  'Unheil':'weapon/s/1040809100.jpg',  'Sky Ace':'weapon/s/1040911500.jpg',  'Ivory Ark':'weapon/s/1040112500.jpg',  'Blutgang':'weapon/s/1040008700.jpg',  'Eden':'weapon/s/1040207000.jpg',  'Parazonium':'weapon/s/1040108700.jpg',  'Ixaba':'weapon/s/1040906400.jpg',  'Blue Sphere':'weapon/s/1040410000.jpg',  'Certificus':'weapon/s/1040309000.jpg',  'Fallen Sword':'weapon/s/1040014300.jpg',  'Mirror-Blade Shard':'weapon/s/1040110600.jpg',  'Galilei\'s Insight':'weapon/s/1040211600.jpg',  'Purifying Thunderbolt':'weapon/s/1040709000.jpg',  'Vortex of the Void':'weapon/s/1040212700.jpg',  'Sacred Standard':'weapon/s/1040213400.jpg',  'Bab-el-Mandeb':'weapon/s/1040004600.jpg',  'Cute Ribbon':'weapon/s/1040605900.jpg',  'Kerak':'weapon/s/1040812000.jpg',  'Sunya':'weapon/s/1040811800.jpg',  'Fist of Destruction':'weapon/s/1040612700.jpg',  'Yahata\'s Naginata':'weapon/s/1040312900.jpg',  'Cerastes':'weapon/s/1040215300.jpg',  'World Ender':'weapon/s/1040020900.jpg',  'Ouroboros Prime':'weapon/s/1040418600.jpg', 'Crystals x3000':'item/normal/s/gem.jpg', 'Damascus Crystal':'item/article/s/203.jpg', 'Intricacy Ring':'item/npcaugment/s/3.jpg', 'Gold Spellbook':'item/evolution/s/20403.jpg', 'Moonlight Stone':'item/evolution/s/20013.jpg', 'Gold Moon x2':'item/article/s/30033.jpg', 'Ultima Unit x3':'item/article/s/138.jpg', 'Silver Centrum x5':'item/article/s/107.jpg', 'Primeval Horn x3':'item/article/s/79.jpg', 'Horn of Bahamut x4':'item/article/s/59.jpg', 'Legendary Merit x5':'item/article/s/2003.jpg', 'Steel Brick':'item/evolution/s/20003.jpg', 'Brimston Earrings':'item/npcaugment/s/11.jpg', 'Permafrost Earrings':'item/npcaugment/s/12.jpg', 'Brickearth Earrings':'item/npcaugment/s/13.jpg', 'Jetstream Earrings':'item/npcaugment/s/14.jpg', 'Sunbeam Earrings':'item/npcaugment/s/15.jpg', 'Nightshade Earrings':'item/npcaugment/s/16.jpg', 'Lineage Ring x2':'item/npcaugment/s/2.jpg', 'Coronation Ring x3':'item/npcaugment/s/1.jpg', 'Silver Moon x5':'item/article/s/30032.jpg', 'Bronze Moon x10':'item/article/s/30031.jpg', 'Elixir x100':'item/normal/s/2.jpg', 'Soul Berry x300':'item/normal/s/5.jpg'
        }
        self.scam = [(1000, 'Sunlight Stone', 'evolution/s/20014.jpg'), (1000, 'Damascus Ingot', 'evolution/s/20005.jpg'), (3000, 'Damascus Crystal x2', 'article/s/203.jpg'), (3000, 'Brimstone Earrings x2', 'npcaugment/s/11.jpg'), (3000, 'Permafrost Earrings x2', 'npcaugment/s/12.jpg'), (3000, 'Brickearth Earrings x2', 'npcaugment/s/13.jpg'), (3000, 'Jetstream Earrings x2', 'npcaugment/s/14.jpg'), (3000, 'Sunbeam Earrings x2', 'npcaugment/s/15.jpg'), (3000, 'Nightshade Earrings x2', 'npcaugment/s/16.jpg'), (7000, 'Intracacy Ring', 'npcaugment/s/3.jpg'), (7000, 'Ultima Unit x10', 'article/s/138.jpg'), (7000, 'Silver Centrum x5', 'article/s/107.jpg'), (7000, 'Astaroth Anima x10', 'article/s/20781.jpg'), (7000, 'Sephira Stone x10', 'article/s/25000.jpg'), (7000, 'Weapon Plus Mark x30', 'bonusstock/s/1.jpg'), (7000, 'Summon Plus Mark x30', 'bonusstock/s/2.jpg'), (7000, 'Gold Moon x2', 'article/s/30033.jpg'), (7000, 'Silver Moon x5', 'article/s/30032.jpg'), (7000, 'Half Elixir x100', 'normal/s/2.jpg'), (7000, 'Soul Berry x300', 'normal/s/5.jpg')]
        self.scam_rate = 0
        for r in self.scam:
            self.scam_rate += r[0]
        # scratcher rate calcul
        self.scratcher_total = 0
        self.scratcher_total_rare1 = 0
        self.scratcher_total_rare2 = 0
        rare_divider1 = 'Murgleis'
        rare_divider2 = 'Crystals x3000'
        for r in self.scratcher_loot:
            self.scratcher_total += r * len(self.scratcher_loot[r])
            if self.scratcher_loot[r][0] == rare_divider1: self.scratcher_total_rare1 = self.scratcher_total
            if self.scratcher_loot[r][0] == rare_divider2: self.scratcher_total_rare2 = self.scratcher_total

    """gachaRateUp()
    Return the current real gacha from GBF, if it exists in the bot memory.
    If not, a dummy/limited one is generated.
    
    Returns
    --------
    tuple: Containing:
        - The whole rate list
        - The banner rate up
        - The ssr rate, in %
        - Boolean indicating if the gacha is the real one
    """
    def gachaRateUp(self):
        try:
            self.bot.get_cog('GranblueFantasy').getCurrentGacha()
            data = self.bot.data.save['gbfdata']['rateup']
            if len(data) == 0: raise Exception()
            rateups = self.bot.data.save['gbfdata']['gacharateups']
            ssrrate = int(data[2]['rate'])
            extended = True
        except:
            data = [{}, {'rate':15}, {'rate':3}]
            rateups = None
            ssrrate = 3
            extended = False
        return data, rateups, ssrrate, extended

    """gachaRoll()
    Simulate GBF gacha and return the result.
    
    Parameters
    ----------
    options: Keyword arguments:
        - mode : str = single, srssr, memerollA, memerollB, ten, gachapin, mukku or supermukku
        - count : int = maximum number of rolls to do
        - legfest : bool = True for 6% rate, False for 3% rate
    
    Returns
    --------
    dict: Containing:
        - 'list', the full list of generated gacha rolls
        - 'detail', a list containing the number of R, SR and SSR obtained
        - 'extended', a boolean indicating if the gacha used was the real one
        - 'rate', the SSR rate used, in %
    """
    def gachaRoll(self, **options):
        mode = {'single':0, 'srssr':1, 'memerollA':2, 'memerollB':3, 'ten':10, 'gachapin':11, 'mukku':12, 'supermukku':13}[options['mode']]
        count = options.get('count', 300)
        if count < 1: count = 1
        data, rateups, ssrrate, extended = self.gachaRateUp() # get current gacha (dummy one if error)
        legfest = options.get('legfest', True if ssrrate == 6 else False) # legfest parameter
        ssrrate = 15 if mode == 13 else (9 if mode == 12 else (6 if legfest else 3)) # set the ssr rate
        result = {'list':[], 'detail':[0, 0, 0], 'extended':extended, 'rate':ssrrate} # result container
        tenrollsr = False # flag for guaranted SR in ten rolls
        for i in range(0, count):
            d = random.randint(1, 10000000) / 100000 # random value (don't use .random(), it doesn't work well with this)
            if mode == 1 or (mode >= 10 and (i % 10 == 9) and not tenrollsr): sr_mode = True # force sr in srssr mode OR when 10th roll of ten roll)
            else: sr_mode = False # else doesn't set
            if d < ssrrate: # SSR CASE
                r = 2
                if extended and ssrrate != data[r]['rate']:
                    d = d * (data[r]['rate'] / ssrrate)
                tenrollsr = True
            elif (not sr_mode and d < 15 + ssrrate) or sr_mode: # SR CASE
                r = 1
                d -= ssrrate
                while d >= 15: d -= 15
                tenrollsr = True
            else: # R CASE
                r = 0
                d -= ssrrate + 15
            if i % 10 == 9: tenrollsr = False # unset flag if we did 10 rolls
            if extended: # if we have a real gacha
                roll = None
                for rate in data[r]['list']: # find which item we rolled
                    fr = float(rate)
                    for item in data[r]['list'][rate]:
                        if r == 2 and rate in rateups: last = "**" + item + "**"
                        else: last = item
                        if d < fr:
                            roll = [r, last]
                            break
                        d -= fr
                    if roll is not None:
                        break
                if roll is None:
                    roll = [r, last]
                result['list'].append(roll) # store roll
                result['detail'][r] += 1
                if r == 2:
                    if mode == 2: break # memeroll mode A
                    elif mode == 3 and result['list'][-1][1].startswith("**"): break # memeroll mode B
            else: # using dummy gacha
                result['list'].append([r])
                result['detail'][r] += 1
                if r == 2:
                    if mode == 2 or mode == 3: break  # memeroll mode A and B
            if i % 10 == 9:
                if (mode == 11 or mode == 12) and result['detail'][2] >= 1: break # gachapin and mukku mode
                elif mode == 13 and result['detail'][2] >= 5: break # super mukku mode
        return result

    """checkLegfest()
    Check the provided parameter and the real gacha to determine if we will be using a 6 or 3% SSR rate
    
    Parameters
    ----------
    word: A string inputted by the user, check self.legfest for 6% values and self.notfest for 3% values
    
    Returns
    --------
    bool: True if 6%, False if 3%
    """
    def checkLegfest(self, word):
        word = word.lower()
        s = self.bot.data.save['gbfdata'].get('gachacontent', '') # check the real gacha
        if s is None or s.find("**Premium Gala**") == -1: isleg = False
        else: isleg = True
        if word not in self.notfest and (word in self.legfest or isleg): return True
        return False

    """getSSRList()
    Extract the SSR from a full gacha list generated by gachaRoll()
    
    Parameters
    ----------
    result: Return value of gachaRoll()
    
    Returns
    --------
    dict: SSR List. The keys are the SSR name and the values are how many your rolled
    """
    def getSSRList(self, result):
        rolls = {}
        for r in result['list']:
            if r[0] == 2: rolls[r[1]] = rolls.get(r[1], 0) + 1
        return rolls

    """_roll()
    Unified function to display the simulate the GBF gacha, used by most gacha commands
    
    Parameters
    ----------
    ctx: The command context
    titles: The titles used in the message. Second string is for the final message
    rmode: Display type = 0 for the single roll mode, 1 for the memeroll mode, 2 for the ten roll mode and 3 or more for anything else (spark, gachapin, ...)
    message: The message to process
    """
    async def _roll(self, ctx, titles:tuple=("{}", "{}"), rmode:int=-1, **rollOptions):
        if rmode < 0: return # invalid mode
        result = await self.bot.do(self.gachaRoll, **rollOptions) # do the rolling
        footer = "{}% SSR rate".format(result['rate']) # message footer
        if rollOptions.get('mode', '') == 'memerollB': footer += " ▫️ until rate up"
        
        # select crystal image
        if (100 * result['detail'][2] / len(result['list'])) >= result['rate']: crystal = random.choice(['https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png', 'https://media.discordapp.net/attachments/614716155646705676/761969229095632916/3_s.png'])
        elif (100 * result['detail'][1] / len(result['list'])) >= result['rate']: crystal = 'https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png'
        else: crystal = random.choice(['https://media.discordapp.net/attachments/614716155646705676/761969231323070494/0_s.png', 'https://media.discordapp.net/attachments/614716155646705676/761976275706445844/1_s.png'])

        # startup msg
        final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':titles[0].format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, image=crystal, color=self.color, footer=footer))
        await asyncio.sleep(5)

        # display result
        if rmode == 0: # single roll mode
            r = result['list'][0]
            if result['extended']:
                await final_msg.edit(embed=self.bot.util.embed(author={'name':titles[1].format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="{} {}".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(r[0])), r[1]), color=self.color, footer=footer))
            else:
                await final_msg.edit(embed=self.bot.util.embed(author={'name':titles[1].format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="{}".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(r[0]))), color=self.color, footer=footer))
        elif rmode == 1: # memeroll mode
            counter = [0, 0, 0]
            text = ""
            for i in range(0, len(result['list'])):
                if i > 0 and i % 3 == 0:
                    await final_msg.edit(embed=self.bot.util.embed(author={'name':titles[0].format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="{} {} ▫️ {} {} ▫️ {} {}\n{}".format(counter[2], self.bot.emote.get('SSR'), counter[1], self.bot.emote.get('SR'), counter[0], self.bot.emote.get('R'), text), color=self.color, footer=footer))
                    await asyncio.sleep(1)
                    text = ""
                if result['extended']:
                    text += "{} {}\n".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(result['list'][i][0])), result['list'][i][1])
                else:
                    text += "{} ".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(result['list'][i][0])))
                counter[result['list'][i][0]] += 1
            title = titles[1].format(ctx.author.display_name, len(result['list'])) if (len(result['list']) < 300) else "{} sparked".format(ctx.author.display_name)
            await final_msg.edit(embed=self.bot.util.embed(author={'name':title, 'icon_url':ctx.author.avatar_url}, description="{} {} ▫️ {} {} ▫️ {} {}\n{}".format(counter[2], self.bot.emote.get('SSR'), counter[1], self.bot.emote.get('SR'), counter[0], self.bot.emote.get('R'), text), color=self.color, footer=footer))
        elif rmode == 2: # ten roll mode
            if result['extended']:
                for i in range(0, 11):
                    msg = ""
                    for j in range(0, i):
                        if j >= 10: break
                        msg += "{} {} ".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(result['list'][j][0])), result['list'][j][1])
                        if j % 2 == 1: msg += "\n"
                    for j in range(i, 10):
                        msg += '{}'.format(self.bot.emote.get('crystal{}'.format(result['list'][j][0])))
                        if j % 2 == 1: msg += "\n"
                    await asyncio.sleep(0.75)
                    await final_msg.edit(embed=self.bot.util.embed(author={'name':titles[1].format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
            else:
                msg = ""
                i = 0
                for i in len(result['list']):
                    r = result['list'][i][0]
                    if i == 5: msg += '\n'
                    if r == 2: msg += '{}'.format(self.bot.emote.get('SSR'))
                    elif r == 1: msg += '{}'.format(self.bot.emote.get('SR'))
                    else: msg += '{}'.format(self.bot.emote.get('R'))
                await final_msg.edit(embed=self.bot.util.embed(author={'name':titles[1].format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        else: # others
            count = len(result['list'])
            rate = (100*result['detail'][2]/count)
            msg = ""
            if result['extended']:
                rolls = self.getSSRList(result)
                if len(rolls) > 0:
                    msg = "{} ".format(self.bot.emote.get('SSR'))
                    for item in rolls:
                        msg += item
                        if rolls[item] > 1: msg += " x{}".format(rolls[item])
                        await final_msg.edit(embed=self.bot.util.embed(author={'name':titles[1].format(ctx.author.display_name, count), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
                        await asyncio.sleep(0.75)
                        msg += ", "
                    msg = msg[:-2]
            if rollOptions.get('mode', '') == 'gachapin': amsg = "Gachapin stopped after **{}** rolls\n".format(len(result['list']))
            elif rollOptions.get('mode', '') == 'mukku': amsg = "Mukku stopped after **{}** rolls\n".format(len(result['list']))
            else: amsg = ""
            msg = "{}{:} {:} ▫️ {:} {:} ▫️ {:} {:}\n{:}\n**{:.2f}%** SSR rate".format(amsg, result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), msg, rate)
            await final_msg.edit(embed=self.bot.util.embed(author={'name':titles[1].format(ctx.author.display_name, count), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        await self.bot.util.clean(ctx, final_msg, 25)


    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def single(self, ctx, double : str = ""):
        """Do a single roll
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        await self._roll(ctx, ("{} did a single roll...", "{} did a single roll"), 0, count=1, mode='single', legfest=self.checkLegfest(double))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def srssr(self, ctx, double : str = ""):
        """Do a single SR/SSR ticket roll
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        await self._roll(ctx, ("{} is using a SR/SSR ticket...", "{} used a SR/SSR ticket"), 0, count=1, mode='srssr', legfest=self.checkLegfest(double))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['memerolls'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def memeroll(self, ctx, double : str = ""):
        """Do single rolls until a SSR
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1".
        Add R at the end of the keyword to target rate up SSRs (example: doubleR, it's not compatible with the legacy mode)."""
        if len(double) > 0 and double[-1] in ['r', 'R']:
            rateup = True
            double = double[:-1].replace(' ', '')
        else:
            rateup = False
        await self._roll(ctx, ("{} is memerolling...", "{} memerolled {} times"), 1, mode='memerollB' if rateup else 'memerollA', legfest=self.checkLegfest(double))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def ten(self, ctx, double : str = ""):
        """Do ten gacha rolls
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        await self._roll(ctx, ("{} did ten rolls...", "{} did ten rolls"), 2, count=10, mode='ten', legfest=self.checkLegfest(double))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def roll(self, ctx, count : str = "0", double : str = ""):
        """Do an user-specified number gacha rolls
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        try:
            count = int(count)
            if count <= 0 or count > 600: raise Exception()
        except:
            msg = await ctx.reply(embed=self.bot.util.embed(title="Roll Error", description="Please specify a valid number of rolls (between **1** and **600** included)", color=self.color))
            await self.bot.util.clean(ctx, msg, 20)
            return
        await self._roll(ctx, ("{}" + " is rolling {} times...".format(count), "{} " + "rolled {} times".format(count)), 3, count=count, mode='ten', legfest=self.checkLegfest(double))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(15, 30, commands.BucketType.guild)
    async def spark(self, ctx, double : str = ""):
        """Do thirty times ten gacha rolls
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        await self._roll(ctx, ("{} is sparking...", "{} sparked"), 3, count=300, mode='ten', legfest=self.checkLegfest(double))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['frenzy'])
    @commands.cooldown(15, 30, commands.BucketType.guild)
    async def gachapin(self, ctx, double : str = ""):
        """Do ten rolls until you get a ssr
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        await self._roll(ctx, ("{} is rolling the Gachapin...", "{} rolled the Gachapin"), 3, count=300, mode='gachapin', legfest=self.checkLegfest(double))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['mook'])
    @commands.cooldown(15, 30, commands.BucketType.guild)
    async def mukku(self, ctx, super : str = ""):
        """Do ten rolls until you get a ssr, 9% ssr rate
        You can add "super" for a 9% rate and 5 ssr mukku"""
        await self._roll(ctx, ("{} is rolling the Mukku...", "{} rolled the Mukku"), 3, count=300, mode=('supermukku' if (super.lower() == "super") else 'mukku'))

    def getRoulette(self, count, mode, double):
        result = self.gachaRoll(count=count, mode=mode, legfest=self.checkLegfest(double))
        footer = "{}% SSR rate".format(result['rate'])
        count = len(result['list'])
        rate = (100*result['detail'][2]/count)
        tmp = ""
        if result['extended']:
            ssrs = self.getSSRList(result)
            if len(ssrs) > 0:
                tmp = "\n{} ".format(self.bot.emote.get('SSR'))
                for item in ssrs:
                    tmp += item
                    if ssrs[item] > 1: tmp += " x{}".format(ssrs[item])
                    tmp += ", "
                tmp = tmp[:-2]
        return result, rate, tmp, count

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def roulette(self, ctx, double : str = ""):
        """Imitate the GBF roulette
        6% keywords: "double", "x2", "6%", "legfest", "flashfest", "flash", "leg", "gala", "2".
        3% keywords: "normal", "x1", "3%", "gacha", "1"."""
        footer = ""
        roll = 0
        rps = ['rock', 'paper', 'scissor']
        ct = self.bot.util.JST()
        # customization settings
        fixedS = ct.replace(year=2021, month=3, day=29, hour=19, minute=0, second=0, microsecond=0) # beginning of fixed rolls
        fixedE = fixedS.replace(day=31, hour=19) # end of fixed rolls
        forced3pc = True # force 3%
        forcedRollCount = 100 # number of rolls during fixed rolls
        forcedSuperMukku = True
        enable200 = False # add 200 on wheel
        enableJanken = False
        maxJanken = 2 # number of RPS
        doubleMukku = True
        # settings end
        state = 0
        superFlag = False
        if ct >= fixedS and ct < fixedE:
            msg = "{} {} :confetti_ball: :tada: Guaranteed **{} 0 0** R O L L S :tada: :confetti_ball: {} {}\n".format(self.bot.emote.get('crystal'), self.bot.emote.get('crystal'), forcedRollCount//100, self.bot.emote.get('crystal'), self.bot.emote.get('crystal'))
            roll = forcedRollCount
            if forcedSuperMukku: superFlag = True
            if l == 2 and forced3pc:
                l = self.isLegfest("")
                if l == 2: footer = "6% SSR rate ▪️ Fixed rate"
                else: footer = "3% SSR rate ▪️ Fixed rate"
            d = 0
            state = 1
        else:
            d = random.randint(1, 36000)
            if enable200 and d < 300:
                msg = "{} {} :confetti_ball: :tada: **2 0 0 R O L L S** :tada: :confetti_ball: {} {}\n".format(self.bot.emote.get('crystal'), self.bot.emote.get('crystal'), self.bot.emote.get('crystal'), self.bot.emote.get('crystal'))
                roll = 200
            elif d < 3000:
                msg = "**Gachapin Frenzy** :four_leaf_clover:\n"
                roll = -1
                state = 2
            elif d < 4500:
                msg = ":confetti_ball: :tada: **100** rolls!! :tada: :confetti_ball:\n"
                roll = 100
            elif d < 7700:
                msg = "**30** rolls! :clap:\n"
                roll = 30
            elif d < 19500:
                msg = "**20** rolls :open_mouth:\n"
                roll = 20
            else:
                msg = "**10** rolls :pensive:\n"
                roll = 10
        final_msg = await ctx.reply(embed=self.bot.util.embed(author={'name':"{} is spinning the Roulette".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        if not enableJanken and state < 2: state = 1
        running = True
        while running:
            await asyncio.sleep(2)
            if state == 0: # RPS
                if enableJanken and d >= 2000 and random.randint(0, 2) > 0:
                    a = 0
                    b = 0
                    while a == b:
                        a = random.randint(0, 2)
                        b = random.randint(0, 2)
                    msg += "You got **{}**, Gachapin got **{}**".format(rps[a], rps[b])
                    if (a == 1 and b == 0) or (a == 2 and b == 1) or (a == 0 and b == 2):
                        msg += " :thumbsup:\nYou **won** rock paper scissor, your rolls are **doubled** :confetti_ball:\n"
                        roll = roll * 2
                        if roll > (200 if enable200 else 100): roll = (200 if enable200 else 100)
                        maxJanken -= 1
                        if maxJanken == 0:
                            state = 1
                    else:
                        msg += " :pensive:\n"
                        state = 1
                else:
                    state = 1
            elif state == 1: # normal rolls
                result, rate, tmp, count = await self.bot.do(self.getRoulette, roll, 'ten', double)
                footer = "{}% SSR rate".format(result['rate'])
                msg += "{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                if superFlag: state = 4
                else: running = False
            elif state == 2: # gachapin
                result, rate, tmp, count = await self.bot.do(self.getRoulette, 300, 'gachapin', double)
                footer = "{}% SSR rate".format(result['rate'])
                msg += "Gachapin ▫️ **{}** rolls\n{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(count, result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                if count == 10 and random.randint(1, 100) < 99: state = 3
                elif count == 20 and random.randint(1, 100) < 60: state = 3
                elif count == 30 and random.randint(1, 100) < 30: state = 3
                else: running = False
            elif state == 3:
                result, rate, tmp, count = await self.bot.do(self.getRoulette, 300, 'mukku', double)
                msg += ":confetti_ball: Mukku ▫️ **{}** rolls\n{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(count, result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                if doubleMukku:
                    if random.randint(1, 100) < 25: pass
                    else: running = False
                    doubleMukku = False
                else:
                    running = False
            elif state == 4:
                result, rate, tmp, count = await self.bot.do(self.getRoulette, 300, 'supermukku', double)
                msg += ":confetti_ball: **Super Mukku** ▫️ **{}** rolls\n{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(count, result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                running = False

            await final_msg.edit(embed=self.bot.util.embed(author={'name':"{} spun the Roulette".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))

        await self.bot.util.clean(ctx, final_msg, 45)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['scamgacha', 'stargacha', 'starlegendgacha', 'starlegend'])
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def scam(self, ctx, mode : str = ""):
        """Star gacha item simulation"""
        roll = random.randint(1, self.scam_rate)
        loot = None
        n = 0
        for r in self.scam:
            n += r[0]
            if roll < n:
                loot = r
                break
        if loot is None: loot = self.scam[-1]
        msg = await ctx.reply(embed=self.bot.util.embed(author={'name':"{} is getting scammed...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=":question: :question: :question:", color=self.color))
        await asyncio.sleep(2)
        await msg.edit(embed=self.bot.util.embed(author={'name':"{} got scammed".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="{}".format(loot[1]), thumbnail='http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/item/{}'.format(loot[2]), color=self.color))
        await self.bot.util.clean(ctx, msg, 45)
        

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['scratcher'])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def scratch(self, ctx, mode : str = ""):
        """Imitate the GBF scratch game from Anniversary 2020"""
        message = None
        ct = self.bot.util.JST()
        # settings
        fixedS = ct.replace(year=2021, month=3, day=29, hour=19, minute=0, second=0, microsecond=0) # beginning of good scratcher
        fixedE = fixedS.replace(day=31, hour=19) # end of good scratcher
        enableBetterDuringPeriod = True
        betterScratcher = False # if true, only good results possible
        # settings end
        footer = ""
        if enableBetterDuringPeriod and ct >= fixedS and ct < fixedE:
            betterScratcher = True

        # user options
        if mode == "debug" and ctx.author.id == self.bot.data.config['ids']['owner']:
            msg = "`$scratch` Debug Values\nTotal: {} (100%)\n".format(self.scratcher_total)
            for r in self.scratcher_loot:
                msg += "{} Tier: {} ({}%)\n".format(self.scratcher_loot[r][0], r * len(self.scratcher_loot[r]), ((10000 * r * len(self.scratcher_loot[r])) // self.scratcher_total) / 100)
            debug_msg = await ctx.reply(embed=self.bot.util.embed(title="Scratcher Debug", description=msg, color=self.color))
            await self.bot.util.clean(ctx, debug_msg, 30)
        elif mode == "rigged" and ctx.author.id == self.bot.data.config['ids']['owner']:
            betterScratcher = True
            footer = "Debug mode"

        if random.randint(1, 100) <= 10:
            betterScratcher = True # to simulate the rare scratcher card thing, currently 10%
        if footer == "" and betterScratcher: footer = "Rare card"
        selected = {}
        nloot = random.randint(4, 5)
        while len(selected) < nloot:
            n = self.scratcher_total
            if betterScratcher:
                while n > self.scratcher_total_rare2: # force a rare, according to settings
                    n = random.randint(1, self.scratcher_total)
            elif len(selected) == 1:
                while n > self.scratcher_total_rare1: # force a rare, for the salt
                    n = random.randint(1, self.scratcher_total)
            else:
                n = random.randint(1, self.scratcher_total)
            c = 0
            found = False
            for r in self.scratcher_loot:
                for item in self.scratcher_loot[r]:
                    if n <= c:
                        if item in selected:
                            n += r
                        else:
                            selected[item] = 0
                            found = True
                        break
                    else:
                        c += r
                if found: break
        
        # build the scratch grid
        hidden = "▄▄▄▄▄▄▄▄▄▄▄"
        grid = []
        win = ""
        keys = list(selected.keys())
        for x in keys: # add all our loots once
            grid.append([x, False])
            selected[x] = 1
        # add the first one twice (it's the winning one)
        grid.append([keys[0], False])
        grid.append([keys[0], False])
        selected[keys[0]] = 3
        win = keys[0]
        nofinal = False
        while len(grid) < 10: # fill the grid up to TEN times
            n = random.randint(1, len(keys)-1)
            if selected[keys[n]] < 2:
                grid.append([keys[n], False])
                selected[keys[n]] += 1
            elif len(grid) == 9: # 10 means final scratch so we stop at 9 and raise a flag if the chance arises
                grid.append(['', False])
                nofinal = True
                break
        while True: # shuffle the grid until we get a valid one
            random.shuffle(grid)
            if nofinal and grid[-1][0] == "":
                break
            elif not nofinal and grid[-1][0] == keys[0]:
                win = ""
                break
            await asyncio.sleep(0.001)

        # play the game
        win_flag = False
        reveal_count = 0
        fields = [{'name': "{}".format(self.bot.emote.get('1')), 'value':''}, {'name': "{}".format(self.bot.emote.get('2')), 'value':''}, {'name': "{}".format(self.bot.emote.get('3')), 'value':''}]
        pulled = {}
        msg = ""
        # main loop
        while True:
            # print the grid
            for i in range(0, 9):
                if i < 3: fields[i]['value'] = ''
                if grid[i][1] == False: fields[i%3]['value'] += "{}\n".format(hidden)
                else:
                    c = pulled[grid[i][0]]
                    if c == 3: fields[i%3]['value'] += "**{}**\n".format(grid[i][0])
                    elif c == 2: fields[i%3]['value'] += "__{}__\n".format(grid[i][0])
                    else: fields[i%3]['value'] += "{}\n".format(grid[i][0])
            # send the message
            if message is None:
                message = await ctx.reply(embed=self.bot.util.embed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, inline=True, footer=footer, fields=fields, color=self.color))
            else:
                await message.edit(embed=self.bot.util.embed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, inline=True, footer=footer, fields=fields, color=self.color))
            await asyncio.sleep(1)
            # win sequence
            if win_flag:
                if win == "": # final scratch must happens
                    win = grid[-1][0]
                    msg += "*The Final scratch...*\n"
                    await message.edit(embed=self.bot.util.embed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, inline=True, footer=footer, fields=fields, color=self.color))
                    await asyncio.sleep(2)
                msg += ":confetti_ball: :tada: **{}** :tada: :confetti_ball:".format(win)
                for i in range(0, 9): # update the grid
                    if i < 3: fields[i%3]['value'] = ''
                    c = pulled.get(grid[i][0], 0)
                    if grid[i][1] == False: fields[i%3]['value'] += "~~{}~~\n".format(grid[i][0])
                    elif c == 3: fields[i%3]['value'] += "**{}**\n".format(grid[i][0])
                    elif c == 2: fields[i%3]['value'] += "__{}__\n".format(grid[i][0])
                    else: fields[i%3]['value'] += "{}\n".format(grid[i][0])
                await message.edit(embed=self.bot.util.embed(author={'name':"{} scratched".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, inline=True, footer=footer, fields=fields, thumbnail='http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/' + self.scratcher_thumb.get(win, ''), color=self.color))
                await self.bot.util.clean(ctx, message, 45)
                return
            # next pull
            i = random.randint(0, 8)
            while grid[i][1] == True:
                i = random.randint(0, 8)
            grid[i][1] = True
            reveal_count += 1
            selected[grid[i][0]] -= 1
            pulled[grid[i][0]] = pulled.get(grid[i][0], 0) + 1
            if reveal_count == 9 or (selected[grid[i][0]] == 0 and grid[i][0] == win):
                win_flag = True

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['chests', 'rush'])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def chest(self, ctx):
        """Imitate the GBF treasure game from Summer 2020"""
        message = None
        loot = {
            'Murgleis':150, 'Benedia':150, 'Gambanteinn':150, 'Love Eternal':150, 'AK-4A':150, 'Reunion':150, 'Ichigo-Hitofuri':150, 'Taisai Spirit Bow':150, 'Unheil':150, 'Sky Ace':150, 'Ivory Ark':150, 'Blutgang':150, 'Eden':150, 'Parazonium':150, 'Ixaba':150, 'Blue Sphere':150, 'Certificus':150, 'Fallen Sword':150, 'Mirror-Blade Shard':150, 'Galilei\'s Insight':150, 'Purifying Thunderbolt':150, 'Vortex of the Void':150, 'Sacred Standard':150, 'Bab-el-Mandeb':150, 'Cute Ribbon':150, 'Kerak':150, 'Sunya':150, 'Fist of Destruction':150, 'Yahata\'s Naginata':150,
            'Ruler of Fate':150, 'Ancient Bandages':150, 'Gottfried':150, 'Acid Bolt Shooter':150, 'Mystic Spray Gun':150, 'Metal Destroyer':150, 'Gangsta Knife':150, 'Vagabond':150, 'Heavenly Fawn Bow':150, 'Another Sky':150,
            'Agni':150, 'Varuna':150, 'Titan':150, 'Zephyrus':150, 'Zeus':150, 'Hades':150, 'Shiva':150, 'Europa':150, 'Godsworn Alexiel':150, 'Grimnir':150, 'Lucifer':150, 'Bahamut':150, 'Michael':150, 'Gabriel':150, 'Uriel':150, 'Raphael':150, 'Metatron':150, 'Sariel':150, 'Belial':150,
            '10K Crystal':100,
            '3K Crystal':400,'Intricacy Ring x3':400,'Damascus Crystal x3':400, 'Premium 10-Part Ticket':400,
            'Intricacy Ring':500, 'Lineage Ring x2':500, 'Coronation Ring x3':500, 'Gold Moon x2':500,
            'Gold Moon':800, 'Silver Moon x5':800, 'Bronze Moon x10':800, 'Premium Draw Ticket':800, 'Gold Spellbook x3':800,
            'Half Elixir x10':1000, 'Soul Berry x10':1000, 
            "Satin Feather x10":1250, "Zephyr Feather x10":1250, "Untamed Flame x10":1250, "Rough Stone x10":1250, "Fresh Water Jug x10":1250, "Swirling Amber x10":1250, "Falcon Feather x10":1250, "Vermilion Stone x10":1250, "Hollow Soul x10":1250, "Lacrimosa x10":1250, "Foreboding Clover x10":1250, "Blood Amber x10":1250, "Antique Cloth x10":1250, 
            "White Dragon Scale x10":1250, "Champion Merit x10":1250, "Supreme Merit x10":1250, "Blue Sky Crystal x10":1250, "Rainbow Prism x10":1250, "Rubeus Centrum x10":1250, "Indicus Centrum x10":1250, "Luteus Centrum x10":1250, "Galbinus Centrum x10":1250, "Niveus Centrum x10":1250, "Ater Centrum x10":1250, "Fire Urn x10":1250, "Water Urn x10":1250, "Earth Urn x10":1250, "Wind Urn x10":1250, "Light Urn x10":1250, "Dark Urn x10":1250, "Horn of Bahamut x10":1250, "Primeval Horn x10":1250, "Legendary Merit":1250, 
            "Sword Stone x50":1000, "Dagger Stone x50":1000, "Spear Stone x50":1000, "Axe Stone x50":1000, "Staff Stone x50":1000, "Pistol Stone x50":1000, "Melee Stone x50":1000, "Bow Stone x50":1000, "Harp Stone x50":1000, "Katana Stone x50":1000, "Silver Centrum x5":1000, "Ultima Unit x3":1000, "Fire Quartz x50":1000, "Water Quartz x50":1000, "Earth Quartz x50":1000, "Wind Quartz x50":1000, "Light Quartz x50":1000, "Dark Quartz x50":1000, "Shiva Omega Anima x3":1000, "Europa Omega Anima x3":1000, "Alexiel Omega Anima x3":1000, "Grimnir Omega Anima x3":1000, "Metatron Omega Anima x3":1000, "Avatar Omega Anima x3":1000
        }

        mm = 0 # maximum random loot value
        rm = 0 # rare loot value
        for x in loot:
            mm += loot[x] # calculated here
            if x == 'Premium 10-Part Ticket': rm = mm

        results = []
        l = random.randint(0, 9)
        while len(results) < l:
            n = random.randint(1, mm)
            c = 0
            check = ""
            for x in loot:
                if n < c + loot[x]:
                    check = x
                    break
                else:
                    c += loot[x]
            if check != "":
                if n < rm and len(results) == l - 1: results.append(["**" + check + "**", -1])
                else: results.append([check, 0])

        while len(results) < 9: results.append([None, 0])
        random.shuffle(results)

        opened = 0
        game_over = False
        display_chest = True
        fields = [{'name': "{}".format(self.bot.emote.get('1')), 'value':''}, {'name': "{}".format(self.bot.emote.get('2')), 'value':''}, {'name': "{}".format(self.bot.emote.get('3')), 'value':''}]
        title = "{} is opening...".format(ctx.author.display_name)
        while True:
            for i in range(9):
                if i < 3: fields[i]['value'] = ''
                if results[i][1] == -3: fields[i%3]['value'] += "{0}{0}{0}{0}{0}{0}\n".format(self.bot.emote.get('red'))
                elif results[i][1] == -2: fields[i%3]['value'] += "{0}{0}{0}{0}{0}{0}\n".format(self.bot.emote.get('kmr'))
                elif results[i][1] <= 0 and display_chest: fields[i%3]['value'] += "{0}{0}{0}{0}{0}{0}\n".format(self.bot.emote.get('gold'))
                elif results[i][1] <= 0: fields[i%3]['value'] += "✖️\n"
                elif results[i][0] is None: fields[i%3]['value'] += "{0}{0}{0}{0}{0}{0}\n".format(self.bot.emote.get('kmr'))
                else: fields[i%3]['value'] += results[i][0] + "\n"

            if game_over:
                title = "{} opened".format(ctx.author.display_name)
            if message is None:
                message = await ctx.reply(embed=self.bot.util.embed(author={'name':title, 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            else:
                await message.edit(embed=self.bot.util.embed(author={'name':title, 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            if game_over:
                await self.bot.util.clean(ctx, message, 45)
                return
            await asyncio.sleep(1)

            while True:
                n = random.randint(0, 8)
                if results[n][1] <= 0:
                    if results[n][1] == -3:
                        results[n][1] = 1
                        opened += 1
                        game_over = True
                        break
                    elif results[n][1] < 0:
                        if l == opened + 1:
                            results[n][1] -= 1
                            display_chest = False
                            break
                    elif results[n][0] is None:
                        if l == opened:
                            results[n][1] = 1
                            game_over = True
                            display_chest = False
                            break
                    else:
                        results[n][1] = 1
                        opened += 1
                        if opened == 9:
                            game_over = True
                            display_chest = False
                        break
                await asyncio.sleep(0.001)


    """genLoto()
    Generate cards and winning numbers for the summer fortune minigame
    
    Returns
    --------
    tuple: Containing:
        - List of cards
        - List of tier winning digits
    """
    def genLoto(self):
        cards = []
        for i in range(0, 14):
            while True:
                if i < 10: c = str(10 * random.randint(0, 99) + i % 10).zfill(3) # generate unique last digit
                else: c = str(random.randint(0, 999)).zfill(3)
                if c not in cards:
                    cards.append(c)
                    break
        random.shuffle(cards)
        winning = []
        for c in [2, 2, 3, 2]:
            while True:
                a = [str(random.randint(0, 9)) for i in range(0, c)]
                bad = False
                for i in range(0, len(a)-1):
                    if a[i] in a[i+1:]:
                        bad = True
                        break
                if not bad:
                    break
            winning.append(list(''.join(a)))
        return cards, winning

    """printLoto()
    Generate the string and thumbnail for the summer fortune minigame
    
    Parameters
    ----------
    revealedCards: List of revealed cards
    revealedWinning: List of revealed winning digits
    prize: List of prize won currently
    total: If true, will print the total prize won
    
    Returns
    --------
    tuple: Containing:
        - Description string
        - Thumbnail url
    """
    def printLoto(self, revealedCards, revealedWinning, prize, total=False):
        desc = ''
        thumb = None
        if len(revealedWinning) > 0:
            desc += "The winning numbers are:\n"
            for i in range(0, len(revealedWinning)):
                desc += "**Tier {}**▫️{} ".format(4-i, ' '.join(revealedWinning[len(revealedWinning)-1-i]))
                for j in range(0, prize[3-i]): desc += ":confetti_ball:"
                desc += "\n"
        if len(revealedCards) > 0:
            desc += "Your cards are: "
            for c in revealedCards:
                desc += "**" + c + "**"
                if c is not revealedCards[-1]: desc += ", "
        if total:
            if sum(prize) == 0: desc += "\n{} You won nothing".format(self.bot.emote.get('kmr'))
            else:
                if prize[0] > 0:
                    desc += '\n:confetti_ball: '
                    thumb = 'http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/item/article/m/30041.jpg'
                elif prize[1] > 0:
                    desc += '\n:clap: '
                    thumb = 'http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/item/normal/m/gem.jpg'
                elif prize[2] > 0:
                    desc += '\n:hushed: '
                    thumb = 'http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/1040004600.jpg'
                elif prize[3] > 0:
                    desc += '\n:pensive: '
                    thumb = 'http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/item/article/m/30033.jpg'
                add_comma = False
                for i in range(0, 4):
                    if prize[3-i] > 0:
                        if add_comma: desc += ", "
                        desc += "**{}** Tier {}".format(prize[3-i], 4-i)
                        add_comma = True
                desc += " prizes"
                    
        return desc, thumb

    """checkLotoWin()
    Check which tier the card is elligible for
    (summer fortune minigame)
    
    Parameters
    ----------
    card: Card to compare
    winning: List of winning digits
    
    Returns
    --------
    int: Prize tier (0 = lost)
    """
    def checkLotoWin(self, card, winning):
        for i in range(0, 4):
            lost = False
            if i == 0: x = card
            elif i == 1: x = card[1:]
            elif i == 2: x = card[:2]
            elif i == 3: x = card[2]
            for c in x:
                if c not in winning[i]:
                    lost = True
                    break
            if not lost:
                return i + 1
        return 0

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['loto', 'lotto'])
    @commands.cooldown(1, 200, commands.BucketType.user)
    async def fortune(self, ctx):
        """Imitate the GBF summer fortune game from Summer 2021"""
        title = '{} is tempting fate...'.format(ctx.author.display_name)
        message = await ctx.reply(embed=self.bot.util.embed(author={'name':title, 'icon_url':ctx.author.avatar_url}, description="The winning numbers are...", color=self.color))
        cards, winning = await self.bot.do(self.genLoto)
        await asyncio.sleep(2)
        prize = [0, 0, 0, 0]
        desc, thumb = await self.bot.do(self.printLoto, [], winning, prize)
        await message.edit(embed=self.bot.util.embed(author={'name':title, 'icon_url':ctx.author.avatar_url}, description=desc, thumbnail=thumb, color=self.color))
        title = "{}'s fortune is".format(ctx.author.display_name)
        for i in range(0, len(cards)):
            tier = self.checkLotoWin(cards[:i+1][-1], winning)
            if tier != 0: prize[tier-1] += 1
            desc, thumb = await self.bot.do(self.printLoto, cards[:i+1], winning, prize, (i == len(cards)-1))
            await asyncio.sleep(0.5)
            await message.edit(embed=self.bot.util.embed(author={'name':title, 'icon_url':ctx.author.avatar_url}, description=desc, thumbnail=thumb, color=self.color))
        await self.bot.util.clean(ctx, message, 45)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def quota(self, ctx):
        """Give you your GW quota for the day"""
        if ctx.author.id in self.bot.data.config['ids'].get('branded', []):
            await ctx.reply(embed=self.bot.util.embed(title="{} {} is a bad boy".format(self.bot.emote.get('gw'), ctx.author.display_name), description="Your account is **restricted.**", thumbnail=ctx.author.avatar_url, color=self.color))
            return

        h = random.randint(800, 4000)
        m = random.randint(70, 180)
        c = random.randint(1, 100)

        if ctx.author.id == self.bot.data.config['ids'].get('wawi', -1):
            c = 12

        if c <= 3:
            c = random.randint(1, 110)
            if c <= 2:
                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), ctx.author.display_name), description="You got the **Eternal Battlefield Pass** 🤖\nCongratulations!!!\nYou will now revive GW over and ovḛ̸̛̠͕̑̋͌̄̎̍͆̆͑̿͌̇̇̕r̸̛̗̥͆͂̒̀̈́͑̑̊͐̉̎̚̚͝ ̵̨̛͔͎͍̞̰̠́͛̒̊̊̀̃͘ư̷͎̤̥̜̘͈̪̬̅̑͂̂̀̃̀̃̅̊̏̎̚͜͝ͅņ̴̢̛̛̥̮͖͉̻̩͍̱̓̽̂̂͌́̃t̵̞̦̿͐̌͗͑̀͛̇̚͝͝ỉ̵͉͕̙͔̯̯͓̘̬̫͚̬̮̪͋̉͆̎̈́́͛̕͘̚͠ͅļ̸̧̨̛͖̹͕̭̝͉̣̜͉̘͙̪͙͔͔̫̟̹̞̪̦̼̻̘͙̮͕̜̼͉̦̜̰̙̬͎͚̝̩̥̪̖͇̖̲̣͎̖̤̥͖͇̟͎̿̊͗̿̈̊͗̆̈́͋͊̔͂̏̍̔̒̐͋̄̐̄̅̇͐̊̈́̐͛͑̌͛̔͗̈́͌̀͑̌̅̉́̔̇́̆̉͆̄̂͂̃̿̏̈͛̇̒͆͗̈́̀̃̕̕͘̚̚͘͘͠͠͠͝͝͠͝͝ͅͅ ̴̢̛̛̛̯̫̯͕̙͙͇͕͕̪̩̗̤̗̺̩̬̞̞͉̱̊̽̇̉̏̃̑̋̋̌̎̾́̉́͌̿̐̆̒̾̆͒͛͌́͒̄͗͊͑̈́̑̐̂̿̋̊͊̈́̃̋̀̀̈̏̅̍̈͆̊̋͋̀̽͑̉̈́͘͘̕̕͝y̷̧̧̨̢̧̮̭̝̦͙͈͉̜͈̳̰̯͔͓̘͚̳̭͎̳̯͈͓̣͕͙̳̭̱͍͎͖̋͊̀͋͘͘ơ̸̢̗̖̹̹͖̣̫̝̞̦̘̙̭̮͕̘̱̆͋̓͗̾͐̉̏̀͂̄̎̂̈́͌͑̅̆̉̈̒͆̈̈̊͐̔̓̀̿̓̈́͝͝͝͠͝u̶̡̧̡̧̨̧̡̡̢̢̢̪̯͙͍̱̦̠̗̹̼̠̳̣͉̞̩̹͕̫͔͚̬̭̗̳̗̫̥̞̰̘̖̞̤͖̳̮̙͎͎̗̙̳͙͖͓̪̱̞͖̠̣̮̘͍̱̥̹͎͎̦̬̹̼̜͕͙͖̫̝̰̯̜̹̬̯͚͕̰̪̼͓̞̫̖̘͙̞͖̺̩͓̹̘̙̫̩̲̻̪̠̞̺͚̫̰̠̼̖̬͔̗̮͙̱̬̩̮̟͓̫̭̲̘̤͎̱̓̊̇́̀̏̏̾̀̄̆̒̂͐̌͂̈̂̓͋̌̓͘̕̕̚͜͜͜͝ͅͅͅͅŗ̷̡̧̨̢̢̢̧̡̡̧̡̢̧̨̨̡̧̛̛̛̬͚̮̜̟̣̤͕̼̫̪̗̙͚͉̦̭̣͓̩̫̞͚̤͇̗̲̪͕̝͍͍̫̞̬̣̯̤̮͉̹̫̬͕̫̥̱̹̲͔͔̪̖̱͔̹͈͔̳͖̩͕͚͓̤̤̪̤̩̰̬͙̞͙̘̯̮̫͕͚̙̜̼̩̰̻̞̺͈̝̝̖͎̻̹̞̥̰̮̥̙̠͔͎̤̲͎͍̟̥̞̗̰͓͍̞̹͍̬͎̲̬̞͈͉̼̥̝͈̼̠̫̙͖̪̼̲̯̲̫̼̺̘̗̘͚̤͓̯̦̣̬͒̑̒́͑͊̍̿̉̇̓̒̅̎͌̈́̐̽͋̏̒͂̈̒̃̿̓̇̈̿̊̎̈́͐̒͂͊̿̈́̿̅̏̀͐͛̎̍͑͂̈́̃̇̀̈͋̾̔̈́̽͌̿̍̇̅̏̋̑̈́̾̊͐̉̊̅͑̀͊̽̂̈́̽̓͗́̄͆̄͑͒̈́́͋̏͊͋̒͗̆̋̌̈̀͑͗̽͂̄̌̕͘͘̚͘̕̕͜͜͜͜͜͜͜͠͝͝͝͝͝͝ͅͅͅ ̷̧̡̧̨̢̧̨̡̨̧̛̛̛̛̮̭͇̣͓̙̺͍̟̜̞̫̪̘̼̞̜̠͇̗̮͕̬̥͓͔͈̟̦͇̥̖̭̝̱̗̠̘̝̹̖͓̝͇̖̫̯̩̞̞̯̲̤̱̻̤͇̲͍͈͓͖̹̗̟̲̪̪̟̩͙̪̝̮̘̽̋̍́̔̊̍̈́͂̌̽͒̆͐͊̏̐͑͛̓̆̈́͌̂͒͆̔̅̓̽͊̅́̾̽̓̏̆̀̀͌̾̀͒̓̇̊̀̐͛̌̋̈͑̇́̂̆̽̈̕̕̚̚͜͠ͅͅͅͅḑ̶̛̛̯͓̠̖͎̭̞̫͑̋̄̄̈̽̎̊͛̽͌̾̋̔̽̔̀̀͐̿̈́̀̃͐͂͆̈̃͑̀̋̑͊̃̆̓̾̎̅̀̆̓̏͊̆̔̈̅͛̍̎̓̀͛͒́̐͆̂̋̋͛̆̈͐͂̏̊̏̏̓̿̔͆̓̽̂̅͆̔͑̔̈̾̈̽̂̃̋̈́̾̎̈́̂̓̃̒͐͆̌̍̀͗̈́̑̌̚̕̕̚͠͠͝ę̴̧̨̨̨̢̨̢̧̧̧̨̧̛̛̛̛̛̛̛̺̪̹̘͈̣͔̜͓̥̥̟͇̱͚͖̠͙͙̱̞̣̤͚̣̟̫̬̟͓̺͙̬͚̹͓̗̬̼͇͙̻͍̖̙̥̩͔̜͕̖͕͔͚̳͙̩͇͙̺͔̲̱̙͉̝̠̤̝̭̮̩̦͇̖̳̞̞̖͎̙͙̲̮̠̣͍̪͙̰̣͉̘͉̦̖̳̫͖͖̘̖̮̲̱̪͕̳̫̫̞̪̜̞̬͙͖͍͖̦͉̯̟̖͇̩͚͙͔̳̫͗̈́̒̎͂̇̀͒̈́̃͐̉͛̾̑̆̃͐̈́̉͒̇̓̏̀͌̐͌̅̓͐́̿͒̅͑̍̓̈́̉̊́̉̀̔̊̍̽͛͛͆̓̈͋̉͋̿̉́̋̈̓̐̈́̔̃͆͗͛̏́̀̑͋̀̽̔̓̎̒̆̌̐̈́̓͂̐̋͊̌͑̓̈́̊̿͋̈́́̃̏̓̉͛͆̂͐͗͗̾̅̌̾͌̈́͊͘̕̚̕̚̚̕͘̕͜͜͜͜͜͜͜͠͝͝͠͝͝͠ͅͅa̸̡͔̯͎̟͙̖̗͔̺̰͇͚̭̲̭͕̫̜͉̯͕̅̈͋̒͋͂̐̕ͅţ̶̡̨̢̢̡̡̡̨̢̡̧̨̢̛̥̭̞͈̼̖͙͇̝̳͇̞̬͎̲̙̰̙̱̳̟̣̗̫̣͉͖̪̩͙̲͇͙̫̘͖̖̜̝̦̥̟̜̠͔̠͎̭͔̘͓͚̩͇͙͎͎̰̘̟̳̪͖̠̪̦̦̫̞̟̗̹̹̤͓͍̜̯͔̼̱̮̹͎͖͍̲͎̠͉̟͈̠̦̯̲̼̥̱̬̜͙̘͕̣̳͇̞͓̝͈̼̞̻͚̘̩̟̩̖̼͍̯̘͉͔̤̘̥̦͑̒͗̅̉̾͗̾̓̈́̍̉̈́͛̀͊̋̀͐̏̈́̀̀̍̇̀̀̈́̃̀̅͛̅̈́̇̽̆̌̈̄͆̄̂͂̔͗͌͊̽̿́͑̒̾̑̊̿͗́̇̋̊̄̀̍̓̆͂̆̔̏̍̑̔̊̾̎̆͛͑̓͒̈̎͌̓͗̀̿̓̃̔̈́͗̃̓̽̓̉̀͛͂̿́̀̌͊̆̋̀̓̇́̔̓͆̋̊̀̋͑́̔́̌̒̾̂̎̋̈́́̀͗̈́̈́́̾̈́͑͋̇͒̀͋͆͗̾͐̆̈́͂͐̈̐̓̍̈́̈̅̓͐̚̚̚̚̕͘̕͘̚̚̚͘͜͜͜͜͜͜͝͠͠͠͝͠ͅͅḥ̴̨̧̧̢̧̢̢̛̛̙̱͚̺̬̖̮̪͈̟͉̦̪̘̰̺̳̱̲͔̲̮̦̦̪̪̲̠͓͎͇͕̯̥͉͍̱̥͓̲̤̫̳̠̝͖̺̙͖͎͙̠͓̺̗̝̩͍͕͎̞͕̤̻̰̘͇͕̟̹̳͇͈͇̳̳̞̗̣͖̙͓̼̬̯͚͎̮͚̳̰͙̙̟̊͆͒͆͌̂̈́̀́̽̿͌̓́̐̑͌͋͆͊͑͛͑̀̋͐̏͌̑̀͛͗̀́̈̀̓̽̇̐̋͊̅͑̊͒̈́̀̀̔̀̇͗̆͑̅̌̑̈́͌̒̅̌̓͋͂̀̍̈́͐̈́̆̐̈́̍͛͂̔̐̎͂̎̇͑̈́̈́̎̉̈́́̒̒̆̌̃̓̈́͂̽̓̆̋̈̂̽̆̓̔͗̓̀̄̈́̂̏͗̐̔͘̕͘͘͜͜͜͜͠͠͝͠͠͝͝͝͠͠͝ͅͅ", thumbnail=ctx.author.avatar_url, color=self.color))
            elif c <= 6:
                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), ctx.author.display_name), description="You got a **Slave Pass** 🤖\nCongratulations!!!\nCall your boss and take a day off now!", footer="Full Auto and Botting are forbidden", thumbnail=ctx.author.avatar_url, color=self.color))
            elif c <= 16:
                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), ctx.author.display_name), description="You got a **Chen Pass** 😈\nCongratulations!!!\nYour daily honor or meat count must be composed only of the digit 6.", thumbnail=ctx.author.avatar_url, color=self.color))
            elif c <= 21:
                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), ctx.author.display_name), description="You got a **Carry Pass** 😈\nDon't stop grinding, continue until your Crew gets the max rewards!", thumbnail=ctx.author.avatar_url, color=self.color))
            elif c <= 26:
                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), ctx.author.display_name), description="You got a **Relief Ace Pass** 😈\nPrepare to relieve carries of their 'stress' after the day!!!", footer="wuv wuv", thumbnail=ctx.author.avatar_url, color=self.color))
            else:
                final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), ctx.author.display_name), description="You got a **Free Leech Pass** 👍\nCongratulations!!!", thumbnail=ctx.author.avatar_url, color=self.color))
            await self.bot.util.clean(ctx, final_msg, 40)
            return
        elif c == 3:
            h = h * random.randint(50, 80)
            m = m * random.randint(50, 80)
        elif c <= 6:
            h = h * random.randint(20, 30)
            m = m * random.randint(20, 30)
        elif c <= 9:
            h = h * random.randint(8, 15)
            m = m * random.randint(8, 15)
        elif c == 10:
            h = h // random.randint(30, 50)
            m = m // random.randint(30, 50)
        elif c <= 12:
            h = h // random.randint(10, 20)
            m = m // random.randint(10, 20)
        elif c <= 14:
            h = h // random.randint(3, 6)
            m = m // random.randint(3, 6)
        h = h * 100000
        m = m * 10

        if ctx.author.id == self.bot.data.config['ids'].get('chen', -1):
            c = random.randint(3, 8)
            if c == 3: h = 666
            elif c == 4: h = 6666
            elif c == 5: h = 66666
            elif c == 6: h = 666666
            elif c == 7: h = 6666666
            elif c == 8: h = 66666666
            c = random.randint(1, 4)
            if c == 1: m = 6
            elif c == 2: m = 66
            elif c == 3: m = 666
            elif c == 4: m = 6666

        final_msg = await ctx.reply(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), ctx.author.display_name), description="**Honor:** {:,}\n**Meat:** {:,}".format(h, m), thumbnail=ctx.author.avatar_url, color=self.color))
        await self.bot.util.clean(ctx, final_msg, 40)

    """randint()
    Generate a simple pseudo random number based on the seed value
    
    Parameters
    ----------
    seed: Integer used as the seed
    
    Returns
    ----------
    int: Pseudo random value which you can use as the next seed
    """
    def randint(self, seed):
        return ((seed * 1103515245) % 4294967296) + 12345

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(2, 7, commands.BucketType.user)
    async def character(self, ctx):
        """Generate a random GBF character"""
        seed = (ctx.author.id + int(datetime.utcnow().timestamp()) // 86400) # based on user id + day
        values = {
            'Rarity' : [['SSR', 'SR', 'R'], 3, True, None], # random strings, modulo to use, bool to use emote.get, seed needed to enable
            'Race' : [['Human', 'Erun', 'Draph', 'Harvin', 'Primal', 'Other'], 6, False, None],
            'Element' : [['fire', 'water', 'earth', 'wind', 'light', 'dark'], 6, True, None],
            'Gender' : [['Unknown', '\♂️', '\♀️'], 3, False, None],
            'Series' : [['Summer', 'Yukata', 'Grand', 'Holiday', 'Halloween', 'Valentine'], 30, True, 6]
        }
        msg = ""
        rarity_mod = 0
        for k in values:
            v = seed % values[k][1]
            if k == "Rarity": rarity_mod = 7 - 2 * v
            if values[k][3] is not None and v >= values[k][3]:
                continue
            if values[k][2]: msg += "**{}** ▫️ {}\n".format(k, self.bot.emote.get(values[k][0][v]))
            else: msg += "**{}** ▫️ {}\n".format(k, values[k][0][v])
            seed = self.randint(seed)
        msg += "**Rating** ▫️ {:.1f}".format(rarity_mod + (seed % 31) / 10)

        msg = await ctx.reply(embed=self.bot.util.embed(author={'name':"{}'s daily character".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color))
        await self.bot.util.clean(ctx, msg, 30)

    @commands.command(no_pm=True, hidden=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def xil(self, ctx):
        """Generate a random element for Xil"""
        g = random.Random()
        elems = ['fire', 'water', 'earth', 'wind', 'light', 'dark']
        g.seed(int((int(datetime.utcnow().timestamp()) // 86400) * (1.0 + 1.0/4.2)))
        e = g.choice(elems)

        final_msg = await ctx.send(embed=self.bot.util.embed(title="Today, Xil's main element is", description="{} **{}**".format(self.bot.emote.get(e), e.capitalize()), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 30)

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
            msg = "`{}` = **{}**".format(m[0], self.bot.calc.evaluate(m[0], d))
            if len(d) > 0:
                msg += "\nwith:\n"
                for k in d:
                    msg += "{} = {}\n".format(k, d[k])
            await ctx.reply(embed=self.bot.util.embed(title="Calculator", description=msg, color=self.color))
        except Exception as e:
            await ctx.reply(embed=self.bot.util.embed(title="Error", description=str(e), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['leek', 'leaks', 'leeks'])
    async def leak(self, ctx):
        """Do nothing"""
        await self.bot.util.react(ctx.message, '✅') # white check mark