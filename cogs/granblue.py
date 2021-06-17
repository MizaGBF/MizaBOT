import discord
from discord.ext import commands
import aiohttp
from datetime import datetime, timedelta
import random
import re
from bs4 import BeautifulSoup
from urllib import request, parse
from urllib.parse import unquote
from xml.sax import saxutils as su
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import threading

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
        self.badprofilecache = []
        self.possiblesum = {'10':'fire', '11':'fire', '20':'water', '21':'water', '30':'earth', '31':'earth', '40':'wind', '41':'wind', '50':'light', '51':'light', '60':'dark', '61':'dark', '00':'misc', '01':'misc'}
        self.imgcache = {}
        self.imglock = threading.Lock()

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    def isYou(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isServer(ctx, 'you_server')
        return commands.check(predicate)

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

    # function to fix the case (for $wiki)
    def fixCase(self, term): # term is a string
        fixed = ""
        up = False
        if term.lower() == "and": # if it's just 'and', we don't don't fix anything and return a lowercase 'and'
            return "and"
        elif term.lower() == "of":
            return "of"
        elif term.lower() == "(sr)":
            return "(SR)"
        elif term.lower() == "(ssr)":
            return "(SSR)"
        elif term.lower() == "(r)":
            return "(R)"
        for i in range(0, len(term)): # for each character
            if term[i].isalpha(): # if letter
                if term[i].isupper(): # is uppercase
                    if not up: # we haven't encountered an uppercase letter
                        up = True
                        fixed += term[i] # save
                    else: # we have
                        fixed += term[i].lower() # make it lowercase and save
                elif term[i].islower(): # is lowercase
                    if not up: # we haven't encountered an uppercase letter
                        fixed += term[i].upper() # make it uppercase and save
                        up = True
                    else: # we have
                        fixed += term[i] # save
                else: # other characters
                    fixed += term[i] # we just save
            elif term[i] == "/" or term[i] == ":" or term[i] == "#" or term[i] == "-": # we reset the uppercase detection if we encounter those
                up = False
                fixed += term[i]
            else: # everything else,
                fixed += term[i] # we save
        return fixed # return the result

    def stripWikiStr(self, elem):
        txt = elem.text.replace('foeBoost', 'foe. Boost') # special cases
        checks = [['span', 'tooltiptext'], ['sup', 'reference'], ['span', 'skill-upgrade-text']]
        for target in checks:
            f = elem.findChildren(target[0], class_=target[1])
            for e in f:
                txt = txt.replace(e.text, "")
        return txt.replace('Slight', '_sligHt_').replace('C.A.', 'CA').replace('.', '. ').replace('!', '! ').replace('?', '? ').replace(':', ': ').replace('. )', '.)').replace("Damage cap", "Cap").replace("Damage", "DMG").replace("damage", "DMG").replace(" and ", " and").replace(" and", " and ").replace("  ", " ").replace("fire", str(self.bot.emote.get('fire'))).replace("water", str(self.bot.emote.get('water'))).replace("earth", str(self.bot.emote.get('earth'))).replace("wind", str(self.bot.emote.get('wind'))).replace("dark", str(self.bot.emote.get('dark'))).replace("light", str(self.bot.emote.get('light'))).replace("Fire", str(self.bot.emote.get('fire'))).replace("Water", str(self.bot.emote.get('water'))).replace("Earth", str(self.bot.emote.get('earth'))).replace("Wind", str(self.bot.emote.get('wind'))).replace("Dark", str(self.bot.emote.get('dark'))).replace("Light", str(self.bot.emote.get('light'))).replace('_sligHt_', 'Slight')

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

    def processWikiItem(self, soup, data, tables):
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

    async def requestWiki(self, ctx, url, search_mode = False): # url MUST be for gbf.wiki
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
                            await self.requestWiki(ctx, "https://gbf.wiki/{}".format(matches[0]))
                            return
                        desc = ""
                        for m in matches: # build the message with the results
                            desc += "[{}](https://gbf.wiki/{})\n".format(m, m.replace(" ", "_"))
                        desc = "First five results\n{}".format(desc)
                        final_msg = await ctx.reply(embed=self.bot.util.embed(title="Not Found, click here to refine", description=desc, url=url, color=self.color))
                    else: # direct access to the page (assume a match)
                        data, tables = await self.bot.do(self.processWikiMatch, soup)

                        x = data.get('object', None)
                        if x is None: # if no match
                            final_msg = await ctx.reply(embed=self.bot.util.embed(title=title, description=data.get('description', None), image=data.get('image', None), url=url, footer=data.get('id', None), color=self.color))
                        elif x == 0: # charater
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
                                final_msg = await ctx.reply(embed=self.bot.util.embed(title=title, description=desc, image=data.get('image', None), url=url, footer=data.get('id', None), color=self.color))
                            except: # if none, just send the link
                                final_msg = await ctx.reply(embed=self.bot.util.embed(title=title, description=data.get('description', None), image=data.get('image', None), url=url, footer=data.get('id', None), color=self.color))
                        else: # summon and weapon
                            data = await self.bot.do(self.processWikiItem, soup, data, tables)
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

                            final_msg = await ctx.reply(embed=self.bot.util.embed(title=title, description=desc, thumbnail=data.get('image', None), url=url, footer=data.get('id', None), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 80)


    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gbfwiki'])
    @commands.cooldown(3, 4, commands.BucketType.guild)
    async def wiki(self, ctx, *, terms : str = ""):
        """Search the GBF wiki"""
        final_msg = None
        if terms == "":
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Tell me what to search on the wiki", footer="wiki [search terms]", color=self.color))
        else:
            # build the url (the wiki is case sensitive)
            arr = []
            for s in terms.split(" "):
                arr.append(self.fixCase(s))
            sch = "_".join(arr)
            url = "https://gbf.wiki/{}".format(sch)
            try:
                await self.requestWiki(ctx, url) # try to request
            except Exception as e:
                url = "https://gbf.wiki/index.php?title=Special:Search&search={}".format(parse.quote_plus(terms))
                if str(e) != "HTTP Error 404: Not Found": # unknown error, we stop here
                    await self.bot.sendError("wiki", e)
                    final_msg = await ctx.reply(embed=self.bot.util.embed(title="Unexpected error, click here to search", url=url, footer=str(e), color=self.color))
                else: # failed, we try the search function
                    try:
                        await self.requestWiki(ctx, url, True) # try
                    except Exception as f:
                        if str(f) == "No results":
                            final_msg = await ctx.reply(embed=self.bot.util.embed(title="No matches found", color=self.color)) # no results
                        else:
                            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Not Found, click here to refine", url=url, color=self.color)) # no results
        await self.bot.util.clean(ctx, final_msg, 45)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def jst(self, ctx):
        """Post the current time, JST timezone"""
        await ctx.send(embed=self.bot.util.embed(title="{} {:%Y/%m/%d %H:%M} JST".format(self.bot.emote.get('clock'), self.bot.util.JST()), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    async def reddit(self, ctx):
        """Post a link to /r/Granblue_en
        You wouldn't dare, do you?"""
        await ctx.reply(embed=self.bot.util.embed(title="/r/Granblue_en/", url="https://www.reddit.com/r/Granblue_en/", thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/581522602325966864/lTgz7Yx_6n8VZemjf54viYVZgFhW2GlB6dlpj1ZwKbo.png", description="Disgusting :nauseated_face:", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['leech'])
    async def leechlist(self, ctx):
        """Post a link to /gbfg/ leechlist collection"""
        await ctx.reply(embed=self.bot.util.embed(title="/gbfg/ Leechlist", description=self.bot.data.config['strings']["leechlist()"], thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/582191446182985734/unknown.png", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['time', 'st', 'reset', 'gbf'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def granblue(self, ctx):
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

        id = str(ctx.message.author.guild.id)
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
            buf = await self.bot.do(self.getCurrentGacha)
            if len(buf) > 0:
                description += "\n{} Current gacha ends in **{}**".format(self.bot.emote.get('SSR'), self.bot.util.delta2str(buf[0], 2))
                if buf[0] != buf[1]:
                    description += " (Spark period ends in **{}**)".format(self.bot.util.delta2str(buf[1], 2))
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
            buf = self.bot.get_cog('GuildWar').getNextBuff(ctx)
            if len(buf) > 0: description += "\n" + buf
        except Exception as e:
            await self.bot.sendError("getnextbuff", e)

        await ctx.send(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['maint'])
    @commands.cooldown(2, 2, commands.BucketType.guild)
    async def maintenance(self, ctx):
        """Post GBF maintenance status"""
        try:
            description = self.getMaintenanceStatus()
            if len(description) > 0:
                await ctx.send(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, color=self.color))
            else:
                await ctx.send(embed=self.bot.util.embed(title="Granblue Fantasy", description="No maintenance in my memory", color=self.color))
        except Exception as e:
            await self.bot.sendError("getMaintenanceStatus", e)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['drive'])
    @isYou()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def gdrive(self, ctx):
        """Post the (You) google drive
        (You) server only"""
        try:
            image = self.bot.get_guild(self.bot.data.config['ids']['you_server']).icon_url
        except:
            image = ""
        await ctx.reply(embed=self.bot.util.embed(title="(You) Public Google Drive", description=self.bot.data.config['strings']["gdrive()"], thumbnail=image, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['arcarum', 'arca', 'oracle', 'evoker', 'astra', 'sandbox', 'veritas', 'newworld', 'luster'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def arcanum(self, ctx):
        """Post a link to my autistic Arcanum Sheet"""
        await ctx.reply(embed=self.bot.util.embed(title="Arcanum Tracking Sheet", description=self.bot.data.config['strings']["arcanum()"], thumbnail="http://game-a.granbluefantasy.jp/assets_en/img_low/sp/assets/item/article/s/250{:02d}.jpg".format(random.randint(1, 74)), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['eternals', 'transcendence', 'transc'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def eternal(self, ctx):
        """Post a link to my autistic Eternal Sheet"""
        await ctx.reply(embed=self.bot.util.embed(title="Eternal Transcendance Tracking Sheet", description=self.bot.data.config['strings']["eternal()"], thumbnail="http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/npc/s/30400{}.jpg".format(random.choice(['30000_04', '31000_04', '32000_03', '33000_03', '34000_03', '35000_03', '36000_03', '37000_03', '38000_03', '39000_03'])), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwskin', 'blueskin'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def stayBlue(self, ctx):
        """Post a link to my autistic blue eternal outfit grinding Sheet"""
        await ctx.reply(embed=self.bot.util.embed(title="5* Eternal Skin Farming Sheet", description=self.bot.data.config['strings']["stayblue()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['soldier'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def bullet(self, ctx):
        """Post a link to my bullet grind Sheet"""
        await ctx.reply(embed=self.bot.util.embed(title="Bullet Grind Sheet", description=self.bot.data.config['strings']["bullet()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gbfgcrew', 'gbfgpastebin'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def pastebin(self, ctx):
        """Post a link to the /gbfg/ crew pastebin"""
        await ctx.reply(embed=self.bot.util.embed(title="/gbfg/ Guild Pastebin", description=self.bot.data.config['strings']["pastebin()"], thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/582191446182985734/unknown.png", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['tracker'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def dps(self, ctx):
        """Post the custom Combat tracker"""
        await ctx.reply(embed=self.bot.util.embed(title="GBF Combat Tracker", description=self.bot.data.config['strings']["dps()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['raidfinder', 'python_raidfinder'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def pyfinder(self, ctx):
        """Post the (You) python raidfinder"""
        await ctx.reply(embed=self.bot.util.embed(title="(You) Python Raidfinder", description=self.bot.data.config['strings']["pyfinder()"], color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def mizatube(self, ctx):
        """Post the owner youtube channel"""
        if 'mizatube()' in self.bot.data.config['strings']:
            await ctx.reply(embed=self.bot.util.embed(title="Mizatube:tm:", description="[Link]({})".format(self.bot.data.config['strings']['mizatube()']), footer="Subscribe ;)", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['ubhl', 'ubahahl'])
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def ubaha(self, ctx):
        """Post the Ultimate Bahamut HL Triggers"""
        await ctx.reply(embed=self.bot.util.embed(title="Empyreal Ascension (Impossible)", url="https://gbf.wiki/Ultimate_Bahamut_(Raid)#impossible", description="**95%**{} Daedalus Wing (uplift)\n**85%**{} Deadly Flare (dispel)\n**80%**♦️ charge diamonds\n**75%**{} Virtuous Verse (swap)\n**70%**{} The Rage (local debuffs)\n**70-50%**♦️ charge diamonds in OD\n**55%**{} Deadly Flare (stone)\n**50 & 40**%{} Sirius (4x30% plain)\n**45 & 35**%▫️ Sirius\n**28%**♦️ charge diamonds\n**22%**{} Ultima Blast (dispel)\n**15%**{} Skyfall Ultimus\n**10% & 1%**▫️ Cosmic Collision\n**5%**{} Deadly Flare".format(self.bot.emote.get('wind'), self.bot.emote.get('fire'), self.bot.emote.get('earth'), self.bot.emote.get('light'), self.bot.emote.get('fire'), self.bot.emote.get('misc'), self.bot.emote.get('water'), self.bot.emote.get('dark'), self.bot.emote.get('dark')), footer="Stay blue", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['darkrapture', 'rapture', 'faa', 'luci', 'lucihl', 'luciliushl'])
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def lucilius(self, ctx):
        """Post the Lucilius HL Triggers"""
        await ctx.reply(embed=self.bot.util.embed(title="Dark Rapture (Hard)", url="https://gbf.wiki/Lucilius_(Raid)#Impossible_.28Hard.29", fields = [{'name': "{} Black Wings".format(self.bot.emote.get('1')), 'value':'**N **{} Phosphosrus (single)\n**OD**{} Iblis (multi, debuffs)\n**OD, both**▫️ Paradise Lost (party)\n**Join**{} Paradise Lost (30K)\n**70%**▫️ Sephiroth (debuff wipe)\n**50%**{} Seven Trumpets (**12 Labors**)\n**1-6**{} increase damage [10M]\n**7**{} use superior element [2M plain]\n**8**{} nullify phalanx [OverChain]\n**9**{} heal [30 hits]\n**10**{} random debuff [10 debuffs]\n**11**{} dispel 2 buffs [trigger PL]\n**12**{} deal plain damage [all labors]'.format(self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('misc'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'), self.bot.emote.get('labor'))}, {'name': "{} Lucilius".format(self.bot.emote.get('2')), 'value':'**95%**{} Phosphosrus (single)\n**85%**{} Axion (multi)\n**70%**♦️ charge diamonds\n**60%**{} Axion (**party**)\n**55%**♦️ charge diamonds\n**25%**{} Gopherwood Ark (racial check)\n**20 & 15%**{} Axion Apocalypse (multi)\n**10 & 3%**{} Paradise Lost (999k)\n\n*Click the title for more details*'.format(self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'), self.bot.emote.get('lucilius'))}], inline=True, footer="Your fate is over", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['beelzebub', 'bubz'])
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def bubs(self, ctx):
        """Post the Beelzebub HL Triggers"""
        await ctx.reply(embed=self.bot.util.embed(title="Long Live the King", url="https://gbf.wiki/Beelzebub_(Raid)", description="**100% & OD**▫️ Chaoscaliber (party, stun) [30 hits]\n**N **▫️ Unisonic (multi, counter) [10M]\n**75, 60% & OD**▫️ Karma (summonless) [FC]\n**N **▫️ Black Flies (multi, slashed) [10M]\n**50%**{} Langelaan Field (4T, reflect 2K, doesn't attack) [5M+20M/death]\n**OD**▫️ Chaoscaliber (party x2, stun) [FC]\n**N **▫️ Just Execution (24 hits, -1T to buff/hit) [FC]\n**30 & 15%**▫️ Black Spear (party, defenless) [FC]\n**25 & 10%**▫️ Chaos Legion (party, 10k guarded) [FC]\n**King's Religion**{} Total turns reached 30xPlayer Count".format(self.bot.emote.get('misc'), self.bot.emote.get('misc')), footer="Qilin Fantasy", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['lust'])
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def belial(self, ctx):
        """Post the Belial HL Triggers"""
        await ctx.reply(embed=self.bot.util.embed(title="The Fallen Angel of Cunning", url="https://gbf.wiki/Belial_(Raid)", description="**On Join**{}️ Lemegeton (20K Plain)\n**75, 50, 25%**▫️ Debuff Wipe\n**65%** ▫️ Asmodeus (multi, debuff) [Dispel]\n**50% Form** ▫️ Triple elemental absorption\n**50%** ▫️ Anagenesis (dark dmg based on stack)\n**30%** ▫️ Goetia (multi, slashed/supp debuff) [FC]\n**5%** ▫️ Lemegeton (Let you continue, Full diamond)\n**Before 50%**\n**N & OD**▫️ Amadeus (Perma debuffs)\n**Turn 3**▫️ Goetia (multi, slashed/supp debuff) [15M]\n**Turn 6**▫️ Lemegeton (party, dispel x2, diamond+1) [35 hits]\n**After 50%**\n**N & OD**{} Amadeus (**Raid Wipe**)\n**Turn 3**▫️ Goetia (multi, atk up, stack up) [FC]\n**Turn 6**▫️ Lemegeton (30K, skill & CA seal) [Dispel]\nTurn Triggers **repeat every 6 turns**\n".format(self.bot.emote.get('misc'), self.bot.emote.get('misc')), footer="Qilin Fantasy", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["christmas", "anniversary", "anniv", "summer"])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def stream(self, ctx, op : str = ""):
        """Post the stream text"""
        if len(self.bot.data.save['stream']['content']) == 0:
            await ctx.send(embed=self.bot.util.embed(title="No event or stream available", color=self.color))
        elif op == "raw":
            msg = ""
            for c in self.bot.data.save['stream']['content']:
                msg += c + '\n'
            await ctx.send('`' + msg + '`')
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

            await ctx.send(embed=self.bot.util.embed(title=title, description=msg, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["event"])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def schedule(self, ctx, raw : str = ""):
        """Post the GBF schedule"""
        if len(self.bot.data.save['schedule']) == 0:
            await ctx.send(embed=self.bot.util.embed(title="No schedule available", color=self.color))
        else:
            l = len(self.bot.data.save['schedule'])
            if raw != 'raw': l = l - (l%2) # need an even amount, skipping the last one if odd
            i = 0
            msg = ""
            c = self.bot.util.JST()
            nx = None
            md = c.month * 100 + c.day
            while i < l:
                if raw == 'raw':
                    if i != 0: msg += ";"
                    else: msg += "`"
                    msg += self.bot.data.save['schedule'][i]
                    i += 1
                else:
                    try: # checking if the event is on going (to bold it)
                        dates = self.bot.data.save['schedule'][i].replace(' ', '').split('-')
                        ev_md = []
                        for di in range(0, len(dates)):
                            ev_md.append(int(dates[di].split('/')[0]) * 100 + int(dates[di].split('/')[1]))
                        if len(dates) == 2:
                            if ev_md[0] >= 1200 and ev_md[1] <= 100: ev_md[0] -= 1200
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
            if raw == 'raw': msg += "`"
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
            await ctx.send(embed=self.bot.util.embed(title="🗓 Event Schedule {} {:%Y/%m/%d %H:%M} JST".format(self.bot.emote.get('clock'), self.bot.util.JST()), url="https://twitter.com/granblue_en", color=self.color, description=msg))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['friday'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def premium(self, ctx):
        """Post the time to the next Premium Friday"""
        c = self.bot.util.JST()
        d = c
        last = None
        searching = True
        thumbnail = "https://cdn.discordapp.com/attachments/354370895575515138/584025273079562240/unknown.png"
        while searching:
            if d.weekday() == 4:
                last = d
            d = d + timedelta(seconds=86400)
            if last is not None and d.month != last.month:
                if c == last:
                    beg = last.replace(hour=15, minute=00, second=00)
                    end = c.replace(hour=23, minute=59, second=59) + timedelta(days=2, seconds=1)
                    if c >= beg and c < end:
                        end = end - c
                        await ctx.send(embed=self.bot.util.embed(title="{} Premium Friday".format(self.bot.emote.get('clock')), description="Premium Friday ends in **{}**".format(self.bot.util.delta2str(end, 2)), url="http://game.granbluefantasy.jp", thumbnail=thumbnail, color=self.color))
                        return
                    elif c >= end:
                        pass
                    elif c < beg:
                        last = beg
                        searching = False
                else:
                    searching = False
        last = last.replace(hour=15, minute=00, second=00) - c
        await ctx.send(embed=self.bot.util.embed(title="{} Premium Friday".format(self.bot.emote.get('clock')), description="Premium Friday starts in **{}**".format(self.bot.util.delta2str(last, 2)),  url="http://game.granbluefantasy.jp", thumbnail=thumbnail, color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['koregura', 'koregra'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def korekara(self, ctx):
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
        await ctx.send(embed=self.bot.util.embed(title="{} Kore Kara".format(self.bot.emote.get('clock')), description="Release approximately in **{}**".format(self.bot.util.delta2str(delta, 2)),  url="https://granbluefantasy.jp/news/index.php", thumbnail="http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['crits', 'critical', 'criticals'])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def crit(self, ctx, *, weapons : str = ""):
        """Calculate critical rate
        Do the command without parameters for the full modifier list
        Add `f` before a modifier to make it unboosted"""
        values = {'small10':2, 'small15':3, 'small20':4, 'medium10':5, 'medium15':6.5, 'medium20':7.5, 'big10':8, 'big15':10, 'big20':11, 'bigii15':12, 'wamdus':20, 'hercules':11.5, 'sephira':25}
        ts = {'small':'small15', 'med':'medium15', 'medium':'medium15', 'big':'big15', 'big2':'bigii15', 's10':'small10', 's15':'small15', 's20':'small20', 'm10':'medium10', 'm15':'medium15', 'm20':'medium20', 'med10':'medium10', 'med15':'medium15', 'med20':'medium20', 'b10':'big10', 'b15':'big15', 'b20':'big20', 'bii10':'bigii10', 'bii15':'bigii15', 'b210':'bigii10', 'b215':'bigii15', 'big210':'bigii10', 'big215':'bigii15', 'ameno':'medium20', 'gaebulg':'medium20', 'bulg':'medium20', 'bulge':'medium20', 'gae':'medium20', 'mjolnir':'small20', 'herc':'hercules', 'ecke':'medium15', 'eckesachs':'medium15', 'sachs':'medium15', 'blut':'small15', 'blutgang':'small15', 'indra':'medium15', 'ivory':'bigii15', 'ivoryark':'bigii15', 'ark':'bigii15', 'auberon':'medium15', 'aub':'medium15', 'taisai':'big15', 'pholia':'big15', 'galilei':'medium15', 'europa':'medium15', 'benedia':'medium15', 'thunderbolt':'big15', 'shibow':'big15', 'rein':'bigii15', 'babel':'bigii15', 'mandeb':'bigii15', 'bab-el-mandeb':'bigii15', 'arca':'sephira', 'arcarum':'sephira', 'spoon':'medium15', 'coruscant':'medium15', 'crozier':'medium15', 'eva':'bigii15', 'evanescence':'bigii15'}
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
                    if len(m) > 0 and m[0] == 'f':
                        flat += values[ts.get(m[1:], m[1:])]
                        s2 += "{}+".format(values[ts.get(m[1:], m[1:])])
                    else:
                        base += values[ts.get(m, m)]
                        s1 += "{}+".format(values[ts.get(m, m)])
            if s1 != "": s1 = "Boosted " + s1[:-1]
            if s2 != "":
                if s1 != "": s1 += ", "
                s1 = s1 + "Flat " + s2[:-1]
            msg =  "**Aura ▫️ Critical ▫️▫️ Aura ▫️ Critical**\n"
            msg += "140% ▫️ {:.1f}% ▫️▫️ 290% ▫️ {:.1f}%\n".format(min(base*2.4 + flat, 100), min(base*3.9 + flat, 100))
            msg += "150% ▫️ {:.1f}% ▫️▫️ 300% ▫️ {:.1f}%\n".format(min(base*2.5 + flat, 100), min(base*4 + flat, 100))
            msg += "160% ▫️ {:.1f}% ▫️▫️ 310% ▫️ {:.1f}%\n".format(min(base*2.6 + flat, 100), min(base*4.1 + flat, 100))
            msg += "170% ▫️ {:.1f}% ▫️▫️ 320% ▫️ {:.1f}%\n".format(min(base*2.7 + flat, 100), min(base*4.2 + flat, 100))
            msg += "280% ▫️ {:.1f}%\n".format(min(base*3.8 + flat, 100))
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Critical Calculator", description=msg.replace('.0%', '%').replace('100%', '**100%**'), footer=s1, color=self.color))
        except Exception as e:
            if str(e) == "Empty Parameter":
                modstr = ""
                for m in values:
                    modstr += "`{}`, ".format(m)
                for m in ts:
                    modstr += "`{}`, ".format(m)
                final_msg = await ctx.reply(embed=self.bot.util.embed(title="Critical Calculator", description="**Posible modifiers:**\n" + modstr[:-2] + "\n\nModifiers must be separated by spaces\nAdd `f` before a modifier to make it unboosted" , color=self.color))
            else:
                final_msg = await ctx.reply(embed=self.bot.util.embed(title="Critical Calculator", description="Error", footer=str(e), color=self.color))
        await self.bot.util.clean(ctx, final_msg, 40)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["doom", "doompost", "magnafest", "magnafes", "campaign", "brick", "bar", "sunlight", "stone", "suptix", "surprise", "evolite", "fugdidmagnafeststart", "alivegame", "alive"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def deadgame(self, ctx):
        """Give the time elapsed of various GBF related releases"""
        msg = ""
        wiki_checks = ["Category:Campaign", "Surprise_Special_Draw_Set", "Damascus_Ingot", "Gold_Brick", "Sunlight_Stone", "Sephira_Evolite"]
        regexs = ["<td>(\\d+ days)<\\/td>\\s*<td><span class=\"image_link\"><a href=\"/Four_Symbols_Stone\"", "<td>(\\d+ days)<\\/td>\\s*<td>Time since last", "<td>(-\\d+ days)<\\/td>\\s*<td>Time since last", "<td>(\\d+ days)<\\/td>\\s*<td>Time since last", "<td>(\\d+ days)<\\/td>\\s*<td style=\"text-align: left;\">Time since last", "<td>(\\d+ days)<\\/td>\\s*<td style=\"text-align: center;\">\\?\\?\\?<\\/td>\\s*<td style=\"text-align: left;\">Time since last", "<td>(\\d+ days)<\\/td>\\s*<td style=\"text-align: center;\">\\?\\?\\?<\\/td>\\s*<td style=\"text-align: left;\">Time since last ", "<td style=\"text-align: center;\">\\?\\?\\?<\\/td>\\s*<td>(\\d+ days)<\\/td>\\s*"]
        for w in wiki_checks:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://gbf.wiki/{}".format(w)) as r:
                    if r.status == 200:
                        t = await r.text()
                        for r in regexs:
                            m = re.search(r, t)
                            if m:
                                msg += "**{}** since the last {}\n".format(m.group(1), w.replace("_", " ").replace("Category:", ""))
                                break

        # grand (for memes, might remove later)
        c = self.bot.util.JST()
        grands = {
            "Water": c.replace(year=2018, month=10, day=17, hour=19, minute=0, second=0, microsecond=0),
            "Wind": c.replace(year=2021, month=4, day=30, hour=19, minute=0, second=0, microsecond=0)
        }
        for e in grands:
            msg += "**{} days** since the last {} Grand\n".format(self.bot.util.delta2str(c - grands[e], 3).split('d')[0], e)

        if msg != "":
            final_msg = await ctx.send(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=msg, color=self.color))
        else:
            final_msg = await ctx.send(embed=self.bot.util.embed(title="Error", description="Unavailable", color=self.color))
        await self.bot.util.clean(ctx, final_msg, 30)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def account(self, ctx, id : int = -1):
        """List GBF accounts used by the bot (Owner Only)
        Specify one to test it"""
        if len(self.bot.data.save['gbfaccounts']) == 0:
            await ctx.send(embed=self.bot.util.embed(title="GBF Account status", description="No accounts set", color=self.color))
            return

        if id == -1:
            msg = ""
            for i in range(0, len(self.bot.data.save['gbfaccounts'])):
                acc = self.bot.data.save['gbfaccounts'][i]
                if i == self.bot.data.save['gbfcurrent']: msg += "👉 "
                else: msg += "{} ".format(i)
                msg += "**{}** ".format(acc[0])
                if acc[3] == 0: msg += "❔"
                elif acc[3] == 1: msg += "✅"
                elif acc[3] == 2: msg += "❎"
                msg += "\n"
            await self.bot.send('debug', embed=self.bot.util.embed(title="GBF Account status", description=msg, color=self.color))
            await self.bot.util.react(ctx.message, '✅') # white check mark
        else:
            acc = self.bot.gbf.get(id)
            if acc is None:
                await ctx.send(embed=self.bot.util.embed(title="GBF Account status", description="No accounts set in slot {}".format(id), color=self.color))
                return
            r = await self.bot.do(self.bot.gbf.request, self.bot.data.config['gbfwatch']['test'], account=id, decompress=True, load_json=True, check=True, force_down=True)
            if r is None or r.get('user_id', None) != acc[0]:
                await self.bot.send('debug', embed=self.bot.util.embed(title="GBF Account status", description="Account #{} is down\nck: `{}`\nuid: `{}`\nua: `{}`\n".format(id, acc[0], acc[1], acc[2]) , color=self.color))
                with self.bot.data.lock:
                    self.bot.data.save['gbfaccounts'][id][3] = 2
                    self.bot.data.pending = True
            elif r == "Maintenance":
                await self.bot.send('debug', embed=self.bot.util.embed(title="GBF Account status", description="Game is in maintenance", color=self.color))
            else:
                await self.bot.send('debug', embed=self.bot.util.embed(title="GBF Account status", description="Account #{} is up\nck: `{}`\nuid: `{}`\nua: `{}`\n".format(id, acc[0], acc[1], acc[2]), color=self.color))
                with self.bot.data.lock:
                    self.bot.data.save['gbfaccounts'][id][3] = 1
                    self.bot.data.save['gbfaccounts'][id][5] = self.bot.util.JST()
                    self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def switch(self, ctx, id : int):
        """Select the current GBF account to use (Owner Only)"""
        if self.bot.gbf.get(id) is not None:
            with self.bot.data.lock:
                self.bot.data.save['gbfcurrent'] = id
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark
        else:
            await self.bot.util.react(ctx.message, '❌')

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def addAccount(self, ctx, uid : int, ck : str, ua : str):
        """Add a GBF account to the bot (Owner Only)"""
        if uid < 1:
            await ctx.send(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(uid), color=self.color))
            return
        if ck == "":
            await ctx.send(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ck), color=self.color))
            return
        if ua == "":
            await ctx.send(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ua), color=self.color))
            return
        self.bot.gbf.add(uid, ck, str)
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def delAccount(self, ctx, num : int):
        """Add a GBF account to the bot (Owner Only)"""
        if self.bot.gbf.remove(num):
            await self.bot.util.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def sauid(self, ctx, num : int, uid : int = -1):
        """Modify a GBF account (Owner Only)"""
        if uid < 0:
            acc = self.bot.gbf.get(num)
            if acc is None:
                await ctx.send(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color))
            else:
                await self.bot.send('debug', embed=self.bot.util.embed(title="Account #{} current UID".format(num), description="`{}`".format(acc[0]), color=self.color))
        elif not self.bot.gbf.update(num, uid=uid):
            await ctx.send(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(uid), color=self.color))
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def sack(self, ctx, num : int, *, ck : str = ""):
        """Modify a GBF account (Owner Only)"""
        if ck == "":
            acc = self.bot.gbf.get(num)
            if acc is None:
                await ctx.send(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color))
            else:
                await self.bot.send('debug', embed=self.bot.util.embed(title="Account #{} current CK".format(num), description="`{}`".format(acc[1]), color=self.color))
        elif not self.bot.gbf.update(num, ck=ck):
            await ctx.send(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ck), color=self.color))
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def saua(self, ctx, num : int, *, ua : str = ""):
        """Modify a GBF account (Owner Only)"""
        if ua == "":
            acc = self.bot.gbf.get(num)
            if acc is None:
                await ctx.send(embed=self.bot.util.embed(title="Error", description="No account in slot {}".format(num), color=self.color))
            else:
                await self.bot.send('debug', embed=self.bot.util.embed(title="Account #{} current UA".format(num), description="`{}`".format(acc[2]), color=self.color))
        elif not self.bot.gbf.update(num, ua=ua):
            await ctx.send(embed=self.bot.util.embed(title="Error", description="Invalid parameter {}".format(ua), color=self.color))
        await self.bot.util.react(ctx.message, '✅') # white check mark

    def getCurrentGacha(self):
        c = self.bot.util.JST().replace(microsecond=0) - timedelta(seconds=80)
        if ('gachatime' not in self.bot.data.save['gbfdata'] or self.bot.data.save['gbfdata']['gachatime'] is None or c >= self.bot.data.save['gbfdata']['gachatime']) and not self.getGacha():
            return []
        if self.bot.data.save['gbfdata']['gachatime'] is None:
            return []
        return [self.bot.data.save['gbfdata']['gachatime'] - c, self.bot.data.save['gbfdata']['gachatimesub'] - c, self.bot.data.save['gbfdata']['gachacontent'], self.bot.data.save['gbfdata']['gachabanner']]

    def getGacha(self): # get current gacha
        if not self.bot.gbf.isAvailable():
            return False
        try:
            c = self.bot.util.JST()
            #gacha page
            data = self.bot.gbf.request("http://game.granbluefantasy.jp/gacha/list?PARAMS", account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check_update=True)
            if data is None: raise Exception()
            gachatime = datetime.strptime(data['legend']['lineup'][-1]['end'], '%m/%d %H:%M').replace(year=c.year, microsecond=0)
            NY = False
            if c > gachatime:
                gachatime.replace(year=gachatime.year+1) # new year fix
                NY = True
            gachatimesub = datetime.strptime(data['ceiling']['end'], '%Y/%m/%d %H:%M').replace(microsecond=0)
            if (NY == False and gachatimesub < gachatime) or (NY == True and gachatimesub > gachatime): gachatime = gachatimesub # switched
            random_key = data['legend']['random_key']
            header_images = data['header_images']
            logo_id = {'logo_fire':1, 'logo_water':2, 'logo_earth':3, 'logo_wind':4, 'logo_dark':5, 'logo_light':6}.get(data.get('logo_image', ''), data.get('logo_image', '').replace('logo_', ''))
            gachabanner = None
            gachaid = data['legend']['lineup'][-1]['id']

            # draw rate
            data = self.bot.gbf.request("http://game.granbluefantasy.jp/gacha/provision_ratio/{}/1?PARAMS".format(gachaid), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check_update=True)
            # build list
            banner_msg = "{} **{}** Rate".format(self.bot.emote.get('SSR'), data['ratio'][0]['ratio'])
            if not data['ratio'][0]['ratio'].startswith('3'):
                banner_msg += " ▫️ **Premium Gala**"
            banner_msg += "\n"
            possible_zodiac_wpn = ['Ramulus', 'Dormius', 'Gallinarius', 'Canisius', 'Porculius', 'Rodentius', 'Bovinius']
            rateuplist = {'zodiac':[]} # SSR list
            rateup = [{'rate':0, 'list':{}}, {'rate':0, 'list':{}}, {'rate':0, 'list':{}}] # to store the gacha (for GBF_Game cog)
            for appear in data['appear']:
                rarity = appear['rarity'] - 2
                if rarity < 0 or rarity > 2: continue # eliminate possible N rarity
                rateup[rarity]['rate'] = float(data['ratio'][2 - rarity]['ratio'][:-1])
                for item in appear['item']:
                    if item['drop_rate'] not in rateup[rarity]['list']: rateup[rarity]['list'][item['drop_rate']] = []
                    rateup[rarity]['list'][item['drop_rate']].append(item['name'])

                    if rarity == 2: # ssr
                        if appear['category_name'] not in rateuplist: rateuplist[appear['category_name']] = {}
                        if 'character_name' in item and item.get('name', '') in possible_zodiac_wpn:
                            rateuplist['zodiac'].append(item['character_name'])
                        if item['incidence'] is not None:
                            if item['drop_rate'] not in rateuplist[appear['category_name']]: rateuplist[appear['category_name']][item['drop_rate']] = []
                            if 'character_name' in item and item['character_name'] is not None: rateuplist[appear['category_name']][item['drop_rate']].append(item['character_name'])
                            else: rateuplist[appear['category_name']][item['drop_rate']].append(item['name'])

            # build rate up
            gacharateups = []
            for k in rateuplist:
                if k == 'zodiac':
                    if len(rateuplist['zodiac']) > 0:
                        banner_msg += "{} **Zodiac** ▫️ ".format(self.bot.emote.get('loot'))
                        comma = False
                        for i in rateuplist[k]:
                            if comma: banner_msg += ", "
                            else: comma = True
                            banner_msg += i
                        banner_msg += "\n"
                else:
                    if len(rateuplist[k]) > 0:
                        for r in rateuplist[k]:
                            if r not in gacharateups: gacharateups.append(r)
                            if k.lower().find("weapon") != -1: banner_msg += "{}**{}%** ▫️ ".format(self.bot.emote.get('sword'), r)
                            elif k.lower().find("summon") != -1: banner_msg += "{}**{}%** ▫️ ".format(self.bot.emote.get('summon'), r)
                            count = 0
                            for i in rateuplist[k][r]:
                                if count >= 8 and len(rateuplist[k][r]) - count > 1:
                                    banner_msg += " and {} more!".format(len(rateuplist[k][r]) - count - 1)
                                    break
                                elif count > 0: banner_msg += ", "
                                count += 1
                                banner_msg += i
                        banner_msg += "\n"
            gachacontent = banner_msg
            # add image
            gachas = ['{}/tips/description_gacha.jpg'.format(random_key), '{}/tips/description_gacha_{}.jpg'.format(random_key, logo_id), '{}/tips/description_{}.jpg'.format(random_key, header_images[0]), 'header/{}.png'.format(header_images[0])]
            for g in gachas:
                data = self.bot.gbf.request("http://game-a.granbluefantasy.jp/assets_en/img/sp/gacha/{}".format(g), no_base_headers=True)
                if data is not None:
                    gachabanner = "http://game-a.granbluefantasy.jp/assets_en/img/sp/gacha/{}".format(g)
                    break

            # save
            with self.bot.data.lock:
                self.bot.data.save['gbfdata']['rateup'] = rateup
                self.bot.data.save['gbfdata']['gachatime'] = gachatime
                self.bot.data.save['gbfdata']['gachatimesub'] = gachatimesub
                self.bot.data.save['gbfdata']['gachabanner'] = gachabanner
                self.bot.data.save['gbfdata']['gachacontent'] = gachacontent
                self.bot.data.save['gbfdata']['gacharateups'] = gacharateups
                self.bot.data.pending = True
            return True
        except Exception as e:
            print('updategacha(): ', self.bot.util.pexc(e))
            self.bot.errn += 1
            with self.bot.data.lock:
                self.bot.data.save['gbfdata']['gachatime'] = None
                self.bot.data.save['gbfdata']['gachatimesub'] = None
                self.bot.data.save['gbfdata']['gachabanner'] = None
                self.bot.data.save['gbfdata']['gachacontent'] = None
                self.bot.data.save['gbfdata']['gacharateups'] = None
                self.bot.data.pending = True # save anyway
            return False

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['rateup', 'banner'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gacha(self, ctx):
        """Post the current gacha informations"""
        try:
            content = await self.bot.do(self.getCurrentGacha)
            if len(content) > 0:
                description = "{} Current gacha ends in **{}**".format(self.bot.emote.get('clock'), self.bot.util.delta2str(content[0], 2))
                if content[0] != content[1]:
                    description += "\n{} Spark period ends in **{}**".format(self.bot.emote.get('mark'), self.bot.util.delta2str(content[1], 2))
                description += "\n" + content[2]
                await ctx.send(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, thumbnail=content[3], color=self.color))
        except Exception as e:
            await self.bot.sendError("getcurrentgacha", e)
            await ctx.send(embed=self.bot.util.embed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description="Unavailable", color=self.color))

    def getProfileData(self, id : int): # get player data
        if not self.bot.gbf.isAvailable():
            return "Maintenance"
        res = self.bot.gbf.request("http://game.granbluefantasy.jp/profile/content/index/{}?PARAMS".format(id), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)
        if res is not None: return unquote(res['data'])
        else: return res

    def searchProfile(self, gbf_id):
        user_ids = list(self.bot.data.save['gbfids'].keys())
        for uid in user_ids:
            if self.bot.data.save['gbfids'].get(uid, None) == gbf_id:
                return uid
        return None

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['clearid'])
    @isOwner()
    async def clearProfile(self, ctx, gbf_id : int):
        """Unlink a GBF id (Owner Only)"""
        user_id = await self.bot.do(self.searchProfile, gbf_id)
        if user_id is None:
            await ctx.send(embed=self.bot.util.embed(title="Clear Profile Error", description="ID not found", color=self.color))
        else:
            try:
                with self.bot.data.lock:
                    del self.bot.data.save['gbfids'][user_id]
                    self.bot.data.pending = True
            except:
                pass
            await self.bot.send('debug', 'User `{}` has been removed'.format(user_id))
            await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['unsetid'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def unsetProfile(self, ctx):
        """Unlink your GBF id"""
        if str(ctx.author.id) not in self.bot.data.save['gbfids']:
            await ctx.reply(embed=self.bot.util.embed(title="Unset Profile Error", description="You didn't set your GBF profile ID", color=self.color))
            return
        with self.bot.data.lock:
            try:
                del self.bot.data.save['gbfids'][str(ctx.author.id)]
                self.bot.data.pending = True
            except:
                pass
        await self.bot.util.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['setid'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def setProfile(self, ctx, id : int):
        """Link your GBF id to your Discord ID"""
        try:
            if id < 0 or id >= 100000000:
                await ctx.reply(embed=self.bot.util.embed(title="Set Profile Error", description="Invalid ID", color=self.color))
                return
            data = await self.bot.do(self.getProfileData, id)
            if data == "Maintenance":
                await ctx.reply(embed=self.bot.util.embed(title="Set Profile Error", description="Game is in maintenance, try again later.", color=self.color))
                return
            elif data == "Down":
                return
            elif data is None:
                await ctx.reply(embed=self.bot.util.embed(title="Set Profile Error", description="Profile not found", color=self.color))
                return
            elif (await self.bot.do(self.searchProfile, id)) is not None:
                await ctx.reply(embed=self.bot.util.embed(title="Set Profile Error", description="This id is already in use", footer="use the bugreport command if it's a case of griefing", color=self.color))
                return
            # register
            with self.bot.data.lock:
                self.bot.data.save['gbfids'][str(ctx.author.id)] = id
                self.bot.data.pending = True
            await self.bot.util.react(ctx.message, '✅') # white check mark
        except Exception as e:
            await self.bot.sendError("setprofile", e)

    def pasteImage(self, img, file, offset, resize=None): # paste and image onto another
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None: buffers.append(buffers[-1].resize(resize, Image.LANCZOS))
        img.paste(buffers[-1], offset, buffers[-1])
        for buf in buffers: buf.close()
        del buffers

    def dlAndPasteImage(self, img, url, offset, resize=None): # dl an image and call pasteImage()
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

    def processProfile(self, id, data):
        soup = BeautifulSoup(data, 'html.parser')
        try: name = soup.find_all("span", class_="txt-other-name")[0].string
        except: name = None
        if name is not None:
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
            comment = su.unescape(soup.find_all("div", class_="prt-other-comment")[0].string).replace('\t', '').replace('\n', '')
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
                    crew = soup.find_all("div", class_="prt-guild-name")[0].string
                    crewid = soup.find_all("div", class_="btn-guild-detail")[0]['data-location-href']
                    crew = "[{}](http://game.granbluefantasy.jp/#{})".format(crew, crewid)
                except: crew = soup.find_all("div", class_="txt-notjoin")[0].string
            except:
                crew = None

            # get the last gw score
            scores = ""
            try:
                pdata = self.bot.get_cog('GuildWar').searchGWDBPlayer(id, 2)
            except:
                pdata = None
            if pdata is not None:
                for n in range(0, 2):
                    if pdata[n] is not None and 'result' in pdata[n] and len(pdata[n]['result']) == 1:
                        try:
                            if pdata[n]['result'][0][0] is None:
                                scores += "{} GW**{}** ▫️ **{:,}** honors\n".format(self.bot.emote.get('gw'), pdata[n].get('gw', ''), pdata[n]['result'][0][3])
                            else:
                                scores += "{} GW**{}** ▫️ #**{}** ▫️ **{:,}** honors\n".format(self.bot.emote.get('gw'), pdata[n].get('gw', ''), pdata[n]['result'][0][0], pdata[n]['result'][0][3])
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
                if starcom is not None and starcom[0] != "(Blank)": msg += "\n\u202d💬 `{}`".format(su.unescape(starcom[0].replace('`', '\'')))
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
                            d.text((equip_size[0]-50, portrait_size[1]+lvl_box_height+equip_size[1]-30), plus[0].text, fill=(255, 255, 95), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
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
                thumbnail = "{}_{}.png".format(id, datetime.utcnow().timestamp())
                img.save(thumbnail, "PNG")
                img.close()
            except Exception as e:
                print(e)
                thumbnail = ""
                try: img.close()
                except: pass
            if trophy == "No Trophy Displayed": title = "\u202d{} **{}**".format(self.bot.emote.get(rarity), name)
            else: title = "\u202d{} **{}**▫️{}".format(self.bot.emote.get(rarity), name, trophy)
            return title, "{}{}\n{} Crew ▫️ {}\n{}{}\n\n[:earth_asia: Preview]({})".format(rank, comment, self.bot.emote.get('gw'), crew, scores, star, thumbnail), thumbnail
        else:
            return None, "Profile is private", ""

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['id'])
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def profile(self, ctx, *target : str):
        """Retrieve a GBF profile"""
        target = " ".join(target)
        try:
            if target == "":
                if str(ctx.author.id) not in self.bot.data.save['gbfids']:
                    await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="{} didn't set its profile ID\nUse `findplayer` to search the GW Database".format(ctx.author.display_name), footer="setProfile <id>", color=self.color))
                    return
                id = self.bot.data.save['gbfids'][str(ctx.author.id)]
            elif target.startswith('<@') and target.endswith('>'):
                try:
                    if target[2] == "!": target = int(target[3:-1])
                    else: target = int(target[2:-1])
                    member = ctx.guild.get_member(target)
                    if str(member.id) not in self.bot.data.save['gbfids']:
                        await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="{} didn't set its profile ID\nUse `findplayer` to search the GW Database".format(member.display_name), footer="setProfile <id>", color=self.color))
                        return
                    id = self.bot.data.save['gbfids'][str(member.id)]
                except:
                    await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Invalid parameter {} -> {}".format(target, type(target)), color=self.color))
                    return
            else:
                try: id = int(target)
                except:
                    member = ctx.guild.get_member_named(target)
                    if member is None:
                        await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Member not found", color=self.color))
                        return
                    elif str(member.id) not in self.bot.data.save['gbfids']:
                        await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="{} didn't set its profile ID\nUse `findplayer` to search the GW Database".format(member.display_name), footer="setProfile <id>", color=self.color))
                        return
                    id = self.bot.data.save['gbfids'][str(member.id)]
            if id < 0 or id >= 100000000:
                await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Invalid ID", color=self.color))
                return
            if id in self.badprofilecache:
                await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Profile not found", color=self.color))
                return
            await self.bot.util.react(ctx.message, 'time')
            data = await self.bot.do(self.getProfileData, id)
            if data == "Maintenance":
                await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Game is in maintenance", color=self.color))
                await self.bot.util.unreact(ctx.message, 'time')
                return
            elif data == "Down":
                await self.bot.util.unreact(ctx.message, 'time')
                return
            elif data is None:
                self.badprofilecache.append(id)
                await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Profile not found", color=self.color))
                await self.bot.util.unreact(ctx.message, 'time')
                return
            title, description, thumbnail = await self.bot.do(self.processProfile, id, data)
            try:
                with open(thumbnail, 'rb') as infile:
                    df = discord.File(infile)
                    message = await self.bot.send('image', file=df)
                    df.close()
                self.bot.file.rm(thumbnail)
                description = description.replace(thumbnail, message.attachments[0].url)
                thumbnail = message.attachments[0].url
            except:
                description = description.replace("\n[:earth_asia: Preview]({})".format(thumbnail), "")
                thumbnail = ""
            await self.bot.util.unreact(ctx.message, 'time')
            final_msg = await ctx.reply(embed=self.bot.util.embed(title=title, description=description, image=thumbnail, url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
            await self.bot.util.clean(ctx, final_msg, 45)
        except Exception as e:
            await self.bot.sendError("profile", e)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def coop(self, ctx):
        """Retrieve the current coop daily missions"""
        try:
            data = await self.bot.do(self.bot.gbf.request, 'http://game.granbluefantasy.jp/coopraid/daily_mission?PARAMS', account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check=True)['daily_mission']
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
            await ctx.send(embed=self.bot.util.embed(author={'name':"Daily Coop Missions", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=msg, color=self.color))
        except:
            await self.bot.util.react(ctx.message, '❎') # white negative mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['badboi', 'branded', 'restricted'])
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def brand(self, ctx, id : int):
        """Check if a GBF profile is restricted"""
        try:
            if id < 0 or id >= 100000000:
                await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Invalid ID", color=self.color))
                return
            if id in self.badprofilecache:
                await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Profile not found", color=self.color))
                return
            data = await self.bot.do(self.bot.gbf.request, "http://game.granbluefantasy.jp/forum/search_users_id?PARAMS", account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True, check=True, payload={"special_token":None,"user_id":id})
            if data == "Maintenance":
                await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Game is in maintenance", color=self.color))
                return
            elif data == "Down":
                return
            elif len(data['user']) == 0:
                await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="In game message:\n`{}`".format(data['no_member_msg'].replace("<br>", " ")), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
                return
            try:
                if data['user']["restriction_flag_list"]["event_point_deny_flag"]:
                    status = "Account is restricted"
                else:
                    status = "Account isn't restricted"
            except:
                status = "Account isn't restricted"
            await ctx.reply(embed=self.bot.util.embed(title="{} {}".format(self.bot.emote.get('gw'), data['user']['nickname']), description=status, thumbnail="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/talk/{}.png".format(data['user']['image']), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
        except Exception as e:
            await ctx.reply(embed=self.bot.util.embed(title="Profile Error", description="Unavailable", color=self.color))
            await self.bot.sendError("brand", e)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def news(self, ctx):
        """Post the latest new posts"""
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
            final_msg = await ctx.send(embed=self.bot.util.embed(title="Unavailable", color=self.color))
        else:
            final_msg = await ctx.send(embed=self.bot.util.embed(author={'name':"Latest Granblue Fantasy News", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=msg, image=thumb, color=self.color))
        await self.bot.util.clean(ctx, final_msg, 45)

    @commands.command(no_pm=True, name='4koma', cooldown_after_parsing=True, aliases=['granblues'])
    @commands.cooldown(2, 40, commands.BucketType.guild)
    async def _4koma(self, ctx, id : int = -123456789):
        """Post a Granblues Episode"""
        try:
            if id == -123456789: id = int(self.bot.data.save['gbfdata']['4koma'])
            if id < 0 or id > int(self.bot.data.save['gbfdata']['4koma']): raise Exception()
            final_msg = await ctx.reply(embed=self.bot.util.embed(title="Granblue Episode {}".format(id), url="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/comic/episode/episode_{}.jpg".format(id), image="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/comic/thumbnail/thum_{}.png".format(str(id).zfill(5)), color=self.color))
            await self.bot.util.clean(ctx, final_msg, 45)
        except:
            await self.bot.util.react(ctx.message, '❎') # white negative mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['tweet'])
    @commands.cooldown(1, 2, commands.BucketType.default)
    async def twitter(self, ctx, term : str = ""):
        """Post a twitter account (Tweepy enhanced)
        If none is found and twitter is enabled, try to get the corresponding user.
        options: granblue_en, en, noel, channel, tv wawi, raidpic, pic, kmr, fkhr,
        kakage, hag, jk, hecate, hecate_mk2, gbfverification, gw, gamewith, anime,
        gbf, granblue"""
        registered = {
            'granblue_en' : ["granblue_en", "Welcome EOP"],
            'en' : ["granblue_en", "Welcome EOP"],
            'noel' : ["noel_gbf", "Japanese Granblue news"],
            'tv' : ["noel_gbf", "Japanese Granblue news"],
            'channel' : ["noel_gbf", "Japanese Granblue news"],
            'wawi' : ["wawigbf", "Subscribe: https://twitter.com/Wawi3313"],
            'raidpic' : ["twihelp_pic", "To grab Granblue raid artworks"],
            'pic' : ["twihelp_pic", "To grab Granblue raid artworks"],
            'kmr' : ["kimurayuito", "Give praise, for he has no equal"],
            'fkhr' : ["hiyopi", "The second in charge"],
            'kakage' : ["kakage0904", "Young JK inside"],
            'hag' : ["kakage0904", "Young JK inside"],
            'jk' : ["kakage0904", "Young JK inside"],
            'hecate' : ["hecate_mk2", "For nerds :nerd:"],
            'hecate_mk2' : ["hecate_mk2", "For nerds :nerd:"],
            'gbfverification' : ["hecate_mk2", "For nerds :nerd:"],
            'gw' : ["granblue_gw", ":nine: / :keycap_ten:"],
            'gamewith' : ["granblue_gw", ":nine: / :keycap_ten:"],
            'anime' : ["anime_gbf", ":u5408:"],
            'gbf' : ["granbluefantasy", "Official account"],
            'granblue' : ["granbluefantasy", "Official account"]
        }

        target = registered.get(term.lower(), None)
        pic = None
        user = None
        accepted = (target is not None)

        if target is None:
            user = self.bot.twitter.user(term.lower())
        else:
            user = self.bot.twitter.user(target[0])
        if user is not None:
            pic = user.profile_image_url.replace("normal", "bigger")
        else:
            pic = None

        if accepted:
            if user is None:
                await ctx.reply(embed=self.bot.util.embed(title=target[0], url="https://twitter.com/{}".format(target[0]), description=target[1], thumbnail=pic, color=self.color))
            else:
                await ctx.reply(embed=self.bot.util.embed(title=user.name, url="https://twitter.com/{}".format(target[0]), description=target[1], thumbnail=pic, color=self.color))
        elif user is None:
            await ctx.reply(embed=self.bot.util.embed(title="Error", description="`{}` not found".format(term), color=self.color))
        elif ctx.channel.is_nsfw():
            await ctx.reply(embed=self.bot.util.embed(title=user.name, url="https://twitter.com/{}".format(user.screen_name), thumbnail=pic, color=self.color))
        else:
            await ctx.reply(embed=self.bot.util.embed(title="NSFW protection", description="Check at your own risk\n[{}](https://twitter.com/{})".format(user.name, user.screen_name), color=self.color))