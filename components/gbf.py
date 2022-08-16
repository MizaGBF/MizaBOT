import re
import json
import zlib
from urllib import request
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# GBF Component
# ----------------------------------------------------------------------------------------------------------------
# This component is the interface with Granblue Fantasy
#
# IMPORTANT
# Documentation will be limited on purpose to avoid possible misuses from people reading this
# ----------------------------------------------------------------------------------------------------------------

class GBF():
    def __init__(self, bot):
        self.bot = bot
        self.data = None
        self.vregex = re.compile("Game\.version = \"(\d+)\";") # for the gbf version check

    def init(self):
        self.data = self.bot.data

    def request(self, url, **options):
        try:
            data = None
            headers = {}
            if not options.get('no_base_headers', False):
                headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
                headers['Accept-Encoding'] = 'gzip, deflate'
                headers['Accept-Language'] = 'en'
                headers['Connection'] = 'close'
                headers['Host'] = 'game.granbluefantasy.jp'
                headers['Origin'] = 'https://game.granbluefantasy.jp' if self.bot.data.save['https'] else 'http://game.granbluefantasy.jp'
                headers['Referer'] = 'https://game.granbluefantasy.jp/' if self.bot.data.save['https'] else 'http://game.granbluefantasy.jp/'
            if "headers" in options: headers = headers | options["headers"]
            id = options.get('account', None)
            if id is not None:
                acc = self.get(id)
                if not options.get('force_down', False) and acc[3] == 2: return "Down"
            if options.get('check', False): ver = self.version()
            else: ver = self.data.save['gbfversion']
            host = url.split('://')[1].split('/')[0]
            if not self.bot.data.save['https'] and (host.endswith('granbluefantasy.jp') or host.endswith('granbluefantasy.akamaized.net')):
                url = url.replace('https://', 'http://')
            url = url.replace("PARAMS", "_=TS1&t=TS2&uid=ID")
            if ver == "Maintenance": 
                url = url.replace("VER/", "")
                ver = None
            elif ver is not None:
                url = url.replace("VER/", "{}/".format(ver))
            ts = int(datetime.utcnow().timestamp() * 1000)
            url = url.replace("TS1", "{}".format(ts))
            url = url.replace("TS2", "{}".format(ts+300))
            if id is not None:
                if ver is None or acc is None:
                    return "Maintenance"
                url = url.replace("ID", "{}".format(acc[0]))
                if 'Cookie' not in headers: headers['Cookie'] = acc[1]
                if 'User-Agent' not in headers: headers['User-Agent'] = acc[2]
                if 'X-Requested-With' not in headers: headers['X-Requested-With'] = 'XMLHttpRequest'
                if 'X-VERSION' not in headers: headers['X-VERSION'] = ver
            payload = options.get('payload', None)
            if payload is None: req = request.Request(url, headers=headers)
            else:
                if not options.get('no_base_headers', False) and 'Content-Type' not in headers: headers['Content-Type'] = 'application/json'
                if 'user_id' in payload:
                    match payload['user_id']:
                        case "ID": payload['user_id'] = acc[0]
                        case "SID": payload['user_id'] = str(acc[0])
                        case "IID": payload['user_id'] = int(acc[0])
                req = request.Request(url, headers=headers, data=json.dumps(payload).encode('utf-8'))
            timeout = options.get('timeout', None)
            if timeout is None or not isinstance(timeout, int): timeout = 20
            url_handle = request.urlopen(req, timeout=timeout)
            if id is not None: self.refresh(id, url_handle.info()['Set-Cookie'])
            if url_handle.info().get('Content-Type', '') != 'application/json' and options.get('expect_JSON', False): raise Exception()
            if url_handle.info().get('Content-Encoding', '') == 'gzip': data = zlib.decompress(url_handle.read(), 16+zlib.MAX_WBITS)
            else: data = url_handle.read()
            url_handle.close()
            if url_handle.info()['Content-Type'] == 'application/json': data = json.loads(data)
            return data
        except:
            try: url_handle.close()
            except: pass
            return None

    def get(self, id : int = 0):
        try: return self.data.save['gbfaccounts'][id]
        except: return None

    def add(self, uid : int, ck : str, ua : str):
        with self.data.lock:
            if 'gbfaccounts' not in self.data.save:
                self.data.save['gbfaccounts'] = []
            self.data.save['gbfaccounts'].append([uid, ck, ua, 0, 0, None])
            self.data.pending = True
        return True

    def update(self, id : int, **options):
        try:
            uid = options.pop('uid', None)
            ck = options.pop('ck', None)
            ua = options.pop('ua', None)
            with self.data.lock:
                if uid is not None:
                    self.data.save['gbfaccounts'][id][0] = uid
                    self.data.save['gbfaccounts'][id][4] = 0
                if ck is not None:
                    self.data.save['gbfaccounts'][id][1] = ck
                    self.data.save['gbfaccounts'][id][5] = None
                if ua is not None:
                    self.data.save['gbfaccounts'][id][2] = ua
                self.data.save['gbfaccounts'][id][3] = 0
                self.data.pending = True
            return True
        except:
            return False

    def remove(self, id : int):
        try:
            with self.data.lock:
                if id < 0 or id >= len(self.data.save['gbfaccounts']):
                    return False
                self.data.save['gbfaccounts'].pop(id)
                if self.bot.data.save['gbfcurrent'] >= id and self.bot.data.save['gbfcurrent'] >= 0: self.bot.data.save['gbfcurrent'] -= 1
                self.data.pending = True
            return True
        except:
            return False

    def refresh(self, id : int, ck : str):
        try:
            if ck is None: return False
            A = self.data.save['gbfaccounts'][id][1].split(';')
            B = ck.split(';')
            for c in B:
                tA = c.split('=')
                if tA[0][0] == " ": tA[0] = tA[0][1:]
                for i, v in enumerate(A):
                    tB = v.split('=')
                    if tB[0][0] == " ": tB[0] = tB[0][1:]
                    if tA[0] == tB[0]:
                        A[i] = c
                        break
            with self.data.lock:
                self.data.save['gbfaccounts'][id][1] = ";".join(A)
                self.data.save['gbfaccounts'][id][3] = 1
                self.data.save['gbfaccounts'][id][5] = self.bot.util.JST()
                self.data.pending = True
            return True
        except Exception as e:
            self.bot.doAsTask(self.bot.sendError('gbf refresh', e))
            return False

    def version(self): # retrieve the game version
        res = self.request('https://game.granbluefantasy.jp/', headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36', 'Accept-Language':'en', 'Accept-Encoding':'gzip, deflate', 'Host':'game.granbluefantasy.jp', 'Connection':'keep-alive'}, no_base_headers=True)
        if res is None: return None
        res = str(res)
        try:
            return int(self.vregex.findall(res)[0])
        except:
            if 'maintenance' in res.lower():
                return "Maintenance"
            else:
                return None

    def updateVersion(self, v): # compare version with given value, then update and return a value depending on difference
        try:
            int(v)
            if v is None:
                return 1 # unchanged because of invalid parameter
            elif self.data.save['gbfversion'] is None:
                with self.data.lock:
                    self.data.save['gbfversion'] = v
                    self.savePending = True
                return 2 # value is set
            elif self.data.save['gbfversion'] != v:
                with self.data.lock:
                    self.data.save['gbfversion'] = v
                    self.data.pending = True
                return 3 # update happened
            return 0 # unchanged
        except:
            return -1 # v isn't an integer

    def version2str(self, version_number): # convert gbf version number to its timestamp
        try: return "{0:%Y/%m/%d %H:%M} JST".format(datetime.fromtimestamp(int(version_number)) + timedelta(seconds=32400)) # JST
        except: return ""

    def isAvailable(self): # use the above to check if the game is up
        v = self.version()
        if v is None or v == "Maintenance": v = self.version() # try again in case their shitty server is lagging
        return ((v is not None) and (v != "Maintenance"))