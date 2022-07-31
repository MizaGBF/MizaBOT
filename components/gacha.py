import disnake
import asyncio
import random
from datetime import datetime, timedelta
from views.roll_tap import Tap

# ----------------------------------------------------------------------------------------------------------------
# Gacha Component
# ----------------------------------------------------------------------------------------------------------------
# Manage the real granblue gacha
# Also provide a simulator for games
# ----------------------------------------------------------------------------------------------------------------

class Gacha():
    def __init__(self, bot):
        self.bot = bot
        # scam gacha simulator
        self.scam = [(2000, 'Sunlight Stone', 'evolution/s/20014.jpg'), (2000, 'Damascus Ingot', 'evolution/s/20005.jpg'), (6000, 'Damascus Crystal x2', 'article/s/203.jpg'), (5000, 'Brimstone Earrings x2', 'npcaugment/s/11.jpg'), (5000, 'Permafrost Earrings x2', 'npcaugment/s/12.jpg'), (5000, 'Brickearth Earrings x2', 'npcaugment/s/13.jpg'), (5000, 'Jetstream Earrings x2', 'npcaugment/s/14.jpg'), (5000, 'Sunbeam Earrings x2', 'npcaugment/s/15.jpg'), (5000, 'Nightshade Earrings x2', 'npcaugment/s/16.jpg'), (5000, 'Intracacy Ring', 'npcaugment/s/3.jpg'), (5000, 'Meteorite x10', 'article/s/137.jpg'), (5000, 'Abyssal Wing x5', 'article/s/555.jpg'), (5000, 'Tears of the Apocalypse x10', 'article/s/538.jpg'), (4000, 'Ruby Awakening Orb x2', 'npcarousal/s/1.jpg'), (4000, 'Sapphire Awakening Orb x2', 'npcarousal/s/2.jpg'), (4000, 'Citrine  Awakening Orb x2', 'npcarousal/s/3.jpg'), (4000, 'Sephira Stone x10', 'article/s/25000.jpg'), (4000, 'Weapon Plus Mark x30', 'bonusstock/s/1.jpg'), (4000, 'Summon Plus Mark x30', 'bonusstock/s/2.jpg'), (4000, 'Gold Moon x2', 'article/s/30033.jpg'), (4000, 'Half Elixir x100', 'normal/s/2.jpg'), (4000, 'Soul Berry x300', 'normal/s/5.jpg')]
        self.scam_rate = 0
        for r in self.scam:
            self.scam_rate += r[0]

    def init(self):
        pass


    """get()
    Get the current GBF gacha banner data.
    
    Returns
    --------
    list: Containing:
        - timedelta: Remaining time
        - timedelta: Remaining time (for multi element spark periods)
        - str: String containing the ssr rate and gacha rate up list
        - str: Gacha banner image
    """
    def get(self):
        c = self.bot.util.JST().replace(microsecond=0) - timedelta(seconds=80)
        if ('gacha' not in self.bot.data.save['gbfdata'] or self.bot.data.save['gbfdata']['gacha'] is None or c >= self.bot.data.save['gbfdata']['gacha']['time']) and not self.update():
            return []
        if self.bot.data.save['gbfdata']['gacha']['time'] is None:
            return []
        return [c, self.bot.data.save['gbfdata']['gacha']]

    """process()
    Reetrieve and process the gacha rates
    
    Prameters
    --------
    id: Banner id
    sub_id: draw id (1 = single roll, 2 = ten roll, 3 = scam gacha)
    
    Returns
    --------
    tuple: Contains:
        -ratio, the gacha rates
        -list, the item list
        -rateup, the rate up items
    """
    def process(self, gtype, id, sub_id):
        try:
            # draw rate
            data = self.bot.gbf.request("https://game.granbluefantasy.jp/gacha/provision_ratio/{}/{}/{}?PARAMS".format(gtype, id, sub_id), account=self.bot.data.save['gbfcurrent'], expect_JSON=True, check=True)
            
            gratio = data['ratio'][0]['ratio']
            
            possible_zodiac_wpn = ['Ramulus', 'Dormius', 'Gallinarius', 'Canisius', 'Porculius', 'Rodentius', 'Bovinius', 'Tigrisius']
            glist = [{'rate':0, 'list':{}}, {'rate':0, 'list':{}}, {'rate':0, 'list':{}}]
            grateup = {'zodiac':[]}
            # loop over data
            for appear in data['appear']:
                rarity = appear['rarity'] - 2
                if rarity < 0 or rarity > 2: continue # eliminate possible N rarity
                glist[rarity]['rate'] = float(data['ratio'][2 - rarity]['ratio'][:-1])
                for item in appear['item']:
                    if item['kind'] is None: kind = "S"
                    else: kind = int(item['kind'])-1
                    if item['drop_rate'] not in glist[rarity]['list']: glist[rarity]['list'][item['drop_rate']] = []
                    glist[rarity]['list'][item['drop_rate']].append("{}{}{}".format(item['attribute'], kind, item['name']))

                    if rarity == 2: # ssr
                        if appear['category_name'] not in grateup: grateup[appear['category_name']] = {}
                        if 'character_name' in item and item.get('name', '') in possible_zodiac_wpn:
                            grateup['zodiac'].append("{}{}{}".format(item['attribute'], kind, item['character_name']))
                        if item['incidence'] is not None:
                            if item['drop_rate'] not in grateup[appear['category_name']]: grateup[appear['category_name']][item['drop_rate']] = []
                            if 'character_name' in item and item['character_name'] is not None: grateup[appear['category_name']][item['drop_rate']].append("{}{}{}".format(item['attribute'], kind, item['character_name']))
                            else: grateup[appear['category_name']][item['drop_rate']].append("{}{}{}".format(item['attribute'], kind, item['name']))
            return gratio, glist, grateup
        except Exception as e:
            print(e)
            return None, None, None

    """update()
    Request and update the GBF gacha in the save data
    
    Returns
    --------
    bool: True if success, False if error
    """
    def update(self):
        if not self.bot.gbf.isAvailable():
            return False
        try:
            c = self.bot.util.JST()
            #gacha page
            data = self.bot.gbf.request("https://game.granbluefantasy.jp/gacha/list?PARAMS", account=self.bot.data.save['gbfcurrent'], expect_JSON=True, check=True)
            if data is None: raise Exception()
            # will contain the data
            gacha_data = {}
            index = -1
            scam_ids = []
            for i, g in enumerate(data['legend']['lineup']):
                if g['name'] == "Premium Draw": index = i
                elif g['name'].find("Star Premium") != -1:
                    for subscam in g['campaign_gacha_ids']:
                        scam_ids.append(subscam['id'])
            
            gacha_data['time'] = datetime.strptime(data['legend']['lineup'][index]['end'], '%m/%d %H:%M').replace(year=c.year, microsecond=0)
            NY = False
            if c > gacha_data['time']:
                gacha_data['time'] = gacha_data['time'].replace(year=gacha_data['time'].year+1) # new year fix
                NY = True
            gacha_data['timesub'] = datetime.strptime(data['ceiling']['end'], '%Y/%m/%d %H:%M').replace(microsecond=0)
            if (NY == False and gacha_data['timesub'] < gacha_data['time']) or (NY == True and gacha_data['timesub'] > gacha_data['time']): gacha_data['time'] = gacha_data['timesub'] # switched
            random_key = data['legend']['random_key']
            header_images = data['header_images']
            logo = {'logo_fire':1, 'logo_water':2, 'logo_earth':3, 'logo_wind':4, 'logo_dark':5, 'logo_light':6}.get(data.get('logo_image', ''), data.get('logo_image', '').replace('logo_', ''))
            id = data['legend']['lineup'][index]['id']

            # draw rate
            gacha_data['ratio'], gacha_data['list'], gacha_data['rateup'] = self.process('legend', id, 1)
            if gacha_data['ratio'] is None:
                raise Exception()

            # scam gachas
            for sid in scam_ids:
                gratio, glist, grateup = self.process('legend', sid, 3)
                if gratio is not None:
                    if 'scam' not in gacha_data:
                        gacha_data['scam'] = []
                    gacha_data['scam'].append({'ratio':gratio, 'list':glist, 'rateup':grateup})

            # classic gacha
            data = self.bot.gbf.request("https://game.granbluefantasy.jp/rest/gacha/classic/toppage_data?PARAMS", account=self.bot.data.save['gbfcurrent'], expect_JSON=True, check=True)
            if data is not None and 'appearance_gacha_id' in data:
                gratio, glist, grateup = self.process('classic', data['appearance_gacha_id'], 1)
                if gratio is not None:
                    gacha_data['classic'] = {'ratio':gratio, 'list':glist, 'rateup':grateup}

            # add image
            gachas = ['{}/tips/description_gacha.jpg'.format(random_key), '{}/tips/description_gacha_{}.jpg'.format(random_key, logo), '{}/tips/description_{}.jpg'.format(random_key, header_images[0]), 'header/{}.png'.format(header_images[0])]
            for g in gachas:
                data = self.bot.gbf.request("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/gacha/{}".format(g), no_base_headers=True)
                if data is not None:
                    gacha_data['image'] = g
                    break

            # save
            with self.bot.data.lock:
                # clean old version
                for key in ['rateup', 'gachatime', 'gachatimesub', 'gachabanner', 'gachacontent', 'gacharateups']:
                    self.bot.data.save['gbfdata'].pop(key, None)
                self.bot.data.save['gbfdata']['gacha'] = gacha_data
                self.bot.data.pending = True
            return True
        except Exception as e:
            print('updategacha(): ', self.bot.util.pexc(e))
            self.bot.errn += 1
            with self.bot.data.lock:
                self.bot.data.save['gbfdata']['gacha'] = None
                self.bot.data.pending = True # save anyway
            return False

    """summary()
    Make a text summary of the current gacha
    
    Raise
    --------
    Exception
    
    Returns
    --------
    tuple:
        - str: Description
        - str: url of thumbnail
    """
    def summary(self):
        try:
            content = self.get()
            if len(content) > 0:
                description = "{} Current gacha ends in **{}**".format(self.bot.emote.get('clock'), self.bot.util.delta2str(content[1]['time'] - content[0], 2))
                if content[1]['time'] != content[1]['timesub']:
                    description += "\n{} Spark period ends in **{}**".format(self.bot.emote.get('mark'), self.bot.util.delta2str(content[1]['timesub'] - content[0], 2))

                # calculate real ssr rate
                sum_ssr = 0
                # sum_total = 0 # NOTE: ignoring it for now
                for i, rarity in enumerate(content[1]['list']):
                    for r in rarity['list']:
                        # sum_total += float(r) * len(rarity['list'][r]) # NOTE: ignoring it for now
                        if i == 2: sum_ssr += float(r) * len(rarity['list'][r])

                # rate description
                description += "\n{} **Rate:** Advertised **{}**".format(self.bot.emote.get('SSR'), content[1]['ratio'])
                if not content[1]['ratio'].startswith('3'):
                    description += " **(Premium Gala)**"
                description += " ▫️ Sum of rates **{:.3f}%**".format(sum_ssr)
                if 'scam' in content[1]: description += "\n{} **{}** Star Premium Draw(s) available".format(self.bot.emote.get('mark'), len(content[1]['scam']))
                description += "\n"
                
                # build rate up list
                for k in content[1]['rateup']:
                    if k == 'zodiac':
                        if len(content[1]['rateup']['zodiac']) > 0:
                            description += "{} **Zodiac** ▫️ ".format(self.bot.emote.get('loot'))
                            for i in content[1]['rateup'][k]:
                                description += self.formatGachaItem(i) + " "
                            description += "\n"
                    else:
                        if len(content[1]['rateup'][k]) > 0:
                            for r in content[1]['rateup'][k]:
                                if k.lower().find("weapon") != -1: description += "{}**{}%** ▫️ ".format(self.bot.emote.get('sword'), r)
                                elif k.lower().find("summon") != -1: description += "{}**{}%** ▫️ ".format(self.bot.emote.get('summon'), r)
                                for i, item in enumerate(content[1]['rateup'][k][r]):
                                    if i >= 8 and len(content[1]['rateup'][k][r]) - i > 1:
                                        description += " and **{} more!**".format(len(content[1]['rateup'][k][r]) - i)
                                        break
                                    description += self.formatGachaItem(item) + " "
                            description += "\n"
                return description, "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/gacha/{}".format(content[1]['image'])
            return None, None
        except Exception as e:
            raise e


    """retrieve()
    Return the current real gacha from GBF, if it exists in the bot memory.
    If not, a dummy/limited one is generated.
    
    Prameters
    --------
    scam: Integer, to retrieve a scam gacha data (None to ignore)
    classic: Boolean, to retrieve the classic gacha (None to ignore, scam has priority)
    
    Returns
    --------
    tuple: Containing:
        - The whole rate list
        - The banner rate up
        - The ssr rate, in %
        - Boolean indicating if the gacha is the real one
        - (OPTIONAL): Integer, star premium gacha index
    """
    def retrieve(self, scam=None, classic=None):
        try:
            data = self.get()[1]
            if scam is None:
                if classic is not None and classic:
                    if 'classic' not in data:
                        raise Exception()
                    gacha_data = data['classic']
                else:
                    gacha_data = data
            else:
                if 'scam' not in data or scam < 0 or scam >= len(data['scam']):
                    raise Exception()
                gacha_data = data['scam'][scam]
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
            complete = True
            if scam is not None:
                return data, rateups, ssrrate, complete, scam
        except:
            data = [{"rate": 82.0, "list": {"82": [None]}}, {"rate": 15.0, "list": {"15": [None]}}, {"rate": 3.0, "list": {"3": [None]}}]
            rateups = None
            ssrrate = 3
            complete = False
        return data, rateups, ssrrate, complete

    """isLegfest()
    Check the provided parameter and the real gacha to determine if we will be using a 6 or 3% SSR rate
    
    Parameters
    ----------
    selected: Integer, selected value by the user (-1 default, 0 is 3%, anything else is 6%)
    
    Returns
    --------
    bool: True if 6%, False if 3%
    """
    def isLegfest(self, ssrrate, selected):
        match selected:
            case 0:
                return False
            case -1:
                try:
                    return (ssrrate == 6)
                except:
                    return False
            case _:
                return True

    """allRates()
    Return a list of all different possible SSR rates in the current gacha
    
    Returns
    --------
    tuple:
        float: ssr rate, return None if error
        list: Rate list, return None if error
    """
    def allRates(self):
        try:
            r = []
            for rate in list(self.bot.data.save['gbfdata']['gacha']['list'][2]['list'].keys()):
                if float(rate) not in r:
                    r.append(float(rate))
            return float(self.bot.data.save['gbfdata']['gacha']['ratio'][:-1]), sorted(r, reverse=True)
        except:
            return None, None

    """formatGachaItem()
    Format the item string used by the gacha simulator to add an element emoji
    
    Parameters
    ----------
    raw: string to format
    
    Returns
    --------
    str: self.resulting string
    """
    def formatGachaItem(self, raw : str):
        if len(raw) < 3: return raw
        res = ""
        match raw[0]:
            case "1": res += str(self.bot.emote.get('fire'))
            case "2": res += str(self.bot.emote.get('water'))
            case "3": res += str(self.bot.emote.get('earth'))
            case "4": res += str(self.bot.emote.get('wind'))
            case "5": res += str(self.bot.emote.get('light'))
            case "6": res += str(self.bot.emote.get('dark'))
            case _: pass
        match raw[1]:
            case "0": res += str(self.bot.emote.get('sword'))
            case "1": res += str(self.bot.emote.get('dagger'))
            case "2": res += str(self.bot.emote.get('spear'))
            case "3": res += str(self.bot.emote.get('axe'))
            case "4": res += str(self.bot.emote.get('staff'))
            case "5": res += str(self.bot.emote.get('gun'))
            case "6": res += str(self.bot.emote.get('melee'))
            case "7": res += str(self.bot.emote.get('bow'))
            case "8": res += str(self.bot.emote.get('harp'))
            case "9": res += str(self.bot.emote.get('katana'))
            case "S": res += str(self.bot.emote.get('summon'))
            case _: pass
        return res + raw[2:]

    """simulate()
    Create a GachaSimulator instance
    
    Parameters
    --------
    simtype: string, case sensitive. possible values: single, srssr, memerollA, memerollB, scam, ten, gachapin, mukku, supermukku
    gachatype: string, type of gacha to use: classic for classic gacha, scam for premium star, anything else for standard prelium draw
    color: color to use for the embeds
    scamindex: index of the premium star gacha to use
    
    Returns
    --------
    GachaSimulator
    """
    def simulate(self, simtype:str, gachatype:str, color, scamindex:int=1):
        scamdata = None
        isclassic = False
        match gachatype: # retrieve the data (no need to copy)
            case 'scam':
                gachadata = self.retrieve()
                scamdata = self.retrieve(scam=scamindex-1)
            case 'classic':
                gachadata = self.retrieve(classic=True)
                isclassic = True
            case _: gachadata = self.retrieve()
        gsim = GachaSimulator(self.bot, gachadata, simtype, scamdata, isclassic, color) # create a simulator instance
        return gsim

