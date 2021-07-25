import discord
import threading
import concurrent.futures
import asyncio
from datetime import timedelta
import time
import leather
import cairosvg
import sqlite3
import random

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

class Ranking():
    def __init__(self, bot):
        self.bot = bot
        self.scraplockIn = threading.Lock()
        self.scraplockOut = threading.Lock()
        self.scrap_mode = False
        self.scrap_qi = None
        self.scrap_qo = None
        self.scrap_count = 0
        self.scrap_update_time = None
        self.scrap_max_thread = 99
        self.scrap_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.scrap_max_thread+1)
        self.loadinggacha = False
        self.ranking_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.rankingtargets = []
        self.rankingtempdata = []
        self.rankinglock = threading.Lock()
        self.stoprankupdate = False
        self.dbstate = [True, True]
        self.dblock = threading.Lock()

    def init(self):
        pass

    """requestRanking()
    Request a page from the GW ranking
    
    Parameters
    ----------
    page: Requested page
    mode: 0=crew ranking, 1=prelim crew ranking, 2=player ranking
    
    Returns
    --------
    dict: JSON data
    """
    def requestRanking(self, page, mode = 0): # get gw ranking data
        if self.bot.data.save['gw']['state'] == False or self.bot.util.JST() <= self.bot.data.save['gw']['dates']["Preliminaries"]:
            return None
        if mode == 0: # crew
            res = self.bot.gbf.request("http://game.granbluefantasy.jp/teamraid{}/rest/ranking/totalguild/detail/{}/0?=TS1&t=TS2&uid=ID".format(str(self.bot.data.save['gw']['id']).zfill(3), page), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)
        elif mode == 1: # prelim crew
            res = self.bot.gbf.request("http://game.granbluefantasy.jp/teamraid{}/rest/ranking/guild/detail/{}/0?=TS1&t=TS2&uid=ID".format(str(self.bot.data.save['gw']['id']).zfill(3), page), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)
        elif mode == 2: # player
            res = self.bot.gbf.request("http://game.granbluefantasy.jp/teamraid{}/rest_ranking_user/detail/{}/0?=TS1&t=TS2&uid=ID".format(str(self.bot.data.save['gw']['id']).zfill(3), page), account=self.bot.data.save['gbfcurrent'], decompress=True, load_json=True)
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
                                update_time = current_time - timedelta(seconds=60 * (current_time.minute % 20))
                                self.rankingtempdata = [{}, {}, {}, {}, update_time]
                                if self.bot.data.save['gw']['ranking'] is not None:
                                    diff = self.rankingtempdata[4] - self.bot.data.save['gw']['ranking'][4]
                                    diff = round(diff.total_seconds() / 60.0)
                                else: diff = 0
                                self.rankingtargets = []
                                for c in crews:
                                    self.rankingtargets.append([ diff, True, mode, c])
                                for p in players:
                                    self.rankingtargets.append([diff, False, 2, p])
                                n_thread = len(self.rankingtargets)
                                
                                coros = [self.request_async(self.ranking_executor, self.updateRankingThread) for _i in range(n_thread)]
                                await asyncio.gather(*coros)

                                for i in range(0, 4):
                                    self.rankingtempdata[i] = dict(sorted(self.rankingtempdata[i].items(), reverse=True, key=lambda item: int(item[1])))

                                with self.bot.data.lock: 
                                    self.bot.data.save['gw']['ranking'] = self.rankingtempdata
                                    self.bot.data.pending = True
                            except Exception as ex:
                                await self.bot.sendError('checkgwranking sub', ex)
                                with self.bot.data.lock:
                                    self.bot.data.save['gw']['ranking'] = None
                                    self.bot.data.pending = True

                            # update DB
                            scrapout = await self.gwscrap(update_time)
                            if scrapout == "":
                                data = await self.bot.do(self.GWDBver)
                                if data is not None and data[1] is not None:
                                    if self.bot.data.save['gw']['id'] != data[1]['gw']: # different gw, we move
                                        if data[0] is not None: # backup old gw if it exists
                                            self.bot.drive.mvFile("GW_old.sql", self.bot.data.config['tokens']['files'], "GW{}_backup.sql".format(data[0]['gw']))
                                        self.bot.drive.mvFile("GW.sql", self.bot.data.config['tokens']['files'], "GW_old.sql")
                                if not self.bot.drive.overwriteFile("temp.sql", "application/sql", "GW.sql", self.bot.data.config['tokens']['files']): # upload
                                    await self.bot.sendError('gwscrap', 'Upload failed')
                                self.bot.file.rm('temp.sql')
                                await self.bot.do(self.reloadGWDB) # reload db
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
                await self.bot.sendError('checkgwranking', e)
                return

    """scrapProcess()
    Thread to retrieve mass data from the ranking
    """
    def scrapProcess(self): # thread for ranking
        while len(self.scrap_qi) > 0: # until the input queue is empty
            if not self.bot.running or self.stoprankupdate: return 
            with self.scraplockIn:
                try:
                    page = self.scrap_qi.pop() # retrieve the page number
                except:
                    continue
            data = None
            while data is None:
                data = self.requestRanking(page, (0 if self.scrap_mode else 2)) # request the page
                if (self.bot.data.save['maintenance']['state'] and self.bot.data.save['maintenance']["duration"] == 0) or self.stoprankupdate: return
            for item in data['list']: # put the entries in the list
                with self.scraplockOut:
                    self.scrap_qo.append(item)

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
        elif current_time > self.bot.data.save['gw']['dates']["Day 5"]:
            return 25
        elif current_time > self.bot.data.save['gw']['dates']["Day 1"]:
            it = ['Day 5', 'Day 4', 'Day 3', 'Day 2', 'Day 1']
            for i in range(1, len(it)): # loop to not copy paste this 5 more times
                if current_time > self.bot.data.save['gw']['dates'][it[i]]:
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
    Thread to build the GW database from scrapProcess output
    """
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

            c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='info'") # create info table if it doesn't exist (contains gw id and db version)
            if c.fetchone()[0] < 1:
                 c.execute('CREATE TABLE info (gw int, ver int)')
                 c.execute('INSERT INTO info VALUES ({}, 2)'.format(self.bot.data.save['gw']['id'])) # ver 2

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
                if not self.bot.running or self.bot.data.save['maintenance']['state'] or self.stoprankupdate or (self.bot.util.JST() - self.scrap_update_time > timedelta(seconds=1150)): # stop if the bot is stopping
                    self.stoprankupdate = True # send the stop signal
                    try:
                        c.execute("commit")
                        conn.close()
                    except:
                        pass
                    return "Forced stop\nMode: {}\nCount: {}/{}".format(self.scrap_mode, i, self.scrap_count)
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
            try:
                c.close()
                conn.close()
            except:
                pass
            self.stoprankupdate = True # send the stop signal if a critical error happened
            return 'gwdbbuilder() exception:\n' + self.bot.util.pexc(err)

    """gwscrap()
    Setup and manage the multithreading to scrap the ranking
    
    Parameters
    ----------
    update_time: time of this ranking interval
    
    Returns
    --------
    str: empty string if success, error message if not
    """
    async def gwscrap(self, update_time):
        try:
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
                        if gw != self.bot.data.save['gw']['id'] or ver != 2: raise Exception()
                    c.close()
                    conn.close()
                except:
                    c.close()
                    conn.close()
                    self.bot.file.rm('temp.sql')

            state = "" # return value
            self.scrap_update_time = update_time
            for n in [0, 1]: # n == 0 (crews) or 1 (players)
                current_time = self.bot.util.JST()
                if n == 0 and current_time >= self.bot.data.save['gw']['dates']["Interlude"] and current_time < self.bot.data.save['gw']['dates']["Day 1"]:
                    continue # disabled during interlude for crews

                self.scrap_mode = (n == 0)
                data = self.requestRanking(1, (0 if self.scrap_mode else 2)) # get the first page
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
                        await self.bot.sendError('updateyoutracker', ue)

            return ""
        except Exception as e:
            self.stoprankupdate = True
            return "Exception: " + self.bot.util.pexc(e)

    def x(self, row, index):
        return row['x']

    def yA(self, row, index):
        return row['q']['y'][0]

    def yB(self, row, index):
        return row['q']['y'][1]

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
            infos.append([data[0][2], data[0][d[day-2]]-data[0][d[day-2]-1]]) # name and score of the day
        c.close()
        conn.close()
        return infos

    """updateYouTracker()
    Update the YouTracker data (GW Match tracker for my crew)
    
    Parameters
    ----------
    t: time of this ranking interval
    """
    async def updateYouTracker(self, t):
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
            speed = [(infos[0][1] - newtracker['scores'][0]) / (d.seconds//60), (infos[1][1] - newtracker['scores'][1]) / (d.seconds//60)]
            if speed[0] > newtracker['top_speed'][0]: newtracker['top_speed'][0] = speed[0]
            if speed[1] > newtracker['top_speed'][1]: newtracker['top_speed'][1] = speed[1]
            newtracker['speed'] = speed
        else:
            newtracker['init'] = True
            newtracker['speed'] = None
            newtracker['top_speed'] = [0, 0]
        newtracker['names'] = [infos[0][0], infos[1][0]]
        newtracker['scores'] = [infos[0][1], infos[1][1]]
        newtracker['last'] = t
        newtracker['gwid'] = self.bot.data.save['gw']['id']
        if newtracker['speed'] is not None: # save chart data
            newtracker['plot'].append({'x': t, 'q': { 'y': [newtracker['speed'][0] / 1000000, newtracker['speed'][1] / 1000000] }})
        if len(newtracker['plot']) > 1: # generate chart
            chart = leather.Chart('Speed Chart')
            chart.add_line(newtracker['plot'], x=self.x, y=self.yA, name="(You)")
            chart.add_line(newtracker['plot'], x=self.x, y=self.yB, name="Opponent")
            chart.to_svg('chart.svg')
            cairosvg.svg2png(url="chart.svg", write_to="chart.png")
            try:
                with open("chart.png", "rb") as f:
                    df = discord.File(f)
                    message = await self.bot.send('image', file=df)
                    df.close()
                    newtracker['chart'] = message.attachments[0].url
            except:
                pass
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
                    for row in c.fetchall():
                        res[i] = {'gw':int(row[0]), 'ver':1}
                        break
                else:
                    c.execute("SELECT * FROM info")
                    for row in c.fetchall():
                        res[i] = {'gw':int(row[0]), 'ver':int(row[1])}
                        break
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
        v = self.GWDBver()
        data = [None, None]
        dbs = [self.bot.sql.get("GW_old.sql"), self.bot.sql.get("GW.sql")]
        cs = []
        for n in [0, 1]:
            cs.append(dbs[n].open())

        st = 1 if mode >= 10 else 0 # score type
        for n in [0, 1]:
            if cs[n] is not None and v[n] is not None:
                try:
                    data[n] = []
                    c = cs[n]
                    if mode == 10:
                        c.execute("SELECT * FROM crews WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 11:
                        c.execute("SELECT * FROM crews WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 12:
                        c.execute("SELECT * FROM crews WHERE id = {}".format(terms))
                    elif mode == 13:
                        c.execute("SELECT * FROM crews WHERE ranking = {}".format(terms))
                    elif mode == 0:
                        c.execute("SELECT * FROM players WHERE lower(name) LIKE '%{}%'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 1:
                        c.execute("SELECT * FROM players WHERE lower(name) LIKE '{}'".format(terms.lower().replace("'", "''").replace("%", "\\%")))
                    elif mode == 2:
                        c.execute("SELECT * FROM players WHERE id = {}".format(terms))
                    elif mode == 3:
                        c.execute("SELECT * FROM players WHERE ranking = {}".format(terms))
                    results = c.fetchall()
                    
                    for r in results:
                        s = Score(type=st, gw=v[n]['gw'], ver=v[n]['ver'])
                        if st == 0: # player
                            s.ranking = r[0]
                            s.id = r[1]
                            s.name = r[2]
                            s.current = r[3]
                        else: # crew
                            if s.ver == 2:
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
                            else:
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
                        if s.gw is None: s.gw = ''
                        data[n].append(s)
                    random.shuffle(data[n])
                except Exception as e:
                    print('searchGWDB', n, 'mode', mode, ':', self.bot.util.pexc(e))
                    self.bot.errn += 1
                    data[n] = None
                dbs[n].close()
        return data