import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib import request, parse
from urllib.parse import unquote
import asyncio
import aiohttp
import json
import zlib
import re
import io
import hashlib
import string
import sqlite3
from bs4 import BeautifulSoup
from xml.sax import saxutils as su
from PIL import Image, ImageFont, ImageDraw
from translate import Translator
from queue import Queue
import concurrent.futures
from threading import Thread

class GBF_Access(commands.Cog):
    """GBF advanced commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xde8633
        self.rankre = re.compile("Rank ([0-9])+")
        self.sumre = re.compile("<div id=\"js-fix-summon([0-9]{2})-name\" class=\"prt-fix-name\" name=\"[A-Za-z'-. ]+\">(Lvl [0-9]+ [A-Za-z'-. ]+)<\/div>")
        self.starre = re.compile("<span class=\"prt-current-npc-name\">\s*(Lvl [0-9]+ [A-Za-z'-.μ ]+)\s*<\/span>")
        self.starcomre = re.compile("<div class=\"prt-pushed-info\">(.+)<\/div>")
        self.empre = re.compile("<div class=\"txt-npc-rank\">([0-9]+)<\/div>")
        self.starringre = re.compile("<div class=\"ico-augment2-s\"><\/div>\s*<\/div>\s*<div class=\"prt-pushed-spec\">\s*<div class=\"prt-pushed-info\">")
        self.starplusre = re.compile("<div class=\"prt-quality\">(\+[0-9]+)<\/div>")
        self.badprofilecache = []
        self.badcrewcache = []
        self.crewcache = {}
        self.possiblesum = {'10':'fire', '20':'water', '30':'earth', '40':'wind', '50':'light', '60':'dark', '00':'misc', '01':'misc'}
        self.subsum = {'chev':'luminiera omega', 'chevalier':'luminiera omega', 'lumi':'luminiera omega', 'luminiera':'luminiera omega', 'colossus':'colossus omega', 'colo':'colossus omega', 'leviathan':'leviathan omega', 'levi':'leviathan omega', 'yggdrasil':'yggdrasil omega', 'yugu':'yggdrasil omega', 'tiamat':'tiamat omega', 'tia':'tiamat omega', 'celeste':'celeste omega', 'boat':'celeste omega', 'alex':'godsworn alexiel', 'alexiel':'godsworn alexiel', 'zeph':'zephyrus', 'longdong':'huanglong', 'dong':'huanglong', 'long':'huanglong', 'bunny':'white rabbit', 'kirin':'qilin', 'sylph gacha':'sylph, flutterspirit of purity', 'poseidon gacha':'poseidon, the tide father', 'anat gacha':'anat, for love and war', 'cerberus gacha':'cerberus, hellhound trifecta', 'marduck gacha':'marduk, battlefield reaper'}
        self.sql = {
            'summon' : [None, None, False], # conn, cursor, status
            'old_gw' : [None, None, None], # conn, cursor, status
            'gw' : [None, None, None] # conn, cursor, status
        }
        self.loadinggw = False
        self.loadinggacha = False
        self.translator = Translator(from_lang='ja', to_lang='en')
        self.blacklist = ["677159", "147448"]
        self.stoprankupdate = False

    def startTasks(self):
        self.bot.runTask('gbfwatch', self.gbfwatch)
        self.bot.runTask('summon', self.summontask)
        self.bot.runTask('check_ranking', self.checkGWRanking)

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    async def checkGWRanking(self):
        cog = self.bot.get_cog('GuildWar')
        if cog is None:
            return
        crewsA = [300, 1000, 2000, 8000, 19000, 30000]
        crewsB = [2000, 5500, 9000, 14000, 18000, 30000]
        players = [2000, 70000, 120000, 160000, 250000, 350000]

        days = ["End", "Day 5", "Day 4", "Day 3", "Day 2", "Day 1", "Interlude", "Preliminaries"]
        minute_update = [3, 23, 43]

        while True:
            cog.getGWState()
            try:
                if self.bot.gw['state'] == False:
                    if 'ranking' not in self.bot.gw or self.bot.gw['ranking'] is not None:
                        self.bot.gw['ranking'] = None
                        self.bot.savePending = True
                    await asyncio.sleep(3600)
                elif self.bot.getJST() < self.bot.gw['dates']["Preliminaries"]:
                    if 'ranking' not in self.bot.gw or self.bot.gw['ranking'] is not None:
                        self.bot.gw['ranking'] = None
                        self.bot.savePending = True
                    d = self.bot.gw['dates']["Preliminaries"] - self.bot.getJST()
                    await asyncio.sleep(d.seconds + 1)
                elif self.bot.getJST() > self.bot.gw['dates']["Day 5"] - timedelta(seconds=21600):
                    await asyncio.sleep(3600)
                else:
                    if await self.bot.isGameAvailable():
                        current_time = self.bot.getJST()
                        m = current_time.minute
                        h = current_time.hour
                        skip = False
                        for d in days:
                            if current_time < self.bot.gw['dates'][d]:
                                continue
                            elif ((d == "Preliminaries" or d.startswith("Day")) and h < 7 and h >= 2) or d == "Day 5":
                                skip = True
                            break
                        if skip:
                            await asyncio.sleep(600)
                        elif m in minute_update:
                            if d.startswith("Day "):
                                crews = crewsB
                            else:
                                crews = crewsA
                            # update $ranking and $estimation
                            try:
                                data = [{}, {}, {}, {}, current_time - timedelta(seconds=60 * (current_time.minute % 20))]
                                if self.bot.gw['ranking'] is not None:
                                    diff = data[4] - self.bot.gw['ranking'][4]
                                    diff = round(diff.total_seconds() / 60.0)
                                else: diff = 0
                                for c in crews:
                                    r = await self.requestRanking(c // 10, True)
                                    if r is not None and 'list' in r and len(r['list']) > 0:
                                        data[0][str(c)] = int(r['list'][-1]['point'])
                                        if diff > 0 and self.bot.gw['ranking'] is not None and str(c) in self.bot.gw['ranking'][0]:
                                            data[2][str(c)] = (data[0][str(c)] - self.bot.gw['ranking'][0][str(c)]) / diff
                                    await asyncio.sleep(0.001)

                                for p in players:
                                    r = await self.requestRanking(p // 10, False)
                                    if r is not None and 'list' in r and len(r['list']) > 0:
                                        data[1][str(p)] = int(r['list'][-1]['point'])
                                        if diff > 0 and self.bot.gw['ranking'] is not None and str(p) in self.bot.gw['ranking'][1]:
                                            data[3][str(p)] = (data[1][str(p)] - self.bot.gw['ranking'][1][str(p)]) / diff
                                    await asyncio.sleep(0.001)

                                self.bot.gw['ranking'] = data
                                self.bot.savePending = True
                            except Exception as ex:
                                await self.bot.sendError('checkgwranking', str(ex))
                                self.bot.gw['ranking'] = None
                                self.bot.savePending = True

                            # update DB
                            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as async_executor:
                                if await self.bot.loop.run_in_executor(async_executor, self.gwscrap):
                                    data = await self.GWDBver()
                                    if data is not None and data[1] is not None:
                                        if self.bot.gw['id'] != data[1]['gw']: # different gw, we move
                                            self.bot.drive.delFiles(["GW_old.sql"], self.bot.tokens['files'])
                                            self.bot.drive.mvFile("GW.sql", self.bot.tokens['files'], "GW_old.sql")
                                    if not self.bot.drive.overwriteFile("temp.sql", "application/sql", "GW.sql", self.bot.tokens['files']): # upload
                                        await self.bot.sendError('gwscrap', 'Upload failed')
                                    self.bot.delFile('temp.sql')
                                    await self.loadGWDB() # reload db
                                else:
                                    await self.bot.sendError('gwscrap', 'Scraping failed')

                            await asyncio.sleep(300)
                        else:
                            await asyncio.sleep(30)
                    else:
                        await asyncio.sleep(60)
            except asyncio.CancelledError:
                await self.bot.sendError('checkgwranking', 'cancelled')
                await asyncio.sleep(30)
            except Exception as e:
                await self.bot.sendError('checkgwranking', str(e))
                return

    async def gbfwatch(self): # watch GBF state
        self.bot.setChannels([['private_update', 'you_private'], ['public_update', 'you_general'], ['gbfg_update', 'gbfg_general']])
        maintenance_time = self.bot.getJST()
        while True:
            if self.bot.exit_flag: return

            # maintenance check
            if not await self.bot.isGameAvailable():
                if self.bot.maintenance['state'] == True:
                    if self.bot.maintenance['duration'] > 0:
                        m_end = self.bot.maintenance['time'] + timedelta(seconds=3600*self.bot.maintenance['duration'])
                        current_time = self.bot.getJST()
                        if current_time >= m_end:
                            await asyncio.sleep(30)
                        else:
                            d = m_end - current_time
                            await asyncio.sleep(d.seconds+1)
                    else:
                        await asyncio.sleep(100)
                else:
                    if self.bot.getJST() - maintenance_time >= timedelta(seconds=500):
                        self.bot.maintenance["state"] = True
                        self.bot.maintenance["duration"] = 0
                        self.bot.savePending = True
                        await self.bot.send('debug', embed=self.bot.buildEmbed(title="Maintenance check", description="Maintenance detected" , color=self.color))
                    await asyncio.sleep(100)
                continue
            else:
                maintenance_time = self.bot.getJST()
                if self.bot.maintenance['state'] == True and (self.bot.maintenance['duration'] == 0 or (self.bot.getJST() > self.bot.maintenance['time'] + timedelta(seconds=3600*self.bot.maintenance['duration']))):
                    self.bot.maintenance = {"state" : False, "time" : None, "duration" : 0}
                    self.bot.savePending = True

            try: # account refresh
                await asyncio.sleep(0.001)
                if 'test' in self.bot.gbfdata:
                    current_time = self.bot.getJST()
                    for i in range(0, len(self.bot.gbfaccounts)):
                        acc = self.bot.gbfaccounts[i]
                        if acc[3] == 0 or (acc[3] == 1 and (acc[5] is None or current_time - acc[5] >= timedelta(seconds=7200))):
                            r = await self.bot.sendRequest(self.bot.gbfwatch['test'], account=i, decompress=True, load_json=True, check=True)
                            if r is None or str(r.get('user_id', None)) != str(acc[0]):
                                await self.bot.send('debug', embed=self.bot.buildEmbed(title="Account refresh", description="Account #{} is down".format(i) , color=self.color))
                                self.bot.gbfaccounts[i][3] = 2
                            elif r == "Maintenance":
                                break
                            else:
                                self.bot.gbfaccounts[i][3] = 1
                                self.bot.gbfaccounts[i][5] = current_time
                            self.bot.savePending = True
            except asyncio.CancelledError:
                await self.bot.sendError('gbfwatch', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('gbfwatch A', str(e))

            try: # news checker
                await asyncio.sleep(0.001)
                news = await self.checkNews()
                if 'news_url' in self.bot.gbfdata:
                    foundNew = False
                    for i in range(0, len(news)):
                        found = False
                        for j in range(0, len(self.bot.gbfdata['news_url'])):
                            if news[i][0] == self.bot.gbfdata['news_url'][j][0]:
                                found = True
                                break
                        if not found:
                            await self.bot.sendMulti(['debug', 'public_update', 'gbfg_update'], embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy News", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description="[{}]({})".format(self.translate(news[i][1]), news[i][0]), image=news[i][2], color=self.color))
                            foundNew = True
                    if foundNew:
                        self.bot.gbfdata['news_url'] = news
                        self.bot.savePending = True
                else:
                    self.bot.gbfdata['news_url'] = news
                    self.bot.savePending = True
            except asyncio.CancelledError:
                await self.bot.sendError('gbfwatch', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('gbfwatch B', str(e))

            try: # 4koma checker
                await asyncio.sleep(0.001)
                last = await self.check4koma()
                if '4koma' in self.bot.gbfdata:
                    if last is not None and last['id'] != self.bot.gbfdata['4koma']:
                        self.bot.gbfdata['4koma'] = last['id']
                        self.bot.savePending = True
                        title = last['title_en']
                        if title == "": title = self.translate(last['title'])
                        await self.bot.sendMulti(['debug', 'public_update', 'gbfg_update'], embed=self.bot.buildEmbed(title=title, url="http://game-a1.granbluefantasy.jp/assets/img/sp/assets/comic/episode/episode_{}.jpg".format(last['id']), image="http://game-a1.granbluefantasy.jp/assets/img/sp/assets/comic/thumbnail/thum_{}.png".format(last['id'].zfill(5)), color=self.color))
                else:
                    self.bot.gbfdata['4koma'] = last['id']
                    self.bot.savePending = True
            except asyncio.CancelledError:
                await self.bot.sendError('gbfwatch', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('gbfwatch C', str(e))

            try: # update check
                await asyncio.sleep(0.001)
                v = await self.bot.getGameversion()
                s = self.bot.updateGameversion(v)
                if s == 3:
                    react = await self.bot.sendMulti(['debug', 'private_update'], embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description="Game version updated to `{}` (`{}`)".format(v, self.bot.versionToDateStr(v)), color=self.color))
                    try:
                        for r in react: await self.bot.react(r, 'time')
                    except:
                        pass
                    # content check
                    msg = ""
                    gbfg_msg = ""
                    thumb = ""
                    # gacha
                    tickets = await self.updateTicket()
                    if len(tickets) > 0:
                        msg += "**Gacha update**\n{} new ticket\n\n".format(len(tickets))
                        thumb = tickets[0]
                        self.bot.gbfdata['new_ticket'] = tickets
                        self.bot.savePending = True
                    news = await self.cc()
                    try:
                        for r in react: await self.bot.unreact(r, 'time')
                    except:
                        pass
                    if len(news) > 0:
                        msg += "**Content update**\n"
                        for k in news:
                            msg += "{} {}\n".format(news[k], k)
                    if msg != "":
                        await self.bot.sendMulti(['debug', 'private_update'], embed=self.bot.buildEmbed(title="Latest Update", description=msg, thumbnail=thumb, color=self.color))
                        await self.bot.send('debug', embed=self.bot.buildEmbed(title="Reminder", description="Keep it private", color=self.color))
                elif s == 2:
                    await self.bot.send('debug', embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description="Game version set to `{}` (`{}`)".format(v, self.bot.versionToDateStr(v)) , color=self.color))
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                await self.bot.sendError('gbfwatch', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('gbfwatch D', str(e))

    async def checkNews(self):
        res = []
        async with aiohttp.ClientSession() as session:
            async with session.get("https://granbluefantasy.jp/news/index.php") as r:
                if r.status != 200:
                    raise Exception("HTTP Error 404: Not Found")
                else:
                    x = await r.text()
                    x = x.encode('utf-8').decode('utf-8','ignore')
                    soup = BeautifulSoup(x, 'html.parser')
                    at = soup.find_all("article", class_="scroll_show_box")
                    try:
                        for a in at:
                            inner = a.findChildren("div", class_="inner", recursive=False)[0]
                            section = inner.findChildren("section", class_="content", recursive=False)[0]
                            h1 = section.findChildren("h1", recursive=False)[0]
                            url = h1.findChildren("a", class_="change_news_trigger", recursive=False)[0]

                            try:
                                mb25 = section.findChildren("div", class_="mb25", recursive=False)[0]
                                href = mb25.findChildren("a", class_="change_news_trigger", recursive=False)[0]
                                img = href.findChildren("img", recursive=False)[0].attrs['src']
                                if not img.startswith('http'):
                                    if img.startswith('/'): img = 'https://granbluefantasy.jp' + img
                                    else: img = 'https://granbluefantasy.jp/' + img
                            except:
                                img = None

                            res.append([url.attrs['href'], self.translate(url.text), img])
                    except:
                        pass
        return res

    async def check4koma(self):
        data = await self.bot.sendRequest('http://game.granbluefantasy.jp/comic/list/1?_=TS1&t=TS2&uid=ID', account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True)
        return data['list'][0]

    def translate(self, text):
        try:
            split = text.replace('「', '」').replace('『', '」').replace('』', '」').replace('！', '!').split('」')
            msg = ""
            count = 0
            for t in split:
                if t != '': msg += self.translator.translate(t)
                if t is not split[-1]:
                    msg += '"'
                    count += 1
                    if (count % 2) == 0: msg += " "
            return msg
        except:
            return text

    def getCurrentGWDayID(self):
        if self.bot.gw['state'] == False: return None
        current_time = self.bot.getJST()
        if current_time < self.bot.gw['dates']["Preliminaries"]:
            return None
        elif current_time >= self.bot.gw['dates']["End"]:
            return 25
        elif current_time > self.bot.gw['dates']["Day 5"]:
            return 25
        elif current_time > self.bot.gw['dates']["Day 1"]:
            it = ['Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
            for i in range(1, len(it)): # loop to not copy paste this 5 more times
                if current_time > self.bot.gw['dates'][it[i]]:
                    d = self.bot.gw['dates'][it[i-1]] - current_time
                    if d < timedelta(seconds=18000): return 16 - i
                    else: return 6 - i
        elif current_time > self.bot.gw['dates']["Interlude"]:
            return 1
        elif current_time > self.bot.gw['dates']["Preliminaries"]:
            d = self.bot.gw['dates']['Interlude'] - current_time
            if d < timedelta(seconds=18000): return 10
            else: return 0
        else:
            return None

    def postPastebin(self, title, paste, duration = '1D'): # to send informations on a pastebin, requires dev and user keys
        try:
            url = "https://pastebin.com/api/api_post.php"
            values = {'api_option' : 'paste',
                      'api_dev_key' : self.bot.pastebin['dev_key'],
                      'api_user_key' : self.bot.pastebin['user_key'],
                      'api_paste_code' : paste,
                      'api_paste_private' : '1',
                      'api_paste_name' : title,
                      'api_paste_expire_date' : duration}
            req = request.Request(url, parse.urlencode(values).encode('utf-8'))
            with request.urlopen(req) as response:
               result = response.read()
            return result.decode('ascii')
        except Exception as e:
            return "Error: " + str(e)

    def delPastebin(self, link): # delete a pastebin
        try:
            link = link.replace('https://pastebin.com/', '')
            url = "https://pastebin.com/api/api_post.php"
            values = {'api_option' : 'delete',
                      'api_dev_key' : self.bot.pastebin['dev_key'],
                      'api_user_key' : self.bot.pastebin['user_key'],
                      'api_paste_key' : link}
            req = request.Request(url, parse.urlencode(values).encode('utf-8'))
            with request.urlopen(req) as response:
               result = response.read()
            return result.decode('ascii')
        except Exception as e:
            return "Error: " + str(e)

    @commands.command(no_pm=True, cooldown_after_parsing=True, hidden=True)
    @isOwner()
    async def getPastebinUserKey(self, ctx):
        """No description"""
        url = "https://pastebin.com/api/api_login.php"
        values = {'api_dev_key' : self.bot.pastebin['dev_key'],
                  'api_user_name' : self.bot.pastebin['user'],
                  'api_user_password' : self.bot.pastebin['pass']}

        try:
            await self.bot.react(ctx.message, '✅') # white check mark
            req = request.Request(url, parse.urlencode(values).encode('utf-8'))
            with request.urlopen(req) as response:
               the_page = response.read()
            await self.bot.send('debug', embed=self.bot.buildEmbed(title=the_page.decode('ascii'), color=self.color))
        except Exception as e:
            await self.bot.sendError('getpastebinuserkey', str(e))

    def pa(self, a, indent): # black magic
        s = ""
        if indent > 0:
            s = "|"
            for i in range(0, indent): s += "-"
            s += " "
        res = ""
        for c in a:
            if isinstance(c, list):
                res += self.pa(c, indent+1)
            else:
                res += s+c+'\n'
        if indent == 0: res += '\n'
        return res

    async def dad(self, id, silent, mode = 0): # black magic
        if id[0] == '3': type = 0
        elif id[0] == '2': type = 1
        elif id[0] == '1': type = 2
        else: return ["", {}]
        try:
            files = self.bot.gbfwatch["files"]
            flags = {}
            for t in self.bot.gbfwatch["flags"]:
                flags[t] = {}
                for k in self.bot.gbfwatch["flags"][t]:
                    flags[t][k] = False
            it = self.bot.gbfwatch["it"]
        except:
            return ["", {}]

        paste = ""
        counter = 0
        font = ImageFont.truetype("assets/font.ttf", 16)
        for f in files[type]:
            await asyncio.sleep(0.001)
            if mode == 1: ff = f[0] + id + f[1] + '_s2'
            else: ff = f[0] + id + f[1]
            uu = self.bot.gbfwatch["base"].format(ff)
            try:
                data = await self.bot.sendRequest(uu, no_base_headers=True)
                if data is None: raise Exception("404")
                data = str(data)

                paste += '# {} ############################################\n'.format(ff)

                root = []
                ref = root
                stack = []
                dupelist = []
                match = 0
                rcs = []
                imc = 1
                wd = 0
                ht = 0
                current = data.find("{", 0) + 1

                while current < len(data):
                    c = data[current]
                    if c == ff[match]:
                        match += 1
                        if match == len(ff):
                            if data[current+1] == '_':
                                x = current+2
                                while x < len(data) and (data[x] == '_' or data[x].isalnum()):
                                    x += 1
                                n = data[current+2:x]
                                if len(n) == 1:
                                    if n == "b":
                                        rcs[-1][-1] = 1
                                        if imc < 2: imc = 2
                                    elif n == "c":
                                        rcs[-1][-1] = 2
                                        if imc < 3: imc = 3
                                elif n != "" and (len(ref) == 0 or(len(ref) > 0 and ref[-1] != n)):
                                    ref.append(n)
                                    if n not in dupelist:
                                        dupelist.append(n)
                                        sub = n.split('_')
                                        for sk in sub:
                                            for fk in flags:
                                                if sk in flags[fk]:
                                                    flags[fk][sk] = True
                                current = x - 1
                            match = 0
                    else:
                        match = 0
                        if c == '{':
                            ref.append([])
                            stack.append(ref)
                            ref = ref[-1]
                        elif c == '}':
                            try:
                                ref = stack[-1]
                                if len(ref[-1]) == 0:
                                    ref.pop()
                                stack.pop()
                            except:
                                pass
                        elif len(stack) == 1:
                            sstr = data[current:]
                            if sstr.startswith("Rectangle("):
                                lp = sstr.find(")")
                                try:
                                    rc = sstr[len("Rectangle("):lp].split(',')
                                    rc = [int(ir.replace('1e3', '1000')) for ir in rc]
                                    for p in rc:
                                        if p < 0: raise Exception()
                                    if sum(rc) == 0:
                                        raise Exception()
                                    rc[2] += rc[0]
                                    rc[3] += rc[1]
                                    if rc[2] > wd: wd = rc[2]
                                    if rc[3] > ht: ht = rc[3]
                                    rc.append(stack[-1][-2])
                                    rc.append(0)
                                    rcs.append(rc)
                                except:
                                    pass
                    current += 1
                await asyncio.sleep(0.001)
                paste += self.pa(root, 0)
                i = Image.new('RGB', (wd*imc+200,ht+200), "black")
                d = ImageDraw.Draw(i)
                txcs = []
                for rc in rcs:
                    try:
                        fill = None
                        for q in it:
                            if fill is not None: break
                            for sfql in q[-1]:
                                if sfql in rc[4].lower():
                                    fill = (q[0],q[1],q[2])
                                    break
                        rc[0] += rc[5]*wd
                        rc[2] += rc[5]*wd
                        d.rectangle(rc[:4],fill=fill,outline=(140,140,140))
                        txcs.append([rc[0], rc[1], rc[4]])
                    except:
                        pass
                rcs.clear()
                txsb = []
                for txc in txcs:
                    bss = txc[:-1]
                    tss = font.getsize(txc[2])
                    bbx = [bss[0], bss[1], bss[0]+tss[0], bss[1]+tss[1]]
                    for tbx in txsb:
                        if bbx[0] < tbx[2] and tbx[0] < bbx[2] and bbx[1] < tbx[3] and tbx[1] < bbx[3]:
                            diff = tbx[3] - bbx[1]
                            bbx[1] += diff
                            bbx[3] += diff
                    txsb.append(bbx)
                    try: d.text((bbx[0], bbx[1]),txc[2],font=font,fill=(255,255,255))
                    except: pass
                txsb.clear()
                txcs.clear()
                i.save("{}.png".format(ff), "PNG")
                with open("{}.png".format(ff), 'rb') as infile:
                    await self.bot.send('debug', "{}.png".format(ff), file=discord.File(infile))
                self.bot.delFile("{}.png".format(ff))
            except:
                if counter >= 3 and len(paste) == 0: return ["", {}]
            counter+=1

        if len(paste) > 0:
            if silent:
                return ["Not posted to pastebin", flags]
            else:
                return [str(self.postPastebin(id, paste)), flags]
        else:
            return ["", {}]

    async def cc(self): # black magic
        found = {}
        silent = False

        if 'c' not in self.bot.gbfdata or 'w' not in self.bot.gbfdata:
            return found

        try:
            num = self.bot.gbfwatch['num']
            ns = self.bot.gbfwatch['ns']
            crt = self.bot.gbfwatch['crt']
            cl = self.bot.gbfwatch['cl']
            wl = self.bot.gbfwatch['wl']
            ws = self.bot.gbfwatch['ws']
            ss = self.bot.gbfwatch['ss']
            wt = self.bot.gbfwatch['wt']
            ee = self.bot.gbfwatch['ee']
            ic = self.bot.gbfwatch['ic']
        except:
            return found

        nc = await self.bot.sendRequest(self.bot.gbfwatch['num'], account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True)
        if nc is not None:
            if 'count' not in self.bot.gbfdata:
                self.bot.gbfdata['count'] = ['?', '?', '?']
                self.bot.savePending = True
            if self.bot.gbfdata['count'][0] != nc['archive']['npc_num']['max']: found[ns[0].format(self.bot.gbfdata['count'][0], nc['archive']['npc_num']['max'])] = ""
            if self.bot.gbfdata['count'][1] != nc['archive']['summon_num']['max']: found[ns[1].format(self.bot.gbfdata['count'][1], nc['archive']['summon_num']['max'])] = ""

        for i in range(0, len(self.bot.gbfdata['c'])):
            cid = crt[i][1]
            id = self.bot.gbfdata['c'][i] + 1
            errc = 0
            while errc < 4:
                data = await self.dad(str(cid + id * 1000), silent)

                if data[0] == "":
                    errc += 1
                else:
                    self.bot.gbfdata['c'][i] = id
                    self.bot.savePending = True
                    if crt[i][0] not in found:
                        found[crt[i][0]] = 1
                    else:
                        found[crt[i][0]] += 1
                    errc = 0

                    if not silent:
                        title = "{} : {}".format(crt[i][0], cid + id * 1000)

                        # processing
                        fields = []

                        for k in data[1]:
                            tmp = ""
                            for t in data[1][k]:
                                if data[1][k][t]:
                                    tmp += t + ', '
                            if len(tmp) > 0:
                                fields.append({'name':k, 'value':tmp[:-2]})

                        await self.bot.send('debug', embed=self.bot.buildEmbed(title=crt[i][0], description=data[0], fields=fields, color=self.color))
                id += 1

        if nc is not None:
            if self.bot.gbfdata['count'][2] != nc['archive']['weapon_num']['max']: found[ns[2].format(self.bot.gbfdata['count'][2], nc['archive']['weapon_num']['max'])] = ""
            self.bot.gbfdata['count'] = [nc['archive']['npc_num']['max'], nc['archive']['summon_num']['max'], nc['archive']['weapon_num']['max']]
            self.bot.savePending = True

        for k in self.bot.gbfdata['w']:
            try:
                x = int(k)
            except:
                continue
            for i in range(0, len(self.bot.gbfdata['w'][k])):
                await asyncio.sleep(0.001)
                errc = 0
                if len(self.bot.gbfdata['w'][k][i]) == 0 or self.bot.gbfdata['w'][k][i][-1] < 10:
                    stid = 0
                    max = 10
                else:
                    stid = self.bot.gbfdata['w'][k][i][-1] - 10
                    max = self.bot.gbfdata['w'][k][i][-1]
                id = (103 + x) * 10000000 + i * 100000 + stid * 100
                while errc < 4 or stid <= max:
                    if stid in self.bot.gbfdata['w'][k][i]:
                        stid += 1
                        continue
                    id = (103 + x) * 10000000 + i * 100000 + stid * 100
                    wfound = False
                    for wul in wl:
                        await asyncio.sleep(0.001)
                        data = await self.bot.sendRequest(wul.format(id), no_base_headers=True)
                        if data is not None:
                            wfound = True
                            break
                        await asyncio.sleep(0.001)
                    if not wfound:
                        errc += 1
                        stid += 1
                        continue

                    errc = 0
                    self.bot.gbfdata['w'][k][i].append(stid)

                    tt = ws[x+2].format(self.bot.getEmote(wt.get(str(i+1), "Error")))
                    if tt not in found:
                        found[tt] = 1
                    else:
                        found[tt] += 1

                    if not silent:
                        await self.bot.send('debug', embed=self.bot.buildEmbed(title=ws[x], description='{} ▫️ {}'.format(tt, id), thumbnail=wl[0].format(id), color=self.color))

                    stid += 1

                self.bot.gbfdata['w'][k][i].sort()
                if len(self.bot.gbfdata['w'][k][i]) > 11: self.bot.gbfdata['w'][k][i] = self.bot.gbfdata['w'][k][i][-11:]
                self.bot.savePending = True

        return found

    async def summontask(self): # discord summon update task
        while True:
            try:
                uptime = self.bot.uptime(False)
                if self.bot.summonlast is None: delta = None
                else: delta = self.bot.getJST() - self.bot.summonlast
                if uptime.seconds > 3600 and uptime.seconds < 30000 and (delta is None or delta.days >= 5):
                    await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="summontask()", description="auto update started", timestamp=datetime.utcnow()))
                    await self.updateSummon()
                    await self.bot.send('debug', embed=self.bot.buildEmbed(color=self.color, title="summontask()", description="auto update ended", timestamp=datetime.utcnow()))
                    await asyncio.sleep(80000)
                    return
                else:
                    await asyncio.sleep(3600)
            except asyncio.CancelledError:
                await self.bot.sendError('summontask', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('summontask', str(e))
                if str(e) == "Maintenance": await asyncio.sleep(80000)

    async def loadSumDB(self): # load the summon db file
        try:
            if self.sql['summon'][2]:
                self.sql['summon'][0] = None
            elif self.bot.drive.dlFile("summon.sql", self.bot.tokens['files']):
                self.sql['summon'][0] = sqlite3.connect("summon.sql")
                self.sql['summon'][1] = self.sql['summon'][0].cursor()
            else:
                self.sql['summon'][0] = None
        except Exception as e:
            self.sql['summon'][0] = None
            await self.bot.sendError('loadSumDB', str(e))
        return (self.sql['summon'][0] is not None)

    async def checkSumDB(self, ctx): # check if the summon db is loaded and try to if not
        if self.sql['summon'][0]:
            return True
        else:
            await self.bot.react(ctx.message, 'time')
            r = await self.loadSumDB()
            await self.bot.unreact(ctx.message, 'time')
            return r

    async def getCrewSummary(self, id):
        res = await self.bot.sendRequest("http://game.granbluefantasy.jp/guild_main/content/detail/{}?_=TS1&t=TS2&uid=ID".format(id), account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True)
        if res is None: return None
        else:
            soup = BeautifulSoup(unquote(res['data']), 'html.parser')
            try:
                summary = soup.find_all("div", class_="prt-status-summary")[0].findChildren("div", class_="prt-status-value", recursive=True)
                data = {}
                data['count'] = int(summary[0].string)
                data['average'] = int(summary[1].string)
                data['online'] = int(summary[2].string)
                return data
            except Exception as e:
                await self.bot.send('debug', str(e))
                return None

    async def getCrewData(self, ctx, target, mode=0): # retrieve a crew data (mode=0 - all, 1 - main page data only, 2 - main page and summary | add 10 to skip the cache check)
        if not await self.bot.isGameAvailable(): # check for maintenance
            return {'error':'Game is in maintenance'}
        if isinstance(target, list) or isinstance(target, tuple): id = " ".join(target)
        elif isinstance(target, int): id = str(target)
        else: id = target
        crew_id_list = {**(self.bot.granblue['gbfgcrew']), **(self.bot.granblue.get('othercrew', {}))}
        id = crew_id_list.get(id.lower(), id) # check if the id is a gbfgcrew
        # check id validityy
        try:
            id = int(id)
        except:
            if id == "": return {'error':"Please input the id or the name of the crew\nOnly some crews are registered, please input an id instead"}
            return {'error':"Invalid name `{}`\nOnly some crews are registered, please input an id instead".format(id)}
        if id < 0 or id >= 10000000:
            return {'error':'Out of range ID'}
        if id in self.badcrewcache: # if already searched (to limit bad requests)
            return {'error':'Crew not found'}

        if mode >= 10:
            skipcache = True
            mode -= 10
        else: skipcache = False

        crew = {'scores':[], 'id':id}
        if not skipcache and id in self.crewcache: # public crews are stored until next reboot (to limit the request amount)
            crew = self.crewcache[id]
            if mode > 0: return crew
        else:
            for i in range(0, 4): # for each page (page 0 being the crew page, 1 to 3 being the crew page
                if i > 0 and mode > 0: break
                get = await self.requestCrew(id, i)
                if get == "Maintenance":
                    return {'error':'Maintenance'}
                if get is None:
                    if i == 0: # if error on page 0, the crew doesn't exist
                        self.badcrewcache.append(id)
                        return {'error':'Crew not found'}
                    elif i == 1: # if error on page 1, the crew is private
                        crew['private'] = True
                    break
                else:
                    # store the data
                    if i == 0:
                        crew['timestamp'] = datetime.utcnow()
                        crew['footer'] = ""
                        crew['private'] = False # in preparation
                        crew['name'] = su.unescape(get['guild_name'])
                        crew['rank'] = get['guild_rank']
                        crew['ship'] = "http://game-a.granbluefantasy.jp/assets_en/img/sp/guild/thumb/top/{}.png".format(get['ship_img'])
                        crew['ship_element'] = {"10001":"wind", "20001":"fire", "30001":"water", "40001":"earth"}.get(get['ship_img'].split('_')[0], 'gw')
                        crew['leader'] = su.unescape(get['leader_name'])
                        crew['leader_id'] = get['leader_user_id']
                        crew['donator'] = su.unescape(get['most_donated_name'])
                        crew['donator_id'] = get['most_donated_id']
                        crew['donator_amount'] = get['most_donated_lupi']
                        crew['message'] = su.unescape(get['introduction'])
                    else:
                        if 'player' not in crew: crew['player'] = []
                        for p in get['list']:
                            crew['player'].append({'id':p['id'], 'name':su.unescape(p['name']), 'level':p['level'], 'is_leader':p['is_leader'], 'member_position':p['member_position'], 'honor':None}) # honor is a placeholder
            
            if mode == 1: return crew
            
            data = await self.getCrewSummary(id)
            if data is not None:
                crew = {**crew, **data}

            if mode > 0: return crew

            # prepare the member list
            fields = []
            if not crew['private']: self.crewcache[id] = crew # only cache public crews


        # get the last gw score
        crew['scores'] = []
        data = await self.searchGWDBCrew(ctx, id, 2)
        if data is not None:
            for n in range(0, 2):
                if data[n] is not None and 'result' in data[n] and len(data[n]['result']) == 1:
                    if data[n].get('ver', 0) == 2:
                        possible = {7:"Total Day 4", 6:"Total Day 3", 5:"Total Day 2", 4:"Total Day 1", 3:"Total Prelim."}
                        last_id = 7
                    else:
                        possible = {11:"Total Day 4", 9:"Total Day 3", 7:"Total Day 2", 5:"Total Day 1", 3:"Total Prelim."}
                        last_id = 11
                    for ps in possible:
                        if data[n]['result'][0][ps] is not None:
                            if ps == last_id and data[n]['result'][0][0] is not None:
                                crew['scores'].append("{} GW**{}** ▫️ #**{}** ▫️ **{:,}** honors ".format(self.bot.getEmote('gw'), data[n].get('gw', ''), data[n]['result'][0][0], data[n]['result'][0][ps]))
                                break
                            else:
                                crew['scores'].append("{} GW**{}** ▫️ {} ▫️ **{:,}** honors ".format(self.bot.getEmote('gw'), data[n].get('gw', ''), possible[ps], data[n]['result'][0][ps]))
                                break

        return crew

    async def postCrewData(self, ctx, id, mode = 0): # mode 0 = auto, 1 = gw mode disabled, 2 = gw mode enabled
        try:
            # retrieve formatted crew data
            crew = await self.getCrewData(ctx, id)

            if 'error' in crew: # print the error if any
                if len(crew['error']) > 0:
                    await ctx.send(embed=self.bot.buildEmbed(title="Crew Error", description=crew['error'], color=self.color))
                return

            # embed initialization
            title = "\u202d{} **{}**".format(self.bot.getEmote(crew['ship_element']), crew['name'])
            if 'count' in crew: title += "▫️{}/30".format(crew['count'])
            if 'average' in crew: title += "▫️Rank {}".format(crew['average'])
            if 'online' in crew: title += "▫️{} online".format(crew['online'])
            description = "💬 ``{}``".format(self.escape(crew['message']))
            footer = ""
            fields = []

            # append GW scores if any
            for s in crew['scores']:
                description += "\n{}".format(s)

            if crew['private']:
                description += '\n{} [{}](http://game.granbluefantasy.jp/#profile/{}) ▫️ *Crew is private*'.format(self.bot.getEmote('captain'), crew['leader'], crew['leader_id'])
            else:
                footer = "Public crews are updated once per day"
                # get GW data
                if mode == 2: gwstate = True
                elif mode == 1: gwstate = False
                else: gwstate = self.isGWRunning()
                players = crew['player'].copy()
                gwid = None
                if gwstate:
                    total = 0
                    unranked = 0
                    for i in range(0, len(players)):
                        # retrieve player honors
                        honor = await self.searchGWDBPlayer(ctx, players[i]['id'], 2)
                        if honor[1] is None or len(honor[1]) == 0 or len(honor[1]['result']) == 0:
                            players[i]['honor'] = None
                            unranked += 1
                        else:
                            res = honor[1].get('result', [None, None, None, None])
                            if gwid is None: gwid = honor[1].get('gw', None)
                            if res is not None and len(res[0]) != 0 and res[0][3] is not None:
                                players[i]['honor'] = res[0][3]
                                total += res[0][3]
                            else:
                                players[i]['honor'] = None
                                unranked += 1
                        if i > 0 and players[i]['honor'] is not None:
                            # sorting
                            for j in range(0, i):
                                if players[j]['honor'] is None or players[i]['honor'] > players[j]['honor']:
                                    tmp = players[j]
                                    players[j] = players[i]
                                    players[i] = tmp
                    if gwid and len(players) - unranked > 0:
                        description += "\n{} GW**{}** ▫️ Player Total **{}** ▫️ Average **{}**".format(self.bot.getEmote('question'), gwid, self.honorFormat(total), self.honorFormat(total // (len(players) - unranked)))
                        if unranked > 0:
                            description += " ▫️ {} Unranked".format(unranked)
                            if unranked > 1: description += "s"
                # create the fields
                i = 0
                for p in players:
                    if i % 10 == 0: fields.append({'name':'Page {}'.format(self.bot.getEmote('{}'.format(len(fields)+1))), 'value':''})
                    i += 1
                    if p['member_position'] == "1": r = "captain"
                    elif p['member_position'] == "2": r = "foace"
                    elif p['member_position'] == "3": r = "atkace"
                    elif p['member_position'] == "4": r = "deface"
                    else: r = "ensign"
                    entry = '{} [{}](http://game.granbluefantasy.jp/#profile/{})'.format(self.bot.getEmote(r), self.escape(p['name']), p['id'])
                    if gwstate:  entry += " \▫️ {}".format(self.honorFormat(p['honor']))
                    else: entry += " \▫️ r**{}**".format(p['level'])
                    entry += "\n"
                    fields[-1]['value'] += entry

            final_msg = await ctx.send(embed=self.bot.buildEmbed(title=title, description=description, fields=fields, inline=True, url="http://game.granbluefantasy.jp/#guild/detail/{}".format(crew['id']), footer=footer, timestamp=crew['timestamp'], color=self.color))
            await self.bot.cleanMessage(ctx, final_msg, 60)

        except Exception as e:
            await self.bot.sendError("postCrewData", str(e))

    async def updateSummon(self): # update summon.sql
        self.bot.drive.delFiles(["summon.sql"], self.bot.tokens['files'])
        self.sql['summon'] = [None, None, True]
        self.bot.delFile('summon.sql')
        conn = sqlite3.connect('summon.sql')
        c = conn.cursor()
        c.execute('CREATE TABLE players (id int, name text)')
        summonnames = []
        for sid in list(self.bot.gbfids.keys()):
            id = self.bot.gbfids[sid]
            data = await self.getProfileData(id)
            if data == "Maintenance":
                raise Exception("Maintenance")
            if data is None:
                continue
            soup = BeautifulSoup(data, 'html.parser')
            try: name = soup.find_all("span", class_="txt-other-name")[0].string
            except: name = None
            if name is not None: # private
                try:
                    c.execute("INSERT INTO players VALUES ({},'{}')".format(id, name.replace("'", "''").replace("%", "\%")))
                    summons_res = self.sumre.findall(data)
                    for s in summons_res:
                        sp = s[1].lower().split() # Lvl 000 Name1 Name2 ... NameN
                        sn = " ".join(sp[2:])
                        if sn not in summonnames:
                            summonnames.append(sn)
                            c.execute('CREATE TABLE `{}` (id int, level int)'.format(sn))
                        c.execute("INSERT INTO `{}` VALUES ({},{})".format(sn, id, sp[1]))
                except:
                    pass
            await asyncio.sleep(0.1)
        conn.commit()
        conn.close()
        self.sql['summon'][2] = False
        if self.bot.drive.saveDiskFile("summon.sql", "application/sql", "summon.sql", self.bot.tokens['files']):
            self.bot.summonlast = self.bot.getJST()
            self.bot.savePending = True
        self.sql['summon'][0] = sqlite3.connect("summon.sql")
        self.sql['summon'][1] = self.sql['summon'][0].cursor()

    def honorFormat(self, h): # convert honor number to a shorter string version
        if h is None: return "n/a"
        elif isinstance(h, str): h = int(h)
        elif h >= 1000000000: return "{:.1f}B".format(h/1000000000)
        elif h >= 1000000: return "{:.1f}M".format(h/1000000)
        elif h >= 1000: return "{:.1f}K".format(h/1000)
        return h

    def escape(self, s): # escape markdown string
        # add the RLO character before
        return '\u202d' + s.replace('\\', '\\\\').replace('`', '\\`').replace('*', '\\*').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('[', '').replace(']', '').replace('(', '\\(').replace(')', '\\)').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('|', '\\|')

    async def requestCrew(self, id : int, page : int): # get crew data
        if page == 0: return await self.bot.sendRequest("http://game.granbluefantasy.jp/guild_other/guild_info/{}?_=TS1&t=TS2&uid=ID".format(id), account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True)
        else: return await self.bot.sendRequest("http://game.granbluefantasy.jp/guild_other/member_list/{}/{}?_=TS1&t=TS2&uid=ID".format(page, id), account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True)

    async def getProfileData(self, id : int): # get player data
        if not await self.bot.isGameAvailable():
            return "Maintenance"
        res = await self.bot.sendRequest("http://game.granbluefantasy.jp/profile/content/index/{}?_=TS1&t=TS2&uid=ID".format(id), account=self.bot.gbfcurrent, decompress=True, load_json=True)
        if res is not None: return unquote(res['data'])
        else: return res

    async def getScoutData(self, id : int): # get player scout data
        return await self.bot.sendRequest("http://game.granbluefantasy.jp/forum/search_users_id?_=TS1&t=TS2&uid=ID", account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True, payload={"special_token":None,"user_id":id})

    async def requestRanking(self, page, crew = True): # get gw ranking data
        if not await self.bot.isGameAvailable():
            return None
        if self.bot.gw['state'] == False or self.bot.getJST() <= self.bot.gw['dates']["Preliminaries"]:
            return None

        if crew:
            res = await self.bot.sendRequest("http://game.granbluefantasy.jp/teamraid{}/rest/ranking/totalguild/detail/{}/0?=TS1&t=TS2&uid=ID".format(str(self.bot.gw['id']).zfill(3), page), account=self.bot.gbfcurrent, decompress=True, load_json=True)
        else:
            res = await self.bot.sendRequest("http://game.granbluefantasy.jp/teamraid{}/rest_ranking_user/detail/{}/0?=TS1&t=TS2&uid=ID".format(str(self.bot.gw['id']).zfill(3), page), account=self.bot.gbfcurrent, decompress=True, load_json=True)
        return res

    async def getGacha(self): # get current gacha
        if not await self.bot.isGameAvailable():
            return False
        if self.loadinggacha:
            return False
        self.loadinggacha = True
        self.bot.gbfdata['rateup'] = None
        self.bot.gbfdata['gachatime'] = None
        self.bot.gbfdata['gachatimesub'] = None
        self.bot.gbfdata['gachabanner'] = None
        self.bot.gbfdata['gachacontent'] = None
        c = self.bot.getJST()
        try:
            #gacha page
            data = await self.bot.sendRequest("http://game.granbluefantasy.jp/gacha/list?_=TS1&t=TS2&uid=ID", account=self.bot.gbfcurrent, decompress=True, load_json=True, check_update=True)
            self.bot.gbfdata['gachatime'] = datetime.strptime(data['legend']['lineup'][-1]['end'], '%m/%d %H:%M').replace(year=c.year, microsecond=0)
            NY = False
            if c > self.bot.gbfdata['gachatime']:
                self.bot.gbfdata['gachatime'].replace(year=self.bot.gbfdata['gachatime'].year+1) # new year fix
                NY = True
            self.bot.gbfdata['gachatimesub'] = datetime.strptime(data['ceiling']['end'], '%Y/%m/%d %H:%M').replace(microsecond=0)
            if (NY == False and self.bot.gbfdata['gachatimesub'] < self.bot.gbfdata['gachatime']) or (NY == True and self.bot.gbfdata['gachatimesub'] > self.bot.gbfdata['gachatime']): self.bot.gbfdata['gachatime'] = self.bot.gbfdata['gachatimesub'] # switched the sign
            random_key = data['legend']['random_key']
            header_images = data['header_images']
            logo_id = {'logo_fire':1, 'logo_water':2, 'logo_earth':3, 'logo_wind':4, 'logo_dark':5, 'logo_light':6}.get(data.get('logo_image', ''), data.get('logo_image', '').replace('logo_', ''))
            self.bot.gbfdata['gachabanner'] = None
            gachaid = data['legend']['lineup'][-1]['id']

            await asyncio.sleep(0.001) # sleep to take a break

            # draw rate
            data = await self.bot.sendRequest("http://game.granbluefantasy.jp/gacha/provision_ratio/{}/1?_=TS1&t=TS2&uid=ID".format(gachaid), account=self.bot.gbfcurrent, decompress=True, load_json=True, check_update=True)
            # build list
            banner_msg = "{} **{}** Rate".format(self.bot.getEmote('SSR'), data['ratio'][0]['ratio'])
            if not data['ratio'][0]['ratio'].startswith('3'):
                banner_msg += " ▫️ **Premium Gala**"
            banner_msg += "\n"
            possible_zodiac_wpn = ['Ramulus', 'Dormius', 'Gallinarius', 'Canisius', 'Porculius', 'Rodentius']
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
            self.bot.gbfdata['rateup'] = rateup

            # build message
            for k in rateuplist:
                if k == 'zodiac':
                    if len(rateuplist['zodiac']) > 0:
                        banner_msg += "{} **Zodiac** ▫️ ".format(self.bot.getEmote('loot'))
                        comma = False
                        for i in rateuplist[k]:
                            if comma: banner_msg += ", "
                            else: comma = True
                            banner_msg += i
                        banner_msg += "\n"
                else:
                    if len(rateuplist[k]) > 0:
                        for r in rateuplist[k]:
                            if k.lower().find("weapon") != -1: banner_msg += "{}**{}%** ▫️ ".format(self.bot.getEmote('sword'), r)
                            elif k.lower().find("summon") != -1: banner_msg += "{}**{}%** ▫️ ".format(self.bot.getEmote('summon'), r)
                            count = 0
                            for i in rateuplist[k][r]:
                                if count >= 8 and len(rateuplist[k][r]) - count > 1:
                                    banner_msg += " and {} more!".format(len(rateuplist[k][r]) - count - 1)
                                    break
                                elif count > 0: banner_msg += ", "
                                count += 1
                                banner_msg += i
                        banner_msg += "\n"
            self.bot.gbfdata['gachacontent'] = banner_msg
            # add image
            gachas = ['{}/tips/description_gacha.jpg'.format(random_key), '{}/tips/description_gacha_{}.jpg'.format(random_key, logo_id), '{}/tips/description_{}.jpg'.format(random_key, header_images[0]), 'header/{}.png'.format(header_images[0])]
            for g in gachas:
                data = await self.bot.sendRequest("http://game-a.granbluefantasy.jp/assets_en/img/sp/gacha/{}".format(g), no_base_headers=True)
                if data is not None:
                    self.bot.gbfdata['gachabanner'] = "http://game-a.granbluefantasy.jp/assets_en/img/sp/gacha/{}".format(g)
                    break

            # save
            self.bot.savePending = True
            self.loadinggacha = False
            return True
        except Exception as e:
            await self.bot.sendError('updategacha', str(e))
            self.bot.gbfdata['gachatime'] = None
            self.bot.gbfdata['gachatimesub'] = None
            self.bot.gbfdata['gachabanner'] = None
            self.bot.gbfdata['gachacontent'] = None
            self.bot.savePending = True # save anyway
            self.loadinggacha = False
            return False

    async def getCurrentGacha(self):
        c = self.bot.getJST().replace(microsecond=0) - timedelta(seconds=80)
        if ('gachatime' not in self.bot.gbfdata or self.bot.gbfdata['gachatime'] is None or c >= self.bot.gbfdata['gachatime']) and not await self.getGacha():
            return []
        if self.bot.gbfdata['gachatime'] is None:
            return []
        return [self.bot.gbfdata['gachatime'] - c, self.bot.gbfdata['gachatimesub'] - c, self.bot.gbfdata['gachacontent'], self.bot.gbfdata['gachabanner']]

    async def updateTicket(self, ctx = None): # check for new tickets
        if 'ticket_id' not in self.bot.gbfdata:
            self.bot.gbfdata['ticket_id'] = 0
            self.bot.savePending = True
            silent = True
            id = 0
        else:
            silent = False
            id = self.bot.gbfdata['ticket_id']
        news = []
        errc = 0
        async with aiohttp.ClientSession() as session:
            while errc < 8:
                id += 1
                url = "http://game-a.granbluefantasy.jp/assets_en/img_low/sp/assets/item/ticket/1{}1.jpg".format(str(id).zfill(4))
                async with session.get(url) as r:
                    if r.status < 400 and r.status >= 200:
                        try:
                            await ctx.send(url)
                        except:
                            pass
                        self.bot.gbfdata['ticket_id'] = id
                        self.bot.savePending = True
                        if not silent: news.append(url)
                        errc = 0
                    else:
                        errc += 1
        return news

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def accounts(self, ctx):
        """List GBF accounts used by the bot (Owner only)"""
        if len(self.bot.gbfaccounts) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="GBF Account status", description="No accounts set", color=self.color))
            return true

        msg = ""
        for i in range(0, len(self.bot.gbfaccounts)):
            acc = self.bot.gbfaccounts[i]
            if i == self.bot.gbfcurrent: msg += "👉 "
            else: msg += "{} ".format(i)
            msg += "**{}** ".format(acc[0])
            if acc[3] == 0: msg += "❔"
            elif acc[3] == 1: msg += "✅"
            elif acc[3] == 2: msg += "❎"
            msg += "\n"
        await self.bot.send('debug', embed=self.bot.buildEmbed(title="GBF Account status", description=msg, color=self.color))
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def account(self, ctx, id : int = -1):
        """Test a GBF account validity (Owner only)"""
        if id == -1: id = self.bot.gbfcurrent
        acc = self.bot.getGBFAccount(id)
        if acc is None:
            await ctx.send(embed=self.bot.buildEmbed(title="GBF Account status", description="No accounts set in slot {}".format(id), color=self.color))
            return
        r = await self.bot.sendRequest(self.bot.gbfwatch['test'], account=id, decompress=True, load_json=True, check=True)
        if r is None or r.get('user_id', None) != acc[0]:
            await self.bot.send('debug', embed=self.bot.buildEmbed(title="GBF Account status", description="Account #{} is down\nck: `{}`\nuid: `{}`\nua: `{}`\n".format(id, acc[0], acc[1], acc[2]) , color=self.color))
            self.bot.gbfaccounts[id][3] = 2
            self.bot.savePending = True
        elif r == "Maintenance":
            await self.bot.send('debug', embed=self.bot.buildEmbed(title="GBF Account status", description="Game is in maintenance", color=self.color))
        else:
            await self.bot.send('debug', embed=self.bot.buildEmbed(title="GBF Account status", description="Account #{} is up\nck: `{}`\nuid: `{}`\nua: `{}`\n".format(id, acc[0], acc[1], acc[2]), color=self.color))
            self.bot.gbfaccounts[id][3] = 1
            self.bot.gbfaccounts[id][5] = self.bot.getJST()
            self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def switch(self, ctx, id : int):
        """Select the current GBF account to use (Owner only)"""
        if self.bot.getGBFAccount(id) is not None:
            self.bot.gbfcurrent = id
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        else:
            await self.bot.react(ctx.message, '❌')

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def addAccount(self, ctx, uid : int, ck : str, ua : str):
        """Add a GBF account to the bot (Owner only)"""
        if uid < 1:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid parameter {}".format(uid), color=self.color))
            return
        if ck == "":
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid parameter {}".format(ck), color=self.color))
            return
        if ua == "":
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid parameter {}".format(ua), color=self.color))
            return
        self.bot.addGBFAccount(uid, ck, str)
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def delAccount(self, ctx, num : int):
        """Add a GBF account to the bot (Owner only)"""
        if self.bot.delGBFAccount(num):
            await self.bot.react(ctx.message, '✅') # white check mark
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="No account in slot {}".format(num), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def setAccountUID(self, ctx, num : int, uid : int = -1):
        """Modify a GBF account (Owner only)"""
        if uid < 0:
            acc = self.bot.getGBFAccount(num)
            if acc is None:
                await ctx.send(embed=self.bot.buildEmbed(title="Error", description="No account in slot {}".format(num), color=self.color))
            else:
                await self.bot.send('debug', embed=self.bot.buildEmbed(title="Account #{} current UID".format(num), description="`{}`".format(acc[0]), color=self.color))
        elif not self.bot.updateGBFAccount(num, uid=uid):
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid parameter {}".format(uid), color=self.color))
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def setAccountCK(self, ctx, num : int, *, ck : str = ""):
        """Modify a GBF account (Owner only)"""
        if ck == "":
            acc = self.bot.getGBFAccount(num)
            if acc is None:
                await ctx.send(embed=self.bot.buildEmbed(title="Error", description="No account in slot {}".format(num), color=self.color))
            else:
                await self.bot.send('debug', embed=self.bot.buildEmbed(title="Account #{} current CK".format(num), description="`{}`".format(acc[1]), color=self.color))
        elif not self.bot.updateGBFAccount(num, ck=ck):
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid parameter {}".format(ck), color=self.color))
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def setAccountUA(self, ctx, num : int, *, ua : str = ""):
        """Modify a GBF account (Owner only)"""
        if ua == "":
            acc = self.bot.getGBFAccount(num)
            if acc is None:
                await ctx.send(embed=self.bot.buildEmbed(title="Error", description="No account in slot {}".format(num), color=self.color))
            else:
                await self.bot.send('debug', embed=self.bot.buildEmbed(title="Account #{} current UA".format(num), description="`{}`".format(acc[2]), color=self.color))
        elif not self.bot.updateGBFAccount(num, ua=ua):
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Invalid parameter {}".format(ua), color=self.color))
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def item(self, ctx, id : int):
        """Retrieve an item description"""
        try:
            data = await self.bot.sendRequest('http://game.granbluefantasy.jp/rest/quest/droplist/drop_item_detail?_=TS1&t=TS2&uid=ID', account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True, payload={"special_token":None,"item_id":id,"item_kind":10})
            await ctx.send(embed=self.bot.buildEmbed(title=data['name'], description=data['comment'].replace('<br>', ' '), thumbnail="http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/item/article/s/{}.jpg".format(id), footer=data['id'], color=self.color))
        except:
            await self.bot.react(ctx.message, '❎') # white negative mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def loot(self, ctx, id : str):
        """Retrieve a weapon or summon description"""
        try:
            type = int(id[0])
            id = int(id)
            if type not in [1, 2]: raise Exception()
            data = await self.bot.sendRequest('http://game.granbluefantasy.jp/result/detail?_=TS1&t=TS2&uid=ID', account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True, payload={"special_token":None,"item_id":id,"item_kind":type})
            data = data['data']

            rarity = "{}".format(self.bot.getEmote({"2":"R", "3":"SR", "4":"SSR"}.get(data['rarity'], '')))
            msg = '{} {} {} {}\n'.format(self.bot.getEmote('hp'), data['max_hp'], self.bot.getEmote('atk'), data['max_attack'])
            if type == 1:
                kind = "{}".format(self.bot.getEmote({'1': 'sword','2': 'dagger','3': 'spear','4': 'axe','5': 'staff','6': 'gun','7': 'melee','8': 'bow','9': 'harp','10': 'katana'}.get(data.get('kind', ''), '')))
                if 'special_skill' in data:
                    msg += "{} **{}**\n".format(self.bot.getEmote('skill1'), data['special_skill']['name'])
                    msg += "{}\n".format(data['special_skill']['comment'].replace('<span class=text-blue>', '').replace('</span>', ''))
                for i in range(1, 4):
                    key = 'skill{}'.format(i)
                    if len(data.get(key, [])) > 0:
                        msg += "{} **{}**".format(self.bot.getEmote('skill2'), data[key]['name'])
                        if 'masterable_level' in data[key] and data[key]['masterable_level'] != '1':
                            msg += " (at lvl {})".format(data[key]['masterable_level'])
                        msg += "\n{}\n".format(data[key]['comment'].replace('<span class=text-blue>', '').replace('</span>', ''))
                url = 'http://game-a.granbluefantasy.jp/assets_en/img_low/sp/assets/weapon/m/{}.jpg'.format(data['id'])
            elif type == 2:
                kind = '{}'.format(self.bot.getEmote('summon'))
                msg += "{} **{}**\n".format(self.bot.getEmote('skill1'), data['special_skill']['name'])
                msg += "{}\n".format(data['special_skill']['comment'])
                if 'recast_comment' in data['special_skill']:
                    msg += "{}\n".format(data['special_skill']['recast_comment'])
                msg += "{} **{}**\n".format(self.bot.getEmote('skill2'), data['skill1']['name'])
                msg += "{}\n".format(data['skill1']['comment'])
                if 'sub_skill' in data:
                    msg += "{} **Sub Aura**\n".format(self.bot.getEmote('skill2'))
                    msg += "{}\n".format(data['sub_skill']['comment'])
                url = 'http://game-a.granbluefantasy.jp/assets_en/img_low/sp/assets/summon/m/{}.jpg'.format(data['id'])

            await ctx.send(embed=self.bot.buildEmbed(title="{}{}{}".format(rarity, kind, data['name']), description=msg, thumbnail=url, footer=data['id'], color=self.color))
        except:
            await self.bot.react(ctx.message, '❎') # white negative mark
            
    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def coop(self, ctx):
        """Retrieve the current coop daily missions"""
        try:
            data = (await self.bot.sendRequest('http://game.granbluefantasy.jp/coopraid/daily_mission?_=TS1&t=TS2&uid=ID', account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True))['daily_mission']
            msg = ""
            for i in range(len(data)):
                if data[i]['category'] == '2':
                    items = {20011:'fire', 20012:'fire', 20111:'fire', 20021:'water', 20022:'water', 20121:'water', 20031:'earth', 20032:'earth', 20131:'earth', 20041:'wind', 20042:'wind', 20141:'wind'}
                    id = int(data[i]['image'].split('/')[-1])
                    msg += '{} {}\n'.format(self.bot.getEmote(items.get(id, 'misc')), data[i]['description'])
                elif data[i]['category'] == '1':
                    quests = {'s00101':'wind', 's00104':'wind', 's00204':'wind', 's00206':'wind', 's00301':'fire', 's00303':'fire', 's00405':'fire', 's00406':'fire', 's00601':'water', 's00602':'water', 's00604':'water', 's00606':'water', 's00802':'earth', 's00704':'earth', 's00705':'earth', 's00806':'earth', 's01005':'wind', 's00905':'wind', 's00906':'wind', 's01006':'wind', 's01105':'fire', 's01403':'fire', 's01106':'fire', 's01206':'fire', 's01001':'water', 's01502':'water', 's01306':'water', 's01406':'water', 's01601':'earth', 's01405':'earth', 's01506':'earth', 's01606':'earth'}
                    id = data[i]['image'].split('/')[-1]
                    msg += '{} {}\n'.format(self.bot.getEmote(quests.get(id, 'misc')), data[i]['description'])
                else:
                    msg += '{} {}\n'.format(self.bot.getEmote(str(i+1)), data[i]['description'])
            await ctx.send(embed=self.bot.buildEmbed(author={'name':"Daily Coop Missions", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=msg, color=self.color))
        except:
            await self.bot.react(ctx.message, '❎') # white negative mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['rateup', 'banner'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gacha(self, ctx):
        """Post the current gacha informations"""
        try:
            content = await self.getCurrentGacha()
            if len(content) > 0:
                description = "{} Current gacha ends in **{}**".format(self.bot.getEmote('clock'), self.bot.getTimedeltaStr(content[0], True))
                if content[0] != content[1]:
                    description += "\n{} Spark period ends in **{}**".format(self.bot.getEmote('mark'), self.bot.getTimedeltaStr(content[1], True))
                description += "\n" + content[2]
                await ctx.send(embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=description, thumbnail=content[3], color=self.color))
        except Exception as e:
            await self.bot.sendError("getcurrentgacha", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['clearid'])
    @isOwner()
    async def clearProfile(self, ctx, gbf_id : int):
        """Unlink a GBF id (Owner only)"""
        for discord_id in self.bot.gbfids:
            if self.bot.gbfids[discord_id] == gbf_id:
                del self.bot.gbfids[discord_id]
                self.bot.savePending = True
                await self.bot.send('debug', 'User `{}` has been removed'.format(discord_id))
                await self.bot.react(ctx.message, '✅') # white check mark
                return
        if str(discord_id) not in self.bot.gbfids:
            await ctx.send(embed=self.bot.buildEmbed(title="Clear Profile Error", description="ID not found", color=self.color))
            return

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def forceSummonUpdate(self, ctx):
        """Force update the summon list (Owner only)"""
        await self.bot.react(ctx.message, 'time')
        await self.updateSummon()
        await self.bot.unreact(ctx.message, 'time')
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def profileStat(self, ctx):
        """Linked GBF id statistics (Owner only)"""
        if self.sql['summon'][0] is not None: msg = "Database loaded"
        else:
            if self.sql['summon'][2]: msg = "Database is locked"
            else: msg = "Database isn't loaded"
        await ctx.send(embed=self.bot.buildEmbed(title="{} Summon statistics".format(self.bot.getEmote('summon')), description="**{}** Registered Users\n{}".format(len(self.bot.gbfids), msg), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['unsetid'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def unsetProfile(self, ctx):
        """Unlink your GBF id"""
        if str(ctx.author.id) not in self.bot.gbfids:
            await ctx.send(embed=self.bot.buildEmbed(title="Unset Profile Error", description="You didn't set your GBF profile ID", color=self.color))
            return
        del self.bot.gbfids[str(ctx.author.id)]
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['setid'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def setProfile(self, ctx, id : int):
        """Link your GBF id to your Discord ID"""
        try:
            if id < 0 or id >= 100000000:
                await ctx.send(embed=self.bot.buildEmbed(title="Set Profile Error", description="Invalid ID", color=self.color))
                return
            data = await self.getProfileData(id)
            if data == "Maintenance":
                await ctx.send(embed=self.bot.buildEmbed(title="Set Profile Error", description="Game is in maintenance, try again later.", color=self.color))
                return
            if data is None:
                await ctx.send(embed=self.bot.buildEmbed(title="Set Profile Error", description="Profile not found", color=self.color))
                return
            for u in self.bot.gbfids:
                if self.bot.gbfids[u] == id:
                    await ctx.send(embed=self.bot.buildEmbed(title="Set Profile Error", description="This id is already in use", footer="use the bug_report command if it's a case of griefing", color=self.color))
                    return
            # register
            self.bot.gbfids[str(ctx.author.id)] = id
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        except Exception as e:
            await self.bot.sendError("setprofile", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['friend'])
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def summon(self, ctx, *search : str):
        """Search a summon
        <summon name> or <level min> <summon name>
         or <summon name> <level min>"""
        if not await self.checkSumDB(ctx):
            await ctx.send(embed=self.bot.buildEmbed(title="Summon Error", description="Currently unavailable".format(name), color=self.color))
            return
        try:
            level = int(search[0])
            name = " ".join(search[1:])
        except:
            try:
                level = int(search[-1])
                name = " ".join(search[:-1])
            except:
                level = 0
                name = " ".join(search)
        name = self.subsum.get(name.lower(), name.lower())
        try:
            self.sql['summon'][1].execute("SELECT * FROM `{}` WHERE level >= {}".format(name.lower(), level))
            data = self.sql['summon'][1].fetchall()
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Summon Error", description="`{}` ▫️ No one has this summon".format(name), footer="Be sure to type the full name", color=self.color))
            return
        random.shuffle(data)
        msg = ""
        count = 0
        fields = []

        history = []
        for u in data:
            if u[0] not in history:
                history.append(u[0])
                self.sql['summon'][1].execute("SELECT * FROM players WHERE id == {}".format(u[0]))
                pname = self.sql['summon'][1].fetchall()
                if len(pname) == 0: continue
                if count < 3:
                    fields.append({'name':'Page {} '.format(self.bot.getEmote(str(len(fields)+1))), 'value':'', 'inline':True})
                fields[count%3]['value'] += "**{}**▫️[{}](http://game.granbluefantasy.jp/#profile/{})\n".format(u[1], self.escape(pname[0][1]), u[0])
                count += 1
                if count >= 30:
                    if level > 0: msg = "*Only {} random results shown*.".format(count)
                    else: msg = "*Only {} random results shown, specify a minimum level to affine the result*.".format(count)
                    break

        if count == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="Summon Error", description="`{}` ▫️ No one has this summon above level {}".format(name, level), footer="Be sure to type the full name", color=self.color))
        else:
            if level > 0:
                await ctx.send(embed=self.bot.buildEmbed(author={'name':"{} ▫️ Lvl {} and more".format(name.capitalize(), level)}, description=msg, fields=fields, footer="Auto updated once per week", color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(author={'name':"{}".format(name.capitalize())}, description=msg, fields=fields, footer="Auto updated once per week", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['badboi', 'branded', 'restricted'])
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def brand(self, ctx, id : int):
        """Check if a GBF profile is restricted"""
        try:
            if id < 0 or id >= 100000000:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid ID", color=self.color))
                return
            if id in self.badprofilecache:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Profile not found", color=self.color))
                return
            data = await self.getScoutData(id)
            if data == "Maintenance":
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Game is in maintenance", color=self.color))
                return
            elif len(data['user']) == 0:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="In game message:\n`{}`".format(data['no_member_msg'].replace("<br>", " ")), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
                return
            try:
                if data['user']["restriction_flag_list"]["event_point_deny_flag"]:
                    status = "Account is restricted"
                else:
                    status = "Account isn't restricted"
            except:
                status = "Account isn't restricted"
            await ctx.send(embed=self.bot.buildEmbed(title="{} {}".format(self.bot.getEmote('gw'), data['user']['nickname']), description=status, thumbnail="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/talk/{}.png".format(data['user']['image']), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))

        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Unavailable", color=self.color))
            await self.bot.sendError("brand", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['id'])
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def profile(self, ctx, *target : str):
        """Retrieve a GBF profile"""
        target = " ".join(target)
        try:
            if target == "":
                if str(ctx.author.id) not in self.bot.gbfids:
                    await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="{} didn't set its profile ID".format(ctx.author.display_name), footer="setProfile <id>", color=self.color))
                    return
                id = self.bot.gbfids[str(ctx.author.id)]
            elif target.startswith('<@') and target.endswith('>'):
                try:
                    if target[2] == "!": target = int(target[3:-1])
                    else: target = int(target[2:-1])
                    member = ctx.guild.get_member(target)
                    if str(member.id) not in self.bot.gbfids:
                        await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="{} didn't set its profile ID".format(member.display_name), footer="setProfile <id>", color=self.color))
                        return
                    id = self.bot.gbfids[str(member.id)]
                except:
                    await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid parameter {} -> {}".format(target, type(target)), color=self.color))
                    return
            else:
                try: id = int(target)
                except:
                    member = ctx.guild.get_member_named(target)
                    if member is None:
                        await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Member not found", color=self.color))
                        return
                    elif str(member.id) not in self.bot.gbfids:
                        await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="{} didn't set its profile ID".format(member.display_name), footer="setProfile <id>", color=self.color))
                        return
                    id = self.bot.gbfids[str(member.id)]
            if id < 0 or id >= 100000000:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid ID", color=self.color))
                return
            if id in self.badprofilecache:
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Profile not found", color=self.color))
                return
            data = await self.getProfileData(id)
            if data == "Maintenance":
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Game is in maintenance", color=self.color))
                return
            elif data is None:
                self.badprofilecache.append(id)
                await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Profile not found", color=self.color))
                return
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
                if header is not None: rank = "**{}**".format(self.rankre.search(str(header)).group(0))
                else:
                    await self.bot.send('debug', 'profile: debug this profile: {}'.format(id))
                    rank = ""
                trophy = soup.find_all("div", class_="prt-title-name")[0].string
                comment = su.unescape(soup.find_all("div", class_="prt-other-comment")[0].string).replace('\t', '').replace('\n', '')
                if comment == "": pass
                elif rank == "": comment = "💬 ``{}``".format(comment)
                else: comment = " ▫️ 💬 ``{}``".format(comment)
                mc_url = soup.find_all("img", class_="img-pc")[0]['src'].replace("/po/", "/talk/").replace("/img_low/", "/img/")
                stats = soup.find_all("div", class_="num")
                hp = int(stats[0].string)
                atk = int(stats[1].string)
                job = soup.find_all("div", class_="txt-other-job-info")[0].string
                job_lvl = soup.find_all("div", class_="txt-other-job-level")[0].string.replace("  ", " ")

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
                pdata = await self.searchGWDBPlayer(ctx, id, 2)
                if pdata is not None:
                    for n in range(0, 2):
                        if pdata[n] is not None and 'result' in pdata[n] and len(pdata[n]['result']) == 1:
                            try:
                                if pdata[n]['result'][0][0] is None:
                                    scores += "{} GW**{}** ▫️ **{:,}** honors\n".format(self.bot.getEmote('gw'), pdata[n].get('gw', ''), pdata[n]['result'][0][3])
                                else:
                                    scores += "{} GW**{}** ▫️ #**{}** ▫️ **{:,}** honors\n".format(self.bot.getEmote('gw'), pdata[n].get('gw', ''), pdata[n]['result'][0][0], pdata[n]['result'][0][3])
                            except:
                                pass

                fields = []

                try:
                    summons_res = self.sumre.findall(data)
                    summons = {}
                    for s in summons_res:
                        summons[s[0]] = s[1]
                    count = 0
                    half = len(summons) // 2
                    if half < 4: half = 4
                    msg = ""
                    for s in self.possiblesum:
                        if s in summons:
                            msg += "{} {}\n".format(self.bot.getEmote(self.possiblesum[s]), summons[s])
                            count += 1
                            if count == half and msg != "":
                                fields.append({'name':'{} Summons'.format(self.bot.getEmote('summon')), 'value':msg, 'inline':True})
                                msg = ""
                    if msg != "":
                        fields.append({'name':'{} Summons'.format(self.bot.getEmote('summon')), 'value':msg, 'inline':True})
                except:
                    pass

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
                    if starcom is not None and starcom[0] != "(Blank)": msg += "\n\u202d💬 ``{}``".format(su.unescape(starcom[0]))
                    fields.append({'name':'{} Star Character'.format(self.bot.getEmote('skill2')), 'value':msg})
                except:
                    pass
                if trophy == "No Trophy Displayed": title = "\u202d{} **{}**".format(self.bot.getEmote(rarity), name)
                else: title = "\u202d{} **{}**▫️{}".format(self.bot.getEmote(rarity), name, trophy)

                final_msg = await ctx.send(embed=self.bot.buildEmbed(title=title, description="{}{}\n{} Crew ▫️ {}\n{}".format(rank, comment, self.bot.getEmote('gw'), crew, scores), fields=fields, thumbnail=mc_url, url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
            else:
                final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Profile Error", description="Profile is private", url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
            await self.bot.cleanMessage(ctx, final_msg, 45)
        except Exception as e:
            await self.bot.sendError("profile", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def crew(self, ctx, *id : str):
        """Get a crew profile"""
        await self.postCrewData(ctx, id)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['contrib', 'contri', 'leeches', 'contribs', 'contris', 'contributions'])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def contribution(self, ctx, *id : str):
        """Get a crew profile (GW scores are force-enabled)"""
        await self.postCrewData(ctx, id, 2)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['supercrew', 'poaching'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gwranking(self, ctx):
        """Sort and post the top 30 server membes per contribution"""
        members = []
        gwid = None
        for sid in self.bot.gbfids:
            m = ctx.guild.get_member(int(sid))
            if m is not None:
                pdata = await self.searchGWDBPlayer(ctx, self.bot.gbfids[sid], 2)
                if pdata is not None and pdata[1] is not None and 'result' in pdata[1] and len(pdata[1]['result']) == 1:
                    if gwid is None: gwid = pdata[1].get('gw', None)
                    members.append([pdata[1]['result'][0][1], pdata[1]['result'][0][2], pdata[1]['result'][0][3]]) # id, name, honor
        if len(members) < 1:
            await ctx.send(embed=self.bot.buildEmbed(title="{} Top 30 of {}".format(self.bot.getEmote('gw'), ctx.guild.name), description="Unavailable", inline=True, thumbnail=ctx.guild.icon_url, color=self.color))
            return
        for i in range(0, len(members)-1):
            for j in range(i, len(members)):
                if int(members[i][2]) < int(members[j][2]):
                    tmp = members[i]
                    members[i] = members[j]
                    members[j] = tmp
        fields = []
        total = 0
        for i in range(0, min(30, len(members))):
            if i % 10 == 0:
                fields.append({'name':'{}'.format(self.bot.getEmote(str(len(fields)+1))), 'value':''})
            fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{}) \▫️ **{}**\n".format(members[i][1], members[i][0], self.honorFormat(members[i][2]))
            total += members[i][2]
        if gwid is None: gwid = ""
        final_msg = await ctx.send(embed=self.bot.buildEmbed(author={'name':"Top 30 of {}".format(ctx.guild.name), 'icon_url':ctx.guild.icon_url}, description="{} GW**{}** ▫️ Player Total **{}** ▫️ Average **{}**".format(self.bot.getEmote('question'), gwid, self.honorFormat(total), self.honorFormat(total // min(30, len(members)))), fields=fields, inline=True, color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 60)

    async def getCrewLeaders(self, ctx, crews):
        if 'leadertime' not in self.bot.gbfdata or 'leader' not in self.bot.gbfdata or self.bot.getJST() - self.bot.gbfdata['leadertime'] > timedelta(days=6) or len(crews) != len(self.bot.gbfdata['leader']):
            await self.bot.react(ctx.message, 'time')
            leaders = {}
            for c in crews:
                if len(leaders) % 3 == 1: await asyncio.sleep(0.001) # to not overload the bot
                crew = await self.getCrewData(None, c, 1)
                if 'error' in crew:
                    continue
                leaders[str(c)] = [crew['name'], crew['leader'], crew['leader_id']]
            self.bot.gbfdata['leader'] = leaders
            self.bot.gbfdata['leadertime'] = self.bot.getJST()
            self.bot.savePending = True
            await self.bot.unreact(ctx.message, 'time')
        return self.bot.gbfdata['leader']

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["danchouranking", "danchous", "danchos", "captains", "captainranking", "capranking"])
    @commands.cooldown(1, 100, commands.BucketType.guild)
    async def danchoranking(self, ctx):
        crews = []
        for e in self.bot.granblue['gbfgcrew']:
            if self.bot.granblue['gbfgcrew'][e] in crews or self.bot.granblue['gbfgcrew'][e] in self.blacklist: continue
            crews.append(self.bot.granblue['gbfgcrew'][e])
        ranking = []
        leaders = await self.getCrewLeaders(ctx, crews)
        for cid in leaders:
            data = await self.searchGWDBPlayer(None, leaders[cid][2], 2)
            if data is None or data[1] is None:
                continue
            gwid = data[1].get('gw', None)
            if len(data[1]['result']) == 0:
                ranking.append([leaders[cid][0], leaders[cid][1], None])
            else:
                ranking.append([leaders[cid][0], leaders[cid][1], data[1]['result'][0][3]])
        if len(ranking) == 0:
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} /gbfg/ Dancho Ranking".format(self.bot.getEmote('gw')), description="Unavailable", color=self.color))
        else:
            for i in range(len(ranking)): # sorting
                for j in range(i+1, len(ranking)):
                    if ranking[j][2] is not None and (ranking[i][2] is None or ranking[i][2] < ranking[j][2]):
                        tmp = ranking[i]
                        ranking[i] = ranking[j]
                        ranking[j] = tmp
            fields = []
            if gwid is None: gwid = ""
            for i in range(0, len(ranking)):
                if i % 15 == 0: fields.append({'name':'{}'.format(self.bot.getEmote(str(len(fields)+1))), 'value':''})
                if ranking[i][2] is None:
                    fields[-1]['value'] += "{} \▫️ {} \▫️ {} \▫️ **n/a**\n".format(i+1, ranking[i][1], ranking[i][0])
                else:
                    fields[-1]['value'] += "{} \▫️ {} \▫️ {} \▫️ **{}**\n".format(i+1, ranking[i][1], ranking[i][0], self.honorFormat(ranking[i][2]))
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} /gbfg/ GW{} Dancho Ranking".format(self.bot.getEmote('gw'), gwid), fields=fields, inline=True, color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 60)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def gbfgranking(self, ctx):
        """Sort and post all /gbfg/ crew per contribution"""
        crews = []
        for e in self.bot.granblue['gbfgcrew']:
            if self.bot.granblue['gbfgcrew'][e] in crews or self.bot.granblue['gbfgcrew'][e] in self.blacklist: continue
            crews.append(self.bot.granblue['gbfgcrew'][e])
        tosort = {}
        data = await self.GWDBver(ctx)
        if data is None or data[1] is None:
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} /gbfg/ GW{} Ranking".format(self.bot.getEmote('gw'), gwid), description="Unavailable", color=self.color))
        else:
            if data[1].get('ver', 0) != 2:
                possible = {11:"Total Day 4", 9:"Total Day 3", 7:"Total Day 2", 5:"Total Day 1", 3:"Total Prelim."}
                last_id = 11
                gwid = data[1].get('gw', None)
            else:
                possible = {7:"Total Day 4", 6:"Total Day 3", 5:"Total Day 2", 4:"Total Day 1", 3:"Total Prelim."}
                last_id = 7
                gwid = data[1].get('gw', None)
            for c in crews:
                data = await self.searchGWDBCrew(ctx, int(c), 2)
                if data is None or data[1] is None or 'result' not in data[1] or len(data[1]['result']) == 0:
                    continue
                result = data[1]['result'][0]
                for ps in possible:
                    if result[ps] is not None:
                        if ps == last_id and result[0] is not None:
                            tosort[c] = [c, result[2], int(result[ps]), str(result[0])] # id, name, honor, rank
                            break
                        else:
                            tosort[c] = [c, result[2], int(result[ps]), possible[ps]] # id, name, honor, day
                            break
            sorted = []
            for c in tosort:
                inserted = False
                for i in range(0, len(sorted)):
                    if tosort[c][2] > sorted[i][2]:
                        inserted = True
                        sorted.insert(i, tosort[c])
                        break
                if not inserted: sorted.append(tosort[c])
            fields = []
            if gwid is None: gwid = ""
            for i in range(0, len(sorted)):
                if i % 15 == 0: fields.append({'name':'{}'.format(self.bot.getEmote(str(len(fields)+1))), 'value':''})
                if sorted[i][3].startswith('Total'):
                    fields[-1]['value'] += "{} \▫️ {} \▫️ **{}**\n".format(i+1, sorted[i][1], self.honorFormat(sorted[i][2]))
                else:
                    fields[-1]['value'] += "#**{}** \▫️ {} \▫️ **{}**\n".format(self.honorFormat(sorted[i][3]), sorted[i][1], self.honorFormat(sorted[i][2]))
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} /gbfg/ GW{} Ranking".format(self.bot.getEmote('gw'), gwid), fields=fields, inline=True, color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 60)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['recruiting', 'opencrew', 'opencrews'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def recruit(self, ctx):
        """Post all recruiting /gbfg/ crew"""
        if not await self.bot.isGameAvailable():
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} /gbfg/ recruiting crews".format(self.bot.getEmote('crew')), description="Unavailable", color=self.color))
        else:
            await self.bot.react(ctx.message, 'time')
            crews = []
            for e in self.bot.granblue['gbfgcrew']:
                if self.bot.granblue['gbfgcrew'][e] in crews or self.bot.granblue['gbfgcrew'][e] in self.blacklist: continue
                crews.append(self.bot.granblue['gbfgcrew'][e])

            sortedcrew = []
            for c in crews:
                data = await self.getCrewData(ctx, int(c), 2)
                await asyncio.sleep(0.001)
                if 'error' not in data and data['count'] != 30:
                    if len(sortedcrew) == 0: sortedcrew.append(data)
                    else:
                        inserted = False
                        for i in range(len(sortedcrew)):
                            if data['average'] >= sortedcrew[i]['average']:
                                sortedcrew.insert(i, data)
                                inserted = True
                                break
                        if not inserted: sortedcrew.append(data)
            await self.bot.unreact(ctx.message, 'time')
            fields = []
            if len(sortedcrew) > 20: size = 15
            elif len(sortedcrew) > 10: size = 10
            else: size = 5
            for i in range(0, len(sortedcrew)):
                if i % size == 0: fields.append({'name':'{}'.format(self.bot.getEmote(str(len(fields)+1))), 'value':''})
                fields[-1]['value'] += "Rank **{}** \▫️  **{}** \▫️ **{}** slot\n".format(sortedcrew[i]['average'], sortedcrew[i]['name'], 30-sortedcrew[i]['count'])
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} /gbfg/ recruiting crews".format(self.bot.getEmote('crew')), fields=fields, inline=True, color=self.color, timestamp=datetime.utcnow()))
        await self.bot.cleanMessage(ctx, final_msg, 90)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def news(self, ctx):
        """Post the latest new posts gacha(s)"""
        if 'news_url' not in self.bot.gbfdata:
            self.bot.gbfdata['news_url'] = []
            self.bot.savePending = True
        msg = ""
        for i in range(len(self.bot.gbfdata['news_url'])):
            msg += "{} [{}]({})\n".format(self.bot.getEmote(str(i+1)), self.bot.gbfdata['news_url'][i][1], self.bot.gbfdata['news_url'][i][0])
        try:
            thumb = self.bot.gbfdata['news_url'][0][2]
            if not thumb.startswith('http://granbluefantasy.jp') and not thumb.startswith('https://granbluefantasy.jp'):
                if thumb.startswith('/'): thumb = 'https://granbluefantasy.jp' + thumb
                else: thumb = 'https://granbluefantasy.jp/' + thumb
        except: thumb = None
        if msg == "":
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Unavailable", color=self.color))
        else:
            final_msg = await ctx.send(embed=self.bot.buildEmbed(author={'name':"Latest Granblue Fantasy News", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description=msg, image=thumb, color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 45)

    @commands.command(no_pm=True, name='4koma', cooldown_after_parsing=True, aliases=['granblues'])
    @commands.cooldown(2, 40, commands.BucketType.guild)
    async def _4koma(self, ctx, id : int = -123456789):
        """Post a Granblues Episode"""
        try:
            if id == -123456789: id = int(self.bot.gbfdata['4koma'])
            if id < 0 or id > int(self.bot.gbfdata['4koma']): raise Exception()
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="Granblue Episode {}".format(id), url="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/comic/episode/episode_{}.jpg".format(id), image="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/comic/thumbnail/thum_{}.png".format(str(id).zfill(5)), color=self.color))
            await self.bot.cleanMessage(ctx, final_msg, 45)
        except:
            await self.bot.react(ctx.message, '❎') # white negative mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def dd(self, ctx, id : str, mode : int = 0):
        """Black magic (Owner only)"""
        if not await self.bot.isGameAvailable():
            await ctx.send(embed=self.bot.buildEmbed(title="Unavailable", color=self.color))
            return
        await self.bot.react(ctx.message, 'time')
        data = await self.dad(id, False, mode)
        await self.bot.unreact(ctx.message, 'time')
        if data[0] != "":
            # processing
            fields = []

            for k in data[1]:
                tmp = ""
                for t in data[1][k]:
                    if data[1][k][t]:
                        tmp += t + ', '
                if len(tmp) > 0:
                    fields.append({'name':k, 'value':tmp[:-2]})

            await self.bot.send('debug', embed=self.bot.buildEmbed(title=id, description=data[0], fields=fields, color=self.color))
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def cn(self, ctx):
        """Black magic (Owner only)"""
        if not await self.bot.isGameAvailable():
            await ctx.send(embed=self.bot.buildEmbed(title="Unavailable", color=self.color))
            return
        await self.bot.react(ctx.message, 'time')
        news = await self.cc()
        await self.bot.unreact(ctx.message, 'time')
        msg = ""
        if len(news) > 0:
            msg += "**Content update**\n"
            for k in news:
                msg += "{} {}\n".format(news[k], k)
        if msg != "":
            await self.bot.send('debug', embed=self.bot.buildEmbed(title="Result", description=msg, color=self.color))
        await self.bot.react(ctx.message, '✅') # white check mark

    def isGWRunning(self): # return True if a guild war is on going
        if self.bot.gw['state'] == True:
            current_time = self.bot.getJST()
            if current_time < self.bot.gw['dates']["Preliminaries"]:
                return False
            elif current_time >= self.bot.gw['dates']["End"]:
                self.bot.gw['state'] = False
                self.bot.gw['dates'] = {}
                self.bot.cancelTask('gwtask')
                self.bot.savePending = True
                return False
            else:
                return True
        else:
            return False

    async def loadGWDB(self):
        self.loadinggw = True
        try:
            if self.bot.drive.dlFile("GW_old.sql", self.bot.tokens['files']):
                self.sql['old_gw'][0] = sqlite3.connect("GW_old.sql")
                self.sql['old_gw'][1] = self.sql['old_gw'][0].cursor()
                self.sql['old_gw'][2] = True
            else:
                self.sql['old_gw'][2] = False
        except Exception as e:
            self.sql['old_gw'][2] = None
            await self.bot.sendError('loadGWDB A', str(e))
        try:
            if self.bot.drive.dlFile("GW.sql", self.bot.tokens['files']):
                self.sql['gw'][0] = sqlite3.connect("GW.sql")
                self.sql['gw'][1] = self.sql['gw'][0].cursor()
                self.sql['gw'][2] = True
            else:
                self.sql['gw'][2] = False
        except Exception as e:
            self.sql['gw'][2] = None
            await self.bot.sendError('loadGWDB B', str(e))
        self.loadinggw = False
        return self.sql

    async def GWDBver(self, ctx = None):
        while self.loadinggw: await asyncio.sleep(0.001)
        if self.sql['old_gw'][2] is None or self.sql['gw'][2] is None:
            if ctx is not None: await self.bot.react(ctx.message, 'time') 
            await self.loadGWDB()
            if ctx is not None: await self.bot.unreact(ctx.message, 'time') 
        data = [None, None]
        for n in range(2):
            if n == 0: k = 'old_gw'
            else: k = 'gw'
            if self.sql[k][2] is not None and self.sql[k][2] == True:
                data[n] = {}
                try:
                    self.sql[k][1].execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'")
                    if self.sql[k][1].fetchone()[0] < 1:
                        self.sql[k][1].execute("SELECT * FROM GW")
                        for row in self.sql[k][1].fetchall():
                            data[n]['gw'] = int(row[0])
                            data[n]['ver'] = 1
                            break
                    else:
                        self.sql[k][1].execute("SELECT * FROM info")
                        for row in self.sql[k][1].fetchall():
                            data[n]['gw'] = int(row[0])
                            data[n]['ver'] = int(row[1])
                            break
                except:
                    data[n]['ver'] = 0
        return data

    async def searchGWDB(self, ctx, terms, mode):
        while self.loadinggw: await asyncio.sleep(0.001)
        if self.sql['old_gw'][2] is None or self.sql['gw'][2] is None:
            if ctx is not None: await self.bot.react(ctx.message, 'time')
            await self.loadGWDB()
            if ctx is not None: await self.bot.unreact(ctx.message, 'time')

        data = [None, None]

        for n in range(2):
            if n == 0: k = 'old_gw'
            else: k = 'gw'
            if self.sql[k][2] is not None and self.sql[k][2] == True:
                data[n] = {}
                try:
                    self.sql[k][1].execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'")
                    if self.sql[k][1].fetchone()[0] < 1:
                        self.sql[k][1].execute("SELECT * FROM GW")
                        for row in self.sql[k][1].fetchall():
                            data[n]['gw'] = int(row[0])
                            data[n]['ver'] = 1
                            break
                    else:
                        self.sql[k][1].execute("SELECT * FROM info")
                        for row in self.sql[k][1].fetchall():
                            data[n]['gw'] = int(row[0])
                            data[n]['ver'] = int(row[1])
                            break
                except:
                    data[n]['ver'] = 0

                try:
                    if mode == 10:
                        self.sql[k][1].execute("SELECT * FROM crews WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\%")))
                    elif mode == 11:
                        self.sql[k][1].execute("SELECT * FROM crews WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\%")))
                    elif mode == 12:
                        self.sql[k][1].execute("SELECT * FROM crews WHERE id = {}".format(terms))
                    elif mode == 13:
                        self.sql[k][1].execute("SELECT * FROM crews WHERE ranking = {}".format(terms))
                    elif mode == 0:
                        self.sql[k][1].execute("SELECT * FROM players WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\%")))
                    elif mode == 1:
                        self.sql[k][1].execute("SELECT * FROM players WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\%")))
                    elif mode == 2:
                        self.sql[k][1].execute("SELECT * FROM players WHERE id = {}".format(terms))
                    elif mode == 3:
                        self.sql[k][1].execute("SELECT * FROM players WHERE ranking = {}".format(terms))
                    data[n]['result'] = self.sql[k][1].fetchall()
                    random.shuffle(data[n]['result'])
                except Exception as e:
                    await self.bot.sendError('searchGWDB {} mode '.format(n, mode), str(e))
                    data[n] = None

        return data

    async def searchGWDBCrew(self, ctx, terms, mode):
        return await self.searchGWDB(ctx, terms, mode+10)

    async def searchGWDBPlayer(self, ctx, terms, mode):
        return await self.searchGWDB(ctx, terms, mode)

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def reloadDB(self, ctx):
        """Download GW.sql (Owner only)"""
        while self.loadinggw: await asyncio.sleep(0.001)
        await self.bot.react(ctx.message, 'time')
        await self.loadGWDB()
        await self.bot.unreact(ctx.message, 'time')
        if False in self.sql or None in self.sql:
            await self.bot.react(ctx.message, '❎') # white negative mark
        else:
            await self.bot.react(ctx.message, '✅') # white check mark

    async def findranking(self, ctx, type, terms): # it's a mess, I won't comment it
        if type: txt = "crew"
        else: txt = "player"
        if terms == "":
            final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="**Usage**\n`find{} [crewname]` to search a {} by name\n`find{} %eq [{}name]` or `find{} %== [{}name]` for an exact match\n`find{} %id [{}id]` for an id search\n`find{} %rank [ranking]` for a ranking search\n`find{} %all ...` to receive all the results by direct message".format(txt, txt, txt, txt, txt, txt, txt, txt, txt, txt), color=self.color))
        else:
            try:
                index = terms.find("%all ")
                if index != -1 and index + 5 < len(terms):
                    terms = terms.replace("%all ", "")
                    all = True
                else:
                    all = False

                index = terms.find("%past ")
                if index != -1 and index + 6 < len(terms):
                    terms = terms.replace("%past ", "")
                    past = True
                else:
                    past = False

                if terms.startswith("%== ") or terms.startswith("%eq "):
                    terms = terms[4:]
                    mode = 1
                elif terms.startswith("%id "):
                    try:
                        terms = int(terms[4:])
                        mode = 2
                    except:
                        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` isn't a valid syntax".format(terms), color=self.color))
                        raise Exception("Returning")
                elif terms.startswith("%rank "):
                    try:
                        terms = int(terms[6:])
                        mode = 3
                    except:
                        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` isn't a valid syntax".format(terms), color=self.color))
                        raise Exception("Returning")
                else:
                    mode = 0
                if type: data = await self.searchGWDBCrew(ctx, terms, mode)
                else: data = await self.searchGWDBPlayer(ctx, terms, mode)
                if data is None:
                    final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Database unavailable", color=self.color))
                    raise Exception("Returning")

                try:
                    if data[1] is None or past:
                        gwnum = data[0].get('gw', '')
                        ver = data[0].get('ver', '')
                        result = data[0].get('result', [])
                    else:
                        gwnum = data[1].get('gw', '')
                        ver = data[1].get('ver', '')
                        result = data[1].get('result', [])
                except:
                    final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Database unavailable", color=self.color))
                    raise Exception("Returning")

                if len(result) == 0:
                    final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` not found".format(terms), footer="help find{} for details".format(txt), color=self.color))
                    raise Exception("Returning")
                elif all:
                    if type: xl = 36
                    else: xl = 80
                    x = len(result)
                    if x > xl: x = xl
                    final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Sending your {}/{} result(s)".format(x, len(result)), footer="help find{} for details".format(txt), color=self.color))
                elif type and len(result) > 6: x = 6 # crew
                elif not type and len(result) > 15: x = 15 # player
                elif len(result) > 1: x = len(result)
                else: x = 1
                fields = []
                for i in range(0, x):
                    if type: # crew -----------------------------------------------------------------
                        fields.append({'name':"{}".format(result[i][2]), 'value':''})
                        if result[i][0] is not None: fields[-1]['value'] += "▫️**#{}**\n".format(result[i][0])
                        else: fields[-1]['value'] += "\n"
                        if result[i][3] is not None: fields[-1]['value'] += "**P.** ▫️{:,}\n".format(result[i][3])
                        if ver == 2:
                            if result[i][4] is not None and result[i][3] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('1'), result[i][4]-result[i][3])
                            if result[i][5] is not None and result[i][4] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('1'), result[i][5]-result[i][4])
                            if result[i][6] is not None and result[i][5] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('1'), result[i][6]-result[i][5])
                            if result[i][7] is not None and result[i][6] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('1'), result[i][7]-result[i][6])
                        else:
                            if result[i][4] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('1'), result[i][4])
                            if result[i][6] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('2'), result[i][6])
                            if result[i][8] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('3'), result[i][8])
                            if result[i][10] is not None: fields[-1]['value'] += "{}▫️{:,}\n".format(self.bot.getEmote('4'), result[i][10])
                        if fields[-1]['value'] == "": fields[-1]['value'] = "No data"
                        fields[-1]['value'] = "[{}](http://game.granbluefantasy.jp/#guild/detail/{}){}".format(result[i][1], result[i][1], fields[-1]['value'])
                        if all and ((i % 6) == 5 or i == x - 1):
                            try:
                                await ctx.author.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), fields=fields, inline=True, footer="help findcrew for details", color=self.color))
                            except:
                                final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="I can't send you the full list by private messages", color=self.color))
                                raise Exception("Returning")
                            fields = []
                    else: # player -----------------------------------------------------------------
                        if i % 5 == 0:
                            fields.append({'name':'Page {}'.format(self.bot.getEmote(str(((i // 5) % 3) + 1))), 'value':''})
                        if result[i][0] is None:
                            fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{})\n".format(self.escape(result[i][2]), result[i][1])
                        else:
                            fields[-1]['value'] += "[{}](http://game.granbluefantasy.jp/#profile/{}) ▫️ **#{}**\n".format(self.escape(result[i][2]), result[i][1], result[i][0])
                        if result[i][3] is not None: fields[-1]['value'] += "{:,}\n".format(result[i][3])
                        else: fields[-1]['value'] += "n/a\n"
                        if all and ((i % 15) == 14 or i == x - 1):
                            try:
                                await ctx.author.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), fields=fields, inline=True, footer="help findplayer for details", color=self.color))
                            except:
                                final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="I can't send you the full list by private messages", color=self.color))
                                raise Exception("Returning")
                            fields = []

                if all:
                    await self.bot.react(ctx.message, '✅') # white check mark
                    raise Exception("Returning")
                elif type and len(result) > 6: desc = "6/{} random result(s) shown".format(len(result)) # crew
                elif not type and len(result) > 30: desc = "30/{} random result(s) shown".format(len(result)) # player
                else: desc = ""
                final_msg = await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), description=desc, fields=fields, inline=True, footer="help find{} for details".format(txt), color=self.color))
            except:
                pass
        await self.bot.cleanMessage(ctx, final_msg, 45)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwcrew'])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def findcrew(self, ctx, *, terms : str = ""):
        """Search a crew GW score in the bot data
        add %id to search by id or %eq to get an exact match
        add %all to receive by dm all results (up to 30)
        add %past to get past GW results"""
        await self.findranking(ctx, True, terms)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwplayer'])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def findplayer(self, ctx, *, terms : str = ""):
        """Search a player GW score in the bot data
        add %id to search by id or %eq to get an exact match
        add %all to receive by dm all results (up to 30)
        add %past to get past GW results"""
        await self.findranking(ctx, False, terms)

    def getRanking(self, page, mode):
        try:
            if mode: return self.bot.sendRequestNoAsync("http://game.granbluefantasy.jp/teamraid{}/rest/ranking/totalguild/detail/{}/0?_=TS1&t=TS2&uid=ID".format(str(self.bot.gw['id']).zfill(3), page), account=self.bot.gbfcurrent, decompress=True, load_json=True)
            else: return self.bot.sendRequestNoAsync("http://game.granbluefantasy.jp/teamraid{}/rest_ranking_user/detail/{}/0?_=TS1&t=TS2&uid=ID".format(str(self.bot.gw['id']).zfill(3), page), account=self.bot.gbfcurrent, decompress=True, load_json=True)
        except:
            return None

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwlead', 'gwcompare', 'gwcmp'])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def lead(self, ctx, IDcrewA : str, IDcrewB : str):
        """Search two crews current score and compare them"""
        day = self.getCurrentGWDayID()
        if day is None or (day % 10) <= 1:
            await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Unavailable", color=self.color))
            return
        if day >= 10: day = day % 10
        infos = [None, None]
        ver = None
        msg = ""
        lead = None
        crew_id_list = {**(self.bot.granblue['gbfgcrew']), **(self.bot.granblue.get('othercrew', {}))}
        for sid in [IDcrewA, IDcrewB]:
            if sid.lower() in crew_id_list:
                id = crew_id_list[sid.lower()]
            else:
                try: id = int(sid)
                except:
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Invalid name `{}`".format(sid), color=self.color))
                    return

            data = await self.searchGWDBCrew(ctx, str(id), 2)
            if data is None:
                await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Unavailable", color=self.color))
                return
            else:
                if data[1] is None or data[1].get('gw', '') != self.bot.gw['id']:
                    await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="No data available for the current GW", color=self.color))
                    return
                result = data[1].get('result', [])
                ver = data[1].get('ver', 0)
                gwnum = data[1].get('gw', '')
                if len(result) == 0:
                    msg += "Crew [{}](http://game.granbluefantasy.jp/#guild/detail/{}) not found\n".format(sid, id)
                    lead = -1
                elif ver == 2:
                    d = [4, 5, 6, 7]
                    msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ {:,}\n".format(result[0][2], id, result[0][d[day-2]]-result[0][d[day-2]-1])
                    if lead is None: lead = result[0][d[day-2]]-result[0][d[day-2]-1]
                    elif lead >= 0: lead = abs(lead - (result[0][d[day-2]]-result[0][d[day-2]-1]))
                else:
                    d = [4, 6, 8, 10]
                    msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ {:,}\n".format(result[0][2], id, result[0][d[day-2]])
                    if lead is None: lead = result[0][d[day-2]]
                    elif lead >= 0: lead = abs(lead - result[0][d[day-2]])
        if lead is not None and lead >= 0:
            msg += "**Difference** ▫️ {:,}\n".format(lead)
        await ctx.send(embed=self.bot.buildEmbed(title="{} **Guild War {} ▫️ Day {}**".format(self.bot.getEmote('gw'), gwnum, day - 1), description=msg, timestamp=datetime.utcnow(), color=self.color))

    def scrapProcess(self, mode, qi, qo): # thread for ranking
        while not qi.empty(): # until the input queue is empty
            if self.bot.exit_flag or self.stoprankupdate: return 
            page = qi.get() # retrieve the page number
            data = None
            while data is None:
                data = self.getRanking(page, mode) # request the page
                if (self.bot.maintenance['state'] and self.bot.maintenance["duration"] == 0) or self.stoprankupdate: return
            for item in data['list']: # put the entries in the list
                qo.put(item)

    def gwdbbuilder(self, mode, qo, count, res):
        try:
            day = self.getCurrentGWDayID() # calculate which day it is (0 being prelim, 1 being interlude/day 1, etc...)
            if day is None or day >= 10 or day == 1:
                res.put(False)
                return
            if day > 1: day -= 1

            conn = sqlite3.connect('temp.sql') # open temp.sql
            c = conn.cursor()

            c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'") # create info table (contains gw id and db version)
            if c.fetchone()[0] < 1:
                 c.execute('CREATE TABLE info (gw int, ver int)')
                 c.execute('INSERT INTO info VALUES ({}, 2)'.format(self.bot.gw['id'])) # ver 2

            if mode: # crew table creation (IF it doesn't exist)
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='crews'")
                if c.fetchone()[0] < 1:
                    c.execute('CREATE TABLE crews (ranking int, id int, name text, preliminaries int, total_1 int, total_2 int, total_3 int, total_4 int)')
            else: # player table creation (delete an existing one, we want the file to keep a small size)
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='players'")
                if c.fetchone()[0] == 1:
                    c.execute('DROP TABLE players')
                c.execute('CREATE TABLE players (ranking int, id int, name text, current_total int)')
            i = 0
            while i < count: # count is the number of entries to process
                if self.bot.exit_flag or (self.bot.maintenance['state'] and self.bot.maintenance["duration"] == 0): # stop if the bot is stopping
                    res.put(False)
                    return
                try: item = qo.get() # retrieve an item
                except: continue # skip if error or no item in the queue

                if mode: # if crew, update the existing crew (if it exists) or create a new entry
                    c.execute("SELECT count(*) FROM crews WHERE id = {}".format(int(item['id'])))
                    if c.fetchone()[0] != 0:
                        c.execute("UPDATE crews SET ranking = {}, name = '{}', {} = {} WHERE id = {}".format(int(item['ranking']), item['name'].replace("'", "''"), {0:'preliminaries',1:'total_1',2:'total_2',3:'total_3',4:'total_4'}.get(day, 'undef'), int(item['point']), int(item['id'])))
                    else:
                        honor = {day: int(item['point'])}
                        c.execute("INSERT INTO crews VALUES ({},{},'{}',{},{},{},{},{})".format(int(item['ranking']), int(item['id']), item['name'].replace("'", "''"), honor.get(0, 'NULL'), honor.get(1, 'NULL'), honor.get(2, 'NULL'), honor.get(3, 'NULL'), honor.get(4, 'NULL')))
                else: # if player, just add to the table
                    c.execute("INSERT INTO players VALUES ({},{},'{}',{})".format(int(item['rank']), int(item['user_id']), item['name'].replace("'", "''"), int(item['point'])))
                i += 1
                if i == count: # if we reached the end, commit
                    conn.commit()
                    conn.close()
            res.put(True)
        except Exception as err:
            print(err)
            self.stoprankupdate = True # send the stop signal if a critical error happened
            res.put(False)

    def gwscrap(self):
        self.bot.drive.delFiles(["temp.sql"], self.bot.tokens['files']) # delete previous temp file (if any)
        self.bot.delFile('temp.sql') # locally too
        if self.bot.drive.cpyFile("GW.sql", self.bot.tokens['files'], "temp.sql"): # copy existing gw.sql to temp.sql
            if not self.bot.drive.dlFile("temp.sql", self.bot.tokens['files']): # retrieve it
                return False
            conn = sqlite3.connect('temp.sql') # open
            c = conn.cursor()
            try:
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'") # check if "info" table exists (backward compatibility with the old format)
                if c.fetchone()[0] == 1:
                    conn.close()
                else:
                    conn.close()
                    self.bot.delFile('temp.sql') # delete if it doesn't (we'll make a clear db instead)
            except:
                conn.close()
                self.bot.delFile('temp.sql') # delete if an error happened too

        self.stoprankupdate = False # if true, this flag will stop the threads
        res = False # return value
        for n in [0, 1]: # n == 0 (crews) or 1 (players)
            current_time = self.bot.getJST()
            if n == 0 and current_time >= self.bot.gw['dates']["Interlude"] and current_time < self.bot.gw['dates']["Day 1"]:
                continue # disabled during interlude for crews

            data = self.getRanking(1, n == 0) # get the first page
            if data is None:
                print("Can't access the ranking")
                return False
            count = int(data['count']) # number of crews/players
            last = data['last'] # number of pages

            qi = Queue() # input queue (contains id of each page not processed yet)
            for i in range(2, last+1): # queue the pages to retrieve
                qi.put(i)
            qo = Queue() # output queue (contains json-data for each crew/player not processed yet)
            for item in data['list']: # queue what we already retrieved on the first page
                qo.put(item)

            threadpool = []
            for i in range(100): # make lot of threads
                threadpool.append(Thread(target=self.scrapProcess, args=(n == 0, qi, qo))) # will request the ranking
                threadpool[-1].setDaemon(True)
                threadpool[-1].start()

            r = Queue() # return value for self.gwdbbuilder
            threadpool.append(Thread(target=self.gwdbbuilder, args=(n == 0, qo, count, r))) # sql builder thread (just need one, not more)
            threadpool[-1].setDaemon(True)
            threadpool[-1].start()

            for t in threadpool:
                t.join() # wait for ALL 100+1 threads to finish (or the garbage collector will mess up)

            threadpool.clear() # delete our finished threads
            qi.queue.clear() # clear the queues
            qo.queue.clear()
            if r.get(): # check if self.gwdbbuilder put True in the queue
                res = True
            else:
                return False
        return res