class GachaSimulator():
    """constructor
    
    Parameters
    --------
    bot: MizaBOT
    gachadata: output from Gacha.retrieve()
    simtype: value from Gacha.simulate() parameter simtype
    scamdata: Optional, output from Gacha.retrieve(scam=X). None to ignore.
    isclassic: Boolean, indicate if classic gacha is used
    color: Embed color
    """
    def __init__(self, bot, gachadata:tuple, simtype:str, scamdata, isclassic, color):
        self.bot = bot
        self.data, self.rateups, self.ssrrate, self.complete = gachadata # unpack the data
        self.scamdata = scamdata # no need to unpack the scam gacha one (assume it might be None too)
        self.isclassic = isclassic
        self.color = color
        self.mode = {'single':0, 'srssr':1, 'memerollA':2, 'memerollB':3, 'ten':10, 'gachapin':11, 'mukku':12, 'supermukku':13, 'scam':14}[simtype] # kept the old modes, might change it later?
        self.result = {} # output of generate()
        self.thumbnail = None # thumbnail of self.best
        self.best = [-1, ""] # best roll
        self.exception = None # contains the last exception

    """changeMode()
    update self.mode with a new value
    
    Parameters
    --------
    simtype: value from Gacha.simulate parameter() simtype
    """
    def changeMode(self, simtype):
        self.mode = {'single':0, 'srssr':1, 'memerollA':2, 'memerollB':3, 'scam':4, 'ten':10, 'gachapin':11, 'mukku':12, 'supermukku':13}[simtype]

    """check_rate()
    check and calculate modifiers to get the exact rates we want
    
    Parameters
    --------
    ssrrate: Integer, wanted SSR rate in percent
    
    Returns
    --------
    tuple:
        - mods: List of modifiers (R, SR, SSR)
        - proba: List of Item rates (R, SR, SSR)
    """
    def check_rate(self, ssrrate):
        # calcul R,SR,SSR & total
        proba = [] # store the % of R, SR and SSR
        mods = [1, 1, 1] # modifiers vs advertised rates, 1 by default
        for r in self.data:
            proba.append(0)
            for rate in r['list']:
                proba[-1] += float(rate) * len(r['list'][rate]) # sum of rates x items
        if ssrrate != self.data[2]['rate']: # if wanted ssr rate different from advertised one
            mods[2] = ssrrate / proba[2] # calculate mod
            tmp = proba[2] * mods[2] # get new proba
            diff = proba[2] - tmp # get diff between old and new
            try: mods[0] = (proba[0] + diff) / proba[0] # calculate lowered R rate modifer
            except: mods[0] = 1
            proba[0] = max(0, proba[0] + diff) # lower R proba
            proba[2] = tmp # store SSR proba
        return mods, proba

    """generate()
    generate X amount of rolls and update self.result
    
    Parameters
    --------
    count: Integer, number of rolls wanted
    legfest: Integer, -1 for auto mod, 0 to force 3%, 1 to force 6%
    """
    def generate(self, count:int, legfest:int=-1):
        try:
            # prep work
            legfest = self.bot.gacha.isLegfest(self.ssrrate, legfest)
            ssrrate = 15 if self.mode == 13 else (9 if self.mode == 12 else (6 if legfest else 3))
            self.result = {} # empty output, used for error check
            result = {'list':[], 'detail':[0, 0, 0], 'rate':ssrrate}
            mods, proba = self.check_rate(ssrrate)
            tenrollsr = False # flag for guaranted SR in ten rolls 
            if self.mode == 3 and len(self.rateups) == 0:
                self.mode = 2 # revert memerollB to A if no rate ups
            # rolling loop
            for i in range(0, count):
                d = random.randint(1, int(sum(proba) * 1000)) / 1000 # our roll
                if self.mode == 1 or (self.mode >= 10 and (i % 10 == 9) and not tenrollsr): sr_mode = True # force sr in srssr self.mode OR when 10th roll of ten roll)
                else: sr_mode = False # else doesn't set
                if d <= proba[2]: # SSR CASE
                    r = 2
                    tenrollsr = True
                    d /= mods[2]
                elif (not sr_mode and d <= proba[1] + proba[2]) or sr_mode: # SR CASE
                    r = 1
                    d -= proba[2]
                    while d >= proba[1]: # for forced sr
                        d -= proba[1]
                    d /= mods[1]
                    tenrollsr = True
                else: # R CASE
                    r = 0
                    d -= proba[2] + proba[1]
                    d /= mods[0]
                if i % 10 == 9: tenrollsr = False # unset flag if we did 10 rolls
                if self.complete: # if we have a real gacha
                    roll = None
                    for rate in self.data[r]['list']: # find which item we rolled
                        fr = float(rate)
                        for item in self.data[r]['list'][rate]:
                            if r == 2 and rate in self.rateups: last = "**" + self.bot.gacha.formatGachaItem(item) + "**"
                            else: last = self.bot.gacha.formatGachaItem(item)
                            if d <= fr:
                                roll = [r, last]
                                break
                            d -= fr
                        if roll is not None:
                            break
                    if roll is None:
                        roll = [r, last]
                    result['list'].append(roll) # store roll
                    result['detail'][r] += 1
                    if rate in self.rateups and r + 1 > self.best[0]:
                        self.best = roll.copy()
                        self.best[0] += 1
                    elif r > self.best[0]:
                        self.best = roll.copy()
                    if r == 2:
                        # check memeroll must stop
                        if self.mode == 2: break # memeroll mode A
                        elif self.mode == 3 and result['list'][-1][1].startswith("**"): break # memeroll mode B
                else: # using dummy gacha
                    result['list'].append([r, '']) # '' because no item names
                    result['detail'][r] += 1
                    if r == 2:
                        if self.mode == 2 or self.mode == 3: break  # memeroll mode A and B
                # end of a serie of 10 rolls, check for gachapin/mukku/etc...
                if i % 10 == 9:
                    if (self.mode == 11 or self.mode == 12) and result['detail'][2] >= 1: break # gachapin and mukku mode
                    elif self.mode == 13 and result['detail'][2] >= 5: break # super mukku mode
            self.result = result # store result
        except Exception as e:
            self.exception = e

    """updateThumbnail()
    Update self.thumbnail based on self.best content
    To use after generate()
    """
    async def updateThumbnail(self):
        if self.best[0] != -1 and self.best[1] != "":
            rid = await self.bot.do(self.bot.util.search_wiki_for_id, '>'.join(self.best[1].replace('**', '').split('>')[2:])) # retrieve the id from the wiki
            if rid is None: self.thumbnail = None # and update self.thumbnail accordingly
            elif rid.startswith('1'): self.thumbnail = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/m/{}.jpg".format(rid)
            elif rid.startswith('2'): self.thumbnail = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/m/{}.jpg".format(rid)
            else: self.thumbnail = None

    """scamRoll()
    Roll the Star Premium SSR and item

    Returns
    --------
    tuple:
        - choice: string, SSR name
        - loot: string, item name
    """
    def scamRoll(self):
        data, rateups, ssrrate, complete, index = self.scamdata # no error check, do it before
        roll = random.randint(1, self.bot.gacha.scam_rate) # roll a dice for the item
        loot = None
        n = 0
        for r in self.bot.gacha.scam: # iterate over items with our dice value
            n += r[0]
            if roll < n:
                loot = r
                break
        # pick the random ssr
        choice = self.bot.gacha.formatGachaItem(random.choice(data[2]['list'][list(data[2]['list'].keys())[0]]))
        self.best = [99, choice] # force ssr in self.best
        return choice, loot[1]

    """output()
    Output the result via a disnake Interaction
    
    Parameters
    --------
    inter: Interaction to use. Must have been deferred beforehand
    display_mode: Integer. 0=single roll, 1=ten roll, 2=memeroll, 3=ssr list
    titles: Tuple of 2 strings. First and Second embed titles to display
    """
    async def output(self, inter, display_mode:int, titles:tuple=("{}", "{}")):
        if 'list' not in self.result or self.exception is not None: # error check
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="An error occured", color=self.color))
            await self.bot.sendError("gachasim", self.exception)
            return
        elif self.mode == 14 and (self.scamdata is None or not self.scamdata[3]): # scam error check
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="No Star Premium Gachas available at selected index", color=self.color))
            return
        # set embed footer
        footer = "{}% SSR rate".format(self.result['rate'])
        match self.mode:
            case 3:
                footer += " ▫️ until rate up"
            case 14:
                footer += " ▫️ Selected Scam #{}".format(self.scamdata[4]+1)
            case _:
                pass
        if self.isclassic:
            footer += " ▫️ Classic"
        # get scam roll
        if self.scamdata is not None:
            sroll = self.scamRoll()
        # update thumbnail
        await self.updateThumbnail()
        # select crystal image
        if (100 * self.result['detail'][2] / len(self.result['list'])) >= self.result['rate']: crystal = random.choice(['https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png', 'https://media.discordapp.net/attachments/614716155646705676/761969229095632916/3_s.png'])
        elif (100 * self.result['detail'][1] / len(self.result['list'])) >= self.result['rate']: crystal = 'https://media.discordapp.net/attachments/614716155646705676/761969232866574376/2_s.png'
        else: crystal = random.choice(['https://media.discordapp.net/attachments/614716155646705676/761969231323070494/0_s.png', 'https://media.discordapp.net/attachments/614716155646705676/761976275706445844/1_s.png'])
        # startup msg
        view = Tap(self.bot, owner_id=inter.author.id)
        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[0].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, image=crystal, color=self.color, footer=footer), view=view)
        await view.wait()

        match display_mode:
            case 0: # single roll display
                r = self.result['list'][0]
                await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="{}{}".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(r[0])), r[1]), color=self.color, footer=footer, thumbnail=self.thumbnail), view=None)
            case 1: # ten roll display
                for i in range(0, 11):
                    msg = ""
                    for j in range(0, i):
                        if j >= 10: break
                        # write
                        msg += "{}{} ".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(self.result['list'][j][0])), self.result['list'][j][1])
                        if j % 2 == 1: msg += "\n"
                    for j in range(i, 10):
                        msg += '{}'.format(self.bot.emote.get('crystal{}'.format(self.result['list'][j][0])))
                        if j % 2 == 1: msg += "\n"
                    if self.scamdata is not None: msg += "{}{}\n{}".format(self.bot.emote.get('SSR'), self.bot.emote.get('crystal2'), self.bot.emote.get('red'))
                    await asyncio.sleep(0.7)
                    await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer, thumbnail=(self.thumbnail if (i == 10 and self.scamdata is None) else None)), view=None)
                if self.scamdata is not None:
                    msg = '\n'.join(msg.split('\n')[:-2])
                    msg += "\n{}**{}**\n{}**{}**".format(self.bot.emote.get('SSR'), sroll[0], self.bot.emote.get('red'), sroll[1])
                    await asyncio.sleep(1)
                    await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer, thumbnail=self.thumbnail), view=None)
            case 2: # meme roll display
                counter = [0, 0, 0]
                text = ""
                best = [-1, ""]
                if self.mode == 3: item_count = 5
                else: item_count = 3
                for i, v in enumerate(self.result['list']):
                    if i > 0 and i % item_count == 0:
                        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[0].format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description="{} {} ▫️ {} {} ▫️ {} {}\n{}".format(counter[2], self.bot.emote.get('SSR'), counter[1], self.bot.emote.get('SR'), counter[0], self.bot.emote.get('R'), text), color=self.color, footer=footer), view=None)
                        await asyncio.sleep(1)
                        text = ""
                    text += "{} {}\n".format(self.bot.emote.get({0:'R', 1:'SR', 2:'SSR'}.get(v[0])), v[1])
                    counter[v[0]] += 1
                title = (titles[1].format(inter.author.display_name, len(self.result['list'])) if (len(self.result['list']) < 300) else "{} sparked".format(inter.author.display_name))
                await inter.edit_original_message(embed=self.bot.util.embed(author={'name':title, 'icon_url':inter.author.display_avatar}, description="{} {} ▫️ {} {} ▫️ {} {}\n{}".format(counter[2], self.bot.emote.get('SSR'), counter[1], self.bot.emote.get('SR'), counter[0], self.bot.emote.get('R'), text), color=self.color, footer=footer, thumbnail=self.thumbnail), view=None)
            case 3: # spark display
                count = len(self.result['list'])
                rate = (100*self.result['detail'][2]/count)
                msg = ""
                best = [-1, ""]
                rolls = self.getSSRList()
                for r in rolls: # check for best roll
                    if best[0] < 3 and '**' in r: best = [3, r.replace('**', '')]
                    elif best[0] < 2: best = [2, r]
                if len(rolls) > 0 and self.complete:
                    msg = "{} ".format(self.bot.emote.get('SSR'))
                    for item in rolls:
                        msg += item
                        if rolls[item] > 1: msg += " x{}".format(rolls[item])
                        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name, count), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer), view=None)
                        await asyncio.sleep(0.75)
                        msg += " "
                if self.mode == 11: amsg = "Gachapin stopped after **{}** rolls\n".format(len(self.result['list']))
                elif self.mode == 12: amsg = "Mukku stopped after **{}** rolls\n".format(len(self.result['list']))
                elif self.mode == 13: amsg = "Super Mukku stopped after **{}** rolls\n".format(len(self.result['list']))
                else: amsg = ""
                msg = "{}{:} {:} ▫️ {:} {:} ▫️ {:} {:}\n{:}\n**{:.2f}%** SSR rate".format(amsg, self.result['detail'][2], self.bot.emote.get('SSR'), self.result['detail'][1], self.bot.emote.get('SR'), self.result['detail'][0], self.bot.emote.get('R'), msg, rate)
                await inter.edit_original_message(embed=self.bot.util.embed(author={'name':titles[1].format(inter.author.display_name, count), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer, thumbnail=self.thumbnail), view=None)

    """getSSRList()
    Extract the SSR from a full gacha list generated by gachaRoll()
    
    Returns
    --------
    dict: SSR List. The keys are the SSR name and the values are how many your rolled
    """
    def getSSRList(self):
        rolls = {}
        for r in self.result['list']:
            if r[0] == 2: rolls[r[1]] = rolls.get(r[1], 0) + 1
        return rolls

    """roulette()
    Simulate a roulette and output the result
    
    Parameters
    --------
    inter: Interaction to use. Must have been deferred beforehand
    legfest: Integer, -1 for auto mod, 0 to force 3%, 1 to force 6%
    """
    async def roulette(self, inter, legfest:int=-1):
        footer = ""
        roll = 0
        rps = ['rock', 'paper', 'scissor']
        ct = self.bot.util.JST()
        # customization settings
        fixedS = ct.replace(year=2022, month=3, day=29, hour=19, minute=0, second=0, microsecond=0) # beginning of fixed rolls
        fixedE = fixedS.replace(day=31, hour=0) # end of fixed rolls
        forced3pc = True # force 3%
        forcedRollCount = 100 # number of rolls during fixed rolls
        forcedSuperMukku = True
        enable200 = False # add 200 on wheel
        enableJanken = False
        maxJanken = 1 # number of RPS
        doubleMukku = False
        # settings end
        state = 0
        superFlag = False
        if ct >= fixedS and ct < fixedE:
            msg = "{} {} :confetti_ball: :tada: Guaranteed **{} 0 0** R O L L S :tada: :confetti_ball: {} {}\n".format(self.bot.emote.get('crystal'), self.bot.emote.get('crystal'), forcedRollCount//100, self.bot.emote.get('crystal'), self.bot.emote.get('crystal'))
            roll = forcedRollCount
            if forcedSuperMukku: superFlag = True
            if legfest == 1 and forced3pc:
                legfest = -1
            d = 0
            state = 1
        else:
            d = random.randint(1, 30000)
            if d < 600:
                if enabled200:
                    msg = "{} {} :confetti_ball: :tada: **2 0 0 R O L L S** :tada: :confetti_ball: {} {}\n".format(self.bot.emote.get('crystal'), self.bot.emote.get('crystal'), self.bot.emote.get('crystal'), self.bot.emote.get('crystal'))
                    roll = 200
                else:
                    msg = ":confetti_ball: :tada: **100** rolls!! :tada: :confetti_ball:\n"
                    roll = 100
            elif d < 3600:
                msg = "**Gachapin Frenzy** :four_leaf_clover:\n"
                roll = -1
                state = 2
            elif d < 14100:
                msg = "**10** rolls :pensive:\n"
                roll = 10
            elif d < 23100:
                msg = "**20** rolls :open_mouth:\n"
                roll = 20
            else:
                msg = "**30** rolls! :clap:\n"
                roll = 30
        await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"{} is spinning the Roulette".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer))
        if not enableJanken and state < 2: state = 1
        running = True
        # loop
        while running:
            if self.exception is not None:
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="An error occured", color=self.color))
                await self.bot.sendError("gachasim", self.exception)
                return
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
                    await self.bot.do(self.generate, roll, legfest)
                    count = len(self.result['list'])
                    rate = (100*self.result['detail'][2]/count)
                    ssrs = self.getSSRList()
                    if len(ssrs) > 0: # make the text
                        tmp = "\n{} ".format(self.bot.emote.get('SSR'))
                        for item in ssrs:
                            tmp += item
                            if ssrs[item] > 1: tmp += " x{}".format(ssrs[item])
                            tmp += " "
                    else:
                        tmp = ""
                    footer = "{}% SSR rate".format(self.result['rate'])
                    if self.isclassic:
                        footer += " ▫️ Classic"
                    msg += "{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(self.result['detail'][2], self.bot.emote.get('SSR'), self.result['detail'][1], self.bot.emote.get('SR'), self.result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                    if superFlag: state = 4
                    else: running = False
                case 2: # gachapin
                    self.changeMode('gachapin')
                    await self.bot.do(self.generate, 300, legfest)
                    count = len(self.result['list'])
                    rate = (100*self.result['detail'][2]/count)
                    ssrs = self.getSSRList()
                    if len(ssrs) > 0: # make the text
                        tmp = "\n{} ".format(self.bot.emote.get('SSR'))
                        for item in ssrs:
                            tmp += item
                            if ssrs[item] > 1: tmp += " x{}".format(ssrs[item])
                            tmp += " "
                    else:
                        tmp = ""
                    footer = "{}% SSR rate".format(self.result['rate'])
                    if self.isclassic:
                        footer += " ▫️ Classic"
                    msg += "Gachapin ▫️ **{}** rolls\n{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(count, self.result['detail'][2], self.bot.emote.get('SSR'), self.result['detail'][1], self.bot.emote.get('SR'), self.result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                    if count == 10 and random.randint(1, 100) < 99: state = 3
                    elif count == 20 and random.randint(1, 100) < 60: state = 3
                    elif count == 30 and random.randint(1, 100) < 30: state = 3
                    else: running = False
                case 3:
                    self.changeMode('mukku')
                    await self.bot.do(self.generate, 300, legfest)
                    count = len(self.result['list'])
                    rate = (100*self.result['detail'][2]/count)
                    ssrs = self.getSSRList()
                    if len(ssrs) > 0: # make the text
                        tmp = "\n{} ".format(self.bot.emote.get('SSR'))
                        for item in ssrs:
                            tmp += item
                            if ssrs[item] > 1: tmp += " x{}".format(ssrs[item])
                            tmp += " "
                    else:
                        tmp = ""
                    msg += ":confetti_ball: Mukku ▫️ **{}** rolls\n{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(count, self.result['detail'][2], self.bot.emote.get('SSR'), self.result['detail'][1], self.bot.emote.get('SR'), self.result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                    if doubleMukku:
                        if random.randint(1, 100) < 25: pass
                        else: running = False
                        doubleMukku = False
                    else:
                        running = False
                case 4:
                    self.changeMode('supermukku')
                    await self.bot.do(self.generate, 300, legfest)
                    count = len(self.result['list'])
                    rate = (100*self.result['detail'][2]/count)
                    ssrs = self.getSSRList()
                    if len(ssrs) > 0: # make the text
                        tmp = "\n{} ".format(self.bot.emote.get('SSR'))
                        for item in ssrs:
                            tmp += item
                            if ssrs[item] > 1: tmp += " x{}".format(ssrs[item])
                            tmp += " "
                    else:
                        tmp = ""
                    msg += ":confetti_ball: **Super Mukku** ▫️ **{}** rolls\n{:} {:} ▫️ {:} {:} ▫️ {:} {:}{:}\n**{:.2f}%** SSR rate\n\n".format(count, self.result['detail'][2], self.bot.emote.get('SSR'), self.result['detail'][1], self.bot.emote.get('SR'), self.result['detail'][0], self.bot.emote.get('R'), tmp, rate)
                    running = False
            await self.updateThumbnail()
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"{} spun the Roulette".format(inter.author.display_name), 'icon_url':inter.author.display_avatar}, description=msg, color=self.color, footer=footer, thumbnail=self.thumbnail))