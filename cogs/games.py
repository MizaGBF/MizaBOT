import disnake
from disnake.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
from views.roll_tap import Tap
from views.scratcher import Scratcher
from views.chest_rush import ChestRush
from views.join_game import JoinGame
from views.tictactoe import TicTacToe
from views.connectfour import ConnectFour
from views.battleship import BattleShip
from views.blackjack import Blackjack
from views.poker import Poker
from views.rockpaperscissor import RPS

# ----------------------------------------------------------------------------------------------------------------
# Games Cog
# ----------------------------------------------------------------------------------------------------------------
# Fun commands
# ----------------------------------------------------------------------------------------------------------------

class Games(commands.Cog):
    """Granblue-themed (or not) Games and more."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xeb6b34
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
        self.scratcher_total = 0
        self.scratcher_total_rare1 = 0
        self.scratcher_total_rare2 = 0
        rare_divider1 = 'Murgleis'
        rare_divider2 = 'Crystals x3000'
        for r in self.scratcher_loot:
            self.scratcher_total += r * len(self.scratcher_loot[r])
            if self.scratcher_loot[r][0] == rare_divider1: self.scratcher_total_rare1 = self.scratcher_total
            if self.scratcher_loot[r][0] == rare_divider2: self.scratcher_total_rare2 = self.scratcher_total
        
        self.scam = [(2000, 'Sunlight Stone', 'evolution/s/20014.jpg'), (2000, 'Damascus Ingot', 'evolution/s/20005.jpg'), (6000, 'Damascus Crystal x2', 'article/s/203.jpg'), (5000, 'Brimstone Earrings x2', 'npcaugment/s/11.jpg'), (5000, 'Permafrost Earrings x2', 'npcaugment/s/12.jpg'), (5000, 'Brickearth Earrings x2', 'npcaugment/s/13.jpg'), (5000, 'Jetstream Earrings x2', 'npcaugment/s/14.jpg'), (5000, 'Sunbeam Earrings x2', 'npcaugment/s/15.jpg'), (5000, 'Nightshade Earrings x2', 'npcaugment/s/16.jpg'), (5000, 'Intracacy Ring', 'npcaugment/s/3.jpg'), (5000, 'Meteorite x10', 'article/s/137.jpg'), (5000, 'Abyssal Wing x5', 'article/s/555.jpg'), (5000, 'Tears of the Apocalypse x10', 'article/s/538.jpg'), (4000, 'Ruby Awakening Orb x2', 'npcarousal/s/1.jpg'), (4000, 'Sapphire Awakening Orb x2', 'npcarousal/s/2.jpg'), (4000, 'Citrine  Awakening Orb x2', 'npcarousal/s/3.jpg'), (4000, 'Sephira Stone x10', 'article/s/25000.jpg'), (4000, 'Weapon Plus Mark x30', 'bonusstock/s/1.jpg'), (4000, 'Summon Plus Mark x30', 'bonusstock/s/2.jpg'), (4000, 'Gold Moon x2', 'article/s/30033.jpg'), (4000, 'Half Elixir x100', 'normal/s/2.jpg'), (4000, 'Soul Berry x300', 'normal/s/5.jpg')]
        self.scam_rate = 0
        for r in self.scam:
            self.scam_rate += r[0]

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
            gacha_data = self.bot.get_cog('GranblueFantasy').getCurrentGacha()[1]
            if len(gacha_data['list']) == 0: raise Exception()
            data = gacha_data['list']
            rateups = []
            # build a list of rate up
            for k in gacha_data['rateup']:
                if k == "zodiac": continue
                if len(gacha_data['rateup'][k]) > 0:
                    for r in gacha_data['rateup'][k]:
                        if r not in rateups: rateups.append(r)
            ssrrate = int(gacha_data['ratio'][0])
            extended = True
        except:
            data = [{}, {'rate':15}, {'rate':3}]
            rateups = None
            ssrrate = 3
            extended = False
        return data, rateups, ssrrate, extended

    """checkLegfest()
    Check the provided parameter and the real gacha to determine if we will be using a 6 or 3% SSR rate
    
    Parameters
    ----------
    selected: Integer, selected value by the user (-1 default, 0 is 3%, anything else is 6%)
    
    Returns
    --------
    bool: True if 6%, False if 3%
    """
    def checkLegfest(self, selected):
        match selected:
            case 0:
                return False
            case -1:
                try:
                    return (self.bot.data.save['gbfdata']['gacha']['ratio'][0] == '6')
                except:
                    return False
            case _:
                return True

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
                        if r == 2 and rate in rateups: last = "**" + self.bot.util.formatGachaItem(item) + "**"
                        else: last = self.bot.util.formatGachaItem(item)
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
    inter: The command interaction
    titles: The titles used in the message. Second string is for the final message
    rmode: Display type = 0 for the single roll mode, 1 for the memeroll mode, 2 for the ten roll mode and 3 or more for anything else (spark, gachapin, ...)
    message: The message to process
    """
    async def _roll(self, inter, titles:tuple=("{}", "{}"), rmode:int=-1, **rollOptions):
        if rmode < 0: raise Exception('Invalid _roll() rmode {}'.format(rmode)) # invalid mode
        await inter.response.defer()
        result = await self.bot.do(self.gachaRoll, **rollOptions) # do the rolling
        footer = "{}% SSR rate".format(result['rate']) # message footer
        if rollOptions.get('mode', '') == 'memerollB': footer += " ▫️ until rate up"
        
        # select crystal image
        if (100 * result['detail'][2] / len(result['list'])) >= result['rate']: crystal = random.choice(['https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png', 'https://media.discordapp.net/attachments/614716155646705676/761969229095632916/3_s.png'])
        elif (100 * result['detail'][1] / len(result['list'])) >= result['rate']: crystal = 'https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png'
        else: crystal = random.choice(['https://media.discordapp.net/attachments/614716155646705676/761969231323070494/0_s.png', 'https://media.discordapp.net/attachments/614716155646705676/761976275706445844/1_s.png'])

        # startup msg
        view = Tap(self.bot, owner_id=inter.author.id)
        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[0].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, image=crystal, color=self.color, footer=footer), view=view)
        await view.wait()

        # display result
        if rmode == 0: # single roll mode
            r = result['list'][0]
            if result['extended']:
                rid = await self.bot.do(self.bot.util.search_wiki_for_id, '>'.join(r[1].split('>')[1:])) # retrieve the id from the wiki
                if rid is None: thumb = None # and try to make a thumbnail
                elif rid.startswith('1'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg".format(rid)
                elif rid.startswith('2'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(rid)
                else: thumb = None
                # post
                await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="{}{}".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(r[0])), r[1]), color=self.color, footer=footer, thumbnail=thumb), view=None)
            else:
                await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="{}".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(r[0]))), color=self.color, footer=footer), view=None)
        elif rmode == 1: # memeroll mode
            counter = [0, 0, 0]
            text = ""
            best = [-1, ""]
            for i, v in enumerate(result['list']):
                if i > 0 and i % 3 == 0:
                    await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[0].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="{} {} ▫️ {} {} ▫️ {} {}\n{}".format(counter[2], self.bot.emote.get('SSR'), counter[1], self.bot.emote.get('SR'), counter[0], self.bot.emote.get('R'), text), color=self.color, footer=footer), view=None)
                    await asyncio.sleep(1)
                    text = ""
                if result['extended']:
                    # store what looks like the best roll
                    if v[0] > best[0] or (v[0] == best[0] and '**' in v[1]):
                        best = [v[0], v[1].replace('**', '')]
                        if '**' in v[1]: best[0] += 1
                    text += "{} {}\n".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(v[0])), v[1])
                else:
                    text += "{} ".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(v[0])))
                counter[v[0]] += 1
            if best[0] != -1: # make a thumbnail
                rid = await self.bot.do(self.bot.util.search_wiki_for_id, '>'.join(best[1].split('>')[1:]))
                if rid is None: thumb = None
                elif rid.startswith('1'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg".format(rid)
                elif rid.startswith('2'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(rid)
                else: thumb = None
            title = titles[1].format(inter.author.display_name, len(result['list'])) if (len(result['list']) < 300) else "{} sparked".format(inter.author.display_name)
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':title, 'icon_url':inter.author.display_avatar}, description="{} {} ▫️ {} {} ▫️ {} {}\n{}".format(counter[2], self.bot.emote.get('SSR'), counter[1], self.bot.emote.get('SR'), counter[0], self.bot.emote.get('R'), text), color=self.color, footer=footer, thumbnail=thumb), view=None)
        elif rmode == 2: # ten roll mode
            if result['extended']:
                best = [-1, ""]
                thumb = None
                for i in range(0, 11):
                    msg = ""
                    for j in range(0, i):
                        if j >= 10: break
                        # check for best roll
                        if result['list'][j][0] > best[0] or (result['list'][j][0] == best[0] and '**' in result['list'][j][1]):
                            best = [result['list'][j][0], result['list'][j][1].replace('**', '')]
                            if '**' in result['list'][j][1]: best[0] += 1
                        # write
                        msg += "{}{} ".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(result['list'][j][0])), result['list'][j][1])
                        if j % 2 == 1: msg += "\n"
                    for j in range(i, 10):
                        msg += '{}'.format(self.bot.emote.get('crystal{}'.format(result['list'][j][0])))
                        if j % 2 == 1: msg += "\n"
                    if i == 10 and best[0] != -1: # make the thumbnail from best roll
                        rid = await self.bot.do(self.bot.util.search_wiki_for_id, '>'.join(best[1].split('>')[1:]))
                        if rid is None: thumb = None
                        elif rid.startswith('1'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg".format(rid)
                        elif rid.startswith('2'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(rid)
                        else: thumb = None
                    await asyncio.sleep(0.7)
                    await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer, thumbnail=thumb), view=None)
            else:
                msg = ""
                i = 0
                for i in range(len(result['list'])):
                    r = result['list'][i][0]
                    if i == 5: msg += '\n'
                    if r == 2: msg += '{}'.format(self.bot.emote.get('SSR'))
                    elif r == 1: msg += '{}'.format(self.bot.emote.get('SR'))
                    else: msg += '{}'.format(self.bot.emote.get('R'))
                await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer), view=None)
        else: # others
            count = len(result['list'])
            rate = (100*result['detail'][2]/count)
            msg = ""
            thumb = None
            if result['extended']:
                best = [-1, ""]
                rolls = self.getSSRList(result)
                for r in rolls: # check for best roll
                    if best[0] < 3 and '**' in r: best = [3, r.replace('**', '')]
                    elif best[0] < 2: best = [2, r]
                if best[0] != -1: # make thumbnail
                    rid = await self.bot.do(self.bot.util.search_wiki_for_id, '>'.join(best[1].split('>')[1:]))
                    if rid is None: thumb = None
                    elif rid.startswith('1'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg".format(rid)
                    elif rid.startswith('2'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(rid)
                    else: thumb = None
                if len(rolls) > 0:
                    msg = "{} ".format(self.bot.emote.get('SSR'))
                    for item in rolls:
                        msg += item
                        if rolls[item] > 1: msg += " x{}".format(rolls[item])
                        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name, count), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer), view=None)
                        await asyncio.sleep(0.75)
                        msg += " "
            if rollOptions.get('mode', '') == 'gachapin': amsg = "Gachapin stopped after **{}** rolls\n".format(len(result['list']))
            elif rollOptions.get('mode', '') == 'mukku': amsg = "Mukku stopped after **{}** rolls\n".format(len(result['list']))
            else: amsg = ""
            msg = "{}{:} {:} ▫️ {:} {:} ▫️ {:} {:}\n{:}\n**{:.2f}%** SSR rate".format(amsg, result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), msg, rate)
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name, count), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer, thumbnail=thumb), view=None)
        await self.bot.util.clean(inter, 40)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 15, commands.BucketType.user)
    @commands.max_concurrency(10, commands.BucketType.default)
    async def roll(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    @roll.sub_command()
    async def single(self, inter: disnake.GuildCommandInteraction, double : int = commands.Param(description='0 to force 3%, 1 to force 6%, leave blank for default', default=-1, ge=-1, le=1)):
        """Simulate a single draw"""
        await self._roll(inter, ("{} did a single roll...", "{} did a single roll"), 0, count=1, mode='single', legfest=self.checkLegfest(double))

    @roll.sub_command()
    async def ten(self, inter: disnake.GuildCommandInteraction, double : int = commands.Param(description='0 to force 3%, 1 to force 6%, leave blank for default', default=-1, ge=-1, le=1)):
        """Simulate a ten draw"""
        await self._roll(inter, ("{} did ten rolls...", "{} did ten rolls"), 2, count=10, mode='ten', legfest=self.checkLegfest(double))

    @roll.sub_command()
    async def spark(self, inter: disnake.GuildCommandInteraction, double : int = commands.Param(description='0 to force 3%, 1 to force 6%, leave blank for default', default=-1, ge=-1, le=1)):
        """Simulate a spark"""
        await self._roll(inter, ("{} is sparking...", "{} sparked"), 3, count=300, mode='ten', legfest=self.checkLegfest(double))

    @roll.sub_command()
    async def count(self, inter: disnake.GuildCommandInteraction, num : int = commands.Param(description='Number of rolls', ge=1, le=600), double : int = commands.Param(description='0 to force 3%, 1 to force 6%, leave blank for default', default=-1, ge=-1, le=1)):
        """Simulate a specific amount of draw"""
        await self._roll(inter, ("{}" + " is rolling {} times...".format(num), "{} " + "rolled {} times".format(num)), 3, count=num, mode='ten', legfest=self.checkLegfest(double))

    @roll.sub_command()
    async def gachapin(self, inter: disnake.GuildCommandInteraction, double : int = commands.Param(description='0 to force 3%, 1 to force 6%, leave blank for default', default=-1, ge=-1, le=1)):
        """Simulate a Gachapin Frenzy"""
        await self._roll(inter, ("{} is rolling the Gachapin...", "{} rolled the Gachapin"), 3, count=300, mode='gachapin', legfest=self.checkLegfest(double))

    @roll.sub_command()
    async def mukku(self, inter: disnake.GuildCommandInteraction):
        """Simulate a Mukku Frenzy"""
        await self._roll(inter, ("{} is rolling the Mukku...", "{} rolled the Mukku"), 3, count=300, mode='mukku')

    @roll.sub_command()
    async def supermukku(self, inter: disnake.GuildCommandInteraction):
        """Simulate a Super Mukku Frenzy"""
        await self._roll(inter, ("{} is rolling the Supper Mukku...", "{} rolled the Super Mukku"), 3, count=300, mode='supermukku')

    @roll.sub_command()
    async def memeroll(self, inter: disnake.GuildCommandInteraction, double : int = commands.Param(description='0 to force 3%, 1 to force 6%, leave blank for default', default=-1, ge=-1, le=1), rateup : str = commands.Param(description='Input anything to roll until a rate up SSR', default="")):
        """Simulate rolls until a SSR"""
        await self._roll(inter, (("{} is memerolling until a rate up SSR..." if rateup != "" else "{} is memerolling..."), ("{} memerolled {} times until a rate up SSR" if rateup != "" else "{} memerolled {} times")), 1, mode=('memerollB' if rateup != "" else 'memerollA'), legfest=self.checkLegfest(double))

    @roll.sub_command()
    async def srssr(self, inter: disnake.GuildCommandInteraction, double : int = commands.Param(description='0 to force 3%, 1 to force 6%, leave blank for default', default=-1, ge=-1, le=1)):
        """Simulate a SR/SSR Ticket draw"""
        await self._roll(inter, ("{} is using a SR/SSR ticket...", "{} used a SR/SSR ticket"), 0, count=1, mode='srssr', legfest=self.checkLegfest(double))

    """getRoulette()
    Return the result of a roulette part
    
    Parameters
    ----------
    count: Integer, number of rolls to do
    mode: String, gacha mode
    double: Integer, value for checkLegfest
    
    Returns
    --------
    typle:
        - result: list of rolls
        - rate: SSR rate used
        - tmp: string containing the output
        - count: number of R, SR and SSR rolled
        - best: best ssr we got
    """
    def getRoulette(self, count, mode, double):
        result = self.gachaRoll(count=count, mode=mode, legfest=self.checkLegfest(double))
        footer = "{}% SSR rate".format(result['rate'])
        count = len(result['list'])
        rate = (100*result['detail'][2]/count)
        tmp = ""
        best = [-1, None]
        if result['extended']:
            ssrs = self.getSSRList(result)
            for r in ssrs: # best roll check
                if best[0] < 3 and '**' in r: best = [3, r.replace('**', '')]
                elif best[0] < 2: best = [2, r]
            if len(ssrs) > 0: # make the text
                tmp = "\n{} ".format(self.bot.emote.get('SSR'))
                for item in ssrs:
                    tmp += item
                    if ssrs[item] > 1: tmp += " x{}".format(ssrs[item])
                    tmp += ", "
                tmp = tmp[:-2]
        return result, rate, tmp, count, best

    @roll.sub_command()
    async def roulette(self, inter: disnake.GuildCommandInteraction, double : int = commands.Param(description='0 to force 3%, 1 to force 6%, leave blank for default', default=-1, ge=-1, le=1)):
        """Imitate the GBF roulette"""
        await inter.response.defer()
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
        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"{} is spinning the Roulette".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer))
        if not enableJanken and state < 2: state = 1
        running = True
        prev_best = [-1, None]
        thumb = None
        while running:
            await asyncio.sleep(2)
            match state:
                case 0: # RPS
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
                case 1: # normal rolls
                    result, rate, tmp, count, best = await self.bot.do(self.getRoulette, roll, 'ten', double)
                    if best[0] > prev_best[0]:
                        prev_best = best
                        if best[0] != -1: # update thumbnail
                            rid = await self.bot.do(self.bot.util.search_wiki_for_id, '>'.join(best[1].split('>')[1:]))
                            if rid is None: thumb = None
                            elif rid.startswith('1'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg".format(rid)
                            elif rid.startswith('2'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(rid)
                            else: thumb = None
                    footer = "{}% SSR rate".format(result['rate'])
                    msg += "{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                    if superFlag: state = 4
                    else: running = False
                case 2: # gachapin
                    result, rate, tmp, count, best = await self.bot.do(self.getRoulette, 300, 'gachapin', double)
                    if best[0] > prev_best[0]:
                        prev_best = best
                        if best[0] != -1: # update thumbnail
                            rid = await self.bot.do(self.bot.util.search_wiki_for_id, '>'.join(best[1].split('>')[1:]))
                            if rid is None: thumb = None
                            elif rid.startswith('1'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg".format(rid)
                            elif rid.startswith('2'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(rid)
                            else: thumb = None
                    footer = "{}% SSR rate".format(result['rate'])
                    msg += "Gachapin ▫️ **{}** rolls\n{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(count, result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                    if count == 10 and random.randint(1, 100) < 99: state = 3
                    elif count == 20 and random.randint(1, 100) < 60: state = 3
                    elif count == 30 and random.randint(1, 100) < 30: state = 3
                    else: running = False
                case 3:
                    result, rate, tmp, count, best = await self.bot.do(self.getRoulette, 300, 'mukku', double)
                    if best[0] > prev_best[0]:
                        prev_best = best
                        if best[0] != -1: # update thumbnail
                            rid = await self.bot.do(self.bot.util.search_wiki_for_id, '>'.join(best[1].split('>')[1:]))
                            if rid is None: thumb = None
                            elif rid.startswith('1'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg".format(rid)
                            elif rid.startswith('2'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(rid)
                            else: thumb = None
                    msg += ":confetti_ball: Mukku ▫️ **{}** rolls\n{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(count, result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                    if doubleMukku:
                        if random.randint(1, 100) < 25: pass
                        else: running = False
                        doubleMukku = False
                    else:
                        running = False
                case 4:
                    result, rate, tmp, count, best = await self.bot.do(self.getRoulette, 300, 'supermukku', double)
                    if best[0] > prev_best[0]:
                        prev_best = best
                        if best[0] != -1: # update thumbnail
                            rid = await self.bot.do(self.bot.util.search_wiki_for_id, '>'.join(best[1].split('>')[1:]))
                            if rid is None: thumb = None
                            elif rid.startswith('1'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg".format(rid)
                            elif rid.startswith('2'): thumb = "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg".format(rid)
                            else: thumb = None
                    msg += ":confetti_ball: **Super Mukku** ▫️ **{}** rolls\n{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(count, result['detail'][2], self.bot.emote.get('SSR'), result['detail'][1], self.bot.emote.get('SR'), result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                    running = False
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"{} spun the Roulette".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer, thumbnail=thumb))
        await self.bot.util.clean(inter, 45)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.max_concurrency(15, commands.BucketType.default)
    async def game(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    @game.sub_command()
    async def scratch(self, inter: disnake.GuildCommandInteraction):
        """Imitate the GBF scratch game from Anniversary 2020"""
        await inter.response.defer()
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

        # scratcher generation
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
        grid = []
        keys = list(selected.keys())
        for x in keys: # add all our loots once
            grid.append(x)
            selected[x] = 1
        # add the first one twice (it's the winning one)
        grid.append(keys[0])
        grid.append(keys[0])
        selected[keys[0]] = 3
        nofinal = False
        while len(grid) < 10: # fill the grid up to TEN times
            n = random.randint(1, len(keys)-1)
            if selected[keys[n]] < 2:
                grid.append(keys[n])
                selected[keys[n]] += 1
            elif len(grid) == 9: # 10 means final scratch so we stop at 9 and raise a flag if the chance arises
                grid.append('')
                nofinal = True
                break
        while True: # shuffle the grid until we get a valid one
            random.shuffle(grid)
            if nofinal and grid[-1] == "":
                break
            elif not nofinal and grid[-1] == keys[0]:
                break
            await asyncio.sleep(0.001)

        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"{} is scratching...".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="Click to play the game", footer=footer, color=self.color), view=Scratcher(self.bot, inter.author.id, grid, self.scratcher_thumb, self.color, footer))
        await self.bot.util.clean(inter, 45)

    @game.sub_command()
    async def chestrush(self, inter: disnake.GuildCommandInteraction):
        """Imitate the GBF treasure game from Summer 2020"""
        await inter.response.defer()
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
        l = random.randint(1, 9)
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
                if n < rm and len(results) == l - 1: results.append("###" + check) # special chest
                elif n < rm: results.append("$$$" + check) # rare loot
                else: results.append(check) # normal loot
        results.reverse()

        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':'{} is opening...'.format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, color=self.color), view=ChestRush(self.bot, inter.author.id, results, self.color))
        await self.bot.util.clean(inter, 45)

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
        for i in range(0, 13):
            if i < 10: c = str(10 * random.randint(0, 99) + i % 10).zfill(3) # generate unique last digit
            else: c = str(random.randint(0, 999)).zfill(3)
            cards.append(c)
            if len(cards) == 10: random.shuffle(cards)
        winning = [[], [], [], []]
        patterns = [[3, 2], [2, 2], [2, 3], [1, 2]]
        for i, v in enumerate(patterns):
            pad = '{:<0' + str(v[0]+1) + 'd}'
            pad = int(pad.format(1))
            for j in range(0, v[1]):
                while True:
                    c = str(random.randint(0, pad-1)).zfill(v[0])
                    if c not in winning[i]:
                        winning[i].append(c)
                        break
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
                desc += "**Tier {}**▫️".format(4-i)
                match i:
                    case 0: desc += "Last Digit▫️" # tier 4
                    case 1: desc += "First Two▫️" # tier 3
                    case 2: desc += "Last Two▫️" # tier 2
                desc += "{} ".format(', '.join(revealedWinning[len(revealedWinning)-1-i]))
                for j in range(0, prize[3-i]): desc += ":confetti_ball:"
                desc += "\n"
        if len(revealedCards) > 0:
            desc += "Your cards are: "
            for c in revealedCards:
                desc += c
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
            match i:
                case 0: x = card
                case 1: x = card[1:]
                case 2: x = card[:2]
                case 3: x = card[2]
            if x in winning[i]:
                return i + 1
        return 0

    @game.sub_command()
    async def fortune(self, inter: disnake.GuildCommandInteraction, usercards : str = commands.Param(description='List your cards here', default="")):
        """Imitate the GBF summer fortune game from Summer 2021"""
        title = '{} is tempting fate...'.format(inter.author.display_name)
        await inter.response.send_message(embed=self.bot.util.embed(author={'name':title, 'icon_url':inter.author.display_avatar}, description="The winning numbers are...", color=self.color))
        cards, winning = await self.bot.do(self.genLoto)
        cvt = []
        usercards = usercards.split(" ")
        for c in usercards:
            try:
                if c == "": continue
                if len(c) > 3 or int(c) < 0: raise Exception()
            except:
                cvt = []
                break
            cvt.append(c.zfill(3))
            if len(cvt) >= 20: break
        if len(cvt) != 0: cards = cvt
        await asyncio.sleep(2)
        prize = [0, 0, 0, 0]
        desc, thumb = await self.bot.do(self.printLoto, [], winning, prize)
        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':title, 'icon_url':inter.author.display_avatar}, description=desc, thumbnail=thumb, color=self.color))
        title = "{}'s fortune is".format(inter.author.display_name)
        for i in range(0, len(cards)):
            tier = self.checkLotoWin(cards[:i+1][-1], winning)
            if tier != 0:
                prize[tier-1] += 1
                cards[i] = '**'+cards[i]+'**'
            desc, thumb = await self.bot.do(self.printLoto, cards[:i+1], winning, prize, (i == len(cards)-1))
            await asyncio.sleep(0.5)
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':title, 'icon_url':inter.author.display_avatar}, description=desc, thumbnail=thumb, color=self.color))
        await self.bot.util.clean(inter, 45)

    @game.sub_command()
    async def deal(self, inter: disnake.GuildCommandInteraction):
        """Deal a random poker hand"""
        hand = []
        while len(hand) < 5:
            card = str(random.randint(2, 14)) + random.choice(["D", "S", "H", "C"])
            if card not in hand:
                hand.append(card)
        await inter.response.send_message(embed=self.bot.util.embed(author={'name':"{}'s hand".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="🎴, 🎴, 🎴, 🎴, 🎴", color=self.color))
        for x in range(0, 5):
            await asyncio.sleep(1)
            # check result
            msg = ""
            for i in range(len(hand)):
                if i > x: msg += "🎴"
                else: msg += Poker.valueNsuit2head(hand[i])
                if i < 4: msg += ", "
                else: msg += "\n"
            if x == 4:
                await asyncio.sleep(2)
                msg += (await self.bot.do(Poker.checkPokerHand, hand))[1]
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"{}'s hand".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color))
        await self.bot.util.clean(inter, 45)

    @game.sub_command()
    async def poker(self, inter: disnake.GuildCommandInteraction, max_round : int = commands.Param(description="Number of rounds to play", ge=1, le=5, default=1)):
        """Play a poker mini-game with other people (2 to 6 players)"""
        await inter.response.defer()
        players = [inter.author]
        view = JoinGame(self.bot, players, 6)
        desc = "**" + str(max_round) + "** Round(s)\nStarting in {}s\n{}/6 players"
        embed = self.bot.util.embed(title="♠️ Multiplayer Poker ♥️", description=desc.format(40, 1), color=self.color)
        await inter.edit_original_message(embed=embed, view=view)
        msg = await inter.original_message()
        self.bot.doAsync(view.updateTimer(msg, embed, desc, 40))
        await view.wait()
        if len(players) == 1:
            await inter.edit_original_message(embed=self.bot.util.embed(title="♠️ Multiplayer Poker ♥️", description="Error, at least two Players are required", color=self.color))
            await self.bot.util.clean(inter, 60)
        else:
            await msg.delete()
            random.shuffle(players) # randomize the player order
            win_tracker = {} # track how many wins each player got
            for p in players: # initialize
                win_tracker[p.id] = [(p.display_name if len(p.display_name) <= 10 else p.display_name[:10] + "..."), 0]
            for i in range(0, max_round): # for loop, the game is composed of 3 rounds
                embed = self.bot.util.embed(title="♠️ Multiplayer Poker ♥️ ▫️ Round {}/{}".format(i+1, max_round), description="Initialization", footer="Round limited to 2 minutes", color=self.color)
                view = Poker(self.bot, players, embed, (0 if max_round == 1 else (max_round - i)))
                await view.update(inter, init=True)
                await view.wait()
                await view.final()
                for p in view.winners: # get the winner and increase their counts
                    win_tracker[p.id][1] += 1
                await asyncio.sleep(10)
                if i < max_round - 1: await view.message.delete()
            if max_round > 1:
                win_tracker = dict(sorted(win_tracker.items(), key=lambda item: item[1], reverse=True)) # sort in reverse order
                msg = ""
                for id, s in win_tracker.items(): # make a string
                    msg += "**{}** ▫️ **{}** win(s)\n".format(s[0], s[1])
                await view.message.edit(embed=self.bot.util.embed(title="♠️ Multiplayer Poker ♥️ ▫️ Results", description=msg, color=self.color)) # post it
            await self.bot.util.clean((inter, view.message), 60)

    @game.sub_command()
    async def blackjack(self, inter: disnake.GuildCommandInteraction):
        """Play a blackjack mini-game with other people (1 to 6 players)"""
        await inter.response.defer()
        players = [inter.author]
        view = JoinGame(self.bot, players, 6)
        desc = "Starting in {}s\n{}/6 players"
        embed = self.bot.util.embed(title="♠️ Multiplayer Blackjack ♥️", description=desc.format(30, 1), color=self.color)
        msg = await inter.channel.send(embed=embed, view=view)
        self.bot.doAsync(view.updateTimer(msg, embed, desc, 30))
        await view.wait()
        await msg.delete()
        embed = self.bot.util.embed(title="♠️ Multiplayer Blackjack ♥️", description="Initialization", footer="Game limited to 4 minutes", color=self.color)
        view = Blackjack(self.bot, players, embed)
        await view.update(inter, init=True)
        await view.wait()
        await self.bot.util.clean(inter, 60)

    @game.sub_command()
    async def tictactoe(self, inter: disnake.GuildCommandInteraction):
        """Play a game of Tic Tac Toe (2 players Only)"""
        await inter.response.defer()
        players = [inter.author]
        view = JoinGame(self.bot, players, 2)
        desc = "Starting in {}s\n{}/2 players"
        embed = self.bot.util.embed(title=":x: Multiplayer Tic Tac Toe :o:", description=desc.format(60, 1), color=self.color)
        msg = await inter.channel.send(embed=embed, view=view)
        self.bot.doAsync(view.updateTimer(msg, embed, desc, 60))
        await view.wait()
        await msg.delete()
        if len(players) == 1:
            await inter.edit_original_message(embed=self.bot.util.embed(title=":x: Multiplayer Tic Tac Toe :o:", description="Error, a 2nd Player is required", color=self.color))
        else:
            random.shuffle(players)
            embed = self.bot.util.embed(title=":x: Multiplayer Tic Tac Toe :o:", description=":x: {} :o: {}\nTurn of **{}**".format(view.players[0].display_name, view.players[1].display_name, view.players[0].display_name), footer="Game limited at 3 minutes", color=self.color)
            view = TicTacToe(self.bot, players, embed)
            await inter.edit_original_message(embed=embed, view=view)
            await view.wait()
        await self.bot.util.clean(inter, 60)

    @game.sub_command()
    async def connectfour(self, inter: disnake.GuildCommandInteraction):
        """Play a game of Connect Four (2 players Only)"""
        await inter.response.defer()
        players = [inter.author]
        view = JoinGame(self.bot, players, 2)
        desc = "Starting in {}s\n{}/2 players"
        embed = self.bot.util.embed(title=":red_circle: Multiplayer Connect Four :yellow_circle:", description=desc.format(60, 1), color=self.color)
        msg = await inter.channel.send(embed=embed, view=view)
        self.bot.doAsync(view.updateTimer(msg, embed, desc, 60))
        await view.wait()
        await msg.delete()
        if len(players) == 1:
            await inter.edit_original_message(embed=self.bot.util.embed(title=":red_circle: Multiplayer Connect Four :yellow_circle:", description="Error, a 2nd Player is required", color=self.color))
        else:
            random.shuffle(players)
            embed = self.bot.util.embed(title=":red_circle: Multiplayer Connect Four :yellow_circle:", description=":red_circle: {} :yellow_circle: {}".format(players[0].display_name, players[1].display_name), footer="Game limited to 8 minutes", color=self.color)
            view = ConnectFour(self.bot, players, embed)
            await view.update(inter, init=True)
            await view.wait()
        await self.bot.util.clean(inter, 60)

    @game.sub_command()
    async def battleship(self, inter: disnake.GuildCommandInteraction):
        """Play a game of Battle Ship (2 players Only)"""
        await inter.response.defer()
        players = [inter.author]
        view = JoinGame(self.bot, players, 2)
        desc = "Starting in {}s\n{}/2 players"
        embed = self.bot.util.embed(title=":ship: Multiplayer Battle Ship :cruise_ship:", description=desc.format(60, 1), color=self.color)
        msg = await inter.channel.send(embed=embed, view=view)
        self.bot.doAsync(view.updateTimer(msg, embed, desc, 60))
        await view.wait()
        await msg.delete()
        if len(players) == 1:
            await inter.edit_original_message(embed=self.bot.util.embed(title=":ship: Multiplayer Battle Ship :cruise_ship:", description="Error, a 2nd Player is required", color=self.color))
        else:
            random.shuffle(players)
            embed = self.bot.util.embed(title=":ship: Multiplayer Battle Ship :cruise_ship:", description=":ship: {} :cruise_ship: {}".format(players[0].display_name, players[1].display_name), fields=[{'name':players[0].display_name, 'value':'dummy'}, {'name':players[1].display_name, 'value':'dummy'}], footer="Game limited to 8 minutes", color=self.color, inline=False)
            view = BattleShip(self.bot, players, embed)
            await view.update(inter, init=True)
            await view.wait()
        await self.bot.util.clean(inter, 60)

    @game.sub_command()
    async def rockpaperscissor(self, inter: disnake.GuildCommandInteraction, bestof : int = commands.Param(description="How many rounds to win", ge=1, le=10, default=1)):
        """Play a Rock Paper Scissor mini-game with other people (2 players Only)"""
        await inter.response.defer()
        players = [inter.author]
        view = JoinGame(self.bot, players, 2)
        desc = "Best of **" + str(bestof) + "**\nStarting in {}s\n{}/2 players"
        embed = self.bot.util.embed(title="🪨 Multiplayer Rock Paper Scissor ✂️", description=desc.format(60, 1), color=self.color)
        msg = await inter.channel.send(embed=embed, view=view)
        self.bot.doAsync(view.updateTimer(msg, embed, desc, 60))
        await view.wait()
        await msg.delete()
        if len(players) == 1:
            await inter.edit_original_message(embed=self.bot.util.embed(title="🪨 Multiplayer Rock Paper Scissor ✂️", description="Error, a 2nd Player is required", color=self.color))
        else:
            scores = [0, 0]
            embed = self.bot.util.embed(title="🪨 Multiplayer Rock Paper Scissor ✂️ ▫️ Best of {}".format(bestof), description="Initialization", footer="Round limited to 60 seconds", color=self.color)
            while True:
                view = RPS(self.bot, players, embed, scores, bestof)
                await view.update(inter, init=True)
                await view.wait()
                await view.timeoutCheck(inter)
                if scores[0] >= bestof or scores[1] >= bestof: break
                await asyncio.sleep(10)
        await self.bot.util.clean(inter, 60)

    @commands.slash_command(default_permission=True, name="random")
    @commands.cooldown(1, 50, commands.BucketType.user)
    async def _random(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    @_random.sub_command()
    async def dice(self, inter: disnake.GuildCommandInteraction, dice_string : str = commands.Param(description="Format is NdN. Minimum is 1d6, Maximum is 10d100")):
        """Roll some dies"""
        try:
            await inter.response.defer()
            tmp = dice_string.lower().split('d')
            n = int(tmp[0])
            d = int(tmp[1])
            if n <= 0 or n> 10 or d < 6 or d > 100: raise Exception()
            rolls = []
            for i in range(n):
                rolls.append(random.randint(1, d))
                msg = ""
                for j in range(len(rolls)):
                    msg += "{}, ".format(rolls[j])
                    if j == (len(rolls) - 1): msg = msg[:-2]
                if len(rolls) == n:
                    msg += "\n**Total**: {:}, **Average**: {:}, **Percentile**: {:.1f}%".format(sum(rolls), round(sum(rolls)/len(rolls)), sum(rolls) * 100 / (n * d)).replace('.0%', '%')
                await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"🎲 {} rolled {}...".format(inter.author.display_name, dice_string), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color))
                await asyncio.sleep(1)
            await self.bot.util.clean(inter, 45)
        except:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Invalid string `{}`\nFormat must be `NdN` (minimum is `1d6`, maximum is `10d100`)".format(dice_string), color=self.color))

    @_random.sub_command()
    async def coin(self, inter: disnake.GuildCommandInteraction):
        """Flip a coin"""
        coin = random.randint(0, 1)
        await inter.response.send_message(embed=self.bot.util.embed(author={'name':"{} flipped a coin...".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=(":coin: It landed on **Head**" if (coin == 0) else ":coin: It landed on **Tail**"), color=self.color))
        await self.bot.util.clean(inter, 45)

    @_random.sub_command()
    async def quota(self, inter: disnake.GuildCommandInteraction):
        """Give you your GW quota for the day"""
        h = random.randint(800, 4000)
        m = random.randint(70, 180)
        c = random.randint(1, 100)

        if inter.author.id == self.bot.data.config['ids'].get('wawi', -1): # joke
            c = 12

        if c <= 3:
            c = random.randint(1, 110)
            if c <= 2:
                await inter.response.send_message(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), inter.author.display_name), description="You got the **Eternal Battlefield Pass** 🤖\nCongratulations!!!\nYou will now relive GW over and ovḛ̸̛̠͕̑̋͌̄̎̍͆̆͑̿͌̇̇̕r̸̛̗̥͆͂̒̀̈́͑̑̊͐̉̎̚̚͝ ̵̨̛͔͎͍̞̰̠́͛̒̊̊̀̃͘ư̷͎̤̥̜̘͈̪̬̅̑͂̂̀̃̀̃̅̊̏̎̚͜͝ͅņ̴̢̛̛̥̮͖͉̻̩͍̱̓̽̂̂͌́̃t̵̞̦̿͐̌͗͑̀͛̇̚͝͝ỉ̵͉͕̙͔̯̯͓̘̬̫͚̬̮̪͋̉͆̎̈́́͛̕͘̚͠ͅļ̸̧̨̛͖̹͕̭̝͉̣̜͉̘͙̪͙͔͔̫̟̹̞̪̦̼̻̘͙̮͕̜̼͉̦̜̰̙̬͎͚̝̩̥̪̖͇̖̲̣͎̖̤̥͖͇̟͎̿̊͗̿̈̊͗̆̈́͋͊̔͂̏̍̔̒̐͋̄̐̄̅̇͐̊̈́̐͛͑̌͛̔͗̈́͌̀͑̌̅̉́̔̇́̆̉͆̄̂͂̃̿̏̈͛̇̒͆͗̈́̀̃̕̕͘̚̚͘͘͠͠͠͝͝͠͝͝ͅͅ ̴̢̛̛̛̯̫̯͕̙͙͇͕͕̪̩̗̤̗̺̩̬̞̞͉̱̊̽̇̉̏̃̑̋̋̌̎̾́̉́͌̿̐̆̒̾̆͒͛͌́͒̄͗͊͑̈́̑̐̂̿̋̊͊̈́̃̋̀̀̈̏̅̍̈͆̊̋͋̀̽͑̉̈́͘͘̕̕͝y̷̧̧̨̢̧̮̭̝̦͙͈͉̜͈̳̰̯͔͓̘͚̳̭͎̳̯͈͓̣͕͙̳̭̱͍͎͖̋͊̀͋͘͘ơ̸̢̗̖̹̹͖̣̫̝̞̦̘̙̭̮͕̘̱̆͋̓͗̾͐̉̏̀͂̄̎̂̈́͌͑̅̆̉̈̒͆̈̈̊͐̔̓̀̿̓̈́͝͝͝͠͝u̶̡̧̡̧̨̧̡̡̢̢̢̪̯͙͍̱̦̠̗̹̼̠̳̣͉̞̩̹͕̫͔͚̬̭̗̳̗̫̥̞̰̘̖̞̤͖̳̮̙͎͎̗̙̳͙͖͓̪̱̞͖̠̣̮̘͍̱̥̹͎͎̦̬̹̼̜͕͙͖̫̝̰̯̜̹̬̯͚͕̰̪̼͓̞̫̖̘͙̞͖̺̩͓̹̘̙̫̩̲̻̪̠̞̺͚̫̰̠̼̖̬͔̗̮͙̱̬̩̮̟͓̫̭̲̘̤͎̱̓̊̇́̀̏̏̾̀̄̆̒̂͐̌͂̈̂̓͋̌̓͘̕̕̚͜͜͜͝ͅͅͅͅŗ̷̡̧̨̢̢̢̧̡̡̧̡̢̧̨̨̡̧̛̛̛̬͚̮̜̟̣̤͕̼̫̪̗̙͚͉̦̭̣͓̩̫̞͚̤͇̗̲̪͕̝͍͍̫̞̬̣̯̤̮͉̹̫̬͕̫̥̱̹̲͔͔̪̖̱͔̹͈͔̳͖̩͕͚͓̤̤̪̤̩̰̬͙̞͙̘̯̮̫͕͚̙̜̼̩̰̻̞̺͈̝̝̖͎̻̹̞̥̰̮̥̙̠͔͎̤̲͎͍̟̥̞̗̰͓͍̞̹͍̬͎̲̬̞͈͉̼̥̝͈̼̠̫̙͖̪̼̲̯̲̫̼̺̘̗̘͚̤͓̯̦̣̬͒̑̒́͑͊̍̿̉̇̓̒̅̎͌̈́̐̽͋̏̒͂̈̒̃̿̓̇̈̿̊̎̈́͐̒͂͊̿̈́̿̅̏̀͐͛̎̍͑͂̈́̃̇̀̈͋̾̔̈́̽͌̿̍̇̅̏̋̑̈́̾̊͐̉̊̅͑̀͊̽̂̈́̽̓͗́̄͆̄͑͒̈́́͋̏͊͋̒͗̆̋̌̈̀͑͗̽͂̄̌̕͘͘̚͘̕̕͜͜͜͜͜͜͜͠͝͝͝͝͝͝ͅͅͅ ̷̧̡̧̨̢̧̨̡̨̧̛̛̛̛̮̭͇̣͓̙̺͍̟̜̞̫̪̘̼̞̜̠͇̗̮͕̬̥͓͔͈̟̦͇̥̖̭̝̱̗̠̘̝̹̖͓̝͇̖̫̯̩̞̞̯̲̤̱̻̤͇̲͍͈͓͖̹̗̟̲̪̪̟̩͙̪̝̮̘̽̋̍́̔̊̍̈́͂̌̽͒̆͐͊̏̐͑͛̓̆̈́͌̂͒͆̔̅̓̽͊̅́̾̽̓̏̆̀̀͌̾̀͒̓̇̊̀̐͛̌̋̈͑̇́̂̆̽̈̕̕̚̚͜͠ͅͅͅͅḑ̶̛̛̯͓̠̖͎̭̞̫͑̋̄̄̈̽̎̊͛̽͌̾̋̔̽̔̀̀͐̿̈́̀̃͐͂͆̈̃͑̀̋̑͊̃̆̓̾̎̅̀̆̓̏͊̆̔̈̅͛̍̎̓̀͛͒́̐͆̂̋̋͛̆̈͐͂̏̊̏̏̓̿̔͆̓̽̂̅͆̔͑̔̈̾̈̽̂̃̋̈́̾̎̈́̂̓̃̒͐͆̌̍̀͗̈́̑̌̚̕̕̚͠͠͝ę̴̧̨̨̨̢̨̢̧̧̧̨̧̛̛̛̛̛̛̛̺̪̹̘͈̣͔̜͓̥̥̟͇̱͚͖̠͙͙̱̞̣̤͚̣̟̫̬̟͓̺͙̬͚̹͓̗̬̼͇͙̻͍̖̙̥̩͔̜͕̖͕͔͚̳͙̩͇͙̺͔̲̱̙͉̝̠̤̝̭̮̩̦͇̖̳̞̞̖͎̙͙̲̮̠̣͍̪͙̰̣͉̘͉̦̖̳̫͖͖̘̖̮̲̱̪͕̳̫̫̞̪̜̞̬͙͖͍͖̦͉̯̟̖͇̩͚͙͔̳̫͗̈́̒̎͂̇̀͒̈́̃͐̉͛̾̑̆̃͐̈́̉͒̇̓̏̀͌̐͌̅̓͐́̿͒̅͑̍̓̈́̉̊́̉̀̔̊̍̽͛͛͆̓̈͋̉͋̿̉́̋̈̓̐̈́̔̃͆͗͛̏́̀̑͋̀̽̔̓̎̒̆̌̐̈́̓͂̐̋͊̌͑̓̈́̊̿͋̈́́̃̏̓̉͛͆̂͐͗͗̾̅̌̾͌̈́͊͘̕̚̕̚̚̕͘̕͜͜͜͜͜͜͜͠͝͝͠͝͝͠ͅͅa̸̡͔̯͎̟͙̖̗͔̺̰͇͚̭̲̭͕̫̜͉̯͕̅̈͋̒͋͂̐̕ͅţ̶̡̨̢̢̡̡̡̨̢̡̧̨̢̛̥̭̞͈̼̖͙͇̝̳͇̞̬͎̲̙̰̙̱̳̟̣̗̫̣͉͖̪̩͙̲͇͙̫̘͖̖̜̝̦̥̟̜̠͔̠͎̭͔̘͓͚̩͇͙͎͎̰̘̟̳̪͖̠̪̦̦̫̞̟̗̹̹̤͓͍̜̯͔̼̱̮̹͎͖͍̲͎̠͉̟͈̠̦̯̲̼̥̱̬̜͙̘͕̣̳͇̞͓̝͈̼̞̻͚̘̩̟̩̖̼͍̯̘͉͔̤̘̥̦͑̒͗̅̉̾͗̾̓̈́̍̉̈́͛̀͊̋̀͐̏̈́̀̀̍̇̀̀̈́̃̀̅͛̅̈́̇̽̆̌̈̄͆̄̂͂̔͗͌͊̽̿́͑̒̾̑̊̿͗́̇̋̊̄̀̍̓̆͂̆̔̏̍̑̔̊̾̎̆͛͑̓͒̈̎͌̓͗̀̿̓̃̔̈́͗̃̓̽̓̉̀͛͂̿́̀̌͊̆̋̀̓̇́̔̓͆̋̊̀̋͑́̔́̌̒̾̂̎̋̈́́̀͗̈́̈́́̾̈́͑͋̇͒̀͋͆͗̾͐̆̈́͂͐̈̐̓̍̈́̈̅̓͐̚̚̚̚̕͘̕͘̚̚̚͘͜͜͜͜͜͜͝͠͠͠͝͠ͅͅḥ̴̨̧̧̢̧̢̢̛̛̙̱͚̺̬̖̮̪͈̟͉̦̪̘̰̺̳̱̲͔̲̮̦̦̪̪̲̠͓͎͇͕̯̥͉͍̱̥͓̲̤̫̳̠̝͖̺̙͖͎͙̠͓̺̗̝̩͍͕͎̞͕̤̻̰̘͇͕̟̹̳͇͈͇̳̳̞̗̣͖̙͓̼̬̯͚͎̮͚̳̰͙̙̟̊͆͒͆͌̂̈́̀́̽̿͌̓́̐̑͌͋͆͊͑͛͑̀̋͐̏͌̑̀͛͗̀́̈̀̓̽̇̐̋͊̅͑̊͒̈́̀̀̔̀̇͗̆͑̅̌̑̈́͌̒̅̌̓͋͂̀̍̈́͐̈́̆̐̈́̍͛͂̔̐̎͂̎̇͑̈́̈́̎̉̈́́̒̒̆̌̃̓̈́͂̽̓̆̋̈̂̽̆̓̔͗̓̀̄̈́̂̏͗̐̔͘̕͘͘͜͜͜͜͠͠͝͠͠͝͝͝͠͠͝ͅͅ", thumbnail=inter.author.display_avatar, color=self.color))
            elif c <= 6:
                await inter.response.send_message(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), inter.author.display_name), description="You got a **Slave Pass** 🤖\nCongratulations!!!\nCall your boss and take a day off now!", footer="Full Auto and Botting are forbidden", thumbnail=inter.author.display_avatar, color=self.color))
            elif c <= 16:
                await inter.response.send_message(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), inter.author.display_name), description="You got a **Chen Pass** 😈\nCongratulations!!!\nYour daily honor or meat count must be composed only of the digit 6.", thumbnail=inter.author.display_avatar, color=self.color))
            elif c <= 21:
                await inter.response.send_message(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), inter.author.display_name), description="You got a **Carry Pass** 😈\nDon't stop grinding, continue until your Crew gets the max rewards!", thumbnail=inter.author.display_avatar, color=self.color))
            elif c <= 26:
                await inter.response.send_message(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), inter.author.display_name), description="You got a **Relief Ace Pass** 😈\nPrepare to relieve carries of their 'stress' after the day!!!", footer="wuv wuv", thumbnail=inter.author.display_avatar, color=self.color))
            else:
                await inter.response.send_message(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), inter.author.display_name), description="You got a **Free Leech Pass** 👍\nCongratulations!!!", thumbnail=inter.author.display_avatar, color=self.color))
            await self.bot.util.clean(inter, 40)
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

        if inter.author.id == self.bot.data.config['ids'].get('chen', -1): # joke
            match random.randint(3, 8):
                case 3: h = 666
                case 4: h = 6666
                case 5: h = 66666
                case 6: h = 666666
                case 7: h = 6666666
                case 8: h = 66666666
            match random.randint(1, 4):
                case 1: m = 6
                case 2: m = 66
                case 3: m = 666
                case 4: m = 6666

        await inter.response.send_message(embed=self.bot.util.embed(title="{} {}'s daily quota".format(self.bot.emote.get('gw'), inter.author.display_name), description="**Honor:** {:,}\n**Meat:** {:,}".format(h, m), thumbnail=inter.author.display_avatar, color=self.color))
        await self.bot.util.clean(inter, 40)

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

    @_random.sub_command()
    async def character(self, inter: disnake.GuildCommandInteraction):
        """Generate a random GBF character"""
        seed = (inter.author.id + int(datetime.utcnow().timestamp()) // 86400) # based on user id + day
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

        await inter.response.send_message(embed=self.bot.util.embed(author={'name':"{}'s daily character".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color))
        await self.bot.util.clean(inter, 30)

    @_random.sub_command()
    async def xil(self, inter: disnake.GuildCommandInteraction):
        """Generate a random element for Xil (Private Joke)"""
        g = random.Random()
        elems = ['fire', 'water', 'earth', 'wind', 'light', 'dark']
        g.seed(int((int(datetime.utcnow().timestamp()) // 86400) * (1.0 + 1.0/4.2)))
        e = g.choice(elems)

        await inter.response.send_message(embed=self.bot.util.embed(title="Today, Xil's main element is", description="{} **{}**".format(self.bot.emote.get(e), e.capitalize()), color=self.color))
        await self.bot.util.clean(inter, 30)

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def ask(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    @ask.sub_command()
    async def choice(self, inter: disnake.GuildCommandInteraction, choices : str = commands.Param(description="Format is Choice 1;Choice 2;...;Choice N")):
        """Ask me to pick a choice"""
        try:
            possible = choices.split(";")
            if len(possible) < 2: raise Exception()
            await inter.response.send_message(embed=self.bot.util.embed(author={'name':"{}'s choice".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="`{}`\n{}".format(' '.join(possible), random.choice(possible)), color=self.color))
            await self.bot.util.clean(inter, 45)
        except:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Give me a list of something to choose from, separated by `;`", color=self.color), ephemeral=True)

    @ask.sub_command()
    async def question(self, inter: disnake.GuildCommandInteraction, question : str = commands.Param()):
        """Ask me a question"""
        await inter.response.send_message(embed=self.bot.util.embed(author={'name':"{} asked".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="`{}`\n{}".format(question, random.choice(["It is Certain.","It is decidedly so.","Without a doubt.","Yes definitely.","You may rely on it.","As I see it, yes.","Most likely.","Outlook good.","Yes.","Signs point to yes.","Reply hazy, try again.","Ask again later.","Better not tell you now.","Cannot predict now.","Concentrate and ask again.","Don't count on it.","My reply is no.","My sources say no.","Outlook not so good.","Very doubtful."])), color=self.color))
        await self.bot.util.clean(inter, 45)

    @ask.sub_command()
    async def when(self, inter: disnake.GuildCommandInteraction, question : str = commands.Param()):
        """Ask me when will something happen"""
        if question.lower().startswith("when ") and len(question) > 5: question = question[5:]
        await inter.response.send_message(embed=self.bot.util.embed(author={'name':"{} asked".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="`When {}`\n{}".format(question, random.choice(["Never", "Soon:tm:", "Ask again tomorrow", "Can't compute", "42", "One day, my friend", "Next year", "It's a secret to everybody", "Soon enough", "When it's ready", "Five minutes", "This week, surely", "My sources say next month", "NOW!", "I'm not so sure", "In three days"])), color=self.color))
        await self.bot.util.clean(inter, 45)

    @commands.message_command(default_permission=True, name="UwU")
    @commands.cooldown(6, 180, commands.BucketType.guild)
    async def uwu(self, inter: disnake.MessageCommandInteraction, message: disnake.Message):
        """UwU-tize a message"""
        msg = message.clean_content.replace("r","w").replace("R","W").replace("than","dan").replace("Than","Dan").replace("THan","Dan").replace("THAn","Dan").replace("THAN","DAN").replace("thaN","daN").replace("thAn","dAn").replace("thAN","dAN").replace("tHAN","DAN").replace("l","w").replace("L","W").replace("oy","oi").replace("oY","oI").replace("Oy","Oi").replace("OY","OI").replace("the","de").replace("The","De").replace("THe","De").replace("THE","DE").replace("thE","dE").replace("tHe","De").replace("you","u").replace("You","U").replace("YOu","U").replace("YOU","U").replace("yoU","u").replace("yOu","u").replace("yOU","U")
        if len(msg) == 0 or len(msg) >= 2000:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="This message can't be converted", color=self.color), ephemeral=True)
        else:
            await inter.response.send_message(msg)