import disnake
import asyncio
import threading
import json
import time
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# Save Component
# ----------------------------------------------------------------------------------------------------------------
# This component manages the save data file (save.json)
# It also lets you load config.json (once at startup)
# Works in tandem with the Drive component
# ----------------------------------------------------------------------------------------------------------------

class Data():
    def __init__(self, bot):
        self.bot = bot
        self.bot.drive = None
        self.config = {}
        self.save = {}
        self.saveversion = 4
        self.pending = False
        self.autosaving = False
        self.lock = threading.Lock()

    def init(self):
        pass

    """loadConfig()
    Read config.json. Only called once during boot
    
    Returns
    --------
    bool: True on success, False on failure
    """
    def loadConfig(self):
        try:
            with open('config.json') as f:
                data = json.load(f, object_pairs_hook=self.bot.util.json_deserial_dict) # deserializer here
                self.config = data
            return True
        except Exception as e:
            print('loadConfig(): {}\nCheck your \'config.json\' for the above error.'.format(self.bot.util.pexc(e)))
            return False

    """loadData()
    Read save.json.
    Assure the retrocompatibility with older save files.
    
    Returns
    --------
    bool: True on success, False on failure
    """
    def loadData(self):
        try:
            with open('save.json') as f:
                data = json.load(f, object_pairs_hook=self.bot.util.json_deserial_dict) # deserializer here
                ver = data.get('version', None)
                if ver is None:
                    raise Exception("This save file isn't compatible")
                elif ver < self.saveversion:
                    if ver == 0:
                        if 'newserver' in data:
                            newserver = data.pop('newserver', None)
                            if 'guilds' not in data:
                                data['guilds'] = {"owners": newserver.get('owners', []), "pending": newserver.get('pending', {}), "banned": newserver.get('servers', [])}
                        for id in data['reminders']:
                            for r in data['reminders'][id]:
                                if len(r) == 2:
                                    r.append("")
                        try: data['gbfdata'].pop('new_ticket', None)
                        except: pass
                        try: data['gbfdata'].pop('count', None)
                        except: pass
                    if ver <= 1:
                        data['ban'] = {}
                        for i in data['guilds']['owners']:
                            data['ban'][str(i)] = 0b1
                        data['guilds'].pop('owners', None)
                        for i in data['spark'][1]:
                            data['ban'][str(i)] = 0b10 | data['ban'].get(str(i), 0)
                        data['spark'] = data['spark'][0]
                    if ver <= 2:
                        data['banned_guilds'] = data['guilds']['banned']
                        data.pop('guilds', None)
                    if ver <= 3:
                        data['guilds'] = None
                    data['version'] = self.saveversion
                elif ver > self.saveversion:
                    raise Exception("Save file version higher than the expected version")
                with self.lock:
                    self.save = self.checkData(data)
                    self.pending = False
                return True
        except Exception as e:
            print('load(): {}'.format(self.bot.util.pexc(e)))
            return False

    """saveData()
    Write save.json.
    
    Returns
    --------
    bool: True on success, False on failure
    """
    def saveData(self): # saving (lock isn't used, use it outside!)
        try:
            with open('save.json', 'w') as outfile:
                json.dump(self.save, outfile, default=self.bot.util.json_serial) # locally first
                if not self.bot.drive.save(json.dumps(self.save, default=self.bot.util.json_serial)): # sending to the google drive
                    raise Exception("Couldn't save to google drive")
            return True
        except Exception as e:
            print('save(): {}'.format(self.bot.util.pexc(e)))
            return False

    """checkData()
    Fill the save data with missing keys, if any
    
    Parameters
    --------
    dict: Save data
    
    Returns
    --------
    dict: Updated data (not a copy)
    """
    def checkData(self, data): # used to initialize missing data or remove useless data from the save file
        expected = {
            'version':self.saveversion,
            'guilds': [],
            'banned_guilds': [],
            'gbfaccounts': [],
            'gbfcurrent': 0,
            'gbfversion': None,
            'gbfdata': {},
            'bot_maintenance': None,
            'maintenance': {"state" : False, "time" : None, "duration" : 0},
            'stream': {'time':None, 'content':[]},
            'schedule': [],
            'st': {},
            'spark': {},
            'gw': {'state':False},
            'valiant': {'state':False},
            'reminders': {},
            'permitted': {},
            'news': {},
            'extra': {},
            'gbfids': {},
            'assignablerole': {},
            'matchtracker': None,
            'pinboard': {},
            'invite': {'state':0, 'limit':50},
            'ban': {}
        }
        for k in list(data.keys()): # remove useless
            if k not in expected:
                data.pop(k)
        for k in expected: # add missing
            if k not in data:
                data[k] = expected[k]
        return data

    """autosave()
    Write save.json. Called periodically by statustask()
    The file is also sent to the google drive or to discord if it failed
    
    Parameters
    --------
    discordDump: If True, save.json will be sent to discord even on success
    """
    async def autosave(self, discordDump = False): # called when pending is true by statustask()
        if self.autosaving: return
        self.autosaving = True
        result = False
        for i in range(0, 3): # try a few times
            with self.lock:
                if self.saveData():
                    self.pending = False
                    result = True
                    break
            await asyncio.sleep(0.001)
        if not result:
            await self.bot.send('debug', embed=self.bot.util.embed(title="Failed Save", timestamp=self.bot.util.timestamp()))
            discordDump = True
        if discordDump:
            try:
                with open('save.json', 'r') as infile:
                    df = disnake.File(infile)
                    await self.bot.send('debug', 'save.json', file=df)
                    df.close()
            except:
                pass
        self.autosaving = False

    """clean_spark()
    Clean user spark data from the save data
    
    Parameters
    --------
    int: Number of cleaned sparks
    """
    def clean_spark(self): # clean up spark data
        count = 0
        c = datetime.utcnow()
        keys = list(self.bot.data.save['spark'].keys())
        for id in keys:
            if len(self.bot.data.save['spark'][id]) == 3: # backward compatibility
                with self.bot.data.lock:
                    self.bot.data.save['spark'][id].append(c)
                    self.bot.data.pending = True
            else:
                d = c - self.bot.data.save['spark'][id][3]
                if d.days >= 30:
                    with self.bot.data.lock:
                        del self.bot.data.save['spark'][id]
                        self.bot.data.pending = True
                    count += 1
        return count

    """clean_profile()
    Coroutine to clean user gbf profiles from the save data
    
    Parameters
    --------
    int: Number of cleaned profiles
    """
    async def clean_profile(self): # clean up profiles
        count = 0
        keys = list(self.bot.data.save['gbfids'].keys())
        for uid in keys:
            found = False
            for g in self.bot.guilds:
                 if await g.get_or_fetch_member(int(uid)) is not None:
                    found = True
                    break
            if not found:
                count += 1
                with self.bot.data.lock:
                    self.bot.data.save['gbfids'].pop(uid)
                    self.bot.data.pending = True
        return count

    """clean_schedule()
    Clean the gbf schedule from the save data
    
    Parameters
    --------
    bool: True if the schedule changed, False if not
    """
    def clean_schedule(self): # clean up schedule
        c = self.bot.util.JST()
        fd = c.replace(day=1, hour=12, minute=45, second=0, microsecond=0) # day of the next schedule drop, 15min after
        if fd < c:
            if fd.month == 12: fd = fd.replace(year=fd.year+1, month=1)
            else: fd = fd.replace(month=fd.month+1)
        d = fd - c
        new_schedule = []
        if self.bot.twitter.client is not None and d.days < 1: # retrieve schedule from @granblue_en if we are close to the date
            time.sleep(d.seconds) # wait until koregra to try to get the schedule
            count = 0
            while count < 5 and len(new_schedule) == 0:
                tw = self.bot.twitter.pinned('granblue_en')
                if tw is not None and tw.created_at.month != c.month:
                    txt = tw.text
                    if txt.find(" = ") != -1 and txt.find("chedule\n") != -1:
                        try:
                            s = txt.find("https://t.co/")
                            if s != -1: txt = txt[:s]
                            txt = txt.replace('\n\n', '\n')
                            txt = txt[txt.find("chedule\n")+len("chedule\n"):]
                            new_schedule = txt.replace('\n', ' = ').split(' = ')
                            while len(new_schedule) > 0 and new_schedule[0] == '': new_schedule.pop(0)
                        except:
                            pass
                        break
                else:
                    count += 1
                    time.sleep(2000)
        else: # else, just clean up old entries
            for i in range(0, ((len(self.bot.data.save['schedule'])//2)*2), 2):
                try:
                    date = self.bot.data.save['schedule'][i].replace(" ", "").split("-")[-1].split("/")
                    x = c.replace(month=int(date[0]), day=int(date[1])+1, microsecond=0)
                    if c - x > timedelta(days=160):
                        x = x.replace(year=x.year+1)
                    if c >= x:
                        continue
                except:
                    pass
                new_schedule.append(self.bot.data.save['schedule'][i])
                new_schedule.append(self.bot.data.save['schedule'][i+1])
        if len(new_schedule) != 0 and len(new_schedule) != len(self.bot.data.save['schedule']):
            with self.bot.data.lock:
                self.bot.data.save['schedule'] = new_schedule
                self.bot.data.pending = True
            return True
        return False