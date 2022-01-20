import disnake
from disnake.ext import commands
import aiohttp
from datetime import datetime, timedelta
import random
import re
from bs4 import BeautifulSoup
from urllib import request, parse
from urllib.parse import unquote
import html
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import threading
import math
from views.url_button import UrlButton

# ----------------------------------------------------------------------------------------------------------------
# GranblueFantasy Cog
# ----------------------------------------------------------------------------------------------------------------
# All other Granblue Fantasy-related commands
# ----------------------------------------------------------------------------------------------------------------

class GranblueFantasy(commands.Cog):
    """Granblue Fantasy Utility."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x34aeeb
        self.rankre = re.compile("Rank ([0-9])+")
        self.rankre = re.compile("Rank ([0-9])+")
        self.sumre = re.compile("alt=\"([0-9]{10}|[0-9]{10}_0[1-9])\" />\\s*(<div class=\"prt-quality\">\\+[0-9]+</div>\\s*)?</div>\\s*<div class=\"prt-fix-spec\">\\s*<div id=\"js-fix-summon([0-9]{2})-name\" class=\"prt-fix-name\" name=\"[A-Za-z'-. ]+\">(Lvl [0-9]+ [A-Za-z'-. ]+)<\\/div>\\s*<div id=\"js-fix-summon[0-9]{2}-info\" class=\"prt-fix-info( bless-rank[0-4])?")
        self.starre = re.compile("<span class=\"prt-current-npc-name\">\\s*(Lvl [0-9]+ [A-Za-z'-.μ ]+)\\s*<\\/span>")
        self.starcomre = re.compile("<div class=\"prt-pushed-info\">(.+)<\\/div>")
        self.empre = re.compile("<div class=\"txt-npc-rank\">([0-9]+)<\\/div>")
        self.starringre = re.compile("<div class=\"ico-augment2-s\"><\\/div>\\s*<\\/div>\\s*<div class=\"prt-pushed-spec\">\\s*<div class=\"prt-pushed-info\">")
        self.starplusre = re.compile("<div class=\"prt-quality\">(\\+[0-9]+)<\\/div>")
        self.possiblesum = {'10':'fire', '11':'fire', '20':'water', '21':'water', '30':'earth', '31':'earth', '40':'wind', '41':'wind', '50':'light', '51':'light', '60':'dark', '61':'dark', '00':'misc', '01':'misc'}
        self.imgcache = {}
        self.imglock = threading.Lock()

    """getMaintenanceStatus()
    Check if GBF is in maintenance and return a string.
    Save data is updated if it doesn't match the current state.
    
    Returns
    --------
    str: Status string
    """
    def getMaintenanceStatus(self): # check the gbf maintenance status, empty string returned = no maintenance
        current_time = self.bot.util.JST()
        msg = ""
        if self.bot.data.save['maintenance']['state'] == True:
            if self.bot.data.save['maintenance']['time'] is not None and current_time < self.bot.data.save['maintenance']['time']:
                d = self.bot.data.save['maintenance']['time'] - current_time
                if self.bot.data.save['maintenance']['duration'] == 0:
                    msg = "{} Maintenance starts in **{}**".format(self.bot.emote.get('cog'), self.bot.util.delta2str(d, 2))
                else:
                    msg = "{} Maintenance starts in **{}**, for **{} hour(s)**".format(self.bot.emote.get('cog'), self.bot.util.delta2str(d, 2), self.bot.data.save['maintenance']['duration'])
            else:
                if self.bot.data.save['maintenance']['duration'] <= 0:
                    msg = "{} Emergency maintenance on going".format(self.bot.emote.get('cog'))
                else:
                    d = current_time - self.bot.data.save['maintenance']['time']
                    if (d.seconds // 3600) >= self.bot.data.save['maintenance']['duration']:
                        with self.bot.data.lock:
                            self.bot.data.save['maintenance'] = {"state" : False, "time" : None, "duration" : 0}
                            self.bot.data.pending = True
                    else:
                        e = self.bot.data.save['maintenance']['time'] + timedelta(seconds=3600*self.bot.data.save['maintenance']['duration'])
                        d = e - current_time
                        msg = "{} Maintenance ends in **{}**".format(self.bot.emote.get('cog'), self.bot.util.delta2str(d, 2))
        return msg

    @commands.slash_command(default_permission=True)
    @commands.cooldown(2, 20, commands.BucketType.user)
    @commands.max_concurrency(8, commands.BucketType.default)
    async def gbf(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    """stripWikiStr()
    Formating function for wiki skill descriptions
    
    Parameters
    ----------
    elem: String, html element
    
    Returns
    --------
    str: Stripped string
    """
    def stripWikiStr(self, elem):
        txt = elem.text.replace('foeBoost', 'foe. Boost') # special cases
        checks = [['span', 'tooltiptext'], ['sup', 'reference'], ['span', 'skill-upgrade-text']]
        for target in checks:
            f = elem.findChildren(target[0], class_=target[1])
            for e in f:
                txt = txt.replace(e.text, "")
        return txt.replace('Slight', '_sligHt_').replace('C.A.', 'CA').replace('.', '. ').replace('!', '! ').replace('?', '? ').replace(':', ': ').replace('. )', '.)').replace("Damage cap", "Cap").replace("Damage", "DMG").replace("damage", "DMG").replace(" and ", " and").replace(" and", " and ").replace("  ", " ").replace("fire", str(self.bot.emote.get('fire'))).replace("water", str(self.bot.emote.get('water'))).replace("earth", str(self.bot.emote.get('earth'))).replace("wind", str(self.bot.emote.get('wind'))).replace("dark", str(self.bot.emote.get('dark'))).replace("light", str(self.bot.emote.get('light'))).replace("Fire", str(self.bot.emote.get('fire'))).replace("Water", str(self.bot.emote.get('water'))).replace("Earth", str(self.bot.emote.get('earth'))).replace("Wind", str(self.bot.emote.get('wind'))).replace("Dark", str(self.bot.emote.get('dark'))).replace("Light", str(self.bot.emote.get('light'))).replace('_sligHt_', 'Slight')

    """processWikiMatch()
    Process a successful wiki search match
    
    Parameters
    ----------
    soup: beautifulsoup object
    
    Returns
    --------
    tuple: Containing:
        - data: Dict containing the match data
        - tables: List of wikitables on the page
    """
    def processWikiMatch(self, soup):
        data = {}
        # what we are interested in
        type_check = {"/Category:Fire_Characters":0, "/Category:Water_Characters":1, "/Category:Earth_Characters":2, "/Category:Wind_Characters":3, "/Category:Dark_Characters":4, "/Category:Light_Characters":5, "/Category:Special_Characters":6, "/Category:Fire_Summons":10, "/Category:Water_Summons":11, "/Category:Earth_Summons":12, "/Category:Wind_Summons":13, "/Category:Dark_Summons":14, "/Category:Light_Summons":15, "/Category:Special_Summons":16, "/Category:Sabre_Weapons":20, "/Category:Dagger_Weapons":21, "/Category:Spear_Weapons":22, "/Category:Axe_Weapons":23, "/Category:Staff_Weapons":24, "/Category:Gun_Weapons":25, "/Category:Melee_Weapons":26, "/Category:Bow_Weapons":27, "/Category:Harp_Weapons":28, "/Category:Katana_Weapons":29}
        for k, n in type_check.items(): # check if the page matches
            r = soup.find_all("a", {'href' : k})
            if len(r) > 0:
                data['object'] = n // 10 # 0 = chara, 1 = summon, 2 = weapon
                if data['object'] < 2: data['element'] = {0:'fire', 1:'water', 2:'earth', 3:'wind', 4:'dark', 5:'light', 6:'misc'}.get(n%10, "") # retrieve the element here for chara and summon
                else: data['type'] = k[len('/Category:'):k.find('_Weapons')].lower().replace('sabre', 'sword') # retrieve the wpn type here
                break
        # retrieve thumbnail if any
        try:
            i = soup.find_all("script", type="application/ld+json")[0].string
            s = i.find("\"image\" : \"")
            if s != -1:
                s += len("\"image\" : \"")
                e = i.find("\"", s)
                data['image'] = i[s:e]
        except:
            pass

        # retrieve ID
        tables = soup.find_all("table", class_='wikitable') # iterate all wikitable
        for t in tables:
            try:
                body = t.findChildren("tbody" , recursive=False)[0].findChildren("tr" , recursive=False) # check for tr tag
                for tr in body:
                    if str(tr).find("ID") != -1:
                        try:
                            if tr.findChildren("th")[0].text.strip() == "ID" and 'id' not in data:
                                data['id'] = tr.findChildren("td")[0].text
                        except: pass
            except:
                pass

        # retrieve description
        try: data['description'] = soup.find_all("meta", {'name' : 'description'})[0].attrs['content']
        except: pass

        # get rarity, title and name
        try: 
            header = soup.find_all("div", class_='char-header')[0] # get it
            try: # first we get the rarity
                data['rarity'] = str(header.findChildren("div" , class_='char-rarity', recursive=False)[0])
                if data['rarity'].find("Rarity SSR") != -1: data['rarity'] = "SSR"
                elif data['rarity'].find("Rarity SR") != -1: data['rarity'] = "SR"
                elif data['rarity'].find("Rarity R") != -1: data['rarity'] = "R"
                else: data['rarity'] = ""
            except:
                pass
            for child in header.findChildren("div" , recursive=False): # then the name and title if any
                if 'class' not in child.attrs:
                    for divs in child.findChildren("div" , recursive=False):
                        if 'class' in divs.attrs:
                            if 'char-name' in divs.attrs['class']: data['name'] = divs.text
                            elif 'char-title' in divs.attrs['class']:
                                try:
                                    tx = divs.findChildren("span", recursive=False)[0].text
                                    data['title'] = tx[1:tx.find("]")]
                                except:
                                    tx = divs.text
                                    data['title'] = tx[1:tx.find("]")]
        except:
            pass
        return data, tables

    """processWikiItem()
    Process the processWikiMatch() wikitables and add the result into data
    
    Parameters
    ----------
    data: processWikiMatch() data
    tables: processWikiMatch() tables
    
    Returns
    --------
    dict: Updated data (not a copy)
    """
    def processWikiItem(self, data, tables):
        # iterate all wikitable again
        for t in tables:
            body = t.findChildren("tbody" , recursive=False)[0].findChildren("tr" , recursive=False) # check for tr tag
            if str(body).find("Copyable?") != -1: continue # for chara skills if I add it one day
            expecting_hp = False
            expecting_wpn_skill = False
            expecting_sum_call = False
            aura = 0
            for tr in body: # iterate on tags
                content = str(tr)
                if expecting_sum_call:
                    if content.find("This is the call for") != -1 or content.find("This is the basic call for") != -1:
                        try: data['call'][1] = self.stripWikiStr(tr.findChildren("td")[0])
                        except: pass
                    else:
                        expecting_sum_call = False
                elif expecting_wpn_skill:
                    if 'class' in tr.attrs and tr.attrs['class'][0].startswith('skill'):
                        if tr.attrs['class'][-1] == "post" or (tr.attrs['class'][0] == "skill" and len(tr.attrs['class']) == 1):
                            try: 
                                n = tr.findChildren("td", class_="skill-name", recursive=False)[0].text.replace("\n", "")
                                d = tr.findChildren("td", class_="skill-desc", recursive=False)[0]
                                if 'skill' not in data: data['skill'] = []
                                data['skill'].append([n, self.stripWikiStr(d)])
                            except: pass
                    else:
                        expecting_wpn_skill = False
                elif expecting_hp:
                    if content.find('Level ') != -1:
                        childs = tr.findChildren(recursive=False)
                        try: data['lvl'] = childs[0].text[len('Level '):]
                        except: pass
                        try: data['hp'] = childs[1].text
                        except: pass
                        try: data['atk'] = childs[2].text
                        except: pass
                    else:
                        expecting_hp = False
                elif content.find('class="hp-text"') != -1 and content.find('class="atk-text"') != -1:
                    try:
                        expecting_hp = True
                        elem_table = {"/Weapon_Lists/SSR/Fire":"fire", "/Weapon_Lists/SSR/Water":"water", "/Weapon_Lists/SSR/Earth":"earth", "/Weapon_Lists/SSR/Wind":"wind", "/Weapon_Lists/SSR/Dark":"dark", "/Weapon_Lists/SSR/Light":"light"}
                        for s, e in elem_table.items():
                            if content.find(s) != -1:
                                data['element'] = e
                                break
                    except: pass
                elif content.find('"Skill charge attack.png"') != -1:
                    try:
                        n = tr.findChildren("td", class_="skill-name", recursive=False)[0].text
                        d = tr.findChildren("td", recursive=False)[-1]
                        data['ca'] = [n, self.stripWikiStr(d)]
                    except: pass
                elif content.find('"/Weapon_Skills"') != -1:
                    expecting_wpn_skill = True
                elif content.find('<a href="/Sword_Master" title="Sword Master">Sword Master</a>') != -1 or content.find('Status_Energized') != -1:
                    try:
                        tds = tr.findChildren("td", recursive=False)
                        n = tds[0].text
                        d = tds[1]
                        if 'sm' not in data: data['sm'] = []
                        data['sm'].append([n, self.stripWikiStr(d)])
                    except: pass
                elif content.find('"/Summons#Calls"') != -1:
                    try:
                        data['call'] = [tr.findChildren("th")[0].text[len("Call - "):], '']
                        expecting_sum_call = True
                    except: pass
                elif content.find("Main Summon") != -1:
                    aura = 1
                elif content.find("Sub Summon") != -1:
                    aura = 2
                elif content.find("This is the basic aura") != -1:
                    try:
                        if aura == 0: aura = 1
                        n = tr.findChildren("span", class_="tooltip")[0].text.split("This is the basic aura")[0]
                        d = tr.findChildren("td")[0]
                        if aura == 1: data['aura'] = self.stripWikiStr(d)
                        elif aura == 2: data['subaura'] = self.stripWikiStr(d)
                    except: pass
                elif content.find("This is the aura") != -1:
                    try:
                        n = tr.findChildren("span", class_="tooltip")[0].text.split("This is the aura")[0]
                        d = tr.findChildren("td")[0]
                        if aura == 1: data['aura'] = self.stripWikiStr(d)
                        elif aura == 2: data['subaura'] = self.stripWikiStr(d)
                    except: pass
        return data

    """requestWiki()
    Request a wiki page and post the result after calling processWikiMatch() and processWikiItem()
    
    Parameters
    ----------
    inter: Command interaction
    url: Wiki url to request (url MUST be for gbf.wiki)
    search_mode: Boolean, if True it expects a search result page
    """
    async def requestWiki(self, inter: disnake.GuildCommandInteraction, url, search_mode = False):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status != 200:
                    raise Exception("HTTP Error 404: Not Found")
                else:
                    cnt = await r.content.read()
                    try: cnt = cnt.decode('utf-8')
                    except: cnt = cnt.decode('iso-8859-1')
                    soup = BeautifulSoup(cnt, 'html.parser') # parse the html
                    try: title = soup.find_all("h1", id="firstHeading", class_="firstHeading")[0].text # page title
                    except: title = ""
                    if search_mode and not title.startswith('Search results'): # handling rare cases of the search function redirecting the user directly to a page
                        search_mode = False
                        url = "https://gbf.wiki/{}".format(title.replace(' ', '_')) # update the url so it looks pretty (with the proper page name)

                    if search_mode: # use the wiki search function
                        try:
                            res = soup.find_all("ul", class_="mw-search-results")[0].findChildren("li", class_="mw-search-result", recursive=False) # recuperate the search results
                        except:
                            raise Exception("HTTP Error 404: Not Found") # no results
                        matches = []
                        for r in res: # for each, get the title
                            matches.append(r.findChildren("div", class_="mw-search-result-heading", recursive=False)[0].findChildren("a", recursive=False)[0].attrs['title'])
                            if len(matches) >= 5: break # max 5
                        if len(matches) == 0: # no results check
                            raise Exception("No results")
                        elif len(matches) == 1: # single result, request it directly
                            await self.requestWiki(inter, "https://gbf.wiki/{}".format(matches[0]))
                            return
                        desc = ""
                        for m in matches: # build the message with the results
                            desc += "[{}](https://gbf.wiki/{})\n".format(m, m.replace(" ", "_"))
                        desc = "First five results\n{}".format(desc)
                        await inter.edit_original_message(embed=self.bot.util.embed(title="Not Found, click here to refine", description=desc, url=url, color=self.color))
                    else: # direct access to the page (assume a match)
                        data, tables = await self.bot.do(self.processWikiMatch, soup)

                        x = data.get('object', None)
                        match x:
                            case None: # if no match
                                await inter.edit_original_message(embed=self.bot.util.embed(title=title, description=data.get('description', ''), image=data.get('image', ''), url=url, footer=data.get('id', ''), color=self.color))
                            case 0: # character
                                if 'title' in data: title = title + ", " + data['title']
                                if 'rarity' in data: title = "{} {}".format(self.bot.emote.get(data['rarity']), title)
                                try:
                                    # check all character versions
                                    versions = soup.find_all("div", class_="character__versions")[0].findChildren("table", recursive=False)[0].findChildren("tbody", recursive=False)[0].findChildren("tr", recursive=False)[2].findChildren("td", recursive=False)
                                    elems = []
                                    for v in versions:
                                        s = v.findChildren("a", recursive=False)[0].text
                                        if s != title: elems.append(s)
                                    if len(elems) == 0: raise Exception()
                                    desc = "This character has other versions\n"
                                    for e in elems:
                                        desc += "[{}](https://gbf.wiki/{})\n".format(e, e.replace(" ", "_"))
                                    await inter.edit_original_message(embed=self.bot.util.embed(title=title, description=desc, image=data.get('image', ''), url=url, footer=data.get('id', ''), color=self.color))
                                except: # if none, just send the link
                                    await inter.edit_original_message(embed=self.bot.util.embed(title=title, description=data.get('description', ''), image=data.get('image', ''), url=url, footer=data.get('id', ''), color=self.color))
                            case _: # summon and weapon
                                data = await self.bot.do(self.processWikiItem, data, tables)
                                # final message
                                title = ""
                                title += "{}".format(self.bot.emote.get(data.get('element', '')))
                                title += "{}".format(self.bot.emote.get(data.get('rarity', '')))
                                title += "{}".format(self.bot.emote.get(data.get('type', '')))
                                title += "{}".format(data.get('name', ''))
                                if 'title' in data: title += ", {}".format(data['title'])

                                desc = ""
                                if 'lvl' in data: desc += "**Lvl {}** ".format(data['lvl'])
                                if 'hp' in data: desc += "{} {} ".format(self.bot.emote.get('hp'), data['hp'])
                                if 'atk' in data: desc += "{} {}".format(self.bot.emote.get('atk'), data['atk'])
                                if desc != "": desc += "\n"
                                if 'ca' in data: desc += "{} **{}**▫️{}\n".format(self.bot.emote.get('skill1'), data['ca'][0], data['ca'][1])
                                if 'skill' in data:
                                    for s in data['skill']:
                                        desc += "{} **{}**▫️{}\n".format(self.bot.emote.get('skill2'), s[0], s[1])
                                if 'sm' in data:
                                    if desc != "": desc += "\n"
                                    for s in data['sm']:
                                        if s[0] == "Attack" or s[0] == "Defend": continue
                                        desc += "**{}**▫️{}\n".format(s[0], s[1])
                                if 'call' in data: desc += "{} **{}**▫️{}\n".format(self.bot.emote.get('skill1'), data['call'][0], data['call'][1])
                                if 'aura' in data: desc += "{} **Aura**▫️{}\n".format(self.bot.emote.get('skill2'), data['aura'])
                                if 'subaura' in data: desc += "{} **Sub Aura**▫️{}\n".format(self.bot.emote.get('skill2'), data['subaura'])

                                await inter.edit_original_message(embed=self.bot.util.embed(title=title, description=desc, thumbnail=data.get('image', ''), url=url, footer=data.get('id', ''), color=self.color))
        await self.bot.util.clean(inter, 80)

    @gbf.sub_command()
    async def wiki(self, inter: disnake.GuildCommandInteraction, terms : str = commands.Param(description="Search expression")):
        """Search the GBF wiki"""
        await inter.response.defer()
        # build the url (the wiki is case sensitive)
        arr = []
        for s in terms.split(" "):
            arr.append(self.bot.util.wiki_fixCase(s))
        sch = "_".join(arr)
        url = "https://gbf.wiki/{}".format(sch)
        try:
            await self.requestWiki(inter, url) # try to request
        except Exception as e:
            url = "https://gbf.wiki/index.php?title=Special:Search&search={}".format(parse.quote_plus(terms))
            if str(e) != "HTTP Error 404: Not Found": # unknown error, we stop here
                await self.bot.sendError("wiki", e)
                await inter.edit_original_message(embed=self.bot.util.embed(title="Unexpected error, click here to search", url=url, footer=str(e), color=self.color))
            else: # failed, we try the search function
                try:
                    await self.requestWiki(inter, url, True) # try
                except Exception as f:
                    if str(f) == "No results":
                        await inter.edit_original_message(embed=self.bot.util.embed(title="No matches found", color=self.color)) # no results
                    else:
                        await inter.edit_original_message(embed=self.bot.util.embed(title="Not Found, click here to refine", url=url, color=self.color)) # no results
        await self.bot.util.clean(inter, 45)

    @gbf.sub_command()
    async def leechlist(self, inter: disnake.GuildCommandInteraction):
        """Post a link to /gbfg/ leechlist collection"""
        ls = self.bot.data.config['strings']["leechlist()"].split(";")
        # note: string is in the following format:
        # button label 1###url 1;button label 2###url 2;...;button label N###url N
        urls = []
        for l in ls:
            if l == "": continue
            urls.append(l.split("###"))
        view = UrlButton(self.bot, urls)
        await inter.response.send_message('\u200b', view=view)
        view.stopall()
        await self.bot.util.clean(inter, 60)

    @gbf.sub_command()
    async def spreadsheet(self, inter: disnake.GuildCommandInteraction):
        """Post a link to my SpreadSheet Folder"""
        view = UrlButton(self.bot, [('SpreadSheet Folder', self.bot.data.config['strings']["sheetfolder()"])])
        await inter.response.send_message('\u200b', view=view)
        view.stopall()
        await self.bot.util.clean(inter, 60)

    @gbf.sub_command()
    async def info(self, inter: disnake.GuildCommandInteraction):
        """Post various Granblue Fantasy informations"""
        current_time = self.bot.util.JST()
        description = "{:} Current Time is **{:02d}:{:02d} JST**".format(self.bot.emote.get('clock'), current_time.hour, current_time.minute)

        if self.bot.data.save['gbfversion'] is not None:
            description += "\n{} Version is `{}` (`{}`)".format(self.bot.emote.get('cog'), self.bot.data.save['gbfversion'], self.bot.gbf.version2str(self.bot.data.save['gbfversion']))

        reset = current_time.replace(hour=5, minute=0, second=0, microsecond=0)
        if current_time.hour >= reset.hour:
            reset += timedelta(days=1)
        d = reset - current_time
        description += "\n{} Reset in **{}**".format(self.bot.emote.get('mark'), self.bot.util.delta2str(d))

        id = str(inter.author.guild.id)
        if id in self.bot.data.save['st']:
            st1 = current_time.replace(hour=self.bot.data.save['st'][id][0], minute=0, second=0, microsecond=0)
            st2 = st1.replace(hour=self.bot.data.save['st'][id][1])

            if current_time.hour >= st1.hour:
                st1 += timedelta(days=1)
            if current_time.hour >= st2.hour:
                st2 += timedelta(days=1)

            d = st1 - current_time
            if d.seconds >= 82800: description += "\n{} Strike times in {} **On going** ".format(self.bot.emote.get('st'), self.bot.emote.get('1'))
            else: description += "\n{} Strike times in {} **{}** ".format(self.bot.emote.get('st'), self.bot.emote.get('1'), self.bot.util.delta2str(d))
            d = st2 - current_time
            if d.seconds >= 82800: description += "{} **On going**".format(self.bot.emote.get('2'))
            else: description += "{} **{}**".format(self.bot.emote.get('2'), self.bot.util.delta2str(d))

        try:
            buf = self.getMaintenanceStatus()
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getMaintenanceStatus", e)

        try:
            buf = await self.bot.do(self.bot.gacha.get)
            if len(buf) > 0:
                description += "\n{} Current gacha ends in **{}**".format(self.bot.emote.get('SSR'), self.bot.util.delta2str(buf[1]['time'] - buf[0], 2))
                if buf[1]['time'] != buf[1]['timesub']:
                    description += " (Spark period ends in **{}**)".format(self.bot.util.delta2str(buf[1]['timesub'] - buf[0], 2))
        except Exception as e:
            await self.bot.sendError("getgachatime", e)

        try:
            if current_time < self.bot.data.save['stream']['time']:
                description += "\n{} Stream starts in **{}**".format(self.bot.emote.get('crystal'), self.bot.util.delta2str(self.bot.data.save['stream']['time'] - current_time, 2))
        except:
            pass

        try:
            buf = self.bot.get_cog('GuildWar').getGWState()
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getgwstate", e)

        try:
            buf = self.bot.get_cog('DreadBarrage').getBarrageState()
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getBarrageState", e)

        try:
            buf = self.bot.get_cog('GuildWar').getNextBuff(inter)
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getnextbuff", e)

        await inter.response.send_message(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, color=self.color))

    @gbf.sub_command()
    async def maintenance(self, inter: disnake.GuildCommandInteraction):
        """Post GBF maintenance status"""
        try:
            description = self.getMaintenanceStatus()
            if len(description) > 0:
                await inter.response.send_message(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, color=self.color))
            else:
                await inter.response.send_message(embed=self.bot.util.embed(title="Granblue Fantasy", description="No maintenance in my memory", color=self.color))
        except Exception as e:
            await self.bot.sendError("getMaintenanceStatus", e)

    @gbf.sub_command()
    async def raidfinder(self, inter: disnake.GuildCommandInteraction):
        """Post the (You) python raidfinder"""
        ls = self.bot.data.config['strings']["pyfinder()"].split(";")
        # note: string is in the following format:
        # button label 1###url 1;button label 2###url 2;...;button label N###url N
        urls = []
        for l in ls:
            if l == "": continue
            urls.append(l.split("###"))
        view = UrlButton(self.bot, urls)
        await inter.response.send_message('\u200b', view=view)
        view.stopall()
        await self.bot.util.clean(inter, 60)

    @gbf.sub_command()
    async def stream(self, inter: disnake.GuildCommandInteraction, op : str = commands.Param(default="")):
        """Post the stream text"""
        if len(self.bot.data.save['stream']['content']) == 0:
            await inter.response.send_message(embed=self.bot.util.embed(title="No event or stream available", color=self.color))
        elif op == "raw":
            msg = ""
            for c in self.bot.data.save['stream']['content']:
                msg += c + '\n'
            await inter.response.send_message(embed=self.bot.util.embed(title="Raw Stream Data", description='`' + msg + '`', color=self.color), ephemeral=True)
        else:
            title = self.bot.data.save['stream']['content'][0]
            msg = ""
            current_time = self.bot.util.JST()
            if self.bot.data.save['stream']['time'] is not None:
                if current_time < self.bot.data.save['stream']['time']:
                    d = self.bot.data.save['stream']['time'] - current_time
                    cd = "{}".format(self.bot.util.delta2str(d, 2))
                else:
                    cd = "On going!!"
            else:
                cd = ""
            for i in range(1, len(self.bot.data.save['stream']['content'])):
                if cd != "" and self.bot.data.save['stream']['content'][i].find('{}') != -1:
                    msg += self.bot.data.save['stream']['content'][i].format(cd) + "\n"
                else:
                    msg += self.bot.data.save['stream']['content'][i] + "\n"
            
            if cd != "" and title.find('{}') != -1:
                title = title.format(cd) + "\n"

            await inter.response.send_message(embed=self.bot.util.embed(title=title, description=msg, color=self.color))

    @gbf.sub_command()
    async def schedule(self, inter: disnake.GuildCommandInteraction, raw : int = commands.Param(default=0)):
        """Post the GBF schedule"""
        if len(self.bot.data.save['schedule']) == 0:
            await inter.response.send_message(embed=self.bot.util.embed(title="No schedule available", color=self.color))
        else:
            l = len(self.bot.data.save['schedule'])
            if raw == 0: l = l - (l%2) # need an even amount, skipping the last one if odd
            i = 0
            msg = ""
            c = self.bot.util.JST()
            nx = None
            md = c.month * 100 + c.day
            while i < l:
                if raw != 0:
                    if i != 0: msg += ";"
                    else: msg += "`"
                    msg += self.bot.data.save['schedule'][i]
                    i += 1
                else:
                    try: # checking if the event is on going (to bold it)
                        dates = self.bot.data.save['schedule'][i].replace(' ', '').split('-')
                        ev_md = []
                        for di in range(0, len(dates)):
                            if "??" in dates[di]: break
                            ev_md.append(int(dates[di].split('/')[0]) * 100 + int(dates[di].split('/')[1]))
                        if len(ev_md) == 2:
                            if ev_md[0] - md >= 1000: ev_md[0] -= 1200 # new year fixes
                            elif md - ev_md[1] >= 1000: ev_md[1] += 1200
                            on_going = (md >= ev_md[0] and md <= ev_md[1])
                        else:
                            on_going = (md >= ev_md[0])
                    except:
                        on_going = False
                    # check if it's the next event in line
                    if not on_going:
                        try:
                            dates = self.bot.data.save['schedule'][i].replace(' ', '').split('-')
                            evd = dates[0].split('/')
                            evt = c.replace(month=int(evd[0]), day=int(evd[1]), hour=18, minute=0, second=0, microsecond=0)
                            if evt > c and (nx is None or evt < nx):
                                nx = evt
                                if nx - c > timedelta(days=300): # new year fix
                                    nx = None
                        except:
                            pass
                    if on_going: msg += "**"
                    if l > 12: # enable or not emotes (I have 6 numbered emotes, so 6 field max aka 12 elements in my array)
                        msg += "{} ▫️ {}".format(self.bot.data.save['schedule'][i], self.bot.data.save['schedule'][i+1])
                        i += 2
                    else:
                        msg += "{} {} ▫️ {}".format(self.bot.emote.get(str((i//2)+1)), self.bot.data.save['schedule'][i], self.bot.data.save['schedule'][i+1])
                        i += 2
                    if on_going: msg += "**"
                    msg += "\n"
            if raw != 0: msg += "`"
            else:
                if nx is not None and c < nx:
                    msg += "{} Next event approximately in **{}**\n".format(self.bot.emote.get('mark'), self.bot.util.delta2str(nx - c, 2))
                try:
                    buf = self.getMaintenanceStatus()
                    if len(buf) > 0: msg += buf + '\n'
                except Exception as e:
                    await self.bot.sendError("getMaintenanceStatus", e)
                try:
                    current_time = self.bot.util.JST()
                    if current_time < self.bot.data.save['stream']['time']:
                        msg += "{} Stream starts in **{}**".format(self.bot.emote.get('crystal'), self.bot.util.delta2str(self.bot.data.save['stream']['time'] - current_time, 2))
                except:
                    pass
            await inter.response.send_message(embed=self.bot.util.embed(title="🗓 Event Schedule {} {:%Y/%m/%d %H:%M} JST".format(self.bot.emote.get('clock'), self.bot.util.JST()), url="https://twitter.com/granblue_en", color=self.color, description=msg))

    @gbf.sub_command()
    async def koregra(self, inter: disnake.GuildCommandInteraction):
        """Post the time to the next monthly dev post"""
        c = self.bot.util.JST()
        try:
            if c < self.bot.data.save['stream']['time']:
                target = self.bot.data.save['stream']['time']
            else:
                raise Exception()
        except:
            if c.day == 1:
                if c.hour >= 12:
                    if c.month == 12: target = datetime(year=c.year+1, month=1, day=1, hour=12, minute=0, second=0, microsecond=0)
                    else: target = datetime(year=c.year, month=c.month+1, day=1, hour=12, minute=0, second=0, microsecond=0)
                else:
                    target = datetime(year=c.year, month=c.month, day=1, hour=12, minute=0, second=0, microsecond=0)
            else:
                if c.month == 12: target = datetime(year=c.year+1, month=1, day=1, hour=12, minute=0, second=0, microsecond=0)
                else: target = datetime(year=c.year, month=c.month+1, day=1, hour=12, minute=0, second=0, microsecond=0)
        delta = target - c
        await inter.response.send_message(embed=self.bot.util.embed(title="{} Kore Kara".format(self.bot.emote.get('clock')), description="Release approximately in **{}**".format(self.bot.util.delta2str(delta, 2)),  url="https://granbluefantasy.jp/news/index.php", thumbnail="http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png", color=self.color))

    @gbf.sub_command()
    async def critical(self, inter: disnake.GuildCommandInteraction, weapons : str = commands.Param(description='List of weapon modifiers. Put nothing to get the list.', default='')):
        """Calculate critical rate"""
        values = {'small10':2, 'small15':3, 'small20':4, 'medium10':5, 'medium15':6.5, 'medium20':7.5, 'big10':8, 'big15':10, 'big20':11, 'bigii15':12, 'wamdus':20, 'hercules':11.5, 'sephira':30}
        ts = {'small':'small15', 'med':'medium15', 'medium':'medium15', 'big':'big15', 'big2':'bigii15', 's10':'small10', 's15':'small15', 's20':'small20', 'm10':'medium10', 'm15':'medium15', 'm20':'medium20', 'med10':'medium10', 'med15':'medium15', 'med20':'medium20', 'b10':'big10', 'b15':'big15', 'b20':'big20', 'bii10':'bigii10', 'bii15':'bigii15', 'b210':'bigii10', 'b215':'bigii15', 'big210':'bigii10', 'big215':'bigii15', 'ameno':'medium20', 'gaebulg':'medium20', 'bulg':'medium20', 'bulge':'medium20', 'gae':'medium20', 'mjolnir':'small20', 'herc':'hercules', 'ecke':'medium15', 'eckesachs':'medium15', 'sachs':'medium15', 'blut':'small15', 'blutgang':'small15', 'indra':'medium15', 'ivory':'bigii15', 'ivoryark':'bigii15', 'ark':'bigii15', 'auberon':'medium15', 'aub':'medium15', 'taisai':'big15', 'pholia':'big15', 'galilei':'medium15', 'europa':'medium15', 'benedia':'medium15', 'thunderbolt':'big15', 'shibow':'big15', 'rein':'bigii15', 'babel':'bigii15', 'mandeb':'bigii15', 'bab-el-mandeb':'bigii15', 'arca':'sephira', 'arcarum':'sephira', 'spoon':'medium15', 'coruscant':'medium15', 'crozier':'medium15', 'eva':'bigii15', 'evanescence':'bigii15', 'opus':'medium20'}
        flats = ['wamdus', 'sephira']
        try:
            if weapons == "": raise Exception("Empty Parameter")
            mods = weapons.lower().split(' ')
            s1 = ""
            s2 = ""
            base = 0
            flat = 0
            for m in mods:
                if ts.get(m, m) in flats:
                    flat += values[ts.get(m, m)]
                    s2 += "{}+".format(values[ts.get(m, m)])
                else:
                    if len(m) > 0 and m[0] == 'u':
                        flat += values[ts.get(m[1:], m[1:])]
                        s2 += "{}+".format(values[ts.get(m[1:], m[1:])])
                    else:
                        base += values[ts.get(m, m)]
                        s1 += "{}+".format(values[ts.get(m, m)])
            if s1 != "": s1 = "Boosted " + s1[:-1]
            if s2 != "":
                if s1 != "": s1 += ", "
                s1 = s1 + "Unboosted " + s2[:-1]
            msg =  "**Aura ▫️ Critical ▫️▫️ Aura ▫️ Critical**\n"
            msg += "140% ▫️ {:.1f}% ▫️▫️ 290% ▫️ {:.1f}%\n".format(min(base*2.4 + flat, 100), min(base*3.9 + flat, 100))
            msg += "150% ▫️ {:.1f}% ▫️▫️ 300% ▫️ {:.1f}%\n".format(min(base*2.5 + flat, 100), min(base*4 + flat, 100))
            msg += "160% ▫️ {:.1f}% ▫️▫️ 310% ▫️ {:.1f}%\n".format(min(base*2.6 + flat, 100), min(base*4.1 + flat, 100))
            msg += "170% ▫️ {:.1f}% ▫️▫️ 320% ▫️ {:.1f}%\n".format(min(base*2.7 + flat, 100), min(base*4.2 + flat, 100))
            msg += "280% ▫️ {:.1f}%\n".format(min(base*3.8 + flat, 100))
            await inter.response.send_message(embed=self.bot.util.embed(title="Critical Calculator", description=msg.replace('.0%', '%').replace('100%', '**100%**'), footer=s1, color=self.color), ephemeral=True)
        except Exception as e:
            if str(e) == "Empty Parameter":
                modstr = ""
                for m in values:
                    modstr += "`{}`, ".format(m)
                for m in ts:
                    modstr += "`{}`, ".format(m)
                await inter.response.send_message(embed=self.bot.util.embed(title="Critical Calculator", description="**Posible modifiers:**\n" + modstr[:-2] + "\n\nModifiers must be separated by spaces\nAdd `u` before a modifier to make it unboosted" , color=self.color), ephemeral=True)
            else:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description=str(e), color=self.color), ephemeral=True)

    @gbf.sub_command()
    async def enmity(self, inter: disnake.GuildCommandInteraction, hp : int = commands.Param(description="HP%", ge=1, le=100, default=60), weapons : str = commands.Param(description='List of weapon modifiers. Put nothing to get the list.', default='')):
        """Calculate enmity strength at a specific hp value"""
        values = {'small10':6, 'small15':7, 'small20':7.5, 'medium10':8, 'medium15':10, 'big10':10, 'big15':12.5, 'big20':13.5}
        ts = {'small':'small15', 'med':'medium15', 'medium':'medium15', 'big':'big15', 's10':'small10', 's15':'small15', 's20':'small20', 'm10':'medium10', 'm15':'medium15', 'med10':'medium10', 'med15':'medium15', 'b10':'big10', 'b15':'big15', 'b20':'big20', 'opus':'big20'}
        flats = []
        try:
            if hp < 1: hp = 1
            elif hp > 100: hp = 100
            if weapons == "": raise Exception("Empty Parameter")
            mods = weapons.lower().split(' ')
            s1 = ""
            s2 = ""
            base = 0
            flat = 0
            for m in mods:
                if ts.get(m, m) in flats:
                    flat += values[ts.get(m, m)]
                    s2 += "{}+".format(values[ts.get(m, m)])
                else:
                    if len(m) > 0 and m[0] == 'u':
                        flat += values[ts.get(m[1:], m[1:])]
                        s2 += "{}+".format(values[ts.get(m[1:], m[1:])])
                    else:
                        base += values[ts.get(m, m)]
                        s1 += "{}+".format(values[ts.get(m, m)])
            if s1 != "": s1 = "Boosted " + s1[:-1]
            if s2 != "":
                if s1 != "": s1 += ", "
                s1 = s1 + "Unboosted " + s2[:-1]
            hp_ratio = 1 - hp / 100.0
            base_val = base * ((1 + 2 * hp_ratio) * hp_ratio)
            flat_val = flat * ((1 + 2 * hp_ratio) * hp_ratio)
            msg =  "**Aura ▫️ Enmity ▫️▫️ Aura ▫️ Enmity**\n"
            msg += "140% ▫️ {:.1f}% ▫️▫️ 290% ▫️ {:.1f}%\n".format(base_val*2.4 + flat_val, base_val*3.9 + flat_val)
            msg += "150% ▫️ {:.1f}% ▫️▫️ 300% ▫️ {:.1f}%\n".format(base_val*2.5 + flat_val, base_val*4 + flat_val)
            msg += "160% ▫️ {:.1f}% ▫️▫️ 310% ▫️ {:.1f}%\n".format(base_val*2.6 + flat_val, base_val*4.1 + flat_val)
            msg += "170% ▫️ {:.1f}% ▫️▫️ 320% ▫️ {:.1f}%\n".format(base_val*2.7 + flat_val, base_val*4.2 + flat_val)
            msg += "280% ▫️ {:.1f}%\n".format(base_val*3.8 + flat_val)
            await inter.response.send_message(embed=self.bot.util.embed(title="Enmity Calculator ▫️ {}% HP".format(hp), description=msg.replace('.0%', '%'), footer=s1, color=self.color), ephemeral=True)
        except Exception as e:
            if str(e) == "Empty Parameter":
                modstr = ""
                for m in values:
                    modstr += "`{}`, ".format(m)
                for m in ts:
                    modstr += "`{}`, ".format(m)
                await inter.response.send_message(embed=self.bot.util.embed(title="Enmity Calculator", description="**Posible modifiers:**\n" + modstr[:-2] + "\n\nModifiers must be separated by spaces\nAdd `u` before a modifier to make it unboosted" , color=self.color), ephemeral=True)
            else:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description=str(e), color=self.color), ephemeral=True)

    @gbf.sub_command()
    async def stamina(self, inter: disnake.GuildCommandInteraction, hp : int = commands.Param(description="HP%", ge=1, le=100, default=100), weapons : str = commands.Param(description='List of weapon modifiers. Put nothing to get the list.', default='')):
        """Calculate stamina strength at a specific hp value"""
        values = {'medium10':(10, 65), 'medium15':(15, 65), 'medium20':(20, 65), 'big10':(10, 56.4), 'big15':(15, 56.4), 'big20':(20, 56.4), 'bigii10':(10, 53.7), 'bigii15':(15, 53.7), 'ancestral':(15, 50.4), 'omegamedium10':(10, 60.4), 'omegamedium15':(15, 60.4), 'omegabig10':(10, 56.4), 'omegabig15':(15, 56.4)}
        ts = {'med':'medium15', 'medium':'medium15', 'big':'big15', 'big2':'bigii15', 'omed':'omegamedium15', 'omedium':'omegamedium15', 'obig':'omegabig15', 'm10':'medium10', 'm15':'medium15', 'm20':'medium20', 'med10':'medium10', 'med15':'medium15', 'med20':'medium20', 'b10':'big10', 'b15':'big15', 'b20':'big20', 'bii10':'bigii10', 'bii15':'bigii15', 'b210':'bigii10', 'b215':'bigii15', 'big210':'bigii10', 'big215':'bigii15', 'dragon':'ancestral', 'opus':'big20', 'om10':'omegamedium10', 'om15':'omegamedium15', 'omed10':'omegamedium10', 'omed15':'omegamedium15', 'ob10':'omegabig10', 'ob15':'omegabig15'}
        flats = ['ancestral']
        try:
            if hp < 1: hp = 1
            elif hp > 100: hp = 100
            if weapons == "": raise Exception("Empty Parameter")
            mods = weapons.lower().split(' ')
            if hp < 25:
                s1 = ""
                base_val = 0
                flat_val = 0
            else:
                s1 = ""
                s2 = ""
                base = 0
                flat = 0
                hp_ratio = 100.0 * hp / 100.0
                for m in mods:
                    if ts.get(m, m) in flats:
                        v = values[ts.get(m, m)]
                        if v[0] > 15: v = math.pow(hp_ratio / (v[1] - (15 + (0.4 * (v[0] - 15)))), 2.9) + 2.1
                        else: v = math.pow(hp_ratio / (v[1] - v[0]), 2.9) + 2.1
                        flat += v
                        s2 += "{:.1f}+".format(v)
                    else:
                        if len(m) > 0 and m[0] == 'u':
                            v = values[ts.get(m[1:], m[1:])]
                            if v[0] > 15: v = math.pow(hp_ratio / (v[1] - (15 + (0.4 * (v[0] - 15)))), 2.9) + 2.1
                            else: v = math.pow(hp_ratio / (v[1] - v[0]), 2.9) + 2.1
                            flat += v
                            s2 += "{:.1f}+".format(v)
                        else:
                            v = values[ts.get(m, m)]
                            if v[0] > 15: v = math.pow(hp_ratio / (v[1] - (15 + (0.4 * (v[0] - 15)))), 2.9) + 2.1
                            else: v = math.pow(hp_ratio / (v[1] - v[0]), 2.9) + 2.1
                            base += v
                            s1 += "{:.1f}+".format(v)
                if s1 != "": s1 = "Boosted " + s1[:-1]
                if s2 != "":
                    if s1 != "": s1 += ", "
                    s1 = s1 + "Unboosted " + s2[:-1]
                base_val = base * ((1 + 2 * hp_ratio) * hp_ratio)
                flat_val = flat * ((1 + 2 * hp_ratio) * hp_ratio)
            msg =  "**Aura ▫️ Stamina ▫️▫️ Aura ▫️ Stamina**\n"
            msg += "140% ▫️ {:.1f}% ▫️▫️ 290% ▫️ {:.1f}%\n".format(base_val*2.4 + flat_val, base_val*3.9 + flat_val)
            msg += "150% ▫️ {:.1f}% ▫️▫️ 300% ▫️ {:.1f}%\n".format(base_val*2.5 + flat_val, base_val*4 + flat_val)
            msg += "160% ▫️ {:.1f}% ▫️▫️ 310% ▫️ {:.1f}%\n".format(base_val*2.6 + flat_val, base_val*4.1 + flat_val)
            msg += "170% ▫️ {:.1f}% ▫️▫️ 320% ▫️ {:.1f}%\n".format(base_val*2.7 + flat_val, base_val*4.2 + flat_val)
            msg += "280% ▫️ {:.1f}%\n".format(base_val*3.8 + flat_val)
            await inter.response.send_message(embed=self.bot.util.embed(title="Stamina Calculator ▫️ {}% HP".format(hp), description=msg.replace('.0%', '%'), footer=s1.replace('.0', ''), color=self.color), ephemeral=True)
        except Exception as e:
            if str(e) == "Empty Parameter":
                modstr = ""
                for m in values:
                    modstr += "`{}`, ".format(m)
                for m in ts:
                    modstr += "`{}`, ".format(m)
                await inter.response.send_message(embed=self.bot.util.embed(title="Stamina Calculator", description="**Posible modifiers:**\n" + modstr[:-2] + "\n\nModifiers must be separated by spaces\nAdd `u` before a modifier to make it unboosted" , color=self.color))
            else:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description=str(e), color=self.color), ephemeral=True)

    @gbf.sub_command()
    async def xp(self, inter: disnake.GuildCommandInteraction, start_level : int = commands.Param(description="Starting Point of the calcul", ge=1, le=149, default=1), end_level : int = commands.Param(description="Final Point of the calcul", ge=1, le=150, default=1)):
        """Character experience calculator"""
        xptable = [None, 30, 70, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 350, 400, 450, 500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400, 4600, 4800, 5000, 5250, 5500, 5750, 6000, 6250, 6500, 6750, 7000, 7250, 7500, 7800, 8100, 8400, 8700, 9000, 9500, 10000, 10500, 11000, 11500, 12000, 12500, 13000, 13500, 14000, 14500, 15000, 15500, 16000, 50000, 20000, 21000, 22000, 23000, 24000, 25000, 26000, 27000, 100000, 150000, 200000, 250000, 300000, 350000, 400000, 450000, 500000, 500000, 1000000, 1000000, 1200000, 1200000, 1200000, 1200000, 1200000, 1250000, 1250000, 1250000, 1250000, 1250000, 1300000, 1300000, 1300000, 1300000, 1300000, 1350000, 1350000, 1350000, 1350000, 1350000, 1400000, 1400000, 1400000, 1400000, 1400000, 1450000, 1450000, 1450000, 1450000, 1450000, 1500000, 1500000, 1500000, 1500000, 1500000, 1550000, 1550000, 1550000, 1550000, 1550000, 1600000, 1600000, 1600000, 1600000, 1600000, 1650000, 1650000, 1650000, 1650000, 0]
        if start_level < 1: start_level = 1
        elif start_level >= 150: start_level = 149
        msg = "From level **{}**, you need:\n".format(start_level)
        xpcount = xptable[start_level]
        for lvl in range(start_level+1, 151):
            if lvl in [80, 100, 110, 120, 130, 140, 150, end_level]:
                msg += "**{:,} XP** for lvl **{:}** ({:} books or {:,} candies)\n".format(xpcount, lvl, math.ceil(xpcount / 300000), math.ceil(xpcount / 745))
                if lvl == end_level: break
            xpcount += xptable[lvl]
        await inter.response.send_message(embed=self.bot.util.embed(title="Experience Calculator", description=msg, color=self.color), ephemeral=True)

    """getGrandList()
    Request the grand character list from the wiki page and return the list of latest released ones
    
    Returns
    ----------
    dict: Grand per element
    """
    async def getGrandList(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://gbf.wiki/SSR_Characters_List#Grand_Series') as r:
                if r.status != 200:
                    raise Exception("HTTP Error 404: Not Found")
                else:
                    cnt = await r.content.read()
                    try: cnt = cnt.decode('utf-8')
                    except: cnt = cnt.decode('iso-8859-1')
                    soup = BeautifulSoup(cnt, 'html.parser') # parse the html
                    tables = soup.find_all("table", class_="wikitable")
                    for t in tables:
                        if "Gala" in str(t):
                            table = t
                            break
                    children = table.findChildren("tr")
                    grand_list = {'fire':None, 'water':None, 'earth':None, 'wind':None, 'light':None, 'dark':None}
                    for c in children:
                        td = c.findChildren("td")
                        grand = {}
                        for elem in td:
                            # name search
                            if 'name' not in grand and elem.text != "" and "Base uncap" not in elem.text:
                                try:
                                    int(elem.text)
                                except:
                                    grand['name'] = elem.text
                            # elem search
                            if 'element' not in grand:
                                imgs = elem.findChildren("img")
                                for i in imgs:
                                    try:
                                        label = i['alt']
                                        if label.startswith('Label Element '):
                                            grand['element'] = label[len('Label Element '):-4].lower()
                                            break
                                    except:
                                        pass
                            # date search
                            if 'date' not in grand and elem.text != "":
                                try:
                                    date_e = elem.text.split('-')
                                    grand['date'] = datetime.utcnow().replace(year=int(date_e[0]), month=int(date_e[1]), day=int(date_e[2]), hour=(12 if (int(date_e[2]) > 25) else 19), minute=0, second=0, microsecond=0)
                                except:
                                    pass
                        if len(grand.keys()) > 2:
                            if grand_list[grand['element']] is None or grand['date'] > grand_list[grand['element']]['date']:
                                grand_list[grand['element']] = grand
                    return grand_list

    @gbf.sub_command()
    async def doom(self, inter: disnake.GuildCommandInteraction):
        """Give the time elapsed of various GBF related releases"""
        await inter.response.defer()
        msg = ""
        wiki_checks = ["Category:Campaign", "Surprise_Special_Draw_Set", "Damascus_Ingot", "Gold_Brick", "Sunlight_Stone", "Sephira_Evolite"]
        regexs = ["<td>(\\d+ days)<\\/td>\\s*<td>Time since last", "<td>(-\\d+ days)<\\/td>\\s*<td>Time since last", "<td>(\\d+ days)<\\/td>\\s*<td>Time since last", "<td>(\\d+ days)<\\/td>\\s*<td style=\"text-align: left;\">Time since last", "<td>(\\d+ days)<\\/td>\\s*<td style=\"text-align: center;\">\\?\\?\\?<\\/td>\\s*<td style=\"text-align: left;\">Time since last", "<td>(\\d+ days)<\\/td>\\s*<td style=\"text-align: center;\">\\?\\?\\?<\\/td>\\s*<td style=\"text-align: left;\">Time since last ", "<td style=\"text-align: center;\">\\?\\?\\?<\\/td>\\s*<td>(\\d+ days)<\\/td>\\s*"]
        async with aiohttp.ClientSession() as session:
            for w in wiki_checks:
                async with session.get("https://gbf.wiki/{}".format(w)) as r:
                    if r.status == 200:
                        t = await r.text()
                        for r in regexs:
                            m = re.search(r, t)
                            if m:
                                msg += "**{}** since the last [{}](https://gbf.wiki/{})\n".format(m.group(1), w.replace("_", " ").replace("Category:", "").replace('Sunlight', 'Arcarum Sunlight').replace('Sephira', 'Arcarum Sephira').replace('Gold', 'ROTB Gold'), w)
                                break

        # summer disaster
        c = self.bot.util.JST()
        msg += "**{} days** since the Summer Fortune 2021\n".format(self.bot.util.delta2str(c - c.replace(year=2021, month=8, day=16, hour=19, minute=0, second=0, microsecond=0), 3).split('d')[0])
        
        # grand
        try:
            grands = await self.getGrandList()
            for e in grands:
                msg += "**{} days** since {} [{}](https://gbf.wiki/{})\n".format(self.bot.util.delta2str(c - grands[e]['date'], 3).split('d')[0], self.bot.emote.get(e), grands[e]['name'], grands[e]['name'].replace(' ', '_'))
        except:
            pass

        if msg != "":
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=msg, color=self.color))
        else:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Unavailable", color=self.color))
        await self.bot.util.clean(inter, 40)

    @gbf.sub_command()
    async def gacha(self, inter: disnake.GuildCommandInteraction):
        """Post the current gacha informations"""
        try:
            await inter.response.defer()
            description, thumbnail = await self.bot.do(self.bot.gacha.summary)
            if description is None: raise Exception('No Gacha')
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, thumbnail=thumbnail, color=self.color))
        except Exception as e:
            if str(e) != 'No Gacha': await self.bot.sendError("getcurrentgacha", e)
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description="Unavailable", color=self.color))

    """getProfileData()
    Request a GBF profile
    
    Parameters
    ----------
    id: Profile id
    
    Returns
    --------
    dict: Profile data, None if error
    """
    def getProfileData(self, id : int): # get player data
        if not self.bot.gbf.isAvailable():
            return "Maintenance"
        res = self.bot.gbf.request("http://game.granbluefantasy.jp/profile/content/index/{}?PARAMS".format(id), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)
        if res is not None: return unquote(res['data'])
        else: return res

    """searchprofile()
    Search a set profile in the save data
    
    Parameters
    ----------
    gbf_id: GBF profile id
    
    Returns
    --------
    int: matching discord ID, None if error
    """
    def searchprofile(self, gbf_id):
        user_ids = list(self.bot.data.save['gbfids'].keys())
        for uid in user_ids:
            if self.bot.data.save['gbfids'].get(uid, None) == gbf_id:
                return uid
        return None

    @gbf.sub_command()
    async def unsetprofile(self, inter: disnake.GuildCommandInteraction):
        """Unlink your GBF id"""
        if str(inter.author.id) not in self.bot.data.save['gbfids']:
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="You didn't set your GBF profile ID", color=self.color), ephemeral=True)
            return
        with self.bot.data.lock:
            try:
                del self.bot.data.save['gbfids'][str(inter.author.id)]
                self.bot.data.pending = True
            except:
                pass
        await inter.response.send_message(embed=self.bot.util.embed(title="The command ran with success", color=self.color), ephemeral=True)

    @gbf.sub_command()
    async def setprofile(self, inter: disnake.GuildCommandInteraction, id : int = commands.Param(description="A valid GBF Profile ID. Usurpation will result in ban.", ge=0)):
        """Link your GBF id to your Discord ID"""
        try:
            if self.bot.ban.check(inter.author.id, self.bot.ban.PROFILE):
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="You are banned to use this feature", color=self.color), ephemeral=True)
                return
            if id < 0 or id >= 100000000:
                await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Invalid ID", color=self.color), ephemeral=True)
                return
            data = await self.bot.do(self.getProfileData, id)
            match data:
                case "Maintenance":
                    await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Game is in maintenance, try again later.", color=self.color), ephemeral=True)
                    return
                case "Down":
                    return
                case None:
                    await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="Profile not found", color=self.color), ephemeral=True)
                    return
                case _:
                    uid = await self.bot.do(self.searchprofile, id)
                    if uid is not None:
                        if uid == id:
                            await inter.response.send_message(embed=self.bot.util.embed(title="Information", description="Your profile is already set to ID `{}`.\nUse `/gbf unsetprofile` if you wish to remove it.".format(id), color=self.color), ephemeral=True)
                        else:
                            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="This id is already in use, use the bug_report command if it's a case of griefing", color=self.color), ephemeral=True)
                        return
            # register
            with self.bot.data.lock:
                self.bot.data.save['gbfids'][str(inter.author.id)] = id
                self.bot.data.pending = True
            await inter.response.send_message(embed=self.bot.util.embed(title="Success", description="Your ID `{}` is now linked to your Discord ID `{}`".format(id, inter.author.id), color=self.color), ephemeral=True)
        except Exception as e:
            await self.bot.sendError("setprofile", e)
            await inter.response.send_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", color=self.color), ephemeral=True)

    """pasteImage()
    Paste an image onto another
    
    Parameters
    ----------
    img: Base image
    file: Image to paste
    offset: Tuple, coordinates
    resize: Tuple (optional), size of the file to paste
    """
    def pasteImage(self, img, file, offset, resize=None): # paste and image onto another
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None: buffers.append(buffers[-1].resize(resize, Image.LANCZOS))
        img.paste(buffers[-1], offset, buffers[-1])
        for buf in buffers: buf.close()
        del buffers

    """dlAndPasteImage()
    Download and image from an url and call pasteImage()
    
    Parameters
    ----------
    img: Base image
    url: Image to download and paste
    offset: Tuple, coordinates
    resize: Tuple (optional), size of the file to paste
    """
    def dlAndPasteImage(self, img, url, offset, resize=None):
        self.imglock.acquire()
        if url not in self.imgcache:
            self.imglock.release()
            req = request.Request(url)
            url_handle = request.urlopen(req)
            data = url_handle.read()
            url_handle.close()
            self.imglock.acquire()
            self.imgcache[url] = data
            if len(self.imgcache) >= 50:
                keys = list(self.imgcache.keys())[:40]
                for k in keys:
                    self.imgcache.pop(k)
        data = self.imgcache[url]
        self.imglock.release()            
        with BytesIO(data) as file_jpgdata:
            self.pasteImage(img, file_jpgdata, offset, resize)

    """processProfile()
    Process profile data into discord embed elements
    
    Parameters
    ----------
    id: Profile id
    data: Profile data
    
    Returns
    --------
    tuple: Containing:
        title: Discord embed title
        description: Discord embed description
        thumbnail: Discord thumbnail
    """
    def processProfile(self, id, data):
        soup = BeautifulSoup(data, 'html.parser')
        try: name = self.bot.util.shortenName(soup.find_all("span", class_="txt-other-name")[0].string)
        except: name = None
        header = None
        rarity = "R"
        possible_headers = [("prt-title-bg-gld", "SSR"), ("prt-title-bg-slv", "SR"), ("prt-title-bg-nml", "R"), ("prt-title-bg-cpr", "R")]
        for h in possible_headers:
            try:
                header = soup.find_all("div", class_=h[0])[0]
                rarity = h[1]
            except:
                pass
        if header is not None:
            brank = self.rankre.search(str(header)).group(0)
            rank = "**{}**".format(brank)
        else:
            brank = " "
            rank = ""
        trophy = soup.find_all("div", class_="prt-title-name")[0].string
        comment = html.unescape(soup.find_all("div", class_="prt-other-comment")[0].string).replace('\t', '').replace('\n', '')
        if comment == "": pass
        elif rank == "": comment = "💬 `{}`".format(comment.replace('`', '\''))
        else: comment = " ▫️ 💬 `{}`".format(comment.replace('`', '\''))
        mc_url = soup.find_all("img", class_="img-pc")[0]['src'].replace("/po/", "/talk/").replace("/img_low/", "/img/")
        # Unused
        stats = soup.find_all("div", class_="num")
        hp = stats[0].string
        atk = stats[1].string
        job_icon = soup.find_all("img", class_="img-job-icon")[0].attrs['src'].replace("img_low", "img")

        try:
            try:
                crew = self.bot.util.shortenName(soup.find_all("div", class_="prt-guild-name")[0].string)
                crewid = soup.find_all("div", class_="btn-guild-detail")[0]['data-location-href']
                crew = "[{}](http://game.granbluefantasy.jp/#{})".format(crew, crewid)
            except: crew = soup.find_all("div", class_="txt-notjoin")[0].string
        except:
            crew = None

        # get the last gw score
        scores = ""
        pdata = self.bot.ranking.searchGWDB(id, 2)
        for n in range(0, 2):
            try:
                pscore = pdata[n][0]
                if pscore.ranking is None: scores += "{} GW**{}** ▫️ **{:,}** honors\n".format(self.bot.emote.get('gw'), pscore.gw, pscore.current)
                else: scores += "{} GW**{}** ▫️ #**{}** ▫️ **{:,}** honors\n".format(self.bot.emote.get('gw'), pscore.gw, pscore.ranking, pscore.current)
            except:
                pass

        try:
            summons_res = self.sumre.findall(data)
            sortsum = {}
            sumimg = {}
            for s in summons_res:
                if self.possiblesum[s[2]] not in sortsum: sortsum[self.possiblesum[s[2]]] = s[3]
                else: sortsum[self.possiblesum[s[2]]] += ' ▫️ ' + s[3]
                sumimg[s[2]] = s
            try:
                misc = sortsum.pop('misc')
                sortsum['misc'] = misc
            except:
                pass
            summons = ""
            for k in sortsum:
                summons += "\n{} {}".format(self.bot.emote.get(k), sortsum[k])
            if summons != "": summons = "\n{} **Summons**{}".format(self.bot.emote.get('summon'), summons)
        except:
            sumimg = {}
            summons = ""

        try:
            beg = data.find('<div class="prt-inner-title">Star Character</div>')
            end = data.find('<div class="prt-2tabs">', beg+1)
            star_section = data[beg:end]
            try:
                ring = self.starringre.findall(star_section)[0]
                msg = "**\💍** "
            except:
                msg = ""
            msg += "{}".format(self.starre.findall(star_section)[0]) # name
            try: msg += " **{}**".format(self.starplusre.findall(star_section)[0]) # plus
            except: pass
            try: msg += " ▫️ **{}** EMP".format(self.empre.findall(star_section)[0]) # emp
            except: pass
            starcom = self.starcomre.findall(star_section)
            if starcom is not None and starcom[0] != "(Blank)": msg += "\n\u202d💬 `{}`".format(html.unescape(starcom[0].replace('`', '\'')))
            star = "\n{} **Star Character**\n{}".format(self.bot.emote.get('skill2'), msg)
        except:
            star = ""

        try: # image processing
            # calculating sizes
            portrait_size = (78, 142)
            equip_size = (280, 160)
            ratio = portrait_size[0] * 2 / equip_size[0]
            equip_size = (int(equip_size[0]*ratio), int(equip_size[1]*ratio))
            lvl_box_height = 30
            sup_summon_size = (200, 420)
            ratio = (portrait_size[1] + lvl_box_height + equip_size[1]) / (sup_summon_size[1] * 2)
            sup_summon_size = (int(sup_summon_size[0]*ratio), int(sup_summon_size[1]*ratio))
            sup_X_offset = portrait_size[0]*6
            if len(sumimg) > 0: imgsize = (portrait_size[0]*6+sup_summon_size[0]*7, portrait_size[1] + lvl_box_height + equip_size[1])
            else: imgsize = (portrait_size[0]*6, portrait_size[1] + lvl_box_height + equip_size[1])
            # creating image
            img = Image.new('RGB', imgsize, "black")
            d = ImageDraw.Draw(img, 'RGBA')
            font = ImageFont.truetype("assets/font.ttf", 18)

            # MC
            self.dlAndPasteImage(img, mc_url.replace("/talk/", "/quest/").replace(".png", ".jpg"), (0, 0), None)
            self.pasteImage(img, "assets/chara_stat.png", (0, portrait_size[1]), (portrait_size[0], lvl_box_height))
            d.text((3, portrait_size[1]+6), brank.replace(' ', ''), fill=(255, 255, 255), font=font)

            # mh and main summon
            self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/1999999999.jpg", (0, portrait_size[1]+lvl_box_height), equip_size)
            self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/2999999999.jpg", (equip_size[0], portrait_size[1]+lvl_box_height), equip_size)
            equip = soup.find_all('div', class_='prt-equip-image')
            for eq in equip:
                mh = eq.findChildren('img', class_='img-weapon', recursive=True)
                if len(mh) > 0: # mainhand
                    self.dlAndPasteImage(img, mh[0].attrs['src'].replace('img_low', 'img').replace('/ls/', '/m/'), (0, portrait_size[1]+lvl_box_height), equip_size)
                    plus = eq.findChildren("div", class_="prt-weapon-quality", recursive=True)
                    if len(plus) > 0:
                        d.text((equip_size[0]-50, portrait_size[1]+lvl_box_height+equip_size[1]-30), plus[0].text, fill=(255, 255, 95), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
                    continue
                ms = eq.findChildren('img', class_='img-summon', recursive=True)
                if len(ms) > 0: # main summon
                    self.dlAndPasteImage(img, ms[0].attrs['src'].replace('img_low', 'img').replace('/ls/', '/m/'), (equip_size[0], portrait_size[1]+lvl_box_height), equip_size)
                    plus = eq.findChildren("div", class_="prt-summon-quality", recursive=True)
                    #if len(plus) > 0:
                    if len(plus) > 0:
                        d.text((equip_size[0]+equip_size[0]-50, portrait_size[1]+lvl_box_height+equip_size[1]-30), plus[0].text, fill=(255, 255, 95), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
                    continue
            
            # party members
            party_section = soup.find_all("div", class_="prt-party-npc")[0]
            party = party_section.findChildren("div", class_="prt-npc-box", recursive=True)
            party_lvl = party_section.findChildren("div", class_="prt-npc-level", recursive=True)
            for i in range(0, 5):
                pos = (portrait_size[0]*(i+1), 0)
                if i >= len(party):
                    imgtag = "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/npc/quest/3999999999.jpg"
                    lvl = ""
                    ring = False
                    plus = ""
                else:
                    npc = party[i]
                    imtag = npc.findChildren("img", class_="img-npc", recursive=True)[0]
                    lvl = party_lvl[i].text.strip()
                    ring = len(npc.findChildren("div", class_="ico-augment2-m", recursive=True)) > 0
                    plus = npc.findChildren("div", class_="prt-quality", recursive=True)
                    if len(plus) > 0: plus = plus[0].text
                    else: plus = ""
                self.dlAndPasteImage(img, imtag['src'].replace('img_low', 'img'), pos)
                if ring:
                    self.pasteImage(img, 'assets/ring.png', pos, (30, 30))
                if plus != "":
                    d.text((pos[0]+portrait_size[0]-50, pos[1]+portrait_size[1]-30), plus, fill=(255, 255, 95), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
                self.pasteImage(img, "assets/chara_stat.png", (portrait_size[0]*(i+1), portrait_size[1]), (portrait_size[0], lvl_box_height))
                if lvl != "":
                    d.text((portrait_size[0]*(i+1)+3, portrait_size[1]+6), lvl, fill=(255, 255, 255), font=font)

            # support summons
            if len(sumimg) > 0:
                for k in self.possiblesum:
                    x = (int(k[0]) + 6) % 7
                    y = int(k[1])
                    s = sumimg.get(k, ['2999999999', '', '', '', None])
                    url = "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/ls/{}.jpg".format(s[0])
                    self.dlAndPasteImage(img, url, (sup_X_offset+x*sup_summon_size[0], sup_summon_size[1]*y), sup_summon_size)
                    if s[4] is not None:
                        if s[4] == "": sumstar = "assets/star_0.png"
                        else: sumstar = "assets/star_{}.png".format(s[4][-1])
                        self.pasteImage(img, sumstar, (sup_X_offset+(x+1)*sup_summon_size[0]-33, sup_summon_size[1]*(y+1)-33))

            # id and stats
            self.pasteImage(img, "assets/chara_stat.png", (equip_size[0]*2, portrait_size[1]+lvl_box_height), (portrait_size[0]*2, equip_size[1]))
            self.pasteImage(img, "assets/atk.png", (equip_size[0]*2+5, portrait_size[1]+lvl_box_height+10), (30, 13))
            self.pasteImage(img, "assets/hp.png", (equip_size[0]*2+5, portrait_size[1]+lvl_box_height*2), (24, 14))
            d.text((equip_size[0]*2+30+10, portrait_size[1]+lvl_box_height+10), atk, fill=(255, 255, 255), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
            d.text((equip_size[0]*2+30+10, portrait_size[1]+lvl_box_height*2), hp, fill=(255, 255, 255), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
            d.text((equip_size[0]*2+10, portrait_size[1]+lvl_box_height*3), "{}".format(id), fill=(255, 255, 255), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
            self.dlAndPasteImage(img, job_icon, (0, portrait_size[1]-30), (36, 30))
            
            # saving
            with BytesIO() as output:
                img.save(output, format="PNG")
                img.close()
                thumbnail = output.getvalue()
        except:
            thumbnail = None
            try: img.close()
            except: pass
        if trophy == "No Trophy Displayed": title = "\u202d{} **{}**".format(self.bot.emote.get(rarity), name)
        else: title = "\u202d{} **{}**▫️{}".format(self.bot.emote.get(rarity), name, trophy)
        return title, "{}{}\n{} Crew ▫️ {}\n{}{}\n".format(rank, comment, self.bot.emote.get('gw'), crew, scores, star), thumbnail

    """_profile()
    Retrieve a GBF profile and post it
    
    Parameters
    ----------
    inter: Command interaction
    id: GBF id
    """
    async def _profile(self, inter: disnake.GuildCommandInteraction, id):
        data = await self.bot.do(self.getProfileData, id)
        match data:
            case "Maintenance":
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Game is in maintenance", color=self.color))
                return
            case "Down":
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Unavailable", color=self.color))
                return
            case None:
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Profile not found", color=self.color))
                return
        soup = BeautifulSoup(data, 'html.parser')
        try: name = soup.find_all("span", class_="txt-other-name")[0].string
        except: name = None
        if name is None:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Profile is Private", color=self.color))
        else:
            x = ""
            title, description, thumbnail = await self.bot.do(self.processProfile, id, data)
            try:
                with BytesIO(thumbnail) as f:
                    df = disnake.File(f, filename="profile.png")
                    message = await self.bot.send('image', file=df)
                    df.close()
                thumbnail = message.attachments[0].url
                description += "\n[:earth_asia: Preview]({})".format(thumbnail)
            except:
                thumbnail = ""
            await inter.edit_original_message(embed=self.bot.util.embed(title=title, description=description, image=thumbnail, url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
        await self.bot.util.clean(inter, 45)

    @gbf.sub_command()
    async def profile(self, inter: disnake.GuildCommandInteraction, target : str = commands.Param(description="Either a valid GBF ID, discord ID or mention", default="")):
        """Retrieve a GBF profile"""
        try:
            await inter.response.defer()
            id = await self.bot.util.str2gbfid(inter, target, self.color)
            if isinstance(id, str):
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description=id, color=self.color))
            else:
                await self._profile(inter, id)
        except Exception as e:
            await self.bot.sendError("profile", e)
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", color=self.color))
        await self.bot.util.clean(inter, 60)

    @commands.user_command(default_permission=True, name="GBF Profile")
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.max_concurrency(4, commands.BucketType.default)
    async def gbfprofile(self, inter: disnake.UserCommandInteraction, member: disnake.Member):
        """Retrieve a GBF profile"""
        try:
            await inter.response.defer()
            id = await self.bot.util.str2gbfid(inter, str(member.id), self.color)
            if isinstance(id, str):
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description=id, color=self.color))
            else:
                await self._profile(inter, id)
        except Exception as e:
            await self.bot.sendError("profile", e)
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="An unexpected error occured", color=self.color))
        await self.bot.util.clean(inter, 60)

    @gbf.sub_command()
    async def brand(self, inter: disnake.GuildCommandInteraction, target : str = commands.Param(description="Either a valid GBF ID, discord ID or mention", default="")):
        """Check if a GBF profile is restricted"""
        try:
            await inter.response.defer(ephemeral=True)
            id = await self.bot.util.str2gbfid(inter, target, self.color)
            if isinstance(id, str):
                await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description=id, color=self.color))
            else:
                data = await self.bot.do(self.bot.gbf.request, "http://game.granbluefantasy.jp/forum/search_users_id?PARAMS", account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check=True, payload={"special_token":None,"user_id":int(id)})
                match data:
                    case "Maintenance":
                        await inter.edit_original_message(embed=self.bot.util.embed(title="Profile Error", description="Game is in maintenance", color=self.color))
                    case "Down":
                        await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Unavailable", color=self.color))
                    case _:
                        if len(data['user']) == 0:
                            await inter.edit_original_message(embed=self.bot.util.embed(title="Profile Error", description="In game message:\n`{}`".format(data['no_member_msg'].replace("<br>", " ")), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
                        else:
                            try:
                                if data['user']["restriction_flag_list"]["event_point_deny_flag"]:
                                    status = "Account is restricted"
                                else:
                                    status = "Account isn't restricted"
                            except:
                                status = "Account isn't restricted"
                            await inter.edit_original_message(embed=self.bot.util.embed(title="{} {}".format(self.bot.emote.get('gw'), self.bot.util.shortenName(data['user']['nickname'])), description=status, thumbnail="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/talk/{}.png".format(data['user']['image']), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
        except:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Unavailable", color=self.color))

    @gbf.sub_command()
    async def coop(self, inter: disnake.GuildCommandInteraction):
        """Retrieve the current coop daily missions"""
        try:
            await inter.response.defer(ephemeral=True)
            data = (await self.bot.do(self.bot.gbf.request, 'http://game.granbluefantasy.jp/coopraid/daily_mission?PARAMS', account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check=True))['daily_mission']
            msg = ""
            for i in range(len(data)):
                if data[i]['category'] == '2':
                    items = {20011:'fire', 20012:'fire', 20111:'fire', 20021:'water', 20022:'water', 20121:'water', 20031:'earth', 20032:'earth', 20131:'earth', 20041:'wind', 20042:'wind', 20141:'wind'}
                    id = int(data[i]['image'].split('/')[-1])
                    msg += '{} {}\n'.format(self.bot.emote.get(items.get(id, 'misc')), data[i]['description'])
                elif data[i]['category'] == '1':
                    quests = {'s00101':'wind', 's00104':'wind', 's00204':'wind', 's00206':'wind', 's00301':'fire', 's00303':'fire', 's00405':'fire', 's00406':'fire', 's00601':'water', 's00602':'water', 's00604':'water', 's00606':'water', 's00802':'earth', 's00704':'earth', 's00705':'earth', 's00806':'earth', 's01005':'wind', 's00905':'wind', 's00906':'wind', 's01006':'wind', 's01105':'fire', 's01403':'fire', 's01106':'fire', 's01206':'fire', 's01001':'water', 's01502':'water', 's01306':'water', 's01406':'water', 's01601':'earth', 's01405':'earth', 's01506':'earth', 's01606':'earth'}
                    id = data[i]['image'].split('/')[-1]
                    msg += '{} {}\n'.format(self.bot.emote.get(quests.get(id, 'misc')), data[i]['description'])
                else:
                    msg += '{} {}\n'.format(self.bot.emote.get(str(i+1)), data[i]['description'])
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"Daily Coop Missions", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=msg, color=self.color))
        except:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Unavailable", color=self.color))

    @gbf.sub_command()
    async def news(self, inter: disnake.GuildCommandInteraction):
        """Post the latest news posts"""
        await inter.response.defer(ephemeral=True)
        if 'news_url' not in self.bot.data.save['gbfdata']:
            self.bot.data.save['gbfdata']['news_url'] = []
            self.bot.data.pending = True
        msg = ""
        for i in range(len(self.bot.data.save['gbfdata']['news_url'])):
            msg += "{} [{}]({})\n".format(self.bot.emote.get(str(i+1)), self.bot.data.save['gbfdata']['news_url'][i][1], self.bot.data.save['gbfdata']['news_url'][i][0])
        try:
            thumb = self.bot.data.save['gbfdata']['news_url'][0][2]
            if not thumb.startswith('http://granbluefantasy.jp') and not thumb.startswith('https://granbluefantasy.jp'):
                if thumb.startswith('/'): thumb = 'https://granbluefantasy.jp' + thumb
                else: thumb = 'https://granbluefantasy.jp/' + thumb
        except: thumb = None
        if msg == "":
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Unavailable", color=self.color))
        else:
            await inter.edit_original_message(embed=self.bot.util.embed(author={'name':"Latest Granblue Fantasy News", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=msg, image=thumb, color=self.color))

    @gbf.sub_command(name="4koma")
    async def _4koma(self, inter: disnake.GuildCommandInteraction, id : int = commands.Param(description="A 4koma number", default=-123456789)):
        """Post a Granblues Episode"""
        try:
            await inter.response.defer(ephemeral=True)
            if id == -123456789: id = int(self.bot.data.save['gbfdata']['4koma'])
            if id < 0 or id > int(self.bot.data.save['gbfdata']['4koma']): raise Exception()
            await inter.edit_original_message(embed=self.bot.util.embed(title="Granblue Episode {}".format(id), url="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/comic/episode/episode_{}.jpg".format(id), image="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/comic/thumbnail/thum_{}.png".format(str(id).zfill(5)), color=self.color))
        except:
            await inter.edit_original_message(embed=self.bot.util.embed(title="Error", description="Invalid 4koma number", color=self.color))

    @commands.slash_command(default_permission=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def guide(self, inter: disnake.GuildCommandInteraction):
        """Command Group"""
        pass

    @guide.sub_command()
    async def ubaha(self, inter: disnake.GuildCommandInteraction):
        """Post the Ultimate Bahamut HL Triggers"""
        await inter.response.send_message(embed=self.bot.util.embed(title="Empyreal Ascension (Impossible)", url="https://gbf.wiki/Ultimate_Bahamut_(Raid)#impossible", description="**95%**{} Daedalus Wing (uplift)\n**85%**{} Deadly Flare (dispel)\n**80%**♦️ charge diamonds\n**75%**{} Virtuous Verse (swap)\n**70%**{} The Rage (local debuffs)\n**70-50%**♦️ charge diamonds in OD\n**55%**{} Deadly Flare (stone)\n**50 & 40**%{} Sirius (4x30% plain)\n**45 & 35**%▫️ Sirius\n**28%**♦️ charge diamonds\n**22%**{} Ultima Blast (dispel)\n**15%**{} Skyfall Ultimus\n**10% & 1%**▫️ Cosmic Collision\n**5%**{} Deadly Flare".format(self.bot.emote.get('wind'), self.bot.emote.get('fire'), self.bot.emote.get('earth'), self.bot.emote.get('light'), self.bot.emote.get('fire'), self.bot.emote.get('misc'), self.bot.emote.get('water'), self.bot.emote.get('dark'), self.bot.emote.get('dark')), footer="Stay blue", color=self.color), ephemeral=True)

    @guide.sub_command()
    async def lucilius(self, inter: disnake.GuildCommandInteraction):
        """Post the Lucilius HL Triggers"""
        await inter.response.send_message(embed=self.bot.util.embed(title="Dark Rapture (Hard)", url="https://gbf.wiki/Lucilius_(Raid)#Impossible_.28Hard.29", fields = [{'name': "{} Black Wings".format(self.bot.emote.get('1')), 'value':'**N **{} Phosphosrus (single)\n**OD**{} Iblis (multi, debuffs)\n**OD, both**▫️ Paradise Lost (party)\n**Join**{} Paradise Lost (30K)\n**70%**▫️ Sephiroth (debuff wipe)\n**50%**{} Seven Trumpets (**12 Labors**)\n**1-6**{} increase damage [10M]\n**7**{} use superior element [2M plain]\n**8**{} nullify phalanx [OverChain]\n**9**{} heal [30 hits]\n**10**{} random debuff [10 debuffs]\n**11**{} dispel 2 buffs [trigger PL]\n**12**{} deal plain damage [all labors]'.format(self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('misc'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'))}, {'name': "{} Lucilius".format(self.bot.emote.get('2')), 'value':'**95%**{} Phosphosrus (single)\n**85%**{} Axion (multi)\n**70%**♦️ charge diamonds\n**60%**{} Axion (**party**)\n**55%**♦️ charge diamonds\n**25%**{} Gopherwood Ark (racial check)\n**20 & 15%**{} Axion Apocalypse (multi)\n**10 & 3%**{} Paradise Lost (999k)\n\n*Click the title for more details*'.format(self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'))}], inline=True, footer="Your fate is over", color=self.color, thumbnail="http://game-a1.granbluefantasy.jp/assets_en/img/sp/quest/assets/lobby/303281.png"), ephemeral=True)

    @guide.sub_command()
    async def beelzebub(self, inter: disnake.GuildCommandInteraction):
        """Post the Beelzebub HL Triggers"""
        await inter.response.send_message(embed=self.bot.util.embed(title="Long Live the King", url="https://gbf.wiki/Beelzebub_(Raid)", description="**100% & OD**▫️ Chaoscaliber (party, stun) [30 hits]\n**N **▫️ Unisonic (multi, counter) [10M]\n**75, 60% & OD**▫️ Karma (summonless) [FC]\n**N **▫️ Black Flies (multi, slashed) [10M]\n**50%**{} Langelaan Field (4T, reflect 2K, doesn't attack) [5M+20M/death]\n**OD**▫️ Chaoscaliber (party x2, stun) [FC]\n**N **▫️ Just Execution (24 hits, -1T to buff/hit) [FC]\n**30 & 15%**▫️ Black Spear (party, defenless) [FC]\n**25 & 10%**▫️ Chaos Legion (party, 10k guarded) [FC]\n**King's Religion**{} Total turns reached 30xPlayer Count".format(self.bot.emote.get('misc'), self.bot.emote.get('misc')), footer="Qilin Fantasy", color=self.color, thumbnail="http://game-a1.granbluefantasy.jp/assets_en/img/sp/quest/assets/lobby/305181.png"), ephemeral=True)

    @guide.sub_command()
    async def belial(self, inter: disnake.GuildCommandInteraction):
        """Post the Belial HL Triggers"""
        await inter.response.send_message(embed=self.bot.util.embed(title="The Fallen Angel of Cunning", url="https://gbf.wiki/Belial_(Raid)", description="**On Join**{}️ Lemegeton (20K Plain)\n**75, 50, 25%**▫️ Debuff Wipe\n**65%** ▫️ Asmodeus (multi, debuff, omega fruit) [Dispel]\n**50% Form** ▫️ Triple elemental absorption\nGroups: {}{} / {}{} / {}{}\n**50%** ▫️ Anagenesis (dark dmg based on stack)\n**30%** ▫️ Goetia (multi, slashed/supp debuff) [FC]\n**5%** ▫️ Lemegeton (Let you continue, Full diamond)\n**Before 50%**\n**N & OD**▫️ Amadeus (party, perma debuffs)\n**Turn 3**▫️ Goetia (multi, slashed/supp debuff) [15M]\n**Turn 6**▫️ Lemegeton (party, dispel x2, diamond+1) [35 hits]\n**After 50%**\n**N & OD**{} Amadeus (**Raid Wipe**)\n**Turn 3**▫️ Goetia (multi, atk up, stack up) [FC]\n**Turn 6**▫️ Lemegeton (30K, skill & CA seal) [Dispel]\nTurn Triggers above **repeat every 6 turns**\n**Every 3T**▫️ Random fruit applied to party".format(self.bot.emote.get('misc'), self.bot.emote.get('fire'), self.bot.emote.get('wind'), self.bot.emote.get('water'), self.bot.emote.get('earth'), self.bot.emote.get('light'), self.bot.emote.get('dark'), self.bot.emote.get('misc')), footer="Delay to win", color=self.color, thumbnail="http://game-a1.granbluefantasy.jp/assets_en/img/sp/quest/assets/lobby/305281.png"), ephemeral=True)

    @guide.sub_command()
    async def subaha(self, inter: disnake.GuildCommandInteraction):
        """Post the Super Ultimate Bahamut HL Triggers"""
        await inter.response.send_message(embed=self.bot.util.embed(title="Rage of Super Ultimate Bahamut", url="https://gbf.wiki/Super_Ultimate_Bahamut_(Raid)", description="{} Each element must cancel omens to reduces the Tenet stacks\n**75-51%**▫️Immune to delay\n{} **Special Attacks**\n**100-76%**▫️Termination Flare (23 hits, Burn/Fear/Cut to buff duration) [15M]\n**75-51%**▫️Verse Ruler (Single DMG. & Swap lowest HP chara.) [20M]\n**51-11**%▫️Crisis Crunch (100% Plain to highest HP chara., can't be revived) [20M]\n**10-0%**▫️Genesis Nova (AOE 999k Plain)\n{} **Cycle Every 6 Turns**\n**100-51%**\nArcadia Foteinos (AOE DMG., Purging Light buff) [10 debuffs]\nArcadia Gnosis (AOE DMG., Godsight buff) [60 hits]\nArcadia Skliros (AOE DMG., DMG Cuts nullified) [20M CA]\nArcadia Laimargos (AOE DMG., Superio Element buff) [20M Skill]\n**50-11%**\nArcadia Tromos (AOE DMG., No guard debuff) [6 Chain]\nArcadia Eclipse (AOE DMG., Max HP capped to 20k) [3.33M Plain]\nArcadia Apocryphos (AOE DMG., Can't summon debuff) [12 skill casts]\n{} **Triggers**\n**75%**▫️Daedalus Drive (AOE 40K Plain)\n**51%**▫️Omnipotent Cocoon (Doesn't attack, Generate Tenets, 5T) [50M]\n**After Cocoon**▫️Double Strike/All Foe Attack, Gain Local Echo of elements at stack 5+, Apply the debuffs from missed 6T Triggers\n**10%**▫️Sirius Origin (4x99k plain, Drain/2->8\\♦️, Apply the debuffs from missed 6T Triggers)".format(self.bot.emote.get('mark'), self.bot.emote.get('skill1'), self.bot.emote.get('mark'), self.bot.emote.get('skill2')), footer="and Knuckles", color=self.color, thumbnail="http://game-a1.granbluefantasy.jp/assets_en/img/sp/quest/assets/lobby/305311.png"), ephemeral=True)