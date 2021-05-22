import os
from shutil import copyfile

# ----------------------------------------------------------------------------------------------------------------
# File Component
# ----------------------------------------------------------------------------------------------------------------
# Let your copy or delete local files
# ----------------------------------------------------------------------------------------------------------------

class File():
    def __init__(self, bot):
        self.bot = bot

    def init(self):
        pass

    def rm(self, filename):
        try: os.remove(filename)
        except: pass

    def cpy(self, src, dst):
        try: copyfile(src, dst)
        except: pass