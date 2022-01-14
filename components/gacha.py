import disnake
import asyncio
import random
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# Gacha Component
# ----------------------------------------------------------------------------------------------------------------
# Manage the real granblue gacha
# ----------------------------------------------------------------------------------------------------------------

class Gacha():
    def __init__(self, bot):
        self.bot = bot


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
    Process and retrieve the gacha rates
    
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
    def process(self, id, sub_id):
        try:
            # draw rate
            data = self.bot.gbf.request("http://game.granbluefantasy.jp/gacha/provision_ratio/{}/{}?PARAMS".format(id, sub_id), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check_update=True)
            
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
        except:
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
            data = self.bot.gbf.request("http://game.granbluefantasy.jp/gacha/list?PARAMS", account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check_update=True)
            if data is None: raise Exception()
            # will contain the data
            gacha_data = {}
            gacha_data['time'] = datetime.strptime(data['legend']['lineup'][-1]['end'], '%m/%d %H:%M').replace(year=c.year, microsecond=0)
            NY = False
            if c > gacha_data['time']:
                gacha_data['time'] = gacha_data['time'].replace(year=gacha_data['time'].year+1) # new year fix
                NY = True
            gacha_data['timesub'] = datetime.strptime(data['ceiling']['end'], '%Y/%m/%d %H:%M').replace(microsecond=0)
            if (NY == False and gacha_data['timesub'] < gacha_data['time']) or (NY == True and gacha_data['timesub'] > gacha_data['time']): gacha_data['time'] = gacha_data['timesub'] # switched
            random_key = data['legend']['random_key']
            header_images = data['header_images']
            logo = {'logo_fire':1, 'logo_water':2, 'logo_earth':3, 'logo_wind':4, 'logo_dark':5, 'logo_light':6}.get(data.get('logo_image', ''), data.get('logo_image', '').replace('logo_', ''))
            id = data['legend']['lineup'][-1]['id']

            # draw rate
            gacha_data['ratio'], gacha_data['list'], gacha_data['rateup'] = self.process(id, 1)
            if gacha_data['ratio'] is None:
                raise Exception()

            # add image
            gachas = ['{}/tips/description_gacha.jpg'.format(random_key), '{}/tips/description_gacha_{}.jpg'.format(random_key, logo), '{}/tips/description_{}.jpg'.format(random_key, header_images[0]), 'header/{}.png'.format(header_images[0])]
            for g in gachas:
                data = self.bot.gbf.request("http://game-a.granbluefantasy.jp/assets_en/img/sp/gacha/{}".format(g), no_base_headers=True)
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
                description += "\n"
                
                # build rate up list
                for k in content[1]['rateup']:
                    if k == 'zodiac':
                        if len(content[1]['rateup']['zodiac']) > 0:
                            description += "{} **Zodiac** ▫️ ".format(self.bot.emote.get('loot'))
                            for i in content[1]['rateup'][k]:
                                description += self.bot.util.formatGachaItem(i) + " "
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
                                    description += self.bot.util.formatGachaItem(item) + " "
                            description += "\n"
                return description, "http://game-a.granbluefantasy.jp/assets_en/img/sp/gacha/{}".format(content[1]['image'])
            return None, None
        except Exception as e:
            raise e


    """retrieve()
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
    def retrieve(self):
        try:
            gacha_data = self.get()[1]
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

    """isLegfest()
    Check the provided parameter and the real gacha to determine if we will be using a 6 or 3% SSR rate
    
    Parameters
    ----------
    selected: Integer, selected value by the user (-1 default, 0 is 3%, anything else is 6%)
    
    Returns
    --------
    bool: True if 6%, False if 3%
    """
    def isLegfest(self, selected):
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