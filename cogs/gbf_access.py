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
import concurrent.futures
import threading
import time
import leather
import cairosvg
from io import BytesIO

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
        self.possiblesum = {'10':'fire', '11':'fire', '20':'water', '21':'water', '30':'earth', '31':'earth', '40':'wind', '41':'wind', '50':'light', '51':'light', '60':'dark', '61':'dark', '00':'misc', '01':'misc'}
        self.sql = {
            'old_gw' : [None, None, None], # conn, cursor, status
            'gw' : [None, None, None] # conn, cursor, status
        }
        self.scraplockIn = threading.Lock()
        self.scraplockOut = threading.Lock()
        self.scrap_mode = False
        self.scrap_qi = None
        self.scrap_qo = None
        self.scrap_count = 0
        self.scrap_update_time = None
        self.scrap_max_thread = 99
        self.scrap_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.scrap_max_thread+1)
        self.loadinggw = False
        self.loadinggacha = False
        self.ranking_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.rankingtargets = []
        self.rankingtempdata = []
        self.rankinglock = threading.Lock()
        self.stoprankupdate = False
        self.dad_running = False

    def startTasks(self):
        self.bot.runTask('gbfwatch', self.gbfwatch)
        self.bot.runTask('check_ranking', self.checkGWRanking)

    def isOwner(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isOwner(ctx)
        return commands.check(predicate)

    def isOwnerOrDebug(): # for decorators
        async def predicate(ctx):
            return (ctx.bot.isOwner(ctx) or ctx.bot.isChannel(ctx, 'debug_bot'))
        return commands.check(predicate)

    def isYou(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isServer(ctx, 'you_server')
        return commands.check(predicate)

    async def request_async(self, executor, func):
        return await self.bot.loop.run_in_executor(executor, func)

    def updateRankingThread(self):
        r = None
        errc = 0
        try:
            with self.rankinglock:
                diff, iscrew, mode, rank = self.rankingtargets.pop()
            while errc < 5 and (r is None or 'list' not in r):
                if iscrew:
                    r = self.requestRanking(rank // 10, mode)
                    if r is not None and 'list' in r and len(r['list']) > 0:
                        with self.rankinglock:
                            self.rankingtempdata[0][str(rank)] = int(r['list'][-1]['point'])
                            if diff > 0 and self.bot.gw['ranking'] is not None and str(rank) in self.bot.gw['ranking'][0]:
                                self.rankingtempdata[2][str(rank)] = (self.rankingtempdata[0][str(rank)] - self.bot.gw['ranking'][0][str(rank)]) / diff
                else:
                    r = self.requestRanking(rank // 10, 2)
                    if r is not None and 'list' in r and len(r['list']) > 0:
                        with self.rankinglock:
                            self.rankingtempdata[1][str(rank)] = int(r['list'][-1]['point'])
                            if diff > 0 and self.bot.gw['ranking'] is not None and str(rank) in self.bot.gw['ranking'][1]:
                                self.rankingtempdata[3][str(rank)] = (self.rankingtempdata[1][str(rank)] - self.bot.gw['ranking'][1][str(rank)]) / diff
                if r is None:
                    errc += 1
                    time.sleep(0.01)
        except:
            return

    async def checkGWRanking(self):
        cog = self.bot.get_cog('GuildWar')
        if cog is None:
            return
        crewsA = [300, 1000, 2000, 8000, 19000, 36000]
        crewsB = [2000, 5500, 9000, 14000, 18000, 30000]
        players = [2000, 70000, 120000, 160000, 250000, 350000]

        while True:
            cog.getGWState()
            try:
                if self.bot.gw['state'] == False:
                    if 'ranking' not in self.bot.gw or self.bot.gw['ranking'] is not None:
                        self.bot.gw['ranking'] = None
                        self.bot.savePending = True
                    return
                elif self.bot.getJST() < self.bot.gw['dates']["Preliminaries"]:
                    if 'ranking' not in self.bot.gw or self.bot.gw['ranking'] is not None:
                        self.bot.gw['ranking'] = None
                        self.bot.savePending = True
                    d = self.bot.gw['dates']["Preliminaries"] - self.bot.getJST()
                    if d >= timedelta(days=1): return
                    await asyncio.sleep(d.seconds + 1)
                elif self.bot.getJST() > self.bot.gw['dates']["Day 5"] - timedelta(seconds=21600):
                    await asyncio.sleep(3600)
                else:
                    if await self.bot.isGameAvailable():
                        current_time = self.bot.getJST()
                        m = current_time.minute
                        h = current_time.hour
                        skip = False
                        for d in ["End", "Day 5", "Day 4", "Day 3", "Day 2", "Day 1", "Interlude", "Preliminaries"]:
                            if current_time < self.bot.gw['dates'][d]:
                                continue
                            if d == "Preliminaries":
                                diff = current_time - self.bot.gw['dates'][d]
                                if diff.days == 1 and diff.seconds >= 25200:
                                    skip = True
                            elif ((d.startswith("Day") and h < 7 and h >= 2) or d == "Day 5"):
                                skip = True
                            break
                        if skip:
                            await asyncio.sleep(600)
                        elif m in [3, 23, 43]: # minute to update
                            if d.startswith("Day "):
                                crews = crewsB
                                mode = 0
                            else:
                                crews = crewsA
                                mode = 1
                            # update $ranking and $estimation
                            try:
                                update_time = current_time - timedelta(seconds=60 * (current_time.minute % 20))
                                self.rankingtempdata = [{}, {}, {}, {}, update_time]
                                if self.bot.gw['ranking'] is not None:
                                    diff = self.rankingtempdata[4] - self.bot.gw['ranking'][4]
                                    diff = round(diff.total_seconds() / 60.0)
                                else: diff = 0
                                self.rankingtargets = []
                                for c in crews:
                                    self.rankingtargets.append([ diff, True, mode, c])
                                for p in players:
                                    self.rankingtargets.append([diff, False, 2, p])
                                n_thread = len(self.rankingtargets)
                                
                                coros = [self.request_async(self.ranking_executor, self.updateRankingThread) for _i in range(n_thread)]
                                results = await asyncio.gather(*coros)

                                for i in range(0, 4):
                                    self.rankingtempdata[i] = dict(sorted(self.rankingtempdata[i].items(), reverse=True, key=lambda item: int(item[1])))

                                self.bot.gw['ranking'] = self.rankingtempdata
                                self.bot.savePending = True
                            except Exception as ex:
                                await self.bot.sendError('checkgwranking sub', str(ex))
                                self.bot.gw['ranking'] = None
                                self.bot.savePending = True

                            # update DB
                            scrapout = await self.gwscrap(update_time)
                            if scrapout == "":
                                data = await self.GWDBver()
                                if data is not None and data[1] is not None:
                                    if self.bot.gw['id'] != data[1]['gw']: # different gw, we move
                                        if data[0] is not None: # backup old gw if it exists
                                            self.bot.drive.mvFile("GW_old.sql", self.bot.tokens['files'], "GW{}_backup.sql".format(data[0]['gw']))
                                        self.bot.drive.mvFile("GW.sql", self.bot.tokens['files'], "GW_old.sql")
                                if not self.bot.drive.overwriteFile("temp.sql", "application/sql", "GW.sql", self.bot.tokens['files']): # upload
                                    await self.bot.sendError('gwscrap', 'Upload failed')
                                self.bot.delFile('temp.sql')
                                await self.loadGWDB() # reload db
                            elif scrapout != "Invalid day":
                                await self.bot.sendError('gwscrap', 'Scraping failed\n' + scrapout)
                            await asyncio.sleep(300)
                        else:
                            await asyncio.sleep(25)
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

            if self.bot.gbfaccounts[self.bot.gbfcurrent][3] == 2:
                await asyncio.sleep(60)
                continue

            try: # account refresh
                await asyncio.sleep(0.001)
                if 'test' in self.bot.gbfdata:
                    current_time = self.bot.getJST()
                    for i in range(0, len(self.bot.gbfaccounts)):
                        acc = self.bot.gbfaccounts[i]
                        if acc[3] == 0 or (acc[3] == 1 and (acc[5] is None or current_time - acc[5] >= timedelta(seconds=7200))):
                            r = await self.bot.sendRequest(self.bot.gbfwatch['test'], account=i, decompress=True, load_json=True, check=True, force_down=True)
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
                            await self.bot.sendMulti(['debug', 'public_update', 'gbfg_update'], embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy News", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description="[{}]({})".format(news[i][1], news[i][0]), image=news[i][2], color=self.color))
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
                        if title == "": title = last['title']
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
                    react = await self.bot.sendMulti(['debug_update', 'private_update'], embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description="Game version updated to `{}` (`{}`)".format(v, self.bot.versionToDateStr(v)), color=self.color))
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
                    ch = self.bot.get_channel(self.bot.ids['debug_update'])
                    news = await self.cc(ch)
                    try:
                        for r in react: await self.bot.unreact(r, 'time')
                    except:
                        pass
                    if len(news) > 0:
                        msg += "**Content update**\n"
                        for k in news:
                            msg += "{} {}\n".format(news[k], k)
                    if msg != "":
                        await self.bot.sendMulti(['debug_update', 'private_update'], embed=self.bot.buildEmbed(title="Latest Update", description=msg, thumbnail=thumb, color=self.color))
                        if len(tickets) > 0 and len(news) > 0:
                            await self.bot.send('debug_update', embed=self.bot.buildEmbed(title="Reminder", description="Keep it private", color=self.color))
                elif s == 2:
                    await self.bot.send('debug_update', embed=self.bot.buildEmbed(author={'name':"Granblue Fantasy", 'icon_url':"http://game-a.granbluefantasy.jp/assets_en/img/sp/touch_icon.png"}, description="Game version set to `{}` (`{}`)".format(v, self.bot.versionToDateStr(v)) , color=self.color))
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

                            res.append([url.attrs['href'], url.text, img])
                    except:
                        pass
        return res

    async def check4koma(self):
        data = await self.bot.sendRequest('http://game.granbluefantasy.jp/comic/list/1?PARAMS', account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True)
        if data is None: return None
        return data['list'][0]

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
                res += s+c+'\r\n'
        if indent == 0: res += '\r\n'
        return res

    async def dad(self, id, silent, mode = 0): # black magic
        if id[0] == '3': type = 0
        elif id[0] == '2': type = 1
        elif id[0] == '1': type = 2
        else: return ["", {}, {}, {}]
        try:
            files = self.bot.gbfwatch["files"]
            flags = {}
            for t in self.bot.gbfwatch["flags"]:
                flags[t] = {}
                for k in self.bot.gbfwatch["flags"][t]:
                    flags[t][k] = False
            it = self.bot.gbfwatch["it"]
            thct = self.bot.gbfwatch["thct"]
            thbd = self.bot.gbfwatch["thbd"]
        except:
            return ["", {}, {}, {}, ""]

        if self.dad_running:
            return ["please wait your turn", {}, {}, thbd[type].format(id), ""]
        self.dad_running = True

        thf = thbd[type].format(id)
        try:
            data = await self.bot.sendRequest(thbd[type].format(id), no_base_headers=True)
            if data is None and type == 0:
                data = await self.bot.sendRequest(thct.format(id).replace("/30", "/38"), no_base_headers=True)
                if data is not None:
                    thf = thct.format(id).replace("/30", "/38")
        except:
            pass

        paste = ""
        iul = {}
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

                paste += '# {} ############################################\r\n'.format(ff)

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
                    message = await self.bot.send('image', file=discord.File(infile))
                    iul["{}.png".format(ff)] = message.attachments[0].url
                self.bot.delFile("{}.png".format(ff))
            except:
                if counter >= 3 and len(paste) == 0:
                    self.dad_running = False
                    return ["", {}, {}, thf, ""]
            counter+=1

        if len(paste) > 0:
            if silent:
                self.dad_running = False
                return ["Not uploaded", flags, iul, thf, paste]
            else:
                title = "{}_dump_{}.txt".format(id, datetime.utcnow().timestamp())
                with open(title, "wb") as f:
                    f.write(paste.encode('utf-8'))
                self.dad_running = False
                return [title, flags, iul, thf, paste]
        else:
            self.dad_running = False
            return ["", {}, {}, thf]

    async def dadp(self, c, data, tt): # black magic
        fields = []

        tmp = ""
        for k in data[2]:
            tmp += "[{}]({})\n".format(k.replace(tt, ''), data[2][k])
        if len(tmp) > 0:
            fields.append({'name':'Sprites', 'value':tmp})

        for k in data[1]:
            tmp = ""
            for t in data[1][k]:
                if data[1][k][t]:
                    tmp += t + ', '
            if len(tmp) > 0:
                fields.append({'name':k, 'value':tmp[:-2]})
        
        for f in fields:
            if len(f['value']) >= 1024:
                f['value'] = f['value'][:1019] + '...'
        try:
            with open(data[0], "rb") as f:
                await c.send(embed=self.bot.buildEmbed(title=tt, fields=fields, color=self.color, thumbnail=data[3]), file=discord.File(f))
            self.bot.delFile(data[0])
        except:
            await c.send(embed=self.bot.buildEmbed(title=tt, description=data[0], fields=fields, color=self.color, thumbnail=data[3]))

    async def cc(self, channel): # black magic
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
            errm = 4 if (i < len(self.bot.gbfdata['c']) - 1) else 8
            while errc < errm:
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
                        await self.dadp(channel, data, "{} : {}".format(crt[i][0], str(cid + id * 1000)))
                        
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
                while errc < 7 or stid <= max:
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
                        await channel.send(embed=self.bot.buildEmbed(title=ws[x], description='{} ▫️ {}'.format(tt, id), thumbnail=wl[0].format(id), color=self.color))

                    stid += 1

                self.bot.gbfdata['w'][k][i].sort()
                if len(self.bot.gbfdata['w'][k][i]) > 11: self.bot.gbfdata['w'][k][i] = self.bot.gbfdata['w'][k][i][-11:]
                self.bot.savePending = True

        return found

    async def getCrewSummary(self, id):
        res = await self.bot.sendRequest("http://game.granbluefantasy.jp/guild_main/content/detail/{}?PARAMS".format(id), account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True)
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
                elif get == "Down":
                    return {'error':'Unavailable'}
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
                        crew['ship_element'] = {"10001":"wind", "20001":"fire", "30001":"water", "40001":"earth", "50001":"light", "60001":"dark"}.get(get['ship_img'].split('_')[0], 'gw')
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
                    await ctx.reply(embed=self.bot.buildEmbed(title="Crew Error", description=crew['error'], color=self.color))
                return

            # embed initialization
            title = "\u202d{} **{}**".format(self.bot.getEmote(crew['ship_element']), crew['name'])
            if 'count' in crew: title += "▫️{}/30".format(crew['count'])
            if 'average' in crew: title += "▫️Rank {}".format(crew['average'])
            if 'online' in crew: title += "▫️{} online".format(crew['online'])
            description = "💬 `{}`".format(self.escape(crew['message'], True))
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
                        description += "\n{} GW**{}** ▫️ Player Sum **{}** ▫️ Average **{}**".format(self.bot.getEmote('question'), gwid, self.honorFormat(total), self.honorFormat(total // (len(players) - unranked)))
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

            final_msg = await ctx.reply(embed=self.bot.buildEmbed(title=title, description=description, fields=fields, inline=True, url="http://game.granbluefantasy.jp/#guild/detail/{}".format(crew['id']), footer=footer, timestamp=crew['timestamp'], color=self.color))
            await self.bot.cleanMessage(ctx, final_msg, 60)

        except Exception as e:
            await self.bot.sendError("postCrewData", str(e))

    def honorFormat(self, h): # convert honor number to a shorter string version
        if h is None: return "n/a"
        elif isinstance(h, str): h = int(h)
        elif h >= 1000000000: return "{:.1f}B".format(h/1000000000)
        elif h >= 1000000: return "{:.1f}M".format(h/1000000)
        elif h >= 1000: return "{:.1f}K".format(h/1000)
        return h

    def escape(self, s, lite=False): # escape markdown string
        # add the RLO character before
        if lite: return '\u202d' + s.replace('\\', '\\\\').replace('`', '\\`')
        else: return '\u202d' + s.replace('\\', '\\\\').replace('`', '\'').replace('*', '\\*').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('[', '').replace(']', '').replace('(', '\\(').replace(')', '\\)').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('|', '\\|')

    async def requestCrew(self, id : int, page : int): # get crew data
        if page == 0: return await self.bot.sendRequest("http://game.granbluefantasy.jp/guild_other/guild_info/{}?PARAMS".format(id), account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True)
        else: return await self.bot.sendRequest("http://game.granbluefantasy.jp/guild_other/member_list/{}/{}?PARAMS".format(page, id), account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True)

    async def getProfileData(self, id : int): # get player data
        if not await self.bot.isGameAvailable():
            return "Maintenance"
        res = await self.bot.sendRequest("http://game.granbluefantasy.jp/profile/content/index/{}?PARAMS".format(id), account=self.bot.gbfcurrent, decompress=True, load_json=True)
        if res is not None: return unquote(res['data'])
        else: return res

    async def getScoutData(self, id : int): # get player scout data
        return await self.bot.sendRequest("http://game.granbluefantasy.jp/forum/search_users_id?PARAMS", account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True, payload={"special_token":None,"user_id":id})

    def requestRanking(self, page, mode = 0): # get gw ranking data
        if self.bot.gw['state'] == False or self.bot.getJST() <= self.bot.gw['dates']["Preliminaries"]:
            return None

        if mode == 0: # crew
            res = self.specialRequest("http://game.granbluefantasy.jp/teamraid{}/rest/ranking/totalguild/detail/{}/0?=TS1&t=TS2&uid=ID".format(str(self.bot.gw['id']).zfill(3), page))
        elif mode == 1: # prelim crew
            res = self.specialRequest("http://game.granbluefantasy.jp/teamraid{}/rest/ranking/guild/detail/{}/0?=TS1&t=TS2&uid=ID".format(str(self.bot.gw['id']).zfill(3), page))
        elif mode == 2: # player
            res = self.specialRequest("http://game.granbluefantasy.jp/teamraid{}/rest_ranking_user/detail/{}/0?=TS1&t=TS2&uid=ID".format(str(self.bot.gw['id']).zfill(3), page))
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
        self.bot.gbfdata['gacharateups'] = None
        c = self.bot.getJST()
        try:
            #gacha page
            data = await self.bot.sendRequest("http://game.granbluefantasy.jp/gacha/list?PARAMS", account=self.bot.gbfcurrent, decompress=True, load_json=True, check_update=True)
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
            data = await self.bot.sendRequest("http://game.granbluefantasy.jp/gacha/provision_ratio/{}/1?PARAMS".format(gachaid), account=self.bot.gbfcurrent, decompress=True, load_json=True, check_update=True)
            # build list
            banner_msg = "{} **{}** Rate".format(self.bot.getEmote('SSR'), data['ratio'][0]['ratio'])
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
            self.bot.gbfdata['rateup'] = rateup

            # build rate up
            self.bot.gbfdata['gacharateups'] = []
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
                            if r not in self.bot.gbfdata['gacharateups']: self.bot.gbfdata['gacharateups'].append(r)
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
            self.bot.gbfdata['gacharateups'] = None
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
        r = await self.bot.sendRequest(self.bot.gbfwatch['test'], account=id, decompress=True, load_json=True, check=True, force_down=True)
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
    @isOwnerOrDebug()
    @commands.cooldown(1, 10, commands.BucketType.default)
    async def item(self, ctx, id : int):
        """Retrieve an item description (Owner or Bot only)"""
        try:
            data = await self.bot.sendRequest('http://game.granbluefantasy.jp/rest/quest/droplist/drop_item_detail?PARAMS', account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True, payload={"special_token":None,"item_id":id,"item_kind":10})
            await ctx.reply(embed=self.bot.buildEmbed(title=data['name'], description=data['comment'].replace('<br>', ' '), thumbnail="http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/item/article/s/{}.jpg".format(id), footer=data['id'], color=self.color))
        except:
            await self.bot.react(ctx.message, '❎') # white negative mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwnerOrDebug()
    @commands.cooldown(1, 10, commands.BucketType.default)
    async def loot(self, ctx, id : str):
        """Retrieve a weapon or summon description (Owner or Bot only)"""
        try:
            type = int(id[0])
            id = int(id)
            if type not in [1, 2]: raise Exception()
            data = await self.bot.sendRequest('http://game.granbluefantasy.jp/result/detail?PARAMS', account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True, payload={"special_token":None,"item_id":id,"item_kind":type})
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

            await ctx.reply(embed=self.bot.buildEmbed(title="{}{}{}".format(rarity, kind, data['name']), description=msg, thumbnail=url, footer=data['id'], color=self.color))
        except:
            await self.bot.react(ctx.message, '❎') # white negative mark
            
    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def coop(self, ctx):
        """Retrieve the current coop daily missions"""
        try:
            data = (await self.bot.sendRequest('http://game.granbluefantasy.jp/coopraid/daily_mission?PARAMS', account=self.bot.gbfcurrent, decompress=True, load_json=True, check=True))['daily_mission']
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
                description = "{} Current gacha ends in **{}**".format(self.bot.getEmote('clock'), self.bot.getTimedeltaStr(content[0], 2))
                if content[0] != content[1]:
                    description += "\n{} Spark period ends in **{}**".format(self.bot.getEmote('mark'), self.bot.getTimedeltaStr(content[1], 2))
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

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['unsetid'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def unsetProfile(self, ctx):
        """Unlink your GBF id"""
        if str(ctx.author.id) not in self.bot.gbfids:
            await ctx.reply(embed=self.bot.buildEmbed(title="Unset Profile Error", description="You didn't set your GBF profile ID", color=self.color))
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
                await ctx.reply(embed=self.bot.buildEmbed(title="Set Profile Error", description="Invalid ID", color=self.color))
                return
            data = await self.getProfileData(id)
            if data == "Maintenance":
                await ctx.reply(embed=self.bot.buildEmbed(title="Set Profile Error", description="Game is in maintenance, try again later.", color=self.color))
                return
            elif data == "Down":
                return
            elif data is None:
                await ctx.reply(embed=self.bot.buildEmbed(title="Set Profile Error", description="Profile not found", color=self.color))
                return
            for u in self.bot.gbfids:
                if self.bot.gbfids[u] == id:
                    await ctx.reply(embed=self.bot.buildEmbed(title="Set Profile Error", description="This id is already in use", footer="use the bug_report command if it's a case of griefing", color=self.color))
                    return
            # register
            self.bot.gbfids[str(ctx.author.id)] = id
            self.bot.savePending = True
            await self.bot.react(ctx.message, '✅') # white check mark
        except Exception as e:
            await self.bot.sendError("setprofile", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['badboi', 'branded', 'restricted'])
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def brand(self, ctx, id : int):
        """Check if a GBF profile is restricted"""
        try:
            if id < 0 or id >= 100000000:
                await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid ID", color=self.color))
                return
            if id in self.badprofilecache:
                await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Profile not found", color=self.color))
                return
            data = await self.getScoutData(id)
            if data == "Maintenance":
                await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Game is in maintenance", color=self.color))
                return
            elif data == "Down":
                return
            elif len(data['user']) == 0:
                await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="In game message:\n`{}`".format(data['no_member_msg'].replace("<br>", " ")), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
                return
            try:
                if data['user']["restriction_flag_list"]["event_point_deny_flag"]:
                    status = "Account is restricted"
                else:
                    status = "Account isn't restricted"
            except:
                status = "Account isn't restricted"
            await ctx.reply(embed=self.bot.buildEmbed(title="{} {}".format(self.bot.getEmote('gw'), data['user']['nickname']), description=status, thumbnail="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/talk/{}.png".format(data['user']['image']), url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))

        except Exception as e:
            await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Unavailable", color=self.color))
            await self.bot.sendError("brand", str(e))

    def dlAndPasteImage(self, img, url, offset, resize):
        req = request.Request(url)
        url_handle = request.urlopen(req, context=self.bot.ssl)
        file_jpgdata = BytesIO(url_handle.read())
        url_handle.close()
        dt = Image.open(file_jpgdata)
        if resize is not None: dt = dt.resize(resize)
        img.paste(dt, offset, dt.convert('RGBA'))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['id'])
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def profile(self, ctx, *target : str):
        """Retrieve a GBF profile"""
        target = " ".join(target)
        try:
            if target == "":
                if str(ctx.author.id) not in self.bot.gbfids:
                    await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="{} didn't set its profile ID".format(ctx.author.display_name), footer="setProfile <id>", color=self.color))
                    return
                id = self.bot.gbfids[str(ctx.author.id)]
            elif target.startswith('<@') and target.endswith('>'):
                try:
                    if target[2] == "!": target = int(target[3:-1])
                    else: target = int(target[2:-1])
                    member = ctx.guild.get_member(target)
                    if str(member.id) not in self.bot.gbfids:
                        await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="{} didn't set its profile ID".format(member.display_name), footer="setProfile <id>", color=self.color))
                        return
                    id = self.bot.gbfids[str(member.id)]
                except:
                    await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid parameter {} -> {}".format(target, type(target)), color=self.color))
                    return
            else:
                try: id = int(target)
                except:
                    member = ctx.guild.get_member_named(target)
                    if member is None:
                        await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Member not found", color=self.color))
                        return
                    elif str(member.id) not in self.bot.gbfids:
                        await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="{} didn't set its profile ID".format(member.display_name), footer="setProfile <id>", color=self.color))
                        return
                    id = self.bot.gbfids[str(member.id)]
            if id < 0 or id >= 100000000:
                await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Invalid ID", color=self.color))
                return
            if id in self.badprofilecache:
                await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Profile not found", color=self.color))
                return
            data = await self.getProfileData(id)
            if data == "Maintenance":
                await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Game is in maintenance", color=self.color))
                return
            elif data == "Down":
                return
            elif data is None:
                self.badprofilecache.append(id)
                await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Profile not found", color=self.color))
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
                elif rank == "": comment = "💬 `{}`".format(comment.replace('`', '\''))
                else: comment = " ▫️ 💬 `{}`".format(comment.replace('`', '\''))
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

                try:
                    summons_res = self.sumre.findall(data)
                    sortsum = {}
                    for s in summons_res:
                        if self.possiblesum[s[0]] not in sortsum: sortsum[self.possiblesum[s[0]]] = s[1]
                        else: sortsum[self.possiblesum[s[0]]] += ' ▫️ ' + s[1]
                    try:
                        misc = sortsum.pop('misc')
                        sortsum['misc'] = misc
                    except:
                        pass
                    summons = ""
                    for k in sortsum:
                        summons += "\n{} {}".format(self.bot.getEmote(k), sortsum[k])
                    if summons != "": summons = "\n{} **Summons**{}".format(self.bot.getEmote('summon'), summons)
                except:
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
                    star = "\n\n{} **Star Character**\n{}".format(self.bot.getEmote('skill2'), msg)
                except:
                    star = ""

                try: # image processing
                    img = Image.new('RGB', (410, 370), "black")
                    d = ImageDraw.Draw(img, 'RGBA')
                    font = ImageFont.truetype("assets/font.ttf", 16)
                    self.dlAndPasteImage(img, mc_url.replace("/talk/", "/po/"), (-40, -80), None)

                    equip = soup.find_all('div', class_='prt-equip-image')
                    for eq in equip:
                        mh = eq.findChildren('img', class_='img-weapon', recursive=True)
                        if len(mh) > 0: # mainhand
                            self.dlAndPasteImage(img, mh[0].attrs['src'].replace('img_low', 'img'), (244, 20), (78, 164))
                            plus = eq.findChildren("div", class_="prt-weapon-quality", recursive=True)
                            if len(plus) > 0:
                                d.text((274, 154), plus[0].text, fill=(255, 255, 95), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
                            continue
                        ms = eq.findChildren('img', class_='img-summon', recursive=True)
                        if len(ms) > 0: # main summon
                            self.dlAndPasteImage(img, ms[0].attrs['src'].replace('img_low', 'img'), (322, 20), (78, 164))
                            plus = eq.findChildren("div", class_="prt-summon-quality", recursive=True)
                            if len(plus) > 0:
                                d.text((352, 154), plus[0].text, fill=(255, 255, 95), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
                            continue
                    
                    # party members
                    party_section = soup.find_all("div", class_="prt-party-npc")[0]
                    party = party_section.findChildren("div", class_="prt-npc-box", recursive=True)
                    count = 0
                    for npc in party:
                        imtag = npc.findChildren("img", class_="img-npc", recursive=True)[0]
                        ring = npc.findChildren("div", class_="ico-augment2-m", recursive=True)
                        self.dlAndPasteImage(img, imtag['src'].replace('img_low', 'img'), (10+78*count, 202), (78, 142))
                        if len(ring) > 0:
                            self.dlAndPasteImage(img, "http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png", (10+78*count, 202), (30, 30))
                        
                        plus = npc.findChildren("div", class_="prt-quality", recursive=True)
                        if len(plus) > 0:
                            d.text((40+78*count, 314), plus[0].text, fill=(255, 255, 95), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
                        count += 1

                    # levels
                    party = party_section.findChildren("div", class_="prt-npc-level", recursive=True)
                    count = 0
                    for lvl in party:
                        d.rectangle([(10+78*count, 344), (10+78*(count+1), 364)], fill=(0, 0, 0, 150), outline=(255, 255, 255), width=1)
                        d.text((16+78*count, 341), lvl.text.strip(), fill=(255, 255, 255), font=font)
                        count += 1

                    # id
                    d.text((0, 0), "{}".format(id), fill=(255, 255, 255), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
                    ifn = "{}_{}.png".format(id, datetime.utcnow().timestamp())
                    img.save(ifn, "PNG")
                    with open(ifn, 'rb') as infile:
                        message = await self.bot.send('image', file=discord.File(infile))
                        thumbnail = message.attachments[0].url
                        self.bot.delFile(ifn)
                except:
                    thumbnail = None

                if trophy == "No Trophy Displayed": title = "\u202d{} **{}**".format(self.bot.getEmote(rarity), name)
                else: title = "\u202d{} **{}**▫️{}".format(self.bot.getEmote(rarity), name, trophy)
                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title=title, description="{}{}\n{} Crew ▫️ {}\n{}{}{}".format(rank, comment, self.bot.getEmote('gw'), crew, scores, summons, star), thumbnail=thumbnail, url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
            else:
                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="Profile Error", description="Profile is private", url="http://game.granbluefantasy.jp/#profile/{}".format(id), color=self.color))
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
        """Sort and post the top 30 server members per contribution"""
        members = []
        gwid = None
        for sid in self.bot.gbfids:
            m = ctx.guild.get_member(int(sid))
            if m is not None:
                pdata = await self.searchGWDBPlayer(ctx, self.bot.gbfids[sid], 2)
                if pdata is not None and pdata[1] is not None and 'result' in pdata[1] and len(pdata[1]['result']) == 1:
                    if gwid is None: gwid = pdata[1].get('gw', None)
                    members.append([pdata[1]['result'][0][1], pdata[1]['result'][0][2], pdata[1]['result'][0][3]]) # id, name, honor
                await asyncio.sleep(0.001)
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
        await asyncio.sleep(0.001)
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

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["resetdancho"])
    @isOwner()
    async def resetleader(self, ctx):
        """Reset the saved captain list"""
        self.bot.gbfdata.pop('leader')
        self.bot.savePending = True
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["danchouranking", "danchous", "danchos", "captains", "captainranking", "capranking"])
    @commands.cooldown(1, 100, commands.BucketType.guild)
    async def danchoranking(self, ctx):
        """Sort and post all /gbfg/ captains per contribution"""
        crews = []
        for e in self.bot.granblue['gbfgcrew']:
            if self.bot.granblue['gbfgcrew'][e] in crews: continue
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
            if self.bot.granblue['gbfgcrew'][e] in crews: continue
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
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} /gbfg/ recruiting crews".format(self.bot.getEmote('crew')), description="Unavailable", color=self.color))
        else:
            await self.bot.react(ctx.message, 'time')
            crews = []
            for e in self.bot.granblue['gbfgcrew']:
                if self.bot.granblue['gbfgcrew'][e] in crews: continue
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
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} /gbfg/ recruiting crews".format(self.bot.getEmote('crew')), fields=fields, inline=True, color=self.color, timestamp=datetime.utcnow()))
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
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="Granblue Episode {}".format(id), url="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/comic/episode/episode_{}.jpg".format(id), image="http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/comic/thumbnail/thum_{}.png".format(str(id).zfill(5)), color=self.color))
            await self.bot.cleanMessage(ctx, final_msg, 45)
        except:
            await self.bot.react(ctx.message, '❎') # white negative mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwnerOrDebug()
    @commands.cooldown(1, 2, commands.BucketType.default)
    async def dd(self, ctx, id : str, mode : int = 0):
        """Black magic (Owner or Bot only)"""
        if not await self.bot.isGameAvailable():
            await ctx.reply(embed=self.bot.buildEmbed(title="Unavailable", color=self.color))
            return
        await self.bot.react(ctx.message, 'time')
        data = await self.dad(id, False, mode)
        if data[0] != "":
            await self.dadp(ctx.channel, data, id)
        await self.bot.unreact(ctx.message, 'time')
        await self.bot.react(ctx.message, '✅') # white check mark

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isOwner()
    async def cn(self, ctx):
        """Black magic (Owner only)"""
        if not await self.bot.isGameAvailable():
            await ctx.reply(embed=self.bot.buildEmbed(title="Unavailable", color=self.color))
            return
        await self.bot.react(ctx.message, 'time')
        news = await self.cc(ctx.channel)
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
            final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="**Usage**\n`find{} [crewname]` to search a {} by name\n`find{} %eq [{}name]` or `find{} %== [{}name]` for an exact match\n`find{} %id [{}id]` for an id search\n`find{} %rank [ranking]` for a ranking search\n`find{} %all ...` to receive all the results by direct message".format(txt, txt, txt, txt, txt, txt, txt, txt, txt, txt), color=self.color))
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
                        final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` isn't a valid syntax".format(terms), color=self.color))
                        raise Exception("Returning")
                elif terms.startswith("%rank "):
                    try:
                        terms = int(terms[6:])
                        mode = 3
                    except:
                        final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` isn't a valid syntax".format(terms), color=self.color))
                        raise Exception("Returning")
                else:
                    mode = 0
                if type: data = await self.searchGWDBCrew(ctx, terms, mode)
                else: data = await self.searchGWDBPlayer(ctx, terms, mode)
                if data is None:
                    final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Database unavailable", color=self.color))
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
                    final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Database unavailable", color=self.color))
                    raise Exception("Returning")

                if len(result) == 0:
                    final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="`{}` not found".format(terms), footer="help find{} for details".format(txt), color=self.color))
                    raise Exception("Returning")
                elif all:
                    if type: xl = 36
                    else: xl = 80
                    x = len(result)
                    if x > xl: x = xl
                    final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Sending your {}/{} result(s)".format(x, len(result)), footer="help find{} for details".format(txt), color=self.color))
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
                                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="I can't send you the full list by private messages", color=self.color))
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
                                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="I can't send you the full list by private messages", color=self.color))
                                raise Exception("Returning")
                            fields = []

                if all:
                    await self.bot.react(ctx.message, '✅') # white check mark
                    raise Exception("Returning")
                elif type and len(result) > 6: desc = "6/{} random result(s) shown".format(len(result)) # crew
                elif not type and len(result) > 30: desc = "30/{} random result(s) shown".format(len(result)) # player
                else: desc = ""
                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War {}**".format(self.bot.getEmote('gw'), gwnum), description=desc, fields=fields, inline=True, footer="help find{} for details".format(txt), color=self.color))
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

    def specialRequest(self, url):
        try:
            data = None
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en',
                'Connection': 'close',
                'Host': 'game.granbluefantasy.jp',
                'Origin': 'http://game.granbluefantasy.jp',
                'Referer': 'http://game.granbluefantasy.jp/',
                'X-Requested-With': 'XMLHttpRequest'
            }
            id = self.bot.gbfcurrent
            acc = self.bot.getGBFAccount(id)
            ver = self.bot.gbfversion
            if ver is None or acc is None:
                return None
            ts = int(datetime.utcnow().timestamp() * 1000)
            url = url.replace("TS1", "{}".format(ts))
            url = url.replace("TS2", "{}".format(ts+300))
            url = url.replace("ID", "{}".format(acc[0]))
            headers['Cookie'] = acc[1]
            headers['User-Agent'] = acc[2]
            headers['X-VERSION'] = ver
            req = request.Request(url, headers=headers)
            url_handle = request.urlopen(req, context=self.bot.ssl)
            self.bot.refreshGBFAccount(id, url_handle.info()['Set-Cookie'])
            data = zlib.decompress(url_handle.read(), 16+zlib.MAX_WBITS)
            url_handle.close()
            data = json.loads(data)
            return data
        except Exception as e:
            return None

    def getRanking(self, page, mode):
        try:
            if mode: return self.specialRequest("http://game.granbluefantasy.jp/teamraid{}/rest/ranking/totalguild/detail/{}/0?PARAMS".format(str(self.bot.gw['id']).zfill(3), page))
            else: return self.specialRequest("http://game.granbluefantasy.jp/teamraid{}/rest_ranking_user/detail/{}/0?PARAMS".format(str(self.bot.gw['id']).zfill(3), page))
        except:
            return None

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['lightchads', 'lightards', 'lightard'])
    @commands.cooldown(1, 40, commands.BucketType.guild)
    async def lightchad(self, ctx):
        """No comment on this thing"""
        ids = [20570061, 1539029, 14506879, 21950001, 7636084, 8817744, 6272981, 6747425, 15627188, 18549435]
        array = []
        for id in ids:
            data = await self.searchGWDBPlayer(ctx, id, 2)
            try:
                if data is not None and data[1] is not None:
                    if len(array) == 0: array.append(data[1]['result'][0])
                    else:
                        for i in range(0, len(array)):
                            if array[i][3] < data[1]['result'][0][3]:
                                array.insert(i, data[1]['result'][0])
                                break
                            if i == len(array) - 1:
                                array.append(data[1]['result'][0])
            except:
                pass
        
        msg = ""
        for p in array:
            msg += "[{}](http://game.granbluefantasy.jp/#profile/{}) :white_small_square: {}\n".format(p[2], p[1], self.honorFormat(p[3]))
        if msg == "":
            msg = "No lightCHADs found in the ranking"
        
        final_msg = await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ LightCHADs", description=msg, thumbnail="https://media.discordapp.net/attachments/614716155646705676/800315410289262602/light.png", color=self.color))
        await self.bot.cleanMessage(ctx, final_msg, 60)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['gwlead', 'gwcompare', 'gwcmp'])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def lead(self, ctx, IDcrewA : str, IDcrewB : str):
        """Search two crews current score and compare them"""
        day = self.getCurrentGWDayID()
        if day is None or (day % 10) <= 1:
            await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Unavailable", color=self.color))
            return
        if day >= 10: day = day % 10
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
                    await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Invalid name `{}`".format(sid), color=self.color))
                    return

            data = await self.searchGWDBCrew(ctx, str(id), 2)
            if data is None:
                await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Unavailable", color=self.color))
                return
            else:
                if data[1] is None or data[1].get('gw', '') != self.bot.gw['id']:
                    await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="No data available for the current GW", color=self.color))
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
        await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War {} ▫️ Day {}**".format(self.bot.getEmote('gw'), gwnum, day - 1), description=msg, timestamp=datetime.utcnow(), color=self.color))

    def x(self, row, index):
        return row['x']

    def yA(self, row, index):
        return row['q']['y'][0]

    def yB(self, row, index):
        return row['q']['y'][1]

    async def updateYouTracker(self, t):
        day = self.getCurrentGWDayID()
        if day is None or day <= 1 or day >= 10: # check if match day
            return
        you_id = self.bot.granblue['gbfgcrew'].get('you', None) # our id
        
        if you_id is None: return
        if self.bot.matchtracker is None: return # not initialized
        if self.bot.matchtracker['day'] != day: # new day, reset
            self.bot.matchtracker = {
                'day':day,
                'init':False,
                'id':self.bot.matchtracker['id'],
                'plot':[]
            }
            
        infos = []
        conn = sqlite3.connect('temp.sql') # open temp.sql
        c = conn.cursor()
        for sid in [you_id, self.bot.matchtracker['id']]:
            c.execute("SELECT * FROM crews WHERE id = {}".format(sid)) # get the score
            data = c.fetchall()
            if data is None or len(data) == 0: raise Exception("Failed to retrieve data")
            d = [4, 5, 6, 7]
            infos.append([data[0][2], data[0][d[day-2]]-data[0][d[day-2]-1]]) # name and score of the day
        conn.close()

        if self.bot.matchtracker['init']:
            d = t - self.bot.matchtracker['last']
            speed = [(infos[0][1] - self.bot.matchtracker['scores'][0]) / (d.seconds//60), (infos[1][1] - self.bot.matchtracker['scores'][1]) / (d.seconds//60)]
            if speed[0] > self.bot.matchtracker['top_speed'][0]: self.bot.matchtracker['top_speed'][0] = speed[0]
            if speed[1] > self.bot.matchtracker['top_speed'][1]: self.bot.matchtracker['top_speed'][1] = speed[1]
            self.bot.matchtracker['speed'] = speed
        else:
            self.bot.matchtracker['init'] = True
            self.bot.matchtracker['speed'] = None
            self.bot.matchtracker['top_speed'] = [0, 0]
        self.bot.matchtracker['names'] = [infos[0][0], infos[1][0]]
        self.bot.matchtracker['scores'] = [infos[0][1], infos[1][1]]
        self.bot.matchtracker['last'] = t
        self.bot.matchtracker['gwid'] = self.bot.gw['id']
        self.bot.savePending = True
        if self.bot.matchtracker['speed'] is not None: # save chart data
            self.bot.matchtracker['plot'].append({'x': t, 'q': { 'y': [self.bot.matchtracker['speed'][0] / 1000000, self.bot.matchtracker['speed'][1] / 1000000] }})
            self.bot.savePending = True # just in case
        if len(self.bot.matchtracker['plot']) > 1: # generate chart
            chart = leather.Chart('Speed Chart')
            chart.add_line(self.bot.matchtracker['plot'], x=self.x, y=self.yA, name="(You)")
            chart.add_line(self.bot.matchtracker['plot'], x=self.x, y=self.yB, name="Opponent")
            chart.to_svg('chart.svg')
            cairosvg.svg2png(url="chart.svg", write_to="chart.png")
            try:
                with open("chart.png", "rb") as f:
                    message = await self.bot.send('image', file=discord.File(f))
                    self.bot.matchtracker['chart'] = message.attachments[0].url
            except:
                pass
            self.bot.savePending = True

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isYou()
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def youlead(self, ctx, opponent : str = ""):
        """Show the current match of (You)"""
        if opponent != "":
            if not self.bot.isMod(ctx):
                await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Only moderators can set the opponent", color=self.color))
                return
            crew_id_list = {**(self.bot.granblue['gbfgcrew']), **(self.bot.granblue.get('othercrew', {}))}
            if opponent.lower() in crew_id_list:
                id = crew_id_list[opponent.lower()]
            else:
                try: id = int(opponent)
                except:
                    await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Invalid name `{}`".format(opponent), color=self.color))
                    return
            if self.bot.matchtracker is None or self.bot.matchtracker['id'] != id:
                self.bot.matchtracker = {
                    'day':None,
                    'init':False,
                    'id':id,
                    'plot':[]
                }
            await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Opponent set to id `{}`, please wait the next ranking update".format(id), color=self.color))
        else:
            if self.bot.matchtracker is None or not self.bot.matchtracker['init']:
                await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War**".format(self.bot.getEmote('gw')), description="Unavailable, either wait the next ranking update or add the opponent id after the command to initialize it", color=self.color))
            else:
                you_id = self.bot.granblue['gbfgcrew'].get('you', None)
                d = self.bot.getJST() - self.bot.matchtracker['last']
                msg = "Updated: **{}** ago".format(self.bot.getTimedeltaStr(d, 0))
                if d.seconds >= 1200 and d.seconds <= 1800: msg += " ▫ *updating*"
                msg += "\n"
                end_time = self.bot.matchtracker['last'].replace(day=self.bot.matchtracker['last'].day+1, hour=0, minute=0, second=0, microsecond=0)
                remaining = end_time - self.bot.matchtracker['last']
                msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ **{:,}**".format(self.bot.matchtracker['names'][0], you_id, self.bot.matchtracker['scores'][0])
                if self.bot.matchtracker['speed'] is not None:
                    if self.bot.matchtracker['speed'][0] == self.bot.matchtracker['top_speed'][0]:
                        msg += "\n**Speed** ▫️ **Now {}/m** ▫️ **Top {}/m**".format(self.honorFormat(self.bot.matchtracker['speed'][0]), self.honorFormat(self.bot.matchtracker['top_speed'][0]))
                    else:
                        msg += "\n**Speed** ▫ Now {}/m ▫️ Top {}/m".format(self.honorFormat(self.bot.matchtracker['speed'][0]), self.honorFormat(self.bot.matchtracker['top_speed'][0]))
                    if end_time > self.bot.matchtracker['last']:
                        msg += "\n**Estimation** ▫ Now {} ▫️ Top {}".format(self.honorFormat(self.bot.matchtracker['scores'][0] + self.bot.matchtracker['speed'][0] * remaining.seconds//60), self.honorFormat(self.bot.matchtracker['scores'][0] + self.bot.matchtracker['top_speed'][0] * remaining.seconds//60))
                msg += "\n\n"
                msg += "[{:}](http://game.granbluefantasy.jp/#guild/detail/{:}) ▫️ **{:,}**".format(self.bot.matchtracker['names'][1], self.bot.matchtracker['id'], self.bot.matchtracker['scores'][1])
                if self.bot.matchtracker['speed'] is not None:
                    if self.bot.matchtracker['speed'][1] == self.bot.matchtracker['top_speed'][1]:
                        msg += "\n**Speed** ▫️ **Now {}/m** ▫️ **Top {}/m**".format(self.honorFormat(self.bot.matchtracker['speed'][1]), self.honorFormat(self.bot.matchtracker['top_speed'][1]))
                    else:
                        msg += "\n**Speed** ▫️ Now {}/m ▫️ Top {}/m".format(self.honorFormat(self.bot.matchtracker['speed'][1]), self.honorFormat(self.bot.matchtracker['top_speed'][1]))
                    if end_time > self.bot.matchtracker['last']:
                        msg += "\n**Estimation** ▫ Now {} ▫️ Top {}".format(self.honorFormat(self.bot.matchtracker['scores'][1] + self.bot.matchtracker['speed'][1] * remaining.seconds//60), self.honorFormat(self.bot.matchtracker['scores'][1] + self.bot.matchtracker['top_speed'][1] * remaining.seconds//60))
                msg += "\n\n"
                lead = abs(self.bot.matchtracker['scores'][0] - self.bot.matchtracker['scores'][1])
                if lead >= 0:
                    msg += "**Difference** ▫️ {:,}\n".format(lead)

                final_msg = await ctx.reply(embed=self.bot.buildEmbed(title="{} **Guild War {} ▫️ Day {}**".format(self.bot.getEmote('gw'), self.bot.matchtracker['gwid'], self.bot.matchtracker['day']-1), description=msg, timestamp=datetime.utcnow(), thumbnail=self.bot.matchtracker.get('chart', None), color=self.color))
                await self.bot.cleanMessage(ctx, final_msg, 90)

    def scrapProcess(self): # thread for ranking
        while len(self.scrap_qi) > 0: # until the input queue is empty
            if self.bot.exit_flag or self.stoprankupdate: return 
            with self.scraplockIn:
                try:
                    page = self.scrap_qi.pop() # retrieve the page number
                except:
                    continue
            data = None
            while data is None:
                data = self.getRanking(page, self.scrap_mode) # request the page
                if (self.bot.maintenance['state'] and self.bot.maintenance["duration"] == 0) or self.stoprankupdate: return
            for item in data['list']: # put the entries in the list
                with self.scraplockOut:
                    self.scrap_qo.append(item)

    def gwdbbuilder(self):
        try:
            day = self.getCurrentGWDayID() # calculate which day it is (0 being prelim, 1 being interlude/day 1, etc...)
            if day is None or day >= 10:
                self.stoprankupdate = True # send the stop signal
                return "Invalid day"
            if day > 0: day -= 1 # interlude is put into prelims

            conn = sqlite3.connect('temp.sql', isolation_level=None) # open temp.sql
            c = conn.cursor()
            c.execute("BEGIN")

            c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'") # create info table (contains gw id and db version)
            if c.fetchone()[0] < 1:
                 c.execute('CREATE TABLE info (gw int, ver int)')
                 c.execute('INSERT INTO info VALUES ({}, 2)'.format(self.bot.gw['id'])) # ver 2

            if self.scrap_mode: # crew table creation (IF it doesn't exist)
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='crews'")
                if c.fetchone()[0] < 1:
                    c.execute('CREATE TABLE crews (ranking int, id int, name text, preliminaries int, total_1 int, total_2 int, total_3 int, total_4 int)')
            else: # player table creation (delete an existing one, we want the file to keep a small size)
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='players'")
                if c.fetchone()[0] == 1:
                    c.execute('DROP TABLE players')
                c.execute('CREATE TABLE players (ranking int, id int, name text, current_total int)')
            i = 0
            while i < self.scrap_count: # count is the number of entries to process
                if self.bot.exit_flag or self.bot.maintenance['state'] or self.stoprankupdate or (self.bot.getJST() - self.scrap_update_time > timedelta(seconds=1150)): # stop if the bot is stopping
                    self.stoprankupdate = True # send the stop signal
                    try:
                        c.execute("commit")
                        conn.close()
                    except:
                        pass
                    return "Forced stop"
                try: 
                    with self.scraplockOut:
                        item = self.scrap_qo.pop() # retrieve an item
                except:
                    continue # skip if error or no item in the queue

                if self.scrap_mode: # if crew, update the existing crew (if it exists) or create a new entry
                    c.execute("SELECT count(*) FROM crews WHERE id = {}".format(int(item['id'])))
                    if c.fetchone()[0] != 0:
                        c.execute("UPDATE crews SET ranking = {}, name = '{}', {} = {} WHERE id = {}".format(int(item['ranking']), item['name'].replace("'", "''"), {0:'preliminaries',1:'total_1',2:'total_2',3:'total_3',4:'total_4'}.get(day, 'undef'), int(item['point']), int(item['id'])))
                    else:
                        honor = {day: int(item['point'])}
                        c.execute("INSERT INTO crews VALUES ({},{},'{}',{},{},{},{},{})".format(int(item['ranking']), int(item['id']), item['name'].replace("'", "''"), honor.get(0, 'NULL'), honor.get(1, 'NULL'), honor.get(2, 'NULL'), honor.get(3, 'NULL'), honor.get(4, 'NULL')))
                else: # if player, just add to the table
                    c.execute("INSERT INTO players VALUES ({},{},'{}',{})".format(int(item['rank']), int(item['user_id']), item['name'].replace("'", "''"), int(item['point'])))
                i += 1
                if i == self.scrap_count: # if we reached the end, commit
                    c.execute("COMMIT")
                    conn.close()
                elif i % 1000 == 0:
                    c.execute("COMMIT")
                    c.execute("BEGIN") # start next one
            
            self.scrap_qi = None
            self.scrap_qo = None
            
            return ""
        except Exception as err:
            self.stoprankupdate = True # send the stop signal if a critical error happened
            return 'gwdbbuilder() exception:\n' + str(err)

    async def gwscrap(self, update_time):
        try:
            self.bot.drive.delFiles(["temp.sql"], self.bot.tokens['files']) # delete previous temp file (if any)
            self.bot.delFile('temp.sql') # locally too
            if self.bot.drive.cpyFile("GW.sql", self.bot.tokens['files'], "temp.sql"): # copy existing gw.sql to temp.sql
                if not self.bot.drive.dlFile("temp.sql", self.bot.tokens['files']): # retrieve it
                    return "Failed to retrieve copied GW.sql"
                conn = sqlite3.connect('temp.sql') # open
                c = conn.cursor()
                try:
                    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'") # check info table
                    if c.fetchone()[0] < 1:
                        raise Exception() # not found, old version
                    else:
                        c.execute("SELECT * FROM info") # retrieve version and gw id
                        for row in c.fetchall():
                            gw = int(row[0])
                            ver = int(row[1])
                            break
                        if gw != self.bot.gw['id'] or ver != 2: raise Exception()
                except:
                    self.bot.delFile('temp.sql')
                conn.close()

            state = "" # return value
            max_thread = 99
            self.scrap_update_time = update_time
            for n in [0, 1]: # n == 0 (crews) or 1 (players)
                current_time = self.bot.getJST()
                if n == 0 and current_time >= self.bot.gw['dates']["Interlude"] and current_time < self.bot.gw['dates']["Day 1"]:
                    continue # disabled during interlude for crews

                self.scrap_mode = (n == 0)

                data = self.getRanking(1, self.scrap_mode) # get the first page
                if data is None or data['count'] == False:
                    return "gwscrap() can't access the ranking"
                self.scrap_count = int(data['count']) # number of crews/players
                last = data['last'] # number of pages

                self.scrap_qi = [] # input queue (contains id of each page not processed yet)
                for i in range(2, last+1): # queue the pages to retrieve
                    self.scrap_qi.append(i)
                self.scrap_qo = [] # output queue (contains json-data for each crew/player not processed yet)
                for item in data['list']: # queue what we already retrieved on the first page
                    self.scrap_qo.append(item)
                self.stoprankupdate = False # if true, this flag will stop the threads
                # run in threads
                coros = [self.request_async(self.scrap_executor, self.scrapProcess) for _i in range(self.scrap_max_thread)]
                coros.append(self.request_async(self.scrap_executor, self.gwdbbuilder))
                results = await asyncio.gather(*coros)
                for r in results:
                    if r is not None: state = r
                
                self.stoprankupdate = True # to be safe
                if state != "":
                    return state
                    
                if self.scrap_mode: # update tracker
                    try:
                        await self.updateYouTracker(update_time)
                    except Exception as ue:
                        await self.bot.sendError('updateyoutracker', str(ue))

            return ""
        except Exception as e:
            self.stoprankupdate = True
            return "Exception: " + str(e)