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

    """open()
    Lock and connect to the file
    
    Returns
    --------
    unknown: sqlite3 cursor if success, None if error
    """
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

    """close()
    Unloack and release the file
    """
    def close(self):
        self.cursor.close()
        self.conn.close()
        self.conn = None
        self.cursor = None
        self.lock.release()

    """isOpen()
    Check if the file is in use
    
    Returns
    --------
    bool: Return True if it's being used, False if not
    """
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

    """make()
    A new SQL file is created with the name and is added to the cache.

    Parameters
    ----------
    filename: SQL file name
    
    Returns
    --------
    Database: The new Database object
    """
    def make(self, filename): # make a new entry, delete existing local file
        self.remove(filename) # remove from db
        self.file.rm(filename) # remove local file
        return self.add(filename) # add and return clean entry

    """remove()
    Remove the Database object from the cache
    
    Parameters
    ----------
    filename: SQL file name
    """
    def remove(self, filename):
        if filename in self.db:
            with self.lock:
                db = self.db[filename]
                with db.lock:
                    self.db.pop(filename)
                    db.loaded = False

    """add()
    Add a new Database object to the cache (Remove the previous one if any).
    The file must exist to avoid future errors
    
    Parameters
    ----------
    filename: SQL file name
    
    Returns
    --------
    Database: The new Database object
    """
    def add(self, filename):
        with self.lock:
            self.db[filename] = Database(filename)
        return self.get(filename)

    """get()
    Retrieve a Database object from the cache
    
    Parameters
    ----------
    filename: SQL file name
    
    Returns
    --------
    Database: The Database object. None if it doesn't exist
    """
    def get(self, filename):
        return self.db.get(filename, None)