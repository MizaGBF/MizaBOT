import sqlite3
import threading

# ----------------------------------------------------------------------------------------------------------------
# SQL Component
# ----------------------------------------------------------------------------------------------------------------
# Manage Database objects
# Database objects are simple wrapper over a sqlite3 connection and cursor with a multithreading protection
# It's made in a way to simplify the way it was used in the previous bot versions
# ----------------------------------------------------------------------------------------------------------------

class Database():
    def __init__(self, filename):
        self.filename = filename
        self.conn = None
        self.cursor = None
        self.lock = threading.Lock()

    def open(self):
        try:
            self.lock.acquire()
            if self.isOpen():
                self.close()
                self.lock.acquire()
            self.conn = sqlite3.connect(self.filename)
            self.cursor = self.conn.cursor()
            return self.cursor
        except:
            try: self.lock.release()
            except: pass
            return None

    def close(self):
        self.conn.close()
        self.conn = None
        self.cursor = None
        self.lock.release()

    def isOpen(self):
        return (self.conn is not None)

class SQL():
    def __init__(self, bot):
        self.bot = bot
        self.file = None
        self.db = {}
        self.lock = threading.Lock()

    def init(self):
        self.file = self.bot.file
        self.db = {}

    def make(self, filename): # make a new entry, delete existing local file
        self.remove(filename) # remove from db
        self.file.rm(filename) # remove local file
        return self.add(filename) # add and return clean entry

    def remove(self, filename):
        if filename in self.db:
            with self.lock:
                db = self.db[filename]
                with db.lock:
                    self.db.pop(filename)
                    db.loaded = False

    def add(self, filename):
        with self.lock:
            self.db[filename] = Database(filename)
        return self.get(filename)

    def get(self, filename):
        return self.db.get(filename, None)