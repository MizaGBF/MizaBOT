import disnake
import threading
import concurrent.futures
import asyncio
from PIL import Image, ImageFont, ImageDraw
from datetime import timedelta, datetime
import time
import sqlite3
import random
import math
from io import BytesIO

# ----------------------------------------------------------------------------------------------------------------
# Ranking Component
# ----------------------------------------------------------------------------------------------------------------
# Manage the Unite and Fight rankings (access, DB update, etc...)
# Provide Score instances when searching the ranking
# ----------------------------------------------------------------------------------------------------------------

class Score():
    def __init__(self, type=None, ver=None, gw=None):
        self.type = type
        self.ver = ver
        self.gw = gw
        self.ranking = None
        self.id = None
        self.name = None
        self.current = None
        self.current_day = None
        self.day = None
        self.preliminaries = None
        self.day1 = None
        self.total1 = None
        self.day2 = None
        self.total2 = None
        self.day3 = None
        self.total3 = None
        self.day4 = None
        self.total4 = None
        self.speed = None

class Ranking():
    def __init__(self, bot):
        self.bot = bot
        # stuff related to retrieving the ranking
        self.getranklockIn = threading.Lock()
        self.getranklockOut = threading.Lock()
        self.getrank_mode = False
        self.getrank_qi = None
        self.getrank_qo = None
        self.getrank_count = 0
        self.getrank_update_time = None
        self.getrank_max_thread = 79
        self.getrank_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.getrank_max_thread+1)
        self.loadinggacha = False
        self.ranking_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.rankingtargets = []
        self.rankingtempdata = []
        self.rankinglock = threading.Lock()
        self.stoprankupdate = False
        # gw databases
        self.dbstate = [True, True] # indicate if dbs are available on the drive, True by default
        self.dblock = threading.Lock()

    def init(self):
        pass

    """requestRanking()
    Request a page from the GW ranking
    
    Parameters
    ----------
    page: Requested page
    mode: 0=crew ranking, 1=prelim crew ranking, 2=player ranking
    timeout: if True, the request will have a timeout of 20 seconds
    
    Returns
    --------
    dict: JSON data
    """
    def requestRanking(self, page, mode = 0): # get gw ranking data
        if self.bot.data.save['gw']['state'] == False or self.bot.util.JST() <= self.bot.data.save['gw']['dates']["Preliminaries"]:
            return None
        match mode:
            case 0: # crew
                res = self.bot.gbf.request("https://game.granbluefantasy.jp/teamraid{}/rest/ranking/totalguild/detail/{}/0?PARAMS".format(str(self.bot.data.save['gw']['id']).zfill(3), page), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)
            case 1: # prelim crew
                res = self.bot.gbf.request("https://game.granbluefantasy.jp/teamraid{}/rest/ranking/guild/detail/{}/0?PARAMS".format(str(self.bot.data.save['gw']['id']).zfill(3), page), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)
            case 2: # player
                res = self.bot.gbf.request("https://game.granbluefantasy.jp/teamraid{}/rest_ranking_user/detail/{}/0?PARAMS".format(str(self.bot.data.save['gw']['id']).zfill(3), page), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)
        return res

    """updateRankingThread()
    Thread to update the cutoff data
    """
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
                            if diff > 0 and self.bot.data.save['gw']['ranking'] is not None and str(rank) in self.bot.data.save['gw']['ranking'][0]:
                                self.rankingtempdata[2][str(rank)] = (self.rankingtempdata[0][str(rank)] - self.bot.data.save['gw']['ranking'][0][str(rank)]) / diff
                else:
                    r = self.requestRanking(rank // 10, 2)
                    if r is not None and 'list' in r and len(r['list']) > 0:
                        with self.rankinglock:
                            self.rankingtempdata[1][str(rank)] = int(r['list'][-1]['point'])
                            if diff > 0 and self.bot.data.save['gw']['ranking'] is not None and str(rank) in self.bot.data.save['gw']['ranking'][1]:
                                self.rankingtempdata[3][str(rank)] = (self.rankingtempdata[1][str(rank)] - self.bot.data.save['gw']['ranking'][1][str(rank)]) / diff
                if r is None:
                    errc += 1
                    time.sleep(0.1)
        except:
            pass

    """request_async()
    Similar to the bot do() function except you can specify the executor
    
    Parameters
    ----------
    executor: Executor to use
    func: Callback
    
    Returns
    --------
    callback return value
    """
    async def request_async(self, executor, func):
        return await self.bot.loop.run_in_executor(executor, func)

    """checkGWRanking()
    Bot task to update the ranking data. Only needed once every 20 minutes
    """
    async def checkGWRanking(self):
        cog = self.bot.get_cog('GuildWar')
        if cog is None:
            return
        crewsA = [300, 1000, 2000, 8000, 19000, 36000]
        crewsB = [2000, 5500, 9000, 14000, 18000, 30000]
        players = [2000, 80000, 140000, 180000, 270000, 370000]

        while True:
            cog.getGWState()
            try:
                if self.bot.data.save['gw']['state'] == False:
                    if 'ranking' not in self.bot.data.save['gw'] or self.bot.data.save['gw']['ranking'] is not None:
                        with self.bot.data.lock:
                            self.bot.data.save['gw']['ranking'] = None
                            self.bot.data.pending = True
                    return
                elif self.bot.util.JST() < self.bot.data.save['gw']['dates']["Preliminaries"]:
                    if 'ranking' not in self.bot.data.save['gw'] or self.bot.data.save['gw']['ranking'] is not None:
                        with self.bot.data.lock:
                            self.bot.data.save['gw']['ranking'] = None
                            self.bot.data.pending = True
                    d = self.bot.data.save['gw']['dates']["Preliminaries"] - self.bot.util.JST()
                    if d >= timedelta(days=1): return
                    await asyncio.sleep(d.seconds + 1)
                elif self.bot.util.JST() > self.bot.data.save['gw']['dates']["Day 5"] - timedelta(seconds=21600):
                    await asyncio.sleep(3600)
                else:
                    if await self.bot.do(self.bot.gbf.isAvailable):
                        current_time = self.bot.util.JST()
                        m = current_time.minute
                        h = current_time.hour
                        skip = False
                        for d in ["End", "Day 5", "Day 4", "Day 3", "Day 2", "Day 1", "Interlude", "Preliminaries"]:
                            if current_time < self.bot.data.save['gw']['dates'][d]:
                                continue
                            if d == "Preliminaries":
                                diff = current_time - self.bot.data.save['gw']['dates'][d]
                                if diff.days == 1 and diff.seconds >= 25200:
                                    skip = True
                            elif ((d.startswith("Day") and h < 7 and h >= 2) or d == "Day 5"):
                                skip = True
                            break
                        if skip:
                            await asyncio.sleep(600)
                        elif m in [3, 4, 23, 24, 43, 44]: # minute to update
                            if d.startswith("Day "):
                                crews = crewsB
                                mode = 0
                            else:
                                crews = crewsA
                                mode = 1
                            # update $ranking and $estimation
                            try:
                                update_time = current_time.replace(minute=20 * (current_time.minute // 20), second=1, microsecond=0) # ranking are updated around minute 2
                                self.rankingtempdata = [{}, {}, {}, {}, update_time]
                                if self.bot.data.save['gw']['ranking'] is not None:
                                    diff = self.rankingtempdata[4] - self.bot.data.save['gw']['ranking'][4]
                                    diff = round(diff.total_seconds() / 60.0)
                                else: diff = 0
                                self.rankingtargets = []
                                for c in crews:
                                    self.rankingtargets.append([diff, True, mode, c])
                                for p in players:
                                    self.rankingtargets.append([diff, False, 2, p])
                                n_thread = len(self.rankingtargets)
                                
                                coros = [self.request_async(self.ranking_executor, self.updateRankingThread) for _i in range(n_thread)]
                                await asyncio.gather(*coros)

                                for i in range(0, 4):
                                    self.rankingtempdata[i] = dict(sorted(self.rankingtempdata[i].items(), reverse=True, key=lambda item: int(item[1])))

                                if len(self.rankingtempdata[0]) + len(self.rankingtempdata[1]) > 0: # only update if we got data (NOTE: check how it affects estimations)
                                    with self.bot.data.lock: 
                                        self.bot.data.save['gw']['ranking'] = self.rankingtempdata
                                        self.bot.data.pending = True
                            except Exception as ex:
                                await self.bot.sendError('checkgwranking sub', ex)
                                with self.bot.data.lock:
                                    self.bot.data.save['gw']['ranking'] = None
                                    self.bot.data.pending = True

                            await self.retrieve_ranking(update_time)
                            await asyncio.sleep(100)
                        else:
                            await asyncio.sleep(25)
                    else:
                        await asyncio.sleep(60)
            except asyncio.CancelledError:
                await self.bot.sendError('checkgwranking', 'cancelled')
                await asyncio.sleep(30)
            except Exception as e:
                await self.bot.sendError('checkgwranking', e)
                return

    """retrieve_ranking()
    Coroutine to start the ranking retrieval process
    
    Parameters
    --------
    update_time: Datetime, current time period of 20min
    force: True to force regardless of time and day (only for debug/test purpose)
    """
    async def retrieve_ranking(self, update_time, force=False):
        getrankout = await self.gwgetrank(update_time, force)
        if getrankout == "":
            data = await self.bot.do(self.GWDBver)
            with self.dblock:
                if data is not None and data[1] is not None:
                    if self.bot.data.save['gw']['id'] != data[1]['gw']: # different gw, we move
                        if data[0] is not None: # backup old gw if it exists
                            self.bot.drive.mvFile("GW_old.sql", self.bot.data.config['tokens']['files'], "GW{}_backup.sql".format(data[0]['gw']))
                        self.bot.drive.mvFile("GW.sql", self.bot.data.config['tokens']['files'], "GW_old.sql")
                        self.bot.file.mv("GW.sql", "GW_old.sql")
                if not self.bot.drive.overwriteFile("temp.sql", "application/sql", "GW.sql", self.bot.data.config['tokens']['files']): # upload
                    await self.bot.sendError('gwgetrank', 'Upload failed')
                self.bot.file.mv('temp.sql', "GW.sql")
                self.dbstate = [False, False]
                fs = ["GW_old.sql", "GW.sql"]
                for i in [0, 1]:
                    self.bot.sql.remove(fs[i])
                    if self.bot.file.exist(fs[i]):
                        self.bot.sql.add(fs[i])
                        self.dbstate[i] = True
        elif getrankout != "Invalid day" and getrankout != "Skipped":
            await self.bot.sendError('gwgetrank', 'Failed\n' + getrankout)

    """getrankProcess()
    Thread to retrieve mass data from the ranking
    """
    def getrankProcess(self): # thread for ranking
        while len(self.getrank_qi) > 0: # until the input queue is empty
            if not self.bot.running or self.stoprankupdate: return 
            with self.getranklockIn:
                try:
                    page = self.getrank_qi.pop() # retrieve the page number
                except:
                    continue
            data = None
            while data is None:
                data = self.requestRanking(page, (0 if self.getrank_mode else 2)) # request the page
                if (self.bot.data.save['maintenance']['state'] and self.bot.data.save['maintenance']["duration"] == 0) or self.stoprankupdate: return
            for item in data['list']: # put the entries in the list
                with self.getranklockOut:
                    self.getrank_qo.append(item)

    """getCurrentGWDayID()
    Associate the current GW day to an integer and return it
    
    Returns
    --------
    int:
        0=prelims, 1=interlude, 2=day 1, 3=day 2, 4=day 3, 5=day 4
        10 to 15: same as above but during the break period
        25: Final rally or end
        None: Undefined
    """
    def getCurrentGWDayID(self):
        if self.bot.data.save['gw']['state'] == False: return None
        current_time = self.bot.util.JST()
        if current_time < self.bot.data.save['gw']['dates']["Preliminaries"]:
            return None
        elif current_time >= self.bot.data.save['gw']['dates']["End"]:
            return 25
        elif current_time >= self.bot.data.save['gw']['dates']["Day 5"]:
            return 25
        elif current_time >= self.bot.data.save['gw']['dates']["Day 1"]:
            it = ['Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
            for i in range(1, len(it)): # loop to not copy paste this 5 more times
                if current_time >= self.bot.data.save['gw']['dates'][it[i]]:
                    d = self.bot.data.save['gw']['dates'][it[i-1]] - current_time
                    if d < timedelta(seconds=18000): return 16 - i
                    else: return 6 - i
        elif current_time > self.bot.data.save['gw']['dates']["Interlude"]:
            return 1
        elif current_time > self.bot.data.save['gw']['dates']["Preliminaries"]:
            d = self.bot.data.save['gw']['dates']['Interlude'] - current_time
            if d < timedelta(seconds=18000): return 10
            else: return 0
        else:
            return None

    """gwdbbuilder()
    Thread to build the GW database from getrankProcess output
    """
    def gwdbbuilder(self):
        try:
            day = self.getCurrentGWDayID() # calculate which day it is (0 being prelim, 1 being interlude, 2 = day 1, etc...)
            if day is None or day >= 10:
                self.stoprankupdate = True # send the stop signal
                return "Invalid day"
            if day > 0: day -= 1 # interlude is put into prelims

            conn = sqlite3.connect('temp.sql', isolation_level=None) # open temp.sql
            c = conn.cursor()
            c.execute("BEGIN")
            diff = None
            timestamp = None
            new_timestamp = int(self.getrank_update_time.timestamp())

            c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'") # create info table if it doesn't exist (contains gw id and db version)
            if c.fetchone()[0] < 1:
                 c.execute('CREATE TABLE info (gw int, ver int, date int)')
                 c.execute('INSERT INTO info VALUES ({}, 3, {})'.format(self.bot.data.save['gw']['id'], new_timestamp)) # ver 3
            else:
                c.execute("SELECT * FROM info")
                x = c.fetchone()
                timestamp = x[2]
                diff = self.getrank_update_time - datetime.fromtimestamp(timestamp)
                diff = diff.seconds / 60
                c.execute("UPDATE info SET date = {} WHERE ver = 3".format(new_timestamp))

            if self.getrank_mode: # crew table creation (IF it doesn't exist)
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='crews'")
                if c.fetchone()[0] < 1:
                    c.execute('CREATE TABLE crews (ranking int, id int, name text, preliminaries int, total_1 int, total_2 int, total_3 int, total_4 int, speed float, last_time int)')
            else: # player table creation (delete an existing one, we want the file to keep a small size)
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='players'")
                if c.fetchone()[0] == 1:
                    c.execute('DROP TABLE players')
                c.execute('CREATE TABLE players (ranking int, id int, name text, current_total int)')
            i = 0
            while i < self.getrank_count: # count is the number of entries to process
                if not self.bot.running or self.bot.data.save['maintenance']['state'] or self.stoprankupdate or (self.bot.util.JST() - self.getrank_update_time > timedelta(seconds=1000)): # stop if the bot is stopping
                    self.stoprankupdate = True # send the stop signal
                    try:
                        c.execute("commit")
                        conn.close()
                    except:
                        pass
                    return "Forced stop\nMode: {}\nCount: {}/{}".format(self.getrank_mode, i, self.getrank_count)
                try: 
                    with self.getranklockOut:
                        item = self.getrank_qo.pop() # retrieve an item
                except:
                    time.sleep(0.1)
                    continue # skip if error or no item in the queue

                if self.getrank_mode: # if crew, update the existing crew (if it exists) or create a new entry
                    c.execute("SELECT * FROM crews WHERE id = {}".format(int(item['id'])))
                    x = c.fetchone()
                    if x is not None:
                        last_val = x[3+day]
                        last_update = x[9]
                        if diff is None or last_val is None or last_val == int(item['point']) or last_update != timestamp or new_timestamp == timestamp:
                            c.execute("UPDATE crews SET ranking = {}, name = '{}', {} = {}, last_time = {} WHERE id = {}".format(int(item['ranking']), item['name'].replace("'", "''"), {0:'preliminaries',1:'total_1',2:'total_2',3:'total_3',4:'total_4'}.get(day, 'undef'), int(item['point']), new_timestamp, int(item['id'])))
                        else:
                            speed = (int(item['point']) - last_val) / diff
                            c.execute("UPDATE crews SET ranking = {}, name = '{}', {} = {}, speed = {}, last_time = {} WHERE id = {}".format(int(item['ranking']), item['name'].replace("'", "''"), {0:'preliminaries',1:'total_1',2:'total_2',3:'total_3',4:'total_4'}.get(day, 'undef'), int(item['point']), (speed if (x[8] is None or speed > x[8]) else x[8]), new_timestamp, int(item['id'])))
                    else:
                        honor = {day: int(item['point'])}
                        c.execute("INSERT INTO crews VALUES ({},{},'{}',{},{},{},{},{},{},{})".format(int(item['ranking']), int(item['id']), item['name'].replace("'", "''"), honor.get(0, 'NULL'), honor.get(1, 'NULL'), honor.get(2, 'NULL'), honor.get(3, 'NULL'), honor.get(4, 'NULL'), 'NULL', new_timestamp))
                else: # if player, just add to the table
                    c.execute("INSERT INTO players VALUES ({},{},'{}',{})".format(int(item['rank']), int(item['user_id']), item['name'].replace("'", "''"), int(item['point'])))
                i += 1
                if i == self.getrank_count: # if we reached the end, commit
                    c.execute("COMMIT")
                    conn.close()
                elif i % 1000 == 0:
                    c.execute("COMMIT")
                    c.execute("BEGIN") # start next one
            
            self.getrank_qi = None
            self.getrank_qo = None
            
            return ""
        except Exception as err:
            try:
                c.close()
                conn.close()
            except:
                pass
            self.stoprankupdate = True # send the stop signal if a critical error happened
            return 'gwdbbuilder() exception:\n' + self.bot.util.pexc(err)

    """gwgetrank()
    Setup and manage the multithreading to retrieve the ranking
    
    Parameters
    ----------
    update_time: time of this ranking interval
    force: True to force the retrieval (debug only)
    
    Returns
    --------
    str: empty string if success, error message if not
    """
    async def gwgetrank(self, update_time, force):
        try:
            state = "" # return value
            self.getrank_update_time = update_time
            it = ['Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1', 'Interlude', 'Preliminaries']
            skip_mode = 0
            for i, itd in enumerate(it): # loop to not copy paste this 5 more times
                if update_time > self.bot.data.save['gw']['dates'][itd]:
                    match itd:
                        case 'Preliminaries':
                            if update_time - self.bot.data.save['gw']['dates'][itd] < timedelta(days=0, seconds=3600): # first hour of gw
                                skip_mode = 1 # skip all
                            elif self.bot.data.save['gw']['dates'][it[i-1]] - update_time < timedelta(days=0, seconds=18800):
                                skip_mode = 1 # skip all
                        case 'Interlude':
                            if update_time.minute > 10: # only update players hourly
                                skip_mode = 1 # skip all
                            else:
                                skip_mode = 2 # skip crew
                        case 'Day 5':
                            skip_mode = 1 # skip all
                        case _:
                            if update_time - self.bot.data.save['gw']['dates'][itd] < timedelta(days=0, seconds=7200): # skip players at the start of rounds
                                skip_mode = 3 # skip player
                            elif self.bot.data.save['gw']['dates'][it[i-1]] - update_time < timedelta(days=0, seconds=18800): # skip during break
                                skip_mode = 1 # skip all
                    break
            if force: skip_mode = 0
            if skip_mode == 1: return 'Skipped'
        
            self.bot.drive.delFiles(["temp.sql"], self.bot.data.config['tokens']['files']) # delete previous temp file (if any)
            self.bot.file.rm('temp.sql') # locally too
            if self.bot.drive.cpyFile("GW.sql", self.bot.data.config['tokens']['files'], "temp.sql"): # copy existing gw.sql to temp.sql
                if not self.bot.drive.dlFile("temp.sql", self.bot.data.config['tokens']['files']): # retrieve it
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
                        if gw != self.bot.data.save['gw']['id'] or ver != 3: raise Exception()
                    c.close()
                    conn.close()
                except:
                    c.close()
                    conn.close()
                    self.bot.file.rm('temp.sql')

            for n in [0, 1]: # n == 0 (crews) or 1 (players)
                if skip_mode == 2 and n == 0: continue
                elif skip_mode == 3 and n == 1: continue

                self.getrank_mode = (n == 0)
                data = self.requestRanking(1, (0 if self.getrank_mode else 2)) # get the first page
                if data is None or data['count'] == False:
                    return "gwgetrank() can't access the ranking"
                self.getrank_count = int(data['count']) # number of crews/players
                last = data['last'] # number of pages

                self.getrank_qi = [] # input queue (contains id of each page not processed yet)
                for i in range(2, last+1): # queue the pages to retrieve
                    self.getrank_qi.append(i)
                self.getrank_qo = [] # output queue (contains json-data for each crew/player not processed yet)
                for item in data['list']: # queue what we already retrieved on the first page
                    self.getrank_qo.append(item)
                self.stoprankupdate = False # if true, this flag will stop the threads
                # run in threads
                coros = [self.request_async(self.getrank_executor, self.getrankProcess) for _i in range(self.getrank_max_thread)]
                coros.append(self.request_async(self.getrank_executor, self.gwdbbuilder))
                results = await asyncio.gather(*coros)
                for r in results:
                    if r is not None: state = r
                
                self.stoprankupdate = True # to be safe
                if state != "":
                    return state
                    
                if self.getrank_mode: # update tracker
                    try:
                        await self.updateTracker(update_time)
                    except Exception as ue:
                        await self.bot.sendError('updatetracker', ue)

            return ""
        except Exception as e:
            self.stoprankupdate = True
            return "Exception: " + self.bot.util.pexc(e)

    """searchScoreForTracker()
    Search the targeted crews for the YouTracker in the database being built
    
    Parameters
    ----------
    crews: List of crew IDs
    
    Returns
    --------
    list: Crew informations
    """
    def searchScoreForTracker(self, day, crews):
        infos = []
        conn = sqlite3.connect('temp.sql') # open temp.sql
        c = conn.cursor()
        for sid in crews:
            c.execute("SELECT * FROM crews WHERE id = {}".format(sid)) # get the score
            data = c.fetchall()
            if data is None or len(data) == 0: raise Exception("Failed to retrieve data")
            d = [4, 5, 6, 7]
            infos.append([data[0][2], data[0][d[day-2]]-data[0][d[day-2]-1], data[0][8]]) # name, score of the day, top speed
        c.close()
        conn.close()
        return infos

    """drawChart()
    Draw the YouTracker chart (GW Match tracker for my crew)
    
    Parameters
    ----------
    plot: list of points, format: [datetime, float, float]
    
    Raises
    ------
    Exception: If an error occurs
    
    Returns
    ----------
    str: filename of the image, None if error
    """
    def drawChart(self, plot):
        if len(plot) == 0: return None
        img = Image.new("RGB", (800, 600), (255,255,255))
        d = ImageDraw.Draw(img)
        font = ImageFont.truetype("assets/font.ttf", 14)
        
        # y grid lines
        for i in range(0, 4):
            d.line([(50, 50+125*i), (750, 50+125*i)], fill=(200, 200, 200), width=1)
        # x grid lines
        for i in range(0, 10):
            d.line([(120+70*i, 50), (120+70*i, 550)], fill=(200, 200, 200), width=1)
        # legend
        d.text((10, 10),"Speed (M/min)",font=font,fill=(0,0,0))
        d.line([(150, 15), (170, 15)], fill=(0, 0, 255), width=2)
        d.text((180, 10),"You",font=font,fill=(0,0,0))
        d.line([(220, 15), (240, 15)], fill=(255, 0, 0), width=2)
        d.text((250, 10),"Opponent",font=font,fill=(0,0,0))
        d.text((720, 580),"Time (JST)",font=font,fill=(0,0,0))
        
        # y notes
        miny = 999
        maxy = 0
        for p in plot:
            miny = math.floor(min(miny, p[1], p[2]))
            maxy = math.ceil(max(maxy, p[1], p[2]))
        deltay= maxy - miny
        if deltay <= 0: return None
        tvar = maxy
        for i in range(0, 5):
            d.text((10, 40+125*i),"{:.2f}".format(float(tvar)).replace('.00', '').replace('.10', '.1').replace('.20', '.2').replace('.30', '.3').replace('.40', '.4').replace('.50', '.5').replace('.60', '.6').replace('.70', '.7').replace('.80', '.8').replace('.90', '.9').replace('.0', '').rjust(6),font=font,fill=(0,0,0))
            tvar -= deltay / 4
        # x notes
        minx = plot[0][0]
        maxx = plot[-1][0]
        deltax = maxx - minx
        deltax = (deltax.seconds + deltax.days * 86400)
        if deltax <= 0: return None
        tvar = minx
        for i in range(0, 11):
            d.text((35+70*i, 560),"{:02d}:{:02d}".format(tvar.hour, tvar.minute),font=font,fill=(0,0,0))
            tvar += timedelta(seconds=deltax/10)

        # lines
        lines = [[], []]
        for p in plot:
            x = p[0] - minx
            x = (x.seconds + x.days * 86400)
            x = 50 + 700 * (x / deltax)
            y = maxy - p[1]
            y = 50 + 500 * (y / deltay)
            lines[0].append((x, y))
            y = maxy - p[2]
            y = 50 + 500 * (y / deltay)
            lines[1].append((x, y))

        # plot lines
        d.line([(50, 50), (50, 550), (750, 550)], fill=(0, 0, 0), width=1)
        d.line(lines[0], fill=(0, 0, 255), width=2, joint="curve")
        d.line(lines[1], fill=(255, 0, 0), width=2, joint="curve")

        with BytesIO() as output:
            img.save(output, format="PNG")
            img.close()
            return output.getvalue()

    """updateTracker()
    Update the YouTracker data (GW Match tracker for my crew)
    
    Parameters
    ----------
    t: time of this ranking interval
    """
    async def updateTracker(self, t):
        day = self.getCurrentGWDayID()
        if day is None or day <= 1 or day >= 10: # check if match day
            return
        you_id = self.bot.data.config['granblue']['gbfgcrew'].get('you', None) # our id
        
        if you_id is None: return
        if self.bot.data.save['matchtracker'] is None: return # not initialized
        if self.bot.data.save['matchtracker']['day'] != day: # new day, reset
            with self.bot.data.lock:
                self.bot.data.save['matchtracker'] = {
                    'day':day,
                    'init':False,
                    'id':self.bot.data.save['matchtracker']['id'],
                    'plot':[]
                }
                self.bot.data.pending = True
            
        infos = await self.bot.do(self.searchScoreForTracker, day, [you_id, self.bot.data.save['matchtracker']['id']])
        newtracker = self.bot.data.save['matchtracker'].copy()
        if newtracker['init']:
            d = t - newtracker['last']
            speed = d.seconds//60
            # rounding to multiple of 20min
            if speed % 20 > 15:
                speed += 20 - (speed % 20)
            elif speed % 20 < 5:
                speed -= (speed % 20)
            # applying
            speed = [(infos[0][1] - newtracker['scores'][0]) / speed, (infos[1][1] - newtracker['scores'][1]) / speed]
            if speed[0] > newtracker['top_speed'][0]: newtracker['top_speed'][0] = speed[0]
            if speed[1] > newtracker['top_speed'][1]: newtracker['top_speed'][1] = speed[1]
            newtracker['speed'] = speed
        else:
            newtracker['init'] = True
            newtracker['speed'] = None
            newtracker['top_speed'] = [0, 0]
        newtracker['names'] = [infos[0][0], infos[1][0]]
        newtracker['scores'] = [infos[0][1], infos[1][1]]
        newtracker['max_speed'] = [infos[0][2], infos[1][2]]
        newtracker['last'] = t
        newtracker['gwid'] = self.bot.data.save['gw']['id']
        if newtracker['speed'] is not None: # save chart data
            newtracker['plot'].append([t, newtracker['speed'][0] / 1000000, newtracker['speed'][1] / 1000000])
        if len(newtracker['plot']) > 1: # generate chart
            try:
                imgdata = self.drawChart(newtracker['plot'])
                with BytesIO(imgdata) as f:
                    df = disnake.File(f, filename="chart.png")
                    message = await self.bot.send('image', file=df)
                    df.close()
                    newtracker['chart'] = message.attachments[0].url
            except Exception as e:
                await self.bot.sendError('updatetracker', e)
        with self.bot.data.lock:
            self.bot.data.save['matchtracker'] = newtracker
            self.bot.data.pending = True

    """loadGWDB()
    Load the Unite & fight ranking databases
    
    Parameters
    ----------
    ids: list of databases to load (0 = old one, 1 = current one)
    """
    def loadGWDB(self, ids = [0, 1]):
        fs = ["GW_old.sql", "GW.sql"]
        for i in ids:
            try:
                self.dbstate[i] = False
                self.bot.sql.remove(fs[i])
                if self.bot.drive.dlFile(fs[i], self.bot.data.config['tokens']['files']):
                    self.bot.sql.add(fs[i])
                    self.dbstate[i] = True
            except:
                print("Failed to load database", fs[i])
                self.bot.errn += 1

    """reloadGWDB()
    Reload the Unite & fight ranking databases
    """
    def reloadGWDB(self):
        with self.dblock:
            self.dbstate = [True, True]
            self.loadGWDB()

    """GWDBver()
    Return the Unite & fight ranking database infos
    
    Returns
    --------
    list: First element is for the old database, second is for the current one
    """
    def GWDBver(self):
        fs = ["GW_old.sql", "GW.sql"]
        res = [None, None]
        for i in [0, 1]:
            with self.dblock:
                db = self.bot.sql.get(fs[i])
                if db is None:
                    if not self.dbstate[i]: continue
                    self.loadGWDB([i])
                    db = self.bot.sql.get(fs[i])
                    if db is None:
                        continue
            c = db.open()
            if c is None: continue
            try:
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'")
                if c.fetchone()[0] < 1:
                    c.execute("SELECT * FROM GW")
                    x = c.fetchone()
                    res[i] = {'gw':int(x[0]), 'ver':1, 'date':None}
                else:
                    c.execute("SELECT * FROM info")
                    x = c.fetchone()
                    res[i] = {'gw':int(x[0]), 'ver':int(x[1]), 'date':None}
                    if res[i]['ver'] >= 3:
                        res[i]['date'] = datetime.fromtimestamp(x[2])
            except:
                res[i] = {'ver':0}
            db.close()
        return res

    """searchGWDB()
    Search the Unite & fight ranking databases
    Returned matches are Score instances
    
    Parameters
    ----------
    terms: Search string
    mode: Search mode (0 = normal search, 1 = exact search, 2 = id search, 3 = ranking search, add 10 to search for crews instead of players)
    
    Returns
    --------
    dict: Containing:
        - list: Matches in the past GW
        - list: Matches in the latest GW
    """
    def searchGWDB(self, terms, mode):
        v = self.GWDBver() # load and get the version of the database files
        data = [None, None]
        dbs = [self.bot.sql.get("GW_old.sql"), self.bot.sql.get("GW.sql")] # get access
        cs = []
        for n in [0, 1]:
            try: cs.append(dbs[n].open()) # get a cursor for both
            except: cs.append(None)

        st = 1 if mode >= 10 else 0 # search type (crew or player)
        for n in [0, 1]: # for both database
            if cs[n] is not None and v[n] is not None: # if the data is loaded and alright
                try:
                    data[n] = []
                    c = cs[n]
                    # search according to the mode
                    if mode == 10: # crew name search
                        c.execute("SELECT * FROM crews WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 11: # crew name exact search
                        c.execute("SELECT * FROM crews WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 12: # crew id search
                        c.execute("SELECT * FROM crews WHERE id = {}".format(terms))
                    elif mode == 13: # crew ranking search
                        c.execute("SELECT * FROM crews WHERE ranking = {}".format(terms))
                    elif mode == 0: # player name search
                        c.execute("SELECT * FROM players WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 1: # player exact name search
                        c.execute("SELECT * FROM players WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 2: # player id search
                        c.execute("SELECT * FROM players WHERE id = {}".format(terms))
                    elif mode == 3: # player ranking search
                        c.execute("SELECT * FROM players WHERE ranking = {}".format(terms))
                    results = c.fetchall() # fetch the result
                    
                    for r in results:
                        s = Score(type=st, gw=v[n]['gw'], ver=v[n]['ver']) # make a Score object
                        if st == 0: # player
                            s.ranking = r[0]
                            s.id = r[1]
                            s.name = r[2]
                            s.current = r[3]
                        else: # crew
                            if s.ver >= 2: # newest database format
                                s.ranking = r[0]
                                s.id = r[1]
                                s.name = r[2]
                                s.preliminaries = r[3]
                                s.total1 = r[4]
                                s.total2 = r[5]
                                s.total3 = r[6]
                                s.total4 = r[7]
                                if s.total1 is not None and s.preliminaries is not None: s.day1 = s.total1 - s.preliminaries
                                if s.total2 is not None and s.total1 is not None: s.day2 = s.total2 - s.total1
                                if s.total3 is not None and s.total2 is not None: s.day3 = s.total3 - s.total2
                                if s.total4 is not None and s.total3 is not None: s.day4 = s.total4 - s.total3
                                if s.ver >= 3:
                                    s.speed = r[8]
                            else: # old database format
                                s.ranking = r[0]
                                s.id = r[1]
                                s.name = r[2]
                                s.preliminaries = r[3]
                                s.day1 = r[4]
                                s.total1 = r[5]
                                s.day2 = r[6]
                                s.total2 = r[7]
                                s.day3 = r[8]
                                s.total3 = r[9]
                                s.day4 = r[10]
                                s.total4 = r[11]
                            # set the current score, etc
                            if s.total4 is not None:
                                s.current = s.total4
                                s.current_day = s.day4
                                s.day = 4
                            elif s.total3 is not None:
                                s.current = s.total3
                                s.current_day = s.day3
                                s.day = 3
                            elif s.total2 is not None:
                                s.current = s.total2
                                s.current_day = s.day2
                                s.day = 2
                            elif s.total1 is not None:
                                s.current = s.total1
                                s.current_day = s.day1
                                s.day = 1
                            elif s.preliminaries is not None:
                                s.current = s.preliminaries
                                s.current_day = s.preliminaries
                                s.day = 0
                        if s.gw is None: s.gw = '' # it's supposed to be the gw id
                        data[n].append(s) # append to our list
                    random.shuffle(data[n]) # shuffle the list once it's done
                except Exception as e:
                    print('searchGWDB:', n, 'mode:', mode, 'terms:', terms, ':\n', self.bot.util.pexc(e))
                    self.bot.errn += 1
                    data[n] = None
                dbs[n].close() # close access
        return